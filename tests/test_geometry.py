# Python 3.11+ | tests/test_geometry.py | portable | intercept and reachable dodge regressions
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from geometry import (Projection, MotionTracker, Threat, intercept, blocked_segment,
                      minimal_dodge, trajectory_clear, length)


class GeometryTests(unittest.TestCase):
    def test_stationary_intercept_includes_windup(self):
        point, t = intercept((1000, 0), (0, 0), 2000, .25)
        self.assertEqual(point, (1000, 0))
        self.assertAlmostEqual(t, .75)

    def test_perpendicular_target_is_led(self):
        point, t = intercept((900, 0), (0, 350), 2000, .25)
        self.assertAlmostEqual(point[1], 350*t)
        self.assertGreater(point[1], 200)
        self.assertAlmostEqual(length(point)/2000+.25, t)

    def test_faster_receding_target_has_no_intercept(self):
        self.assertIsNone(intercept((500, 0), (2500, 0), 2000, .25))

    def test_projected_axes_round_trip(self):
        p = Projection(.4, .28)
        u = p.units(p.pixels((1000, -200)))
        self.assertAlmostEqual(u[0], 1000)
        self.assertAlmostEqual(u[1], -200)

    def test_q_blocked_by_minion_between_caster_and_target(self):
        self.assertTrue(blocked_segment((1000, 0), [(500, 20)]))
        self.assertFalse(blocked_segment((1000, 0), [(500, 200)]))
        self.assertFalse(blocked_segment((1000, 0), [(1200, 0)]))

    def test_minimal_dodge_is_within_limit_and_reachable(self):
        threats = [Threat((-500, 0), (1000, 0), 25)]
        goal = minimal_dodge(threats, (0, 0), 350, max_step=140, body_radius=65)
        self.assertIsNotNone(goal)
        self.assertLessEqual(length(goal), 140.001)
        self.assertTrue(trajectory_clear(goal, threats, (0, 0), 350, .06, .6, 65))

    def test_small_limit_does_not_claim_impossible_dodge(self):
        self.assertIsNone(minimal_dodge([Threat((-500, 0), (1000, 0), 25)],
                                        (0, 0), 350, max_step=20, body_radius=65))

    def test_away_trajectory_needs_no_dodge(self):
        self.assertIsNone(minimal_dodge([Threat((-500, 0), (-1000, 0), 25)], (0, 0), 350))

    def test_allowed_area_can_block_destinations(self):
        self.assertIsNone(minimal_dodge([Threat((-500, 0), (1000, 0), 25)], (0, 0),
                                        350, allowed=lambda _g: False))

    def test_camera_motion_is_removed_from_target_velocity(self):
        tracker = MotionTracker()
        tracker.update([(100, 100)], 10)
        result = tracker.update([(96, 100)], 10.04, camera_shift=(-4, 0))
        obs = next(iter(result.values()))
        self.assertAlmostEqual(length(obs['velocity']), 0)

    def test_target_disappears_no_extrapolated_cast_target(self):
        tracker = MotionTracker()
        tracker.update([(100, 100)], 10)
        self.assertEqual(tracker.update([], 10.04), {})

    def test_long_gap_resets_motion_confidence(self):
        tracker = MotionTracker()
        tracker.update([(100, 100)], 10)
        tracker.update([(102, 100)], 10.04)
        result = tracker.update([(103, 100)], 11)
        self.assertEqual(next(iter(result.values()))['samples'], 1)


if __name__ == '__main__':
    unittest.main()
