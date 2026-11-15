# Python 3.11+ | tests/test_calibration.py | portable | calibration proposals and persistence
import base64
import copy
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from calibration import (pending_steps, pending_message, apply_capture, monitor_resolution,
                         auto_calibrate, range_ellipse, full_bars)
from demo import DemoScene
from engine import DEFAULTS


class CalibrationTests(unittest.TestCase):
    def config(self):
        return dict(DEFAULTS, calibration=copy.deepcopy(DemoScene().calibration),
                    generation=0, confirmed=True, quickcast=True, minion_hp=477)

    def test_first_run_explains_monitor_and_all_missing_steps(self):
        cfg = dict(DEFAULTS, calibration={})
        message = pending_message(cfg)
        self.assertIn('Monitor e resolução', message)
        self.assertIn('1. Área útil do campo', message)
        self.assertNotIn('Calibração ausente: resolution', message)
        self.assertIn('self', pending_steps(cfg))

    def test_complete_calibration_has_no_missing_step(self):
        self.assertEqual(pending_steps(self.config()), [])
        app.validate_calibration(self.config())

    def test_disabled_features_do_not_require_their_templates(self):
        cfg = self.config()
        cfg.update(combo=False, dodge=False)
        for k in ('enemy', 'Q', 'W', 'projectiles'):
            cfg['calibration'].pop(k, None)
        self.assertEqual(pending_steps(cfg), [])

    def test_unknown_and_invalid_resolution_not_accepted(self):
        cfg = self.config()
        for res in (None, [], [0, 0, 0, 0], [float('nan'), 1080, 0, 0]):
            cfg['calibration']['resolution'] = res
            self.assertIn('resolution', pending_steps(cfg))

    def test_monitor_values_come_from_capture_metadata(self):
        self.assertEqual(monitor_resolution(dict(width=1366, height=768, left=-1366, top=0)),
                         [1366, 768, -1366, 0])
        with self.assertRaises(ValueError):
            monitor_resolution(dict(width=0, height=768, left=0, top=0))

    def test_committed_capture_binds_resolution_without_mutating_original(self):
        original = {}
        result = apply_capture(original, 'viewport', [5, 5, 1000, 600], [1366, 768, 0, 0])
        self.assertEqual(original, {})
        self.assertEqual(result['resolution'], [1366, 768, 0, 0])

    def test_resolution_change_invalidates_stale_templates(self):
        old = self.config()['calibration']
        result = apply_capture(old, 'viewport', [5, 5, 1900, 800], [1920, 1080, 0, 0])
        self.assertNotIn('self', result)
        self.assertNotIn('Q', result)
        self.assertNotIn('projectiles', result)
        self.assertIn('self', old)

    def test_same_resolution_preserves_other_completed_steps(self):
        old = self.config()['calibration']
        result = apply_capture(old, 'viewport', [10, 10, 1000, 600], old['resolution'])
        self.assertEqual(result['self'], old['self'])

    def test_arming_rejects_actual_monitor_change(self):
        with self.assertRaisesRegex(ValueError, 'monitor/resolução mudou'):
            app.validate_calibration(self.config(), [1920, 1080, 0, 0])

    def test_capture_persists_independently_of_unfinished_ui_fields(self):
        obj = app.Application.__new__(app.Application)
        obj.config = dict(DEFAULTS, calibration={}, generation=0)
        obj.demo, obj.lock = False, threading.Lock()
        # commit_calibration must not consult/parse these unrelated UI edits.
        obj.vars = {'minion_hp': 'unfinished'}
        with tempfile.TemporaryDirectory() as folder, patch.object(app, 'DATA', Path(folder)):
            obj.commit_calibration('viewport', [5, 5, 1000, 600], [1366, 768, 0, 0])
            saved = json.loads((Path(folder)/'config.json').read_text())
            self.assertEqual(saved['calibration']['resolution'], [1366, 768, 0, 0])
            self.assertEqual(saved['calibration']['viewport'], [5, 5, 1000, 600])

    def test_startup_monitor_registration_does_not_invent_geometry(self):
        obj = app.Application.__new__(app.Application)
        obj.config = dict(DEFAULTS, calibration={}, generation=0)
        obj.demo, obj.lock = False, threading.Lock()
        class Capture:
            monitors = [None, dict(width=1920, height=1080, left=0, top=0)]
            def __enter__(self): return self
            def __exit__(self, *args): pass
        with tempfile.TemporaryDirectory() as folder, patch.object(app, 'DATA', Path(folder)), patch('app.mss.mss', return_value=Capture()):
            obj.detect_monitor()
            self.assertEqual(obj.config['calibration'], {'resolution': [1920, 1080, 0, 0]})
            self.assertIn('geometry', pending_steps(obj.config))


class AutomaticDetectionTests(unittest.TestCase):
    def setUp(self):
        self.icons = app.GAME_ICONS
        self.active = dict(championStats=dict(currentHealth=1500, maxHealth=1500, attackRange=550))

    def scene(self):
        rng = np.random.default_rng(12)
        gray = rng.integers(80, 100, (1000, 1400), dtype=np.uint8)
        frame = np.repeat(gray[:, :, None], 3, axis=2)
        cv2.ellipse(frame, (700, 390), (220, 145), 0, 0, 360, (255, 210, 40), 2)
        for x, y, w, h, color in [(650, 330, 100, 6, (35, 220, 35)),
                                  (950, 350, 120, 6, (30, 40, 220)),
                                  (950, 550, 60, 4, (30, 40, 220))]:
            frame[y-2:y, x:x+w] = 15
            frame[y:y+h, x:x+w] = color
        for key, x in [('Q', 600), ('W', 652)]:
            image = cv2.imdecode(np.frombuffer(base64.b64decode(self.icons[key]), np.uint8), cv2.IMREAD_COLOR)[3:-3, 3:-3]
            frame[910:954, x:x+44] = cv2.resize(image, (44, 44), interpolation=cv2.INTER_AREA)
        return frame

    def test_measured_ring_icons_and_player_are_proposed(self):
        values, assets, notes = auto_calibrate(self.scene(), self.active, self.icons)
        self.assertIn('Q', values)
        self.assertIn('W', values)
        self.assertIn('self', values)
        self.assertIn('projection', values)
        self.assertAlmostEqual(values['projection'][0], .4, delta=.015)
        self.assertAlmostEqual(values['center'][0], 700, delta=3)
        self.assertEqual(len(assets), 2)

    def test_blank_image_leaves_steps_missing(self):
        values, assets, notes = auto_calibrate(np.zeros((1000, 1400, 3), np.uint8), self.active, self.icons)
        self.assertEqual(values, {})
        self.assertEqual(assets, {})
        self.assertTrue(notes)

    def test_partial_player_health_does_not_guess_full_bar_width(self):
        self.active['championStats']['currentHealth'] = 700
        values, assets, notes = auto_calibrate(self.scene(), self.active, self.icons)
        self.assertNotIn('self', values)
        self.assertNotIn('projection', values)
        self.assertTrue(any('vida cheia' in n for n in notes))

    def test_no_ring_does_not_guess_player_feet(self):
        frame = self.scene()
        cv2.ellipse(frame, (700, 390), (220, 145), 0, 0, 360, (90, 90, 90), 8)
        values, _, notes = auto_calibrate(frame, self.active, self.icons)
        self.assertNotIn('self', values)
        self.assertNotIn('projection', values)

    def test_minion_body_and_projectile_profiles_not_invented(self):
        values, _, _ = auto_calibrate(self.scene(), self.active, self.icons)
        self.assertNotIn('minion', values)
        self.assertNotIn('projectiles', values)


if __name__ == '__main__':
    unittest.main()
