# src/core/view_processor.py
import cv2
import numpy as np
from PIL import Image as PILImage
from PySide6.QtGui import QImage

from src.core.logger import logger


def has_cuda():
    """Check if CUDA is available via OpenCV."""
    try:
        return cv2.cuda.getCudaEnabledDeviceCount() > 0
    except AttributeError:
        # OpenCV might not have CUDA support
        return False
    except Exception:
        return False


# Check for GPU availability
try:
    import cupy as cp
    import cupyx.scipy.ndimage as cupy_ndimage

    # Verifica se realmente temos uma GPU acessível pelo CuPy
    if cp.cuda.runtime.getDeviceCount() > 0:
        HAS_GPU = True
        ndimage = cupy_ndimage
        logger.info("CUDA GPU acceleration enabled via CuPy.")
    else:
        HAS_GPU = False
        cp = None
        ndimage = None
except ImportError:
    cp = None
    ndimage = None
    HAS_GPU = False
    logger.warning("CuPy not found. Fallback to CPU processing.")
except Exception as e:
    HAS_GPU = False
    cp = None
    ndimage = None
    logger.warning(f"Error initializing CuPy: {e}")


class ViewProcessor:
    """
    Processador gráfico híbrido (CPU/GPU).
    Usa aceleração CUDA se disponível para filtros pesados.
    """

    @staticmethod
    def to_qimage(cv_img):
        """Converte OpenCV BGR/Gray para QImage Otimizada."""
        if cv_img is None:
            return None

        # Garante que os dados estejam na CPU e contíguos antes de criar QImage
        if HAS_GPU and cp is not None and isinstance(cv_img, cp.ndarray):
            try:
                cv_img = cp.asnumpy(cv_img)
            except Exception:
                # Fallback em caso de erro de memória na GPU
                return None

        if isinstance(cv_img, PILImage.Image):
            if cv_img.mode == "L":
                cv_img = np.asarray(cv_img)
            elif cv_img.mode == "RGB":
                cv_img = cv2.cvtColor(np.asarray(cv_img), cv2.COLOR_RGB2BGR)
            else:
                rgba = np.asarray(cv_img.convert("RGBA"))
                cv_img = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)

        if not isinstance(cv_img, np.ndarray):
            logger.error(
                "Unsupported image type for Qt conversion: %s", type(cv_img).__name__
            )
            return None

        if cv_img.ndim not in (2, 3):
            logger.error(
                "Unsupported image dimensions for Qt conversion: %s", cv_img.ndim
            )
            return None
        if cv_img.ndim == 3 and cv_img.shape[2] not in (3, 4):
            logger.error(
                "Unsupported channel count for Qt conversion: %s", cv_img.shape[2]
            )
            return None
        if any(dimension <= 0 for dimension in cv_img.shape[:2]):
            logger.error("Empty image cannot be converted to QImage")
            return None

        # Ensure contiguous array for Qt
        if not cv_img.flags["C_CONTIGUOUS"]:
            cv_img = np.ascontiguousarray(cv_img)

        height, width = cv_img.shape[:2]

        if cv_img.ndim == 2:
            return QImage(
                cv_img.data,
                width,
                height,
                cv_img.strides[0],
                QImage.Format.Format_Grayscale8,
            ).copy()

        elif cv_img.ndim == 3:
            ch = cv_img.shape[2]
            if ch == 3:
                # BGR -> RGB
                rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                return QImage(
                    rgb.data, width, height, rgb.strides[0], QImage.Format.Format_RGB888
                ).copy()
            elif ch == 4:
                # BGRA -> RGBA
                rgba = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
                return QImage(
                    rgba.data,
                    width,
                    height,
                    rgba.strides[0],
                    QImage.Format.Format_RGBA8888,
                ).copy()

        return None

    @staticmethod
    def _gpu_generate_xray(image_array: np.ndarray, mode: int = 1):
        """Pipeline de processamento na GPU (CUDA) com diferentes modos."""
        # 1. Upload CPU -> GPU
        if image_array.ndim == 3:
            # OpenCV CPU conversion is fast enough and simpler
            gray_cpu = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            gpu_img = cp.asarray(gray_cpu)
        else:
            gpu_img = cp.asarray(image_array)

        if mode == 1:
            # Modo 1: Sobel (gradiente)
            # 2. Gaussian Blur
            gpu_blurred = ndimage.gaussian_filter(gpu_img, sigma=1.0)

            # 3. Sobel X e Y (Float32 para precisão)
            grad_x = ndimage.sobel(gpu_blurred, axis=1)
            grad_y = ndimage.sobel(gpu_blurred, axis=0)

            # 4. Magnitude
            abs_grad_x = cp.abs(grad_x)
            abs_grad_y = cp.abs(grad_y)

            # Normaliza para 0-255
            max_val = cp.max(cp.maximum(abs_grad_x, abs_grad_y))
            if max_val > 0:
                scale_factor = 255.0 / max_val
                abs_grad_x = (abs_grad_x * scale_factor).astype(cp.uint8)
                abs_grad_y = (abs_grad_y * scale_factor).astype(cp.uint8)
            else:
                abs_grad_x = abs_grad_x.astype(cp.uint8)
                abs_grad_y = abs_grad_y.astype(cp.uint8)

            # Magnitude combinada para canal Azul
            magnitude = (
                abs_grad_x.astype(cp.float32) * 0.5
                + abs_grad_y.astype(cp.float32) * 0.5
            ).astype(cp.uint8)

            # 5. Download GPU -> CPU para Merge
            r = cp.asnumpy(abs_grad_x)
            g = cp.asnumpy(abs_grad_y)
            b = cp.asnumpy(magnitude)

        elif mode == 2:
            # Modo 2: Canny-like (bordas finas)
            # Gaussian blur
            gpu_blurred = ndimage.gaussian_filter(gpu_img, sigma=1.0)

            # Sobel gradients
            grad_x = ndimage.sobel(gpu_blurred, axis=1)
            grad_y = ndimage.sobel(gpu_blurred, axis=0)

            # Magnitude
            magnitude = cp.sqrt(grad_x**2 + grad_y**2)

            # Non-maximum suppression approximation
            max_val = cp.max(magnitude)
            if max_val > 0:
                magnitude = (magnitude / max_val * 255).astype(cp.uint8)

            # Thresholding
            high_thresh = 100
            low_thresh = 50
            strong_edges = magnitude > high_thresh
            weak_edges = (magnitude >= low_thresh) & (magnitude <= high_thresh)

            # Hysteresis (simplified)
            r = g = b = ((strong_edges | weak_edges) * 255).astype(cp.uint8)

        elif mode == 3:
            # Modo 3: Laplacian (detecção de bordas de segunda ordem)
            # Gaussian blur first
            gpu_blurred = ndimage.gaussian_filter(gpu_img, sigma=1.0)

            # Laplacian
            laplacian = ndimage.laplace(gpu_blurred)

            # Absolute value and normalize
            abs_laplacian = cp.abs(laplacian)
            max_val = cp.max(abs_laplacian)
            if max_val > 0:
                abs_laplacian = (abs_laplacian / max_val * 255).astype(cp.uint8)

            # Invert for better visualization (dark edges on light background)
            abs_laplacian = 255 - abs_laplacian

            r = g = b = cp.asnumpy(abs_laplacian)

        else:
            # Fallback to mode 1
            r = g = b = cp.asnumpy(gpu_img)

        return cv2.merge([r, g, b])

    @staticmethod
    def _cpu_generate_xray(image_array: np.ndarray, mode: int = 1):
        """Pipeline de processamento na CPU (Fallback) com diferentes modos."""
        if image_array.ndim == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_array

        if mode == 1:
            # Modo 1: Sobel (gradiente)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)

            # Sobel 16S para evitar overflow
            grad_x = cv2.Sobel(blurred, cv2.CV_16S, 1, 0, ksize=3)
            grad_y = cv2.Sobel(blurred, cv2.CV_16S, 0, 1, ksize=3)

            abs_grad_x = cv2.convertScaleAbs(grad_x)
            abs_grad_y = cv2.convertScaleAbs(grad_y)

            magnitude = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

            return cv2.merge([abs_grad_x, abs_grad_y, magnitude])

        elif mode == 2:
            # Modo 2: Canny-like (bordas finas)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)

            # Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)

            return cv2.merge([edges, edges, edges])

        elif mode == 3:
            # Modo 3: Laplacian (detecção de bordas de segunda ordem)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)

            # Laplacian
            laplacian = cv2.Laplacian(blurred, cv2.CV_64F, ksize=3)
            abs_laplacian = cv2.convertScaleAbs(laplacian)

            # Invert for better visualization
            abs_laplacian = 255 - abs_laplacian

            return cv2.merge([abs_laplacian, abs_laplacian, abs_laplacian])

        else:
            # Fallback
            return cv2.merge([gray, gray, gray])

    @staticmethod
    def generate_xray(image_array: np.ndarray, mode: int = 1) -> QImage:
        """
        Gera visualização 'Raio-X' decidindo automaticamente entre CPU e GPU.
        mode: 1=Sobel, 2=Canny, 3=Laplacian
        """
        if image_array is None:
            return None

        xray_cv = None

        if HAS_GPU:
            try:
                xray_cv = ViewProcessor._gpu_generate_xray(image_array, mode)
            except Exception as e:
                logger.error(f"GPU processing failed, falling back to CPU: {e}")
                # Fallback imediato
                try:
                    xray_cv = ViewProcessor._cpu_generate_xray(image_array, mode)
                except Exception:
                    pass
        else:
            xray_cv = ViewProcessor._cpu_generate_xray(image_array, mode)

        return ViewProcessor.to_qimage(xray_cv)
