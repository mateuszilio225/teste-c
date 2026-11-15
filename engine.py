# Python 3.11+ | engine.py | Windows 10 x64 | Ezreal projected-screen controller
from dataclasses import dataclass
import math
from core import LastHitTracker
from geometry import (Projection, MotionTracker, Threat, add, sub, mul, length,
                      intercept, blocked_segment, closest_distance, minimal_dodge)
from perception import entities, find_player, Camera, icon_ready, projectile_positions


@dataclass(frozen=True)
class Action:
    kind: str
    point: tuple
    hold_key: int
    spell: str | None = None
    reason: str = ''


DEFAULTS = dict(combo=True, dodge=False, farm=True, max_step=140, horizon=.6,
                body_radius=65, dodge_margin=10, reaction_ms=70, range_margin=100,
                cursor_radius=220, minion_hp=0, minion_armor=0, impact_ms=400,
                farm_key='X', match_threshold=.88, confirmed=False, quickcast=False)


def inside(point, rect):
    x, y, w, h = rect
    return x <= point[0] < x+w and y <= point[1] < y+h


def live_valid(data, age):
    from live import own_player
    own = own_player(data)
    return bool(age <= 1 and own and own.get('championName') == 'Ezreal'
                and not own.get('isDead') and data.get('gameData', {}).get('mapNumber') == 11
                and data.get('gameData', {}).get('gameMode') == 'CLASSIC')


class Engine:
    def __init__(self, rules):
        self.rules = rules
        self.camera = Camera()
        self.enemies = MotionTracker()
        self.missiles = {}
        self.minion = LastHitTracker()
        self.last_cast = {'Q': -1e9, 'W': -1e9}
        self.spent = []
        self.last_attack = -1e9
        self.dodge_until = 0
        self.last_move = -1e9
        self.timestamp = None
        self.player_position = None
        self.status = 'Aguardando configuração.'
        self.details = {}

    def reset_tracking(self):
        self.camera.reset()
        self.enemies.reset()
        for tracker in self.missiles.values():
            tracker.reset()
        self.minion.reset()
        self.timestamp = None
        self.player_position = None

    def mark_sent(self, action, now, active, config):
        if action.spell:
            self.last_cast[action.spell] = now
            rank = active['abilities'][action.spell]['abilityLevel']
            self.spent.append((now, self.rules['spells'][action.spell]['mana'][rank-1]))
        elif action.kind == 'farm':
            self.last_attack = now
            self.minion.reset()
        elif action.kind == 'dodge':
            self.last_move = now
            p = self.player_position
            projection = Projection(*config['calibration']['projection'])
            travel = length(projection.units(sub(action.point, p)))/active['championStats']['moveSpeed']
            self.dodge_until = now+travel+.12

    def step(self, frame, data, config, templates, cursor, space, farm_held, now):
        self.details = {}
        if not space and not farm_held:
            self.reset_tracking()
            self.status = 'Solte/segure Espaço para combo/esquiva ou X para last hit.'
            return None
        if not config.get('confirmed') or not config.get('quickcast'):
            self.status = 'Confirme patch, câmera e Q/W em conjuração rápida.'
            return None
        calibration = config['calibration']
        viewport = calibration['viewport']
        projection = Projection(*calibration['projection'])
        active = data['activePlayer']
        stats = active['championStats']
        player = find_player(frame, calibration['self'], calibration['center'],
                             stats['currentHealth']/max(1, stats['maxHealth']))
        if player is None:
            self.reset_tracking()
            self.status = 'Barra do jogador não confirmada; nenhuma ação.'
            return None
        position = player['position']
        if not inside(position, viewport):
            self.reset_tracking()
            self.status = 'Jogador fora da área calibrada.'
            return None
        shift, camera_ok = self.camera.update(frame, viewport)
        dt = now-self.timestamp if self.timestamp is not None else 0
        old_position = self.player_position
        self.timestamp, self.player_position = now, position
        if not camera_ok or not .008 <= dt <= .18:
            self.enemies.reset()
            for tracker in self.missiles.values():
                tracker.reset()
            self.minion.reset()
            self.status = 'Estabilizando câmera/leitura.'
            return None
        player_velocity = projection.units(mul(sub(sub(position, old_position), shift), 1/dt))
        if length(player_velocity) > stats['moveSpeed']*1.8+100:
            self.reset_tracking()
            self.status = 'Salto/movimento de câmera: leitura reiniciada.'
            return None
        enemies = entities(frame, calibration['enemy']) if 'enemy' in calibration else []
        enemies = [p for p in enemies if inside(p['position'], viewport)]
        tracked = self.enemies.update([p['position'] for p in enemies], now, shift)
        minions = entities(frame, calibration['minion']) if 'minion' in calibration else []
        minions = [p for p in minions if inside(p['position'], viewport)]
        self.details.update(player=position, enemies=len(enemies), minions=len(minions), threats=0)

        # Dodge has priority. Only explicitly captured projectile appearances are used.
        if space and config['dodge']:
            threats = []
            for index, profile in enumerate(calibration.get('projectiles', [])):
                template = templates.get(profile['file'])
                points = projectile_positions(frame, viewport, template, config['match_threshold'])
                tracker = self.missiles.setdefault(index, MotionTracker())
                observations = tracker.update(points, now, shift)
                for obs in observations.values():
                    velocity = projection.units(obs['velocity'])
                    if obs['samples'] < 3 or not 200 <= length(velocity) <= 4000:
                        continue
                    threats.append(Threat(projection.units(sub(obs['position'], position)),
                                          velocity, profile['radius']))
            self.details['threats'] = len(threats)
            danger = any(closest_distance(t.position, sub(t.velocity, player_velocity),
                                          0, config['horizon'])[0] <=
                         config['body_radius']+config['dodge_margin']+t.radius for t in threats)
            if danger:
                goal = minimal_dodge(threats, player_velocity, stats['moveSpeed'],
                    config['max_step'], config['horizon'], config['body_radius']+config['dodge_margin'],
                    config['reaction_ms']/1000, projection.units(sub(cursor, position)),
                    allowed=lambda g: inside(add(position, projection.pixels(g)), viewport))
                self.status = 'Ameaça: sem rota viável no limite configurado.'
                if goal is not None and now-self.last_move > .15:
                    self.status = f'Esquiva projetada: {length(goal):.0f} unidades.'
                    return Action('dodge', add(position, projection.pixels(goal)), 0x20,
                                  reason=self.status)
                return None
        if now < self.dodge_until:
            self.status = 'Concluindo deslocamento; Q/W/AA aguardam.'
            return None

        if space and config['combo'] and now-max(self.last_cast.values()) >= .34:
            self.spent = [(t, mana) for t, mana in self.spent if now-t < 1.6]
            mana = stats['resourceValue']-sum(m for _, m in self.spent)
            haste = max(0, stats.get('abilityHaste', 0))
            ready = {}
            for spell in ('Q', 'W'):
                rule = self.rules['spells'][spell]
                rank = active.get('abilities', {}).get(spell, {}).get('abilityLevel', 0)
                hud = calibration.get(spell)
                ready[spell] = bool(1 <= rank <= 5 and hud and templates.get(hud['file']) is not None
                    and now-self.last_cast[spell] >= rule['cooldown'][rank-1]/(1+haste/100)
                    and mana >= rule['mana'][rank-1]
                    and icon_ready(frame, hud, templates[hud['file']]))
            choices = []
            if ready['Q']:
                for key, target in tracked.items():
                    if target['samples'] < 3 or length(sub(target['position'], cursor)) > config['cursor_radius']:
                        continue
                    relative = projection.units(sub(target['position'], position))
                    velocity = projection.units(target['velocity'])
                    if length(velocity) > 1000:
                        continue
                    aim = intercept(relative, velocity, self.rules['spells']['Q']['speed'],
                                    self.rules['spells']['Q']['delay']+.045)
                    if aim is None:
                        continue
                    end, flight = aim
                    blockers = [projection.units(sub(p['position'], position)) for p in minions]
                    blockers += [projection.units(sub(t['position'], position))
                                 for other, t in tracked.items() if other != key]
                    if length(end) > self.rules['spells']['Q']['range']-config['range_margin'] or blocked_segment(end, blockers):
                        continue
                    point = add(position, projection.pixels(end))
                    if not inside(point, viewport):
                        continue
                    choices.append((length(sub(target['position'], cursor)), target, end))
            if choices:
                _, target, end = min(choices, key=lambda c: c[0])
                if ready['W']:
                    qr = active['abilities']['Q']['abilityLevel']
                    wr = active['abilities']['W']['abilityLevel']
                    if mana >= self.rules['spells']['Q']['mana'][qr-1]+self.rules['spells']['W']['mana'][wr-1]:
                        aim_w = intercept(projection.units(sub(target['position'], position)),
                                          projection.units(target['velocity']),
                                          self.rules['spells']['W']['speed'], .295)
                        if aim_w and length(aim_w[0]) <= self.rules['spells']['W']['range']-config['range_margin']:
                            point_w = add(position, projection.pixels(aim_w[0]))
                            if inside(point_w, viewport):
                                self.status = 'W projetado no campeão visual perto do cursor.'
                                return Action('cast', point_w, 0x20, 'W', self.status)
                self.status = 'Q projetado; caminho sem bloqueador visual identificado.'
                return Action('cast', add(position, projection.pixels(end)), 0x20, 'Q', self.status)

        if farm_held and config['farm'] and config['minion_hp'] > 0:
            candidates = [p for p in minions if length(sub(p['position'], cursor)) < 140
                          and length(projection.units(sub(p['position'], position))) < stats['attackRange']-40]
            if candidates:
                target = min(candidates, key=lambda p: length(sub(p['position'], cursor)))
                self.minion.observe(now, target['position'], target['fraction']*config['minion_hp'])
                prediction = self.minion.predict(config['impact_ms']/1000, stats['attackDamage'], config['minion_armor'])
                if prediction:
                    self.details['farm'] = prediction
                    if prediction['fire'] and now-self.last_attack > 1/max(.1, stats['attackSpeed'])+.05:
                        self.status = 'AA para last hit na janela prevista.'
                        return Action('farm', target['position'], ord(config['farm_key']), reason=self.status)
            else:
                self.minion.reset()
        self.status = 'Observando: aguardando alvo, disponibilidade ou janela de last hit.'
        return None
