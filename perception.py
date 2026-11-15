# Python 3.11+ | perception.py | Windows 10 x64 | calibrated screen observations
from dataclasses import dataclass
import cv2
import numpy as np
from vision import BarProfile, detect_bars
from geometry import length, sub


def entities(frame, calibration):
    bars = detect_bars(frame, BarProfile(**calibration['profile']))
    dx, dy = calibration['offset']
    return [dict(position=(b['x']+b['width']/2+dx, b['y']+dy), fraction=b['fraction']) for b in bars]


def find_player(frame, calibration, expected, health_fraction):
    matches = [x for x in entities(frame, calibration)
               if length(sub(x['position'], expected)) < 70
               and abs(x['fraction']-health_fraction) < .15]
    return min(matches, key=lambda x: length(sub(x['position'], expected))) if matches else None


def icon_ready(frame, calibration, template):
    x, y, w, h = calibration['rect']
    crop = frame[y:y+h, x:x+w]
    if crop.shape != template.shape or crop.size == 0:
        return False
    error = np.abs(crop.astype(float)-template.astype(float)).mean()/255
    hsv_a = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV).astype(float)
    hsv_b = cv2.cvtColor(template, cv2.COLOR_BGR2HSV).astype(float)
    return bool(error < .055 and hsv_a[:, :, 1].mean() >= hsv_b[:, :, 1].mean()*.82
                and hsv_a[:, :, 2].mean() >= hsv_b[:, :, 2].mean()*.92)


class Camera:
    def __init__(self):
        self.previous = None
        self.window = None

    def reset(self):
        self.previous = None

    def update(self, frame, rect):
        x, y, w, h = rect
        gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=.25, fy=.25).astype(np.float32)
        if self.previous is None or self.previous.shape != gray.shape:
            self.previous = gray
            self.window = cv2.createHanningWindow((gray.shape[1], gray.shape[0]), cv2.CV_32F)
            return (0, 0), False
        shift, response = cv2.phaseCorrelate(self.previous, gray, self.window)
        self.previous = gray
        shift = (shift[0]*4, shift[1]*4)
        return shift, bool(response > .12 and length(shift) < 32)


def projectile_positions(frame, rect, template, threshold=.88, limit=12):
    """Template-based supported appearances; no assumption about team or spell identity."""
    x, y, w, h = rect
    area = frame[y:y+h, x:x+w]
    if template is None or area.shape[0] < template.shape[0] or area.shape[1] < template.shape[1]:
        return []
    score = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
    result = []
    th, tw = template.shape[:2]
    for _ in range(limit):
        _, best, _, pos = cv2.minMaxLoc(score)
        if best < threshold:
            break
        px, py = pos
        result.append((x+px+tw/2, y+py+th/2))
        score[max(0, py-th//2):min(score.shape[0], py+th//2+1),
              max(0, px-tw//2):min(score.shape[1], px+tw//2+1)] = -1
    return result
