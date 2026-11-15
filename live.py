# Python 3.11+ | live.py | Windows 10 x64 | Riot local live feed
import threading
import time
import ssl
import urllib.request
import json
import math
import unicodedata
import urllib.error

class Feed:
    def __init__(self, demo=False):
        self.lock = threading.Lock()
        self.data, self.timestamp, self.error = {}, 0., "Aguardando uma partida."
        self.stop = threading.Event()
        self.thread = None
        self.demo = demo
        if demo:
            self.data = {
                "activePlayer": {
                    "riotId": "DEMO#TEST", "level": 9,
                    "abilities": {k: {"abilityLevel": r, "id": "Ezreal" + k}
                                  for k, r in zip("QWER", (5, 2, 1, 1))},
                    "championStats": dict(abilityPower=100, attackDamage=70, currentHealth=1000,
                                          maxHealth=1500, resourceValue=800, attackSpeed=.85, moveSpeed=350, attackRange=550, abilityHaste=0,
                                          magicPenetrationFlat=0)},
                "allPlayers": [dict(riotId="DEMO#TEST", championName="Ezreal", team="ORDER",
                                    isDead=False, level=9),
                               dict(riotId="ALVO#DEMO", championName="Alvo simulado", team="CHAOS",
                                    isDead=False, level=9)],
                "gameData": dict(gameMode="CLASSIC", mapNumber=11)}
            self.error = "DEMO: dados simulados; cliques desativados."
        else:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=2)

    def read(self):
        with self.lock:
            return self.data, (0 if self.demo else time.monotonic() - self.timestamp), self.error

    def _run(self):
        # A self-signed certificate is accepted ONLY for the fixed local endpoint.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
        while not self.stop.is_set():
            try:
                with opener.open("https://127.0.0.1:2999/liveclientdata/allgamedata", timeout=.5) as response:
                    data = json.load(response)
                if not isinstance(data.get("activePlayer", {}).get("championStats"), dict):
                    raise ValueError("API sem atributos do jogador.")
                with self.lock:
                    self.data, self.timestamp, self.error = data, time.monotonic(), "Conectado à API local."
            except (OSError, ValueError, AttributeError, TypeError) as exc:
                if isinstance(exc, urllib.error.HTTPError):
                    message = f'API local respondeu HTTP {exc.code}; aguarde o carregamento da partida.'
                elif isinstance(exc, (TimeoutError,)):
                    message = 'API local demorou a responder; aguardando nova tentativa.'
                elif isinstance(exc, urllib.error.URLError):
                    message = 'Sem conexão com a API local na porta 2999; ela ainda não respondeu.'
                else:
                    message = f'Resposta da API local incompleta ou inválida ({type(exc).__name__}).'
                with self.lock:
                    self.error = message
            self.stop.wait(.5)


def identity(player):
    return player.get('riotId') or (player.get('riotIdGameName', '')+'#'+player.get('riotIdTagLine', '')
        if player.get('riotIdGameName') and player.get('riotIdTagLine') else player.get('summonerName', ''))


def normalized(value):
    if not isinstance(value, str):
        return ''
    value = unicodedata.normalize('NFKC', value).strip().casefold()
    if '#' in value:
        name, tag = value.split('#', 1)
        value = name.strip()+'#'+tag.strip()
    return value


def player_ids(player):
    values = {normalized(player.get(k)) for k in ('riotId', 'summonerName')}
    if player.get('riotIdGameName') and player.get('riotIdTagLine'):
        values.add(normalized(player['riotIdGameName']+'#'+player['riotIdTagLine']))
    return {v for v in values if v}


def champion_key(player):
    raw = normalized(player.get('rawChampionName'))
    if raw.startswith('game_character_displayname_'):
        return raw[len('game_character_displayname_'):]
    return normalized(player.get('championName'))


def resolve_player(data):
    active = data.get('activePlayer', {})
    players = data.get('allPlayers', [])
    if not isinstance(active, dict) or not isinstance(players, list):
        return None, 'missing'
    players = [p for p in players if isinstance(p, dict)]
    active_ids = player_ids(active)
    full = {v for v in active_ids if '#' in v}
    exact = [p for p in players if full.intersection(player_ids(p))]
    if len(exact) == 1:
        return exact[0], 'identity'
    if len(exact) > 1:
        return None, 'ambiguous'
    names = {v.split('#', 1)[0] for v in active_ids}
    if active.get('riotIdGameName'):
        names.add(normalized(active['riotIdGameName']))
    candidates = []
    for player in players:
        ids = player_ids(player)
        # Never merge different explicit tags merely because game names coincide.
        if full and any('#' in v for v in ids) and not full.intersection(ids):
            continue
        player_names = {v.split('#', 1)[0] for v in ids}
        if player.get('riotIdGameName'):
            player_names.add(normalized(player['riotIdGameName']))
        if names.intersection(player_names):
            candidates.append(player)
    if len(candidates) == 1:
        return candidates[0], 'unique_game_name'
    if len(candidates) > 1:
        return None, 'ambiguous'
    # When IDs are absent, two active ability IDs can identify the champion;
    # this fallback still refuses a mirror matchup with two Ezreals.
    abilities = active.get('abilities', {})
    if not active_ids and not names and isinstance(abilities, dict):
        q_obj, w_obj = abilities.get('Q'), abilities.get('W')
        q = normalized(q_obj.get('id')) if isinstance(q_obj, dict) else ''
        w = normalized(w_obj.get('id')) if isinstance(w_obj, dict) else ''
        if q in ('ezrealq', 'ezrealmysticshot') and w in ('ezrealw', 'ezrealessenceflux'):
            matches = [p for p in players if champion_key(p) == 'ezreal']
            if len(matches) == 1:
                return matches[0], 'active_abilities'
            if len(matches) > 1:
                return None, 'ambiguous'
    return None, 'missing'


def own_player(data):
    return resolve_player(data)[0]


def live_report(data, age, api_status='', max_age=1):
    """Diagnostic output deliberately omits account names and the full API response."""
    report = dict(ok=False, code='no_data', reason='A API local ainda não forneceu os dados da partida.',
                  champion=None, mode=None, map_number=None, alive=None, identity_method=None,
                  age_seconds=round(age, 2) if isinstance(age, (int, float)) and math.isfinite(age) and age < 1e6 else None,
                  api_status=api_status, missing_stats=[])
    if not isinstance(data, dict) or not data:
        return report
    game = data.get('gameData', {})
    game = game if isinstance(game, dict) else {}
    report['mode'] = str(game.get('gameMode') or '').strip().upper() or None
    try:
        report['map_number'] = int(game.get('mapNumber'))
    except (TypeError, ValueError):
        if normalized(game.get('mapName')) == 'map11':
            report['map_number'] = 11
    own, method = resolve_player(data)
    report['identity_method'] = method
    if own:
        report['champion'] = own.get('championName') or champion_key(own)
        report['alive'] = not bool(own.get('isDead'))
    if not isinstance(age, (int, float)) or not math.isfinite(age) or age > max_age:
        report.update(code='stale', reason='Os dados da API local estão antigos; aguardando nova leitura.')
    elif not own:
        reason = 'A identificação do jogador está ambígua.' if method == 'ambiguous' else 'A API respondeu, mas não foi possível identificar o jogador local.'
        report.update(code='player_missing', reason=reason)
    elif champion_key(own) != 'ezreal':
        report.update(code='wrong_champion', reason=f'Campeão identificado: {report["champion"]}. Esta versão exige Ezreal.')
    elif report['map_number'] != 11:
        report.update(code='wrong_map', reason=f'Mapa identificado: {report["map_number"]}. Esta versão exige Summoner\'s Rift (mapa 11).')
    elif report['mode'] not in ('CLASSIC', 'PRACTICETOOL'):
        report.update(code='wrong_mode', reason=f'Modo identificado: {report["mode"] or "desconhecido"}. Suportados: normal/personalizada e Ferramenta de Treino.')
    elif not report['alive']:
        report.update(code='dead', reason='Ezreal foi identificado, mas a API informa que está morto. Aguarde o renascimento.')
    else:
        active = data.get('activePlayer', {})
        stats = active.get('championStats', {}) if isinstance(active, dict) else {}
        stats = stats if isinstance(stats, dict) else {}
        required = ('currentHealth', 'maxHealth', 'attackRange', 'attackSpeed', 'moveSpeed', 'attackDamage', 'resourceValue')
        missing = [k for k in required if not isinstance(stats.get(k), (int, float)) or not math.isfinite(stats[k])
                   or stats[k] < 0 or (k in ('currentHealth', 'maxHealth', 'attackRange', 'attackSpeed', 'moveSpeed') and stats[k] <= 0)]
        report['missing_stats'] = missing
        if missing:
            report.update(code='loading_stats', reason='Ezreal identificado; aguardando os atributos terminarem de carregar.')
        else:
            mode = 'Ferramenta de Treino' if report['mode'] == 'PRACTICETOOL' else 'normal/personalizada'
            report.update(ok=True, code='ready', reason=f'Ezreal vivo identificado | {mode} | API atual.')
    return report


