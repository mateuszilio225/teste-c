# Python 3.11+ | tests/test_engine.py | portable | synthetic observations and action gates
import copy
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch
import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from demo import DemoScene
from engine import DEFAULTS, Engine, live_valid
from live import Feed
from perception import icon_ready

RULES = json.loads((Path(__file__).resolve().parents[1]/'rules.json').read_text())


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.scene = DemoScene()
        self.cfg = dict(DEFAULTS, calibration=copy.deepcopy(self.scene.calibration),
                        confirmed=True, quickcast=True, dodge=False, minion_hp=100)
        self.data = Feed(demo=True).read()[0]
        self.engine = Engine(RULES)

    def run_frames(self, frame=None, space=True, farm=False, cursor=(800, 350), count=15):
        actions = []
        frame = self.scene.frame(.1) if frame is None else frame
        for i in range(count):
            now = 10+i*.05
            action = self.engine.step(frame.copy(), self.data, self.cfg, self.scene.templates,
                                      cursor, space, farm, now)
            if action:
                actions.append(action)
                self.engine.mark_sent(action, now, self.data['activePlayer'], self.cfg)
        return actions

    def test_w_then_q_on_in_range_target(self):
        actions = self.run_frames()
        self.assertEqual([a.spell for a in actions], ['W', 'Q'])
        self.assertTrue(all(abs(a.point[0]-800) < 2 for a in actions))

    def test_out_of_range_target_not_cast_on(self):
        self.cfg['calibration']['projection'] = [.2, .28]
        self.assertEqual(self.run_frames(), [])

    def test_blocking_minion_prevents_q_and_followup_w(self):
        frame = self.scene.frame(.1)
        frame[315:319, 620:680] = (15, 15, 15)
        frame[315:319, 620:650] = (30, 40, 220)
        self.assertEqual(self.run_frames(frame), [])

    def test_missing_player_prevents_all_actions(self):
        frame = self.scene.frame(.1)
        frame[300:306, 400:500] = 15
        self.assertEqual(self.run_frames(frame), [])

    def test_cooldown_icons_prevent_cast_even_if_local_clock_ready(self):
        frame = self.scene.frame(.1)
        for key in ('Q', 'W'):
            x, y, w, h = self.cfg['calibration'][key]['rect']
            frame[y:y+h, x:x+w] = frame[y:y+h, x:x+w]//4
        self.assertEqual(self.run_frames(frame), [])

    def test_no_hold_key_no_input(self):
        self.assertEqual(self.run_frames(space=False), [])

    def test_insufficient_mana_no_cast(self):
        self.data['activePlayer']['championStats']['resourceValue'] = 0
        self.assertEqual(self.run_frames(), [])

    def test_farm_x_generates_aa_only_in_range(self):
        frame = self.scene.frame(.1)
        frame[365:369, 520:580] = (15, 15, 15)
        frame[365:369, 520:544] = (30, 40, 220)
        actions = self.run_frames(frame, space=False, farm=True, cursor=(550, 400))
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].kind, 'farm')
        self.assertEqual(actions[0].hold_key, ord('X'))

    def test_farm_out_of_range_does_not_walk_after_minion(self):
        self.assertEqual(self.run_frames(space=False, farm=True, cursor=(650, 445)), [])

    def test_no_patch_confirmation_no_action(self):
        self.cfg['confirmed'] = False
        self.assertEqual(self.run_frames(), [])

    def test_visible_icon_ready_and_dark_icon_not_ready(self):
        frame = self.scene.frame(.1)
        hud = self.cfg['calibration']['Q']
        self.assertTrue(icon_ready(frame, hud, self.scene.templates['demo-q']))
        self.assertFalse(icon_ready(frame//2, hud, self.scene.templates['demo-q']))

    def test_registered_incoming_projectile_triggers_bounded_dodge(self):
        self.cfg.update(combo=False, dodge=True, max_step=180)
        actions = []
        for i in range(12):
            now = 10+i*.04
            action = self.engine.step(self.scene.frame(.4+i*.04), self.data, self.cfg,
                self.scene.templates, (800, 350), True, False, now)
            if action:
                actions.append(action)
                self.engine.mark_sent(action, now, self.data['activePlayer'], self.cfg)
        self.assertTrue(any(a.kind == 'dodge' for a in actions))
        for a in actions:
            dx = (a.point[0]-450)/.4
            dy = (a.point[1]-350)/.28
            self.assertLessEqual((dx*dx+dy*dy)**.5, 180.001)

    def test_unregistered_projectile_has_no_dodge_claim(self):
        self.cfg.update(combo=False, dodge=True)
        self.cfg['calibration']['projectiles'] = []
        self.assertEqual(self.run_frames(), [])

    def test_data_age_and_wrong_champion_block_runtime(self):
        self.assertTrue(live_valid(self.data, .5))
        self.assertFalse(live_valid(self.data, 2))
        self.data['allPlayers'][0]['championName'] = 'Ahri'
        self.assertFalse(live_valid(self.data, .1))

    def test_dead_player_blocks_runtime(self):
        self.data['allPlayers'][0]['isDead'] = True
        self.assertFalse(live_valid(self.data, .1))

    def test_input_guard_blocks_disarm_release_stop_and_stale_frame(self):
        obj = app.Application.__new__(app.Application)
        obj.armed = threading.Event()
        obj.calibrating = False
        obj.feed = Feed(demo=True)
        class Keys:
            emergency = False
            space = True
            def held(self, key):
                return self.emergency if key == 0x79 else self.space
        obj.inputs = Keys()
        self.assertFalse(obj.can_act(0x20, time.monotonic()))
        obj.armed.set()
        self.assertTrue(obj.can_act(0x20, time.monotonic()))
        self.assertFalse(obj.can_act(0x20, time.monotonic()-1))
        obj.inputs.space = False
        self.assertFalse(obj.can_act(0x20, time.monotonic()))
        obj.inputs.space, obj.inputs.emergency = True, True
        self.assertFalse(obj.can_act(0x20, time.monotonic()))


if __name__ == '__main__':
    unittest.main()
