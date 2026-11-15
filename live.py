# Python 3.11+ | live.py | Windows 10 x64 | Riot local live feed
import threading
import time
import ssl
import urllib.request
import json

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
                with self.lock:
                    self.error = f"Sem dados atuais: {type(exc).__name__}. Abra uma partida."
            self.stop.wait(.5)


def identity(player):
    return player.get("riotId") or player.get("summonerName", "")


def own_player(data):
    active = data.get("activePlayer", {})
    ids = {active.get(k) for k in ("riotId", "summonerName")} - {None, ""}
    return next((p for p in data.get("allPlayers", []) if ids.intersection(
        {p.get(k) for k in ("riotId", "summonerName")} - {None, ""})), None)


