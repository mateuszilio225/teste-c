# Python 3.11+ | vision.py | Windows 10 x64 | calibrated health-bar detection
from dataclasses import dataclass, asdict
import cv2
import numpy as np


@dataclass
class BarProfile:
    width: int
    height: int
    hue: float
    saturation: float
    value: float

    @classmethod
    def from_image(cls, image):
        h, w = image.shape[:2]
        if not 12 <= w <= 250 or not 2 <= h <= 16:
            raise ValueError("Selecione somente o interior colorido da barra: 12..250 x 2..16 px.")
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        valid = hsv[:, :, 1] > 65
        if valid.mean() < .65:
            raise ValueError("Calibre com a barra cheia; retire bordas e fundo da seleção.")
        pixels = hsv[valid]
        # Circular hue mean handles red straddling the 0/179 boundary.
        angles = pixels[:, 0].astype(float) * (2 * np.pi / 180)
        hue = (np.arctan2(np.sin(angles).mean(), np.cos(angles).mean()) * 180 / (2 * np.pi)) % 180
        return cls(w, h, float(hue), float(np.median(pixels[:, 1])),
                   float(np.median(pixels[:, 2])))

    def serializable(self):
        return asdict(self)


def detect_bars(image, profile):
    """Return colored fill positions; profile width is the full HP interior."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0].astype(float)
    delta = np.abs(hue - profile.hue)
    delta = np.minimum(delta, 180 - delta)
    mask = ((delta < 9) & (hsv[:, :, 1] >= max(50, profile.saturation * .55))
            & (hsv[:, :, 2] >= max(40, profile.value * .45))).astype(np.uint8) * 255
    # Close the small black HP ticks without connecting separate rows.
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((1, 3), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    found = []
    for x, y, w, h, area in stats[1:count]:
        if not (3 <= w <= profile.width + 1 and abs(h - profile.height) <= 1
                and area / (w * h) > .68):
            continue
        right = x + profile.width
        if right + 2 >= image.shape[1] or y < 1 or y + h + 1 >= image.shape[0]:
            continue
        # An overlong colored region is a different bar size, not a minion.
        if mask[y:y + h, right + 1:right + 3].mean() > 80:
            continue
        if w < profile.width - 3:
            empty = hsv[y:y + h, x + w + 1:right, 2]
            if empty.size and (empty < 105).mean() < .68:
                continue
        found.append(dict(x=int(x), y=int(y), width=int(profile.width),
                          height=int(h), fraction=min(1., w / profile.width)))
    return found


def nearest_bar(image, profile, cursor, radius=100):
    bars = detect_bars(image, profile)
    if not bars:
        return None
    def distance(b):
        return ((b["x"] + profile.width / 2 - cursor[0]) ** 2
                + (b["y"] - cursor[1]) ** 2) ** .5
    bar = min(bars, key=distance)
    return bar if distance(bar) <= radius else None
