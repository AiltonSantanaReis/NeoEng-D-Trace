# src/core/view_processor.py
import cv2
import numpy as np

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
        from src.ui.image_conversion import to_qimage

        return to_qimage(cv_img, has_gpu=HAS_GPU, cupy_module=cp)

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
    def generate_xray_array(image_array: np.ndarray, mode: int = 1):
        if image_array is None:
            return None

        xray_cv = None
        if HAS_GPU:
            try:
                xray_cv = ViewProcessor._gpu_generate_xray(image_array, mode)
            except Exception as exc:
                logger.error("GPU processing failed, falling back to CPU: %s", exc)
                try:
                    xray_cv = ViewProcessor._cpu_generate_xray(image_array, mode)
                except Exception:
                    pass
        else:
            xray_cv = ViewProcessor._cpu_generate_xray(image_array, mode)
        return xray_cv

    @staticmethod
    def generate_xray(image_array: np.ndarray, mode: int = 1):
        return ViewProcessor.to_qimage(
            ViewProcessor.generate_xray_array(image_array, mode)
        )
