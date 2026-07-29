import unittest
import tempfile
import os
from PIL import Image
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

class TestExportPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up headless Qt application
        cls.app = QCoreApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def test_export_preview_headless(self):
        """Test headless preview export."""
        from src.ui.export_preview import export_preview_headless

        # Create test image
        image = Image.new('RGBA', (100, 100), (255, 0, 0, 255))
        metadata = {
            'id': 'test_sprite',
            'rect': {'x': 0, 'y': 0, 'w': 100, 'h': 100},
            'pivot': [50.0, 50.0]
        }

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = tmp.name

        try:
            export_preview_headless(image, metadata, output_path)
            self.assertTrue(os.path.exists(output_path))
            # Check file is valid PNG
            with Image.open(output_path) as img:
                self.assertEqual(img.size, (100, 100))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_export_preview_dialog_headless(self):
        """Test dialog instantiation in headless mode (offscreen)."""
        from src.ui.export_preview import ExportPreviewDialog

        # Create test data
        image = Image.new('RGBA', (50, 50), (0, 255, 0, 255))
        metadata = {
            'id': 'test_sprite',
            'rect': {'x': 10, 'y': 10, 'w': 50, 'h': 50},
            'pivot': [25.0, 25.0]
        }

        # Create dialog in headless mode
        dialog = ExportPreviewDialog(image, metadata)
        self.assertIsNotNone(dialog)

        # Test that UI elements are created
        self.assertIsNotNone(dialog.preview_label)
        self.assertIsNotNone(dialog.zoom_slider)
        self.assertIsNotNone(dialog.metadata_label)

        # Test metadata display
        metadata_text = dialog.metadata_label.text()
        self.assertIn('test_sprite', metadata_text)
        self.assertIn('w=50', metadata_text)
        self.assertIn('h=50', metadata_text)

        # Clean up
        dialog.close()

if __name__ == '__main__':
    unittest.main()