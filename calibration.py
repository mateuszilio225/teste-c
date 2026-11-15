# Python 3.11+ | calibration.py | Windows 10 x64 | calibration progress and screenshot proposals
import base64
import copy
import math
import cv2
import numpy as np
from vision import BarProfile


SPATIAL_KEYS = ('viewport', 'projection', 'center', 'self', 'enemy', 'minion', 'Q', 'W', 'projectiles')
STEP_LABELS = {'resolution': 'Monitor e resolução', 'viewport': '1. Área útil do campo',
               'geometry': '2. Centro e círculo de alcance do AA', 'self': '3. Sua barra cheia e seus pés',
               'enemy': '4. Barra de campeão inimigo', 'minion': '5. Barra de minion inimigo',
               'Q': '6. Ícone Q disponível', 'W': '7. Ícone W disponível',
               'projectile': '8. Aparência de projétil inimigo', 'minion_hp': 'HP máximo do minion',
               'confirmed': 'Confirmação do patch e câmera', 'quickcast': 'Confirmação de conjuração rápida',
               'features': 'Selecione ao menos uma função'}


def monitor_resolution(monitor):
    values = [monitor[k] for k in ('width', 'height', 'left', 'top')]
    if any(not isinstance(v, int) for v in values) or values[0] <= 0 or values[1] <= 0:
        raise ValueError('Não foi possível obter o tamanho real do monitor.')
    return values


def pending_steps(config):
    c = config.get('calibration')
    c = c if isinstance(c, dict) else {}
    pending = []
    res = c.get('resolution')
    if not isinstance(res, (list, tuple)) or len(res) != 4 or any(
            not isinstance(v, (int, float)) or not math.isfinite(v) for v in res) or res[0] <= 0 or res[1] <= 0:
        pending.append('resolution')
    for key in ('viewport', 'self'):
        if not c.get(key):
            pending.append(key)
    projection, center = c.get('projection'), c.get('center')
    if not projection or not center:
        pending.append('geometry')
    else:
        try:
            sx, sy = projection
            x, y = center
            if not (.05 <= sx <= 2 and .03 <= sy <= 2 and all(math.isfinite(v) for v in (sx, sy, x, y))):
                pending.append('geometry')
        except (ValueError, TypeError):
            pending.append('geometry')
    if config.get('combo'):
        pending += [k for k in ('enemy', 'minion', 'Q', 'W') if not c.get(k)]
    if config.get('farm'):
        if not c.get('minion') and 'minion' not in pending:
            pending.append('minion')
        if not isinstance(config.get('minion_hp'), (int, float)) or config['minion_hp'] <= 0:
            pending.append('minion_hp')
    if config.get('dodge') and not c.get('projectiles'):
        pending.append('projectile')
    for key in ('confirmed', 'quickcast'):
        if not config.get(key):
            pending.append(key)
    if not any(config.get(k) for k in ('combo', 'farm', 'dodge')):
        pending.append('features')
    return pending


def pending_message(config):
    steps = pending_steps(config)
    if not steps:
        return ''
    lines = ['Faltam estas etapas antes de armar:']
    lines += ['• '+STEP_LABELS[k] for k in steps]
    lines += ['', 'Abra Calibração e use Calibrar automaticamente ou conclua as etapas indicadas.',
              'Na seleção manual, arraste sobre a região e solte; Esc cancela sem salvar.']
    return '\n'.join(lines)


def apply_capture(calibration, kind, value, resolution=None):
    """Only committed captures bind geometry to a monitor; canceled captures change nothing."""
    result = copy.deepcopy(calibration)
    if resolution is not None:
        old = result.get('resolution')
        if old is not None and old != resolution:
            for key in SPATIAL_KEYS:
                result.pop(key, None)
        result['resolution'] = list(resolution)
    if kind in ('geometry', 'automatic'):
        result.update(copy.deepcopy(value))
    elif kind == 'projectile':
        result.setdefault('projectiles', []).append(copy.deepcopy(value))
    else:
        result[kind] = copy.deepcopy(value)
    return result


def full_bars(frame, color):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hue, sat, value = cv2.split(hsv)
    mask = (((hue < 15) | (hue > 165)) if color == 'red' else ((hue > 35) & (hue < 86)))
    mask = (mask & (sat > 80) & (value > 75)).astype(np.uint8)*255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((1, 3), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    bars = []
    for x, y, w, h, area in stats[1:count]:
        if not (25 <= w <= 230 and 2 <= h <= 12 and w/h >= 5 and area/(w*h) > .82):
            continue
        if x < 3 or y < 2 or x+w+10 >= frame.shape[1] or y+h+2 >= frame.shape[0]:
            continue
        # Reject a colored prefix followed by empty black HP interior.
        if (value[y:y+h, x+w+3:x+w+9] < 40).mean() > .7:
            continue
        if (value[y-2:y, x:x+w] < 100).mean() < .55:
            continue
        bars.append((int(x), int(y), int(w), int(h)))
    return bars


def range_ellipse(frame, bar):
    """Require a mostly complete bright ring below the known player HP bar."""
    bx, by, bw, bh = bar
    edges = cv2.Canny(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 70, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    choices = []
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    bright_mask = (((hsv[:, :, 0] > 75) & (hsv[:, :, 0] < 135) & (hsv[:, :, 1] > 60))
                   | ((hsv[:, :, 1] < 65) & (hsv[:, :, 2] > 200))).astype(np.uint8)
    # Canny traces either side of a thin stroke, often on a background pixel.
    bright_mask = cv2.dilate(bright_mask, np.ones((3, 3), np.uint8))
    for contour in contours:
        if len(contour) < 120:
            continue
        (cx, cy), (a, b), angle = cv2.fitEllipse(contour)
        if not (abs(cx-(bx+bw/2)) < 35 and 15 < cy-by < 160 and min(a, b) > 80):
            continue
        if abs(angle % 90) > 12 and abs(angle % 90-90) > 12:
            continue
        radians = math.radians(angle)
        co, si = math.cos(radians), math.sin(radians)
        rx = math.sqrt((a*co/2)**2+(b*si/2)**2)
        ry = math.sqrt((a*si/2)**2+(b*co/2)**2)
        if not (max(70, bw*1.3) < rx < min(frame.shape[1]*.45, bw*5)
                and 40 < ry < frame.shape[0]*.4 and 1.1 < rx/ry < 2.6):
            continue
        pts = contour[:, 0, :].astype(float)
        dx, dy = pts[:, 0]-cx, pts[:, 1]-cy
        u, v = (dx*co+dy*si)/(a/2), (-dx*si+dy*co)/(b/2)
        radial = np.abs(np.sqrt(u*u+v*v)-1)
        bins = np.unique(((np.arctan2(v, u)+np.pi)*24/(2*np.pi)).astype(int))
        bright_ring = bright_mask[contour[:, 0, 1], contour[:, 0, 0]]
        if (radial < .06).mean() < .85 or len(bins) < 19 or bright_ring.mean() < .65:
            continue
        choices.append((float(radial.mean()), (cx, cy, rx, ry)))
    return min(choices, key=lambda x: x[0])[1] if choices else None


def icon_matches(frame, icons):
    height, width = frame.shape[:2]
    left, top = int(width*.15), int(height*.60)
    area = frame[top:, left:int(width*.85)]
    found = {}
    for key in ('Q', 'W'):
        raw = cv2.imdecode(np.frombuffer(base64.b64decode(icons[key]), np.uint8), cv2.IMREAD_COLOR)
        raw = raw[3:-3, 3:-3]
        best = None
        for size in range(24, 73, 2):
            if size > min(area.shape[:2]):
                continue
            template = cv2.resize(raw, (size, size), interpolation=cv2.INTER_AREA)
            score = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
            _, maximum, _, point = cv2.minMaxLoc(score)
            if maximum >= .86 and (best is None or maximum > best[0]):
                best = (maximum, [left+point[0], top+point[1], size, size])
        if best:
            found[key] = best[1]
    if len(found) == 2:
        q, w = found['Q'], found['W']
        if not (.8*q[2] <= w[0]-q[0] <= 2.3*q[2] and abs(w[1]-q[1]) < 8 and abs(q[2]-w[2]) <= 4):
            return {}
    return found


def auto_calibrate(frame, active, icons):
    """Return measured proposals, capture assets, and explanations; never fill undetected values."""
    result, assets, notes = {}, {}, []
    height, width = frame.shape[:2]
    located = icon_matches(frame, icons)
    for key, rect in located.items():
        x, y, w, h = rect
        file = f'assets/{key}-ready.png'
        crop = frame[y:y+h, x:x+w].copy()
        if cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)[:, :, 1].mean() < 50:
            notes.append(f'{key}: ícone sem cor suficiente; deixe a habilidade disponível.')
            continue
        result[key] = dict(rect=rect, file=file)
        assets[file] = crop
    if len(located) == 2:
        # This is a proposed crop above the localized HUD, not a map reconstruction.
        bottom = int(min(r[1] for r in located.values())-4*max(r[3] for r in located.values()))
        if bottom > height*.5:
            result['viewport'] = [5, 5, width-10, bottom-5]
            notes.append('Área útil estimada acima da HUD localizada; confira o recorte na prévia.')
    stats = active.get('championStats', {})
    hp_fraction = stats.get('currentHealth', 0)/max(1, stats.get('maxHealth', 1))
    greens = [r for r in full_bars(frame, 'green') if abs(r[0]+r[2]/2-width/2) < width*.18
              and height*.2 < r[1] < height*.65]
    if hp_fraction < .98:
        notes.append('Para detectar sua barra automaticamente, fique com a vida cheia.')
    elif greens:
        greens.sort(key=lambda r: abs(r[0]+r[2]/2-width/2)+abs(r[1]-height*.45))
        bar = greens[0]
        ellipse = range_ellipse(frame, bar)
        if ellipse:
            cx, cy, rx, ry = ellipse
            attack_range = stats.get('attackRange', 0)
            if attack_range > 0 and .05 <= rx/attack_range <= 2 and .03 <= ry/attack_range <= 2:
                x, y, w, h = bar
                result.update(center=[cx, cy], projection=[rx/attack_range, ry/attack_range])
                result['self'] = dict(profile=BarProfile.from_image(frame[y:y+h, x:x+w]).serializable(),
                                      offset=[cx-(x+w/2), cy-y])
                reds = full_bars(frame, 'red')
                champions = [r for r in reds if .85*w <= r[2] <= 1.4*w and r[1] < height*.75]
                minions = [r for r in reds if .35*w <= r[2] < .75*w and r[1] < height*.75]
                # A bar alone doesn't measure another unit's feet. Reuse only the measured
                # champion bar offset; require manual minion body selection for click accuracy.
                if champions:
                    x2, y2, w2, h2 = champions[0]
                    result['enemy'] = dict(profile=BarProfile.from_image(frame[y2:y2+h2, x2:x2+w2]).serializable(),
                                           offset=[0, cy-y])
                    notes.append('Barra inimiga detectada; posição dos pés aproximada pelo deslocamento medido do seu campeão.')
                if minions:
                    notes.append('Barras de minions encontradas; confirme o corpo no passo 5 para definir o clique.')
        else:
            notes.append('Círculo de AA não confirmado. Mostre-o durante a captura ou faça o passo 2 manualmente.')
    else:
        notes.append('Sua barra cheia não foi localizada com confiança; faça o passo 3 manualmente.')
    if not located:
        notes.append('Ícones Q/W não localizados; deixe-os disponíveis e visíveis ou faça os passos 6/7.')
    return result, assets, notes
