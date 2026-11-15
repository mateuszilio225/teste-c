# Python 3.11+ | geometry.py | Windows 10 x64 target | projected aim and dodge geometry
from dataclasses import dataclass
import math

def add(a, b): return (a[0]+b[0], a[1]+b[1])
def sub(a, b): return (a[0]-b[0], a[1]-b[1])
def mul(a, s): return (a[0]*s, a[1]*s)
def dot(a, b): return a[0]*b[0]+a[1]*b[1]
def length(a): return math.hypot(*a)


@dataclass(frozen=True)
class Projection:
    sx: float
    sy: float

    def units(self, pixels):
        return (pixels[0]/self.sx, pixels[1]/self.sy)

    def pixels(self, units):
        return (units[0]*self.sx, units[1]*self.sy)


def closest_distance(position, velocity, start, end):
    """Minimum separation of a relative trajectory within a time interval."""
    vv = dot(velocity, velocity)
    t = max(start, min(end, -dot(position, velocity)/vv)) if vv > 1e-9 else start
    return length(add(position, mul(velocity, t))), t


def intercept(relative, velocity, missile_speed, delay, horizon=2):
    """Point relative to the caster and total time, including cast delay."""
    p = add(relative, mul(velocity, delay))
    a = dot(velocity, velocity) - missile_speed**2
    b, c = 2*dot(p, velocity), dot(p, p)
    roots = []
    if abs(a) < 1e-9:
        if abs(b) > 1e-9:
            roots = [-c/b]
    else:
        discriminant = b*b - 4*a*c
        if discriminant >= 0:
            d = math.sqrt(discriminant)
            roots = [(-b-d)/(2*a), (-b+d)/(2*a)]
    valid = [t for t in roots if 0 <= t and t+delay <= horizon]
    if not valid:
        return None
    t = min(valid)+delay
    return add(relative, mul(velocity, t)), t


def segment_distance(point, a, b):
    ab = sub(b, a)
    t = max(0, min(1, dot(sub(point, a), ab)/max(1e-9, dot(ab, ab))))
    return length(sub(point, add(a, mul(ab, t)))), t


def blocked_segment(end, blockers, width=90):
    # Caster is the origin; blockers are already in ground-plane game units.
    for point in blockers:
        distance, fraction = segment_distance(point, (0, 0), end)
        if .01 < fraction < .98 and distance < width:
            return True
    return False


@dataclass(frozen=True)
class Threat:
    position: tuple
    velocity: tuple
    radius: float


def trajectory_clear(goal, threats, current_velocity, speed, delay, horizon, body_radius):
    """Piecewise continuous test: reaction, movement, then standing at destination."""
    reaction_end = mul(current_velocity, delay)
    walk = sub(goal, reaction_end)
    distance = length(walk)
    velocity = mul(walk, speed/distance) if distance else (0, 0)
    arrival = delay + distance/speed
    segments = [(0, min(delay, horizon), (0, 0), current_velocity)]
    if delay < horizon:
        # p(t) = intercept + velocity * t, with global time t.
        segments.append((delay, min(arrival, horizon), sub(reaction_end, mul(velocity, delay)), velocity))
    if arrival < horizon:
        segments.append((arrival, horizon, goal, (0, 0)))
    for threat in threats:
        for start, end, intercept_pos, player_velocity in segments:
            if end < start:
                continue
            distance, _ = closest_distance(sub(threat.position, intercept_pos),
                                           sub(threat.velocity, player_velocity), start, end)
            if distance <= body_radius + threat.radius:
                return False
    return True


def minimal_dodge(threats, player_velocity, speed, max_step=140, horizon=.6,
                  body_radius=70, delay=.06, preferred=(1, 0), allowed=None):
    danger = any(closest_distance(t.position, sub(t.velocity, player_velocity), 0, horizon)[0]
                 <= body_radius+t.radius for t in threats)
    if not danger:
        return None
    candidates = []
    for radius in range(10, int(max_step)+1, 10):
        for i in range(32):
            angle = i * 2*math.pi/32
            goal = (radius*math.cos(angle), radius*math.sin(angle))
            if allowed is not None and not allowed(goal):
                continue
            if trajectory_clear(goal, threats, player_velocity, speed, delay, horizon, body_radius):
                alignment = dot(goal, preferred)/max(1, length(goal)*length(preferred))
                candidates.append((radius + (1-alignment)*2, goal))
        if candidates:
            return min(candidates, key=lambda x: x[0])[1]
    return None


class MotionTracker:
    """Short lived screen-space identities, with camera-adjusted velocity."""
    def __init__(self):
        self.tracks = {}
        self.serial = 0
        self.timestamp = None

    def reset(self):
        self.tracks.clear()
        self.timestamp = None

    def update(self, points, now, camera_shift=(0, 0), gate=100):
        dt = now-self.timestamp if self.timestamp is not None else 0
        self.timestamp = now
        if not .008 <= dt <= .18:
            self.tracks.clear()
            dt = 0
        old = self.tracks
        unused = set(old)
        result = {}
        for point in points:
            # Compare against last position moved with the camera/background.
            choices = [(length(sub(point, add(old[k]['position'], camera_shift))), k) for k in unused]
            distance, key = min(choices) if choices else (math.inf, None)
            if key is not None and distance <= gate and dt:
                prev = old[key]
                raw = mul(sub(sub(point, prev['position']), camera_shift), 1/dt)
                velocity = add(mul(prev['velocity'], .4), mul(raw, .6)) if prev['samples'] > 1 else raw
                result[key] = dict(position=point, velocity=velocity, samples=prev['samples']+1, age=0)
                unused.remove(key)
            else:
                self.serial += 1
                result[self.serial] = dict(position=point, velocity=(0, 0), samples=1, age=0)
        # No extrapolated unseen targets are returned or fired upon.
        self.tracks = result
        return result
