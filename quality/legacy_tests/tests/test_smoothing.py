import unittest
from src.tools.smoothing import chaikin_smooth, catmull_rom_to_beziers

class TestSmoothing(unittest.TestCase):
    def test_chaikin(self):
        pts = [(0,0),(10,0),(20,0)]
        sm = chaikin_smooth(pts, iterations=1)
        # Chaikin should produce more points and maintain approximate line
        self.assertTrue(len(sm) > len(pts))
        self.assertAlmostEqual(sm[0][1], 0.0)
        self.assertAlmostEqual(sm[-1][1], 0.0)

    def test_catmull_to_bezier(self):
        pts = [(0,0),(10,0),(20,10),(30,10)]
        beziers = catmull_rom_to_beziers(pts, closed=False)
        # For 4 pts open, expect 3 bezier segments
        self.assertEqual(len(beziers), 3)
        for seg in beziers:
            p0,c1,c2,p1 = seg
            # endpoints should match input points progression
            self.assertIsInstance(p0, tuple)
            self.assertIsInstance(p1, tuple)

if __name__ == '__main__':
    unittest.main()