# Python 3.11+ | core.py | Windows 10 x64 | minion HP timing
from collections import deque
import math

def number(value, low=0, high=1e7):
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Valor fora do intervalo {low}..{high}")
    return value


def mitigation(resistance):
    """LoL resistance multiplier, including negative resistance."""
    return 100 / (100 + resistance) if resistance >= 0 else 2 - 100 / (100 - resistance)


def effective_resistance(base, percent_pen=0, flat_pen=0):
    # Penetration cannot turn nonnegative resistance negative.
    if base < 0:
        return base
    return max(0, base * (1 - percent_pen) - flat_pen)


class LastHitTracker:
    def __init__(self):
        self.samples = deque(maxlen=15)
        self.position = None

    def reset(self):
        self.samples.clear()
        self.position = None

    def observe(self, now, position, hp):
        if (self.position is None or math.dist(position, self.position) > 10
                or self.samples and (now - self.samples[-1][0] > .18
                                      or hp > self.samples[-1][1] + 4)):
            self.reset()
        self.position = position
        self.samples.append((now, hp))
        while self.samples and now - self.samples[0][0] > .45:
            self.samples.popleft()

    def predict(self, impact_seconds, attack_damage, armor, margin=.90):
        if len(self.samples) < 3 or self.samples[-1][0] - self.samples[0][0] < .06:
            return None
        times = [s[0] - self.samples[0][0] for s in self.samples]
        health = [s[1] for s in self.samples]
        tm, hm = sum(times) / len(times), sum(health) / len(health)
        denom = sum((t - tm) ** 2 for t in times)
        slope = sum((t - tm) * (h - hm) for t, h in zip(times, health)) / max(denom, 1e-9)
        predicted = health[-1] + min(0, slope) * impact_seconds
        damage = attack_damage * mitigation(armor) * margin
        return dict(hp=health[-1], predicted=predicted, damage=damage,
                    fire=0 < predicted <= damage)

