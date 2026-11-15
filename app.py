# Python 3.11+ | app.py | Windows 10 x64 | Ezreal screen controller, local API, Space/X
import argparse
import copy
import ctypes
import json
import logging
import os
from pathlib import Path
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import cv2
import mss
import numpy as np
from PIL import Image, ImageTk

from core import number
from demo import DemoScene
from engine import DEFAULTS, Engine, live_valid
from live import Feed
from vision import BarProfile
from wininput import WindowsInput

BASE = Path(__file__).resolve().parent
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else BASE
DATA = APP_DIR / 'data'
DATA.mkdir(exist_ok=True)
(DATA / 'assets').mkdir(exist_ok=True)
logging.basicConfig(filename=DATA/'app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
RULES = json.loads((BASE/'rules.json').read_text(encoding='utf-8'))


def asset_path(name):
    path = (DATA/name).resolve()
    if DATA.resolve() not in path.parents:
        raise ValueError('Caminho de template inválido.')
    return path


def load_templates(config):
    calibration = config['calibration']
    names = [calibration[k]['file'] for k in ('Q', 'W') if k in calibration]
    names += [p['file'] for p in calibration.get('projectiles', [])]
    templates = {}
    for name in names:
        image = cv2.imdecode(np.frombuffer(asset_path(name).read_bytes(), np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f'Template inválido: {name}')
        templates[name] = image
    return templates


def validate_calibration(config):
    c = config['calibration']
    for key in ('resolution', 'viewport', 'projection', 'center', 'self'):
        if key not in c:
            raise ValueError(f'Calibração ausente: {key}')
    sx, sy = c['projection']
    number(sx, .05, 2)
    number(sy, .03, 2)
    if config['combo'] and not all(k in c for k in ('Q', 'W', 'enemy', 'minion')):
        raise ValueError('Combo exige barras inimigas/minions e ícones Q e W disponíveis.')
    if config['farm'] and ('minion' not in c or config['minion_hp'] <= 0):
        raise ValueError('Last hit exige barra e HP máximo do tipo de minion.')
    if config['dodge'] and not c.get('projectiles'):
        raise ValueError('Esquiva exige cadastrar ao menos um projétil visual.')
    if not config['confirmed'] or not config['quickcast']:
        raise ValueError('Confirme patch/câmera e conjuração rápida de Q/W.')
    if not any(config[k] for k in ('combo', 'farm', 'dodge')):
        raise ValueError('Selecione ao menos uma função.')


class Application:
    def __init__(self, root, demo=False):
        self.root, self.demo = root, demo
        self.feed = Feed(demo)
        self.inputs = WindowsInput() if os.name == 'nt' and not demo else None
        self.scene = DemoScene() if demo else None
        self.stop, self.armed = threading.Event(), threading.Event()
        self.events = queue.Queue(maxsize=24)
        self.lock = threading.Lock()
        self.config = dict(DEFAULTS, calibration={}, generation=0)
        self.calibrating = False
        self.vars = {}
        self.last_message = 'Desarmado. Faça as calibrações antes de armar.'
        if not demo:
            try:
                stored = json.loads((DATA/'config.json').read_text(encoding='utf-8'))
                self.config.update(stored)
            except FileNotFoundError:
                pass
            except (ValueError, TypeError):
                logging.exception('Configuração inválida')
        else:
            self.config.update(calibration=self.scene.calibration, confirmed=True, quickcast=True,
                               minion_hp=477, dodge=True)
        self._build()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()
        self.root.after(100, self.tick)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def post(self, kind, value):
        try:
            self.events.put_nowait((kind, value))
        except queue.Full:
            try:
                self.events.get_nowait()
            except queue.Empty:
                pass
            self.events.put_nowait((kind, value))

    def _build(self):
        self.root.title('Zyon | Ezreal | Espaço: Q/W + esquiva | X: last hit')
        self.root.geometry(f'870x{max(700, min(870, self.root.winfo_screenheight()-90))}')
        self.root.minsize(760, 700)
        tabs = ttk.Notebook(self.root)
        tabs.pack(fill='both', expand=True, padx=8, pady=8)
        controls, setup, help_tab = (ttk.Frame(tabs) for _ in range(3))
        tabs.add(controls, text='Controles')
        tabs.add(setup, text='Calibração')
        tabs.add(help_tab, text='Instruções')
        ttk.Label(controls, text='ESPAÇO segurado: esquiva e Q/W nos alvos visuais ao alcance.\n'
                  'X segurado: last hit por AA perto do cursor. F10: desarma.\n'
                  'Esquiva usa somente as aparências de projéteis que você cadastrar.',
                  wraplength=820).pack(anchor='w', padx=8, pady=8)
        flags = ttk.Frame(controls)
        flags.pack(fill='x')
        for key, title in [('combo', 'Q/W automáticos enquanto segura Espaço'),
                           ('dodge', 'Esquiva enquanto segura Espaço'), ('farm', 'Last hit enquanto segura X'),
                           ('confirmed', 'Confirmo patch 16.22 / Summoner\'s Rift / câmera travada e escala constante'),
                           ('quickcast', 'Q e W usam conjuração rápida SEM indicador')]:
            var = tk.BooleanVar(value=bool(self.config[key]))
            self.vars[key] = var
            ttk.Checkbutton(flags, text=title, variable=var, command=self.armed.clear).pack(anchor='w', padx=8)
        form = ttk.Frame(controls)
        form.pack(fill='x', padx=8, pady=6)
        labels = [('max_step', 'Máximo deslocamento por esquiva (unidades)', 10, 300),
                  ('dodge_margin', 'Folga adicional da esquiva (unidades)', 0, 60),
                  ('horizon', 'Antecipação da esquiva (segundos)', .2, 1.2),
                  ('reaction_ms', 'Orçamento de reação/input (ms)', 30, 250),
                  ('range_margin', 'Margem conservadora de alcance Q/W (unidades)', 40, 250),
                  ('cursor_radius', 'Raio de seleção de campeão junto ao cursor (px)', 30, 500),
                  ('minion_hp', 'HP máximo do tipo de minion (manual)', 0, 20000),
                  ('minion_armor', 'Armadura do minion (manual)', 0, 1000),
                  ('impact_ms', 'AA: windup + viagem + rede (ms)', 50, 2000),
                  ('match_threshold', 'Similaridade mínima do projétil (0,70..0,99)', .70, .99)]
        self.ranges = {}
        for row, (key, label, low, high) in enumerate(labels):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky='w', pady=2)
            var = tk.StringVar(value=str(self.config[key]))
            self.vars[key] = var
            entry = ttk.Entry(form, textvariable=var, width=12)
            entry.grid(row=row, column=1, padx=8)
            entry.bind('<KeyRelease>', lambda _e: self.armed.clear())
            self.ranges[key] = (low, high)
        buttons = ttk.Frame(controls)
        buttons.pack(fill='x', padx=8, pady=5)
        ttk.Button(buttons, text='Salvar configuração', command=self.save).pack(side='left')
        self.arm_button = ttk.Button(buttons, text='Armar', command=self.toggle_arm)
        self.arm_button.pack(side='left', padx=8)
        self.status = ttk.Label(controls, text=self.last_message, wraplength=820)
        self.status.pack(fill='x', padx=8, pady=5)
        self.telemetry = ttk.Label(controls, text='', wraplength=820)
        self.telemetry.pack(fill='x', padx=8)
        self.preview = ttk.Label(controls)
        self.preview.pack(fill='both', expand=True, padx=8, pady=5)

        ttk.Label(setup, text='Calibre com o jogo no monitor principal, em janela sem bordas.\n'
                  'Cada captura começa após 3 segundos, permitindo voltar ao jogo.\n'
                  'Mude zoom, escala ou resolução: refaça todas as calibrações.', wraplength=820).pack(anchor='w', padx=8, pady=8)
        for kind, label in [('viewport', '1. Área útil do campo (excluir HUD/minimapa)'),
                            ('geometry', '2. Centro do Ezreal e círculo de alcance do AA'),
                            ('self', '3. Sua barra CHEIA e seus pés'),
                            ('enemy', '4. Barra CHEIA de campeão INIMIGO e pés'),
                            ('minion', '5. Barra CHEIA de minion INIMIGO e corpo'),
                            ('Q', '6. Interior do ícone Q DISPONÍVEL'),
                            ('W', '7. Interior do ícone W DISPONÍVEL'),
                            ('projectile', '8. Aparência de um projétil INIMIGO')]:
            ttk.Button(setup, text=label, command=lambda k=kind: self.capture(k)).pack(anchor='w', padx=8, pady=4)
        radius = ttk.Frame(setup)
        radius.pack(fill='x', padx=8, pady=5)
        ttk.Label(radius, text='Raio do próximo projétil (unidades; informar conforme a skill):').pack(side='left')
        self.projectile_radius = tk.StringVar(value='40')
        ttk.Entry(radius, textvariable=self.projectile_radius, width=8).pack(side='left', padx=8)
        ttk.Button(setup, text='Cadastrar projétil de uma imagem PNG/JPG',
                   command=self.projectile_from_file).pack(anchor='w', padx=8, pady=5)
        ttk.Button(setup, text='Limpar perfis de projéteis', command=self.clear_projectiles).pack(anchor='w', padx=8, pady=5)
        self.calibration_label = ttk.Label(setup, text='', wraplength=820)
        self.calibration_label.pack(fill='x', padx=8, pady=8)
        scroll = ttk.Scrollbar(help_tab)
        text = tk.Text(help_tab, wrap='word', yscrollcommand=scroll.set)
        scroll.configure(command=text.yview)
        scroll.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)
        text.insert('1.0', (BASE/'LEIA-ME.txt').read_text(encoding='utf-8'))
        text.configure(state='disabled')

    def settings(self):
        cfg = copy.deepcopy(self.config)
        for key, var in self.vars.items():
            cfg[key] = bool(var.get()) if isinstance(var, tk.BooleanVar) else number(var.get().replace(',', '.'), *self.ranges[key])
        return cfg

    def save(self):
        try:
            cfg = self.settings()
            cfg['generation'] = self.config.get('generation', 0)+1
            if not self.demo:
                temp = DATA/'config.tmp'
                temp.write_text(json.dumps(cfg, indent=2, allow_nan=False), encoding='utf-8')
                temp.replace(DATA/'config.json')
            with self.lock:
                self.config = cfg
            self.last_message = 'Configuração salva. Refaça a calibração se a imagem mudou.'
            return True
        except (ValueError, OSError) as exc:
            messagebox.showerror('Configuração', str(exc))
            return False

    def toggle_arm(self):
        if self.armed.is_set():
            self.armed.clear()
            return
        if not self.save():
            return
        try:
            validate_calibration(self.config)
            if not self.demo:
                if self.inputs is None:
                    raise ValueError('Input real exige Windows 10/11.')
                load_templates(self.config)
            self.armed.set()
        except (ValueError, OSError) as exc:
            messagebox.showerror('Armar', str(exc))

    def capture(self, kind):
        if self.demo or self.inputs is None:
            messagebox.showinfo('Calibração', 'Captura real exige Windows; o modo demo já possui calibração simulada.')
            return
        if kind == 'projectile':
            try:
                number(self.projectile_radius.get(), 5, 200)
            except ValueError as exc:
                messagebox.showerror('Projétil', str(exc))
                return
        self.armed.clear()
        self.calibrating = True
        self.root.withdraw()
        self.root.after(3000, lambda: self.capture_now(kind))

    def capture_now(self, kind):
        try:
            with mss.mss() as cap:
                monitor = cap.monitors[1]
                frame = np.asarray(cap.grab(monitor))[:, :, :3].copy()
            with self.lock:
                self.config['calibration']['resolution'] = [monitor[k] for k in ('width', 'height', 'left', 'top')]
            self.selection(frame, kind, monitor['left'], monitor['top'])
        except Exception as exc:
            self.root.deiconify()
            self.calibrating = False
            messagebox.showerror('Captura', str(exc))

    def projectile_from_file(self):
        if self.demo:
            return
        path = filedialog.askopenfilename(filetypes=[('Imagens', '*.png *.jpg *.jpeg')])
        if not path:
            return
        try:
            number(self.projectile_radius.get(), 5, 200)
            frame = cv2.imdecode(np.frombuffer(Path(path).read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError('Imagem inválida.')
            self.armed.clear()
            self.calibrating = True
            self.root.withdraw()
            self.selection(frame, 'projectile', 0, 0)
        except (ValueError, OSError) as exc:
            self.root.deiconify()
            self.calibrating = False
            messagebox.showerror('Imagem', str(exc))

    def clear_projectiles(self):
        self.armed.clear()
        with self.lock:
            self.config['calibration']['projectiles'] = []
        self.save()

    def selection(self, frame, kind, screen_x, screen_y):
        height, width = frame.shape[:2]
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes('-topmost', True)
        window.geometry(f'{width}x{height}{screen_x:+d}{screen_y:+d}')
        canvas = tk.Canvas(window, highlightthickness=0, cursor='crosshair')
        canvas.pack(fill='both', expand=True)
        image = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        canvas.create_image(0, 0, image=image, anchor='nw')
        canvas.image = image
        message = 'Arraste a região solicitada. Esc cancela.'
        if kind == 'geometry':
            message = 'Com círculo de AA visível: 1) clique nos PÉS do Ezreal. Esc cancela.'
        elif kind in ('self', 'enemy', 'minion'):
            message = 'Arraste SOMENTE o interior colorido da barra CHEIA, sem bordas. Esc cancela.'
        elif kind == 'projectile':
            message = 'Recorte pequeno e distinto do projétil inimigo. Evite fundo. Esc cancela.'
        label = canvas.create_text(12, 12, anchor='nw', fill='white', width=max(200, width-24),
                                   font=('Segoe UI', 15, 'bold'), text=message)
        state = {}
        def finish():
            window.destroy()
            self.root.deiconify()
            self.calibrating = False
        def error(exc):
            canvas.itemconfigure(label, text=str(exc)+' | Tente novamente ou Esc.')
        def commit(value):
            with self.lock:
                if kind == 'geometry':
                    self.config['calibration'].update(value)
                elif kind == 'projectile':
                    self.config['calibration'].setdefault('projectiles', []).append(value)
                else:
                    self.config['calibration'][kind] = value
            finish()
            self.save()
        def down(event):
            point = (event.x, event.y)
            if kind == 'geometry':
                points = state.setdefault('points', [])
                points.append(point)
                if len(points) == 1:
                    canvas.itemconfigure(label, text='2) Clique na BORDA DIREITA do círculo de AA.')
                elif len(points) == 2:
                    canvas.itemconfigure(label, text='3) Clique na BORDA INFERIOR do círculo de AA.')
                else:
                    try:
                        center, right, bottom = points
                        data, age, _ = self.feed.read()
                        if not live_valid(data, age):
                            raise ValueError('Calibração de alcance exige Ezreal vivo e API atual.')
                        attack_range = data['activePlayer']['championStats']['attackRange']
                        sx = number((right[0]-center[0])/attack_range, .05, 2)
                        sy = number((bottom[1]-center[1])/attack_range, .03, 2)
                        commit(dict(center=list(center), projection=[sx, sy]))
                    except (ValueError, KeyError, ZeroDivisionError) as exc:
                        state['points'] = []
                        error(exc)
                return
            if 'bar' in state:
                x, y, w, h = state['rect']
                offset = [point[0]-(x+w/2), point[1]-y]
                if abs(offset[0]) > 100 or not 0 < offset[1] < 180:
                    error('Ponto de pés/corpo incompatível com a barra. Clique novamente.')
                    return
                commit(dict(profile=state['bar'].serializable(), offset=offset))
                return
            state['start'] = point
            state['box'] = canvas.create_rectangle(*point, *point, outline='cyan')
        def move(event):
            if 'start' in state and 'bar' not in state:
                canvas.coords(state['box'], *state['start'], event.x, event.y)
        def release(event):
            if 'start' not in state or 'bar' in state or kind == 'geometry':
                return
            x0, x1 = sorted((max(0, min(width, state['start'][0])), max(0, min(width, event.x))))
            y0, y1 = sorted((max(0, min(height, state['start'][1])), max(0, min(height, event.y))))
            rect = [x0, y0, x1-x0, y1-y0]
            crop = frame[y0:y1, x0:x1]
            try:
                if kind in ('self', 'enemy', 'minion'):
                    state.update(bar=BarProfile.from_image(crop), rect=rect)
                    canvas.itemconfigure(label, text='Agora clique nos PÉS do campeão ou no CORPO do minion.')
                elif kind == 'viewport':
                    if rect[2] < 300 or rect[3] < 200:
                        raise ValueError('Área útil muito pequena.')
                    commit(rect)
                elif kind in ('Q', 'W', 'projectile'):
                    if not 6 <= rect[2] <= 128 or not 6 <= rect[3] <= 128 or crop.std() < 8:
                        raise ValueError('Recorte deve ter 6..128 px por lado e detalhes distintos.')
                    if kind in ('Q', 'W'):
                        file = f'assets/{kind}-ready.png'
                    else:
                        if len(self.config['calibration'].get('projectiles', [])) >= 8:
                            raise ValueError('Limite de 8 aparências. Remova perfis antes de adicionar.')
                        file = f'assets/projectile-{time.time_ns()}.png'
                    ok, png = cv2.imencode('.png', crop)
                    if not ok:
                        raise ValueError('Falha ao gravar template.')
                    asset_path(file).write_bytes(png.tobytes())
                    if kind == 'projectile':
                        commit(dict(file=file, radius=number(self.projectile_radius.get(), 5, 200), name='Projétil visual'))
                    else:
                        commit(dict(file=file, rect=rect))
            except (ValueError, OSError, cv2.error) as exc:
                error(exc)
        canvas.bind('<ButtonPress-1>', down)
        canvas.bind('<B1-Motion>', move)
        canvas.bind('<ButtonRelease-1>', release)
        window.bind('<Escape>', lambda _e: finish())
        window.focus_force()

    def can_act(self, hold_key, frame_time):
        if not self.inputs or not self.armed.is_set() or self.calibrating or time.monotonic()-frame_time > .18:
            return False
        if self.inputs.held(0x79) or not self.inputs.held(hold_key):
            return False
        data, age, _ = self.feed.read()
        return live_valid(data, age)

    def _run(self):
        engine = Engine(RULES)
        cap, generation, templates = None, None, {}
        started, last_preview = time.monotonic(), 0
        try:
            if self.inputs:
                cap = mss.mss()
            while not self.stop.wait(.035):
                try:
                    if self.inputs and self.inputs.held(0x79):
                        self.armed.clear()
                        engine.reset_tracking()
                        self.post('status', 'F10: desarmado.')
                        continue
                    if not self.armed.is_set() or self.calibrating:
                        engine.reset_tracking()
                        continue
                    with self.lock:
                        cfg = copy.deepcopy(self.config)
                    if generation != cfg['generation']:
                        templates = self.scene.templates if self.demo else load_templates(cfg)
                        generation = cfg['generation']
                        engine.reset_tracking()
                    data, age, feed_status = self.feed.read()
                    if not live_valid(data, age):
                        engine.reset_tracking()
                        self.post('status', feed_status+' | Sem Ezreal vivo/telemetria atual.')
                        continue
                    if self.demo:
                        now = time.monotonic()
                        frame = self.scene.frame(now-started)
                        cursor, space, farm_held = (800, 350), True, False
                        left = top = 0
                    else:
                        if not self.inputs.game_foreground():
                            engine.reset_tracking()
                            continue
                        space, farm_held = self.inputs.held(0x20), self.inputs.held(ord(cfg['farm_key']))
                        if not space and not farm_held:
                            engine.reset_tracking()
                            continue
                        monitor = cap.monitors[1]
                        resolution = [monitor[k] for k in ('width', 'height', 'left', 'top')]
                        if cfg['calibration']['resolution'] != resolution:
                            self.armed.clear()
                            self.post('status', 'Monitor/resolução mudou. Recalibre.')
                            continue
                        left, top = monitor['left'], monitor['top']
                        cursor_abs = self.inputs.cursor()
                        cursor = (cursor_abs[0]-left, cursor_abs[1]-top)
                        now = time.monotonic()
                        frame = np.asarray(cap.grab(monitor))[:, :, :3].copy()
                    action = engine.step(frame, data, cfg, templates, cursor, space, farm_held, now)
                    if action:
                        sent = self.demo or self.inputs.perform(action.point[0]+left, action.point[1]+top,
                            lambda: self.can_act(action.hold_key, now), action.spell)
                        if sent:
                            engine.mark_sent(action, time.monotonic(), data['activePlayer'], cfg)
                            x, y = map(int, action.point)
                            cv2.circle(frame, (x, y), 16, (0, 255, 255), 2)
                    self.post('status', ('SIMULAÇÃO | ' if self.demo else '')+engine.status)
                    if now-last_preview > .2:
                        self.post('preview', frame)
                        last_preview = now
                except Exception as exc:
                    self.armed.clear()
                    engine.reset_tracking()
                    logging.exception('Falha: automação desarmada')
                    self.post('status', f'Falha: {exc}. Veja data/app.log.')
        except Exception as exc:
            self.armed.clear()
            logging.exception('Falha ao iniciar captura')
            self.post('status', f'Captura indisponível: {exc}')
        finally:
            if cap:
                cap.close()

    def tick(self):
        if self.stop.is_set():
            return
        for _ in range(30):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'status':
                self.last_message = value
            elif kind == 'preview':
                image = Image.fromarray(cv2.cvtColor(value, cv2.COLOR_BGR2RGB))
                image.thumbnail((820, 310))
                self.preview.image = ImageTk.PhotoImage(image)
                self.preview.configure(image=self.preview.image)
        self.status.configure(text=('ARMADO | ' if self.armed.is_set() else 'DESARMADO | ')+self.last_message)
        self.arm_button.configure(text='Desarmar' if self.armed.is_set() else 'Armar')
        data, age, feed_status = self.feed.read()
        if data and age < 1:
            stats = data['activePlayer']['championStats']
            self.telemetry.configure(text=f'{feed_status} HP {stats["currentHealth"]:.0f} | '
                f'AD {stats["attackDamage"]:.0f} | mana {stats["resourceValue"]:.0f} | alcance AA {stats["attackRange"]:.0f}')
        else:
            self.telemetry.configure(text=feed_status)
        with self.lock:
            c = self.config['calibration']
            names = ', '.join(k for k in c if k != 'projectiles')
            n = len(c.get('projectiles', []))
        self.calibration_label.configure(text=f'Calibrado: {names or "nenhum"}. Aparências de projéteis: {n}/8.')
        self.root.after(100, self.tick)

    def close(self):
        self.armed.clear()
        self.stop.set()
        self.feed.close()
        self.worker.join(timeout=3)
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Simulação visual, nunca envia input real.')
    args = parser.parse_args()
    if os.name == 'nt':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (OSError, AttributeError):
            ctypes.windll.user32.SetProcessDPIAware()
    root = tk.Tk()
    Application(root, args.demo)
    root.mainloop()


if __name__ == '__main__':
    main()
