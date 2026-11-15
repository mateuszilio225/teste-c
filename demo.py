# Python 3.11+ | demo.py | portable | deterministic visual simulation, no real game input
import cv2
import numpy as np
from vision import BarProfile


class DemoScene:
    def __init__(self):
        rng = np.random.default_rng(103)
        gray = rng.integers(35, 95, (760, 1200), dtype=np.uint8)
        self.background = np.repeat(gray[:, :, None], 3, axis=2)
        self.templates = {
            'demo-q': rng.integers(50, 255, (28, 28, 3), dtype=np.uint8),
            'demo-w': rng.integers(50, 255, (28, 28, 3), dtype=np.uint8),
            'demo-missile': rng.integers(50, 255, (12, 16, 3), dtype=np.uint8)}
        def bar(width, height, color, offset):
            sample = np.full((height, width, 3), color, np.uint8)
            return dict(profile=BarProfile.from_image(sample).serializable(), offset=offset)
        self.calibration = dict(resolution=[1200, 760, 0, 0], center=[450, 350],
            viewport=[10, 10, 1180, 640], projection=[.4, .28],
            self=bar(100, 6, (35, 220, 35), [0, 50]),
            enemy=bar(120, 6, (30, 40, 220), [0, 50]),
            minion=bar(60, 4, (30, 40, 220), [0, 35]),
            Q=dict(rect=[450, 700, 28, 28], file='demo-q'),
            W=dict(rect=[490, 700, 28, 28], file='demo-w'),
            projectiles=[dict(file='demo-missile', radius=35, name='Simulado')])

    def frame(self, elapsed):
        frame = self.background.copy()
        # Player, enemy champion, minion; fixed camera with a textured background.
        for x, y, w, h, ratio, color in [(400, 300, 100, 6, 2/3, (35, 220, 35)),
                (740, 300, 120, 6, .8, (30, 40, 220)),
                (620, 410, 60, 4, .4, (30, 40, 220))]:
            frame[y:y+h, x:x+w] = 15
            frame[y:y+h, x:x+int(w*ratio)] = color
        cv2.circle(frame, (450, 350), 12, (60, 220, 60), -1)
        cv2.circle(frame, (800, 350), 12, (30, 40, 220), -1)
        cv2.circle(frame, (650, 445), 7, (30, 40, 220), -1)
        for key in ('Q', 'W'):
            x, y, w, h = self.calibration[key]['rect']
            frame[y:y+h, x:x+w] = self.templates['demo-'+key.lower()]
        x = int(950 - (elapsed % 2.8)*400)
        if 10 < x < 1170:
            frame[344:356, x:x+16] = self.templates['demo-missile']
        return frame
