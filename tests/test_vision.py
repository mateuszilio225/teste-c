# Python 3.11+ | tests/test_vision.py | portable | synthetic image detection
from pathlib import Path
import sys
import unittest
import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vision import BarProfile, detect_bars, nearest_bar


class VisionTests(unittest.TestCase):
    def setUp(self):
        self.color = (30, 40, 220)
        self.full = np.full((5, 60, 3), self.color, np.uint8)
        self.profile = BarProfile.from_image(self.full)

    def frame(self, fill=30, width=60):
        image = np.full((200, 300, 3), (80, 95, 75), np.uint8)
        image[50:55, 100:100+width] = (15, 15, 15)
        image[50:55, 100:100+fill] = self.color
        return image

    def test_half_health_bar_and_coordinates(self):
        bar = nearest_bar(self.frame(), self.profile, (130, 52), 50)
        self.assertIsNotNone(bar)
        self.assertAlmostEqual(bar["fraction"], .5, delta=.03)
        self.assertEqual((bar["x"], bar["y"]), (100, 50))

    def test_full_health_bar(self):
        bar = nearest_bar(self.frame(fill=60), self.profile, (130, 52), 50)
        self.assertAlmostEqual(bar["fraction"], 1)

    def test_small_hp_ticks_are_closed(self):
        image = self.frame(fill=30)
        image[50:55, 110:111] = 0
        bar = nearest_bar(image, self.profile, (130, 52), 50)
        self.assertIsNotNone(bar)
        self.assertAlmostEqual(bar["fraction"], .5, delta=.03)

    def test_cursor_outside_radius_does_not_select(self):
        self.assertIsNone(nearest_bar(self.frame(), self.profile, (200, 150), 20))

    def test_missing_bar_is_not_zero_health(self):
        self.assertEqual(detect_bars(np.zeros((200, 300, 3), np.uint8), self.profile), [])

    def test_long_colored_bar_is_rejected(self):
        self.assertEqual(detect_bars(self.frame(fill=110, width=110), self.profile), [])

    def test_calibration_requires_saturated_full_color(self):
        with self.assertRaises(ValueError):
            BarProfile.from_image(np.zeros((5, 60, 3), np.uint8))

    def test_wrong_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            BarProfile.from_image(np.full((80, 60, 3), self.color, np.uint8))


if __name__ == "__main__":
    unittest.main()
