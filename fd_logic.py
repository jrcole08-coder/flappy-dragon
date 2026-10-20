"""Flappy Dragon game logic (state, input, AI, spawning)."""
from fd_core import *
from fd_art import *
from fd_sound import AUDIO, BREATH_LOOP, WEATHER_LOOP

class GameLogic:
  def __init__(self):
    self.data = load_data()
    AUDIO.set_enabled(self.data.get('sound', True))
    AUDIO.set_music(self.data.get('music', True))
    AUDIO.set_sfx(self.data.get('sfx', True))
    AUDIO.start_music()
    self.state = "MENU"
    self.selected = "RED"
    self.pending = None
    self.confirm_menu = False
    self.opt_from = "MENU"
    self.fullscreen = False
    self.anim = 0.0
    self.shake_i = self.shake_t = 0
    self.far_x = self.near_x = self.mid_x = 0.0
    self.twinkle = [(random.randint(0, WIDTH), random.randint(0, 360), random.uniform(0, 6.28)) for _ in range(26)]
    self.clouds = [[random.uniform(-100, WIDTH), random.randint(20, 200), random.randint(0, 2), random.uniform(0.2, 0.5)] for _ in range(7)]
    self.mist = [[random.uniform(0, WIDTH), random.randint(HEIGHT - 100, GROUND_Y - 8), random.uniform(1, 3)] for _ in range(14)]
    self.embers = [self.new_ember(True) for _ in range(34)]
    self.menu_dragon_x = -140.0
    self.scroll = float(BASE_SCROLL)
    self.scroll_px = 6
    self.mouse = (0, 0)
    self.over_t = 0
    self.new_record = False
    self.surface = screen            # the surface we present to (changes if fullscreen is toggled)
    self.view_sy = 1.0
    self.view = (1.0, 0, 0)          # (scale, x_offset, y_offset) of the picture when letterboxed
    self.scale_buf = None
    self.intro_layer = None
    self.intro_t = 0
    self.toast_msg, self.toast_t = '', 0
    self.reset_run()
    self.roll_quest()

  def reset_run(self):
    self.dragon = pygame.Rect(150, HEIGHT // 2, 65, 38)
    self.vel = 0.0
    self.wing = 0.0
    self.pitch = 0.0
    self.score = 0
    self.dp = 0.0
    self.shields = 0
    self.shield_active = False
    self.shield_timer = 0
    self.hearts = 3 if self.data.get('difficulty', 'easy') == 'easy' else 0
    self.hit_inv = 0
    self.dash_state = 'idle'
    self.dash_cd = 0
    self.dash_inv = 0
    self.dash_boss = False
    self.run_coins = 0.0
    self.breath = False
    self.breath_timer = 0
    self.ts = 1.0
    self.slow_acc = 0.0
    self.tick = True
    self.threat = 1
    self.boss = None
    self.b1 = self.b2 = False
    self.init_weather()
    self.day = (random.random() < 0.45 or not self.data.get('weather', True)) and ensure_day_assets()
    for n in GROUND_LISTS + ('enemies', 'fireballs', 'arrows', 'orbs', 'spears', 'scenery', 'particles', 'powerups', 'coins', 'bolts', 'globs', 'lava'):
      setattr(self, n, [])
    self.spawn_t = self.scenery_t = self.power_t = 0
    self.dead = False
    self.prefill_scenery()
    if self.data.get('fullscreen', True):
      self.set_fullscreen(True, quiet=True)

  def init_weather(self):
    k = random.choices(WEATHER_KINDS, WEATHER_WEIGHTS)[0]
    if not self.data.get('weather', True):
      k = "clear"
    self.wx_kind, self.wx_t, self.gust = k, 0, 0.0
    self.flash, self.bolt, self.bolt_t = 0, None, random.randint(90, 240)
    n = {"rain": 70, "storm": 95, "snow": 55, "wind": 22}.get(k, 0)
    self.wx_parts = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(0.7, 1.3), random.uniform(0, 6.28)] for _ in range(n)]

  def update_weather(self):
    try:
      self._update_weather()
    except Exception:
      self.wx_kind = "clear"

  def _update_weather(self):
    k = self.wx_kind
    if k == "clear":
      return
    self.wx_t += 1
    wind = 0.0
    if k in ("wind", "storm"):
      wind = math.sin(self.wx_t * 0.02) * math.sin(self.wx_t * 0.013)
    self.gust = wind * (0.13 if k == "wind" else 0.05)
    for p in self.wx_parts:
      if k in ("rain", "storm"):
        p[1] += 22 * p[2]
        p[0] -= 4 + wind * 4
      elif k == "snow":
        p[1] += 1.8 * p[2]
        p[0] += math.sin(self.wx_t * 0.04 + p[3]) * 0.8 - 1
      elif k == "wind":
        p[0] -= 26 * p[2]
        p[1] += math.sin(self.wx_t * 0.05 + p[3]) * 0.6
      if p[1] > HEIGHT or p[0] < -60 or p[0] > WIDTH + 20:
        if k == "wind":
          p[0], p[1] = WIDTH + random.uniform(0, 80), random.uniform(0, GROUND_Y)
        else:
          p[0], p[1] = random.uniform(0, WIDTH + 40), -random.uniform(0, 30)
    if k == "storm":
      if self.flash > 0:
        self.flash -= 1
      self.bolt_t -= 1
      if self.bolt_t <= 0:
        self.bolt_t = random.randint(150, 420)
        self.flash = 7
        AUDIO.play('thunder')
        bx, by, pts = random.randint(60, WIDTH - 60), 0, []
        while by < GROUND_Y - 20:
          pts.append((bx, by))
          bx += random.randint(-28, 28)
          by += random.randint(30, 60)
        pts.append((bx, GROUND_Y))
        self.bolt = pts
        self.shake_for(3, 6)

  def draw_weather(self, gs):
    try:
      self._draw_weather(gs)
    except Exception:
      self.wx_kind = "clear"

  def _draw_weather(self, gs):
    k = self.wx_kind
    if k == "clear":
      return
    if k == "storm":
      gs.fill((46, 46, 34), special_flags=pygame.BLEND_RGB_SUB)
    elif k == "rain":
      gs.fill((24, 24, 18), special_flags=pygame.BLEND_RGB_SUB)
    elif k == "fog":
      gs.fill((56, 62, 74), special_flags=pygame.BLEND_RGB_ADD)
      for i in range(6 if WISP else 0):
        gs.blit(WISP, (int((self.wx_t * (0.5 + i * 0.12) + i * 190) % (WIDTH + 260)) - 240, 40 + i * 70))
    elif k == "snow":
      gs.fill((14, 16, 24), special_flags=pygame.BLEND_RGB_ADD)
    if k in ("rain", "storm"):
      for p in self.wx_parts:
        x, y = int(p[0]), int(p[1])
        pygame.draw.line(gs, (150, 170, 205), (x, y), (x - 3, y + 11), 1)
    elif k == "snow":
      for p in self.wx_parts:
        pygame.draw.circle(gs, (240, 245, 255), (int(p[0]), int(p[1])), 2 if p[2] > 1.0 else 1)
    elif k == "wind":
      for p in self.wx_parts:
        x, y = int(p[0]), int(p[1])
        pygame.draw.line(gs, (170, 180, 195), (x, y), (x + int(34 * p[2]), y + 1), 1)
    if k == "storm" and self.flash > 0:
      if self.bolt:
        pygame.draw.lines(gs, (190, 200, 255), False, self.bolt, 6)
        pygame.draw.lines(gs, (255, 255, 255), False, self.bolt, 2)
      c = min(120, self.flash * 18)
      gs.fill((c, c, c), special_flags=pygame.BLEND_RGB_ADD)
    if self.state == "PLAYING" and k in WEATHER_NAMES and self.wx_t < 200:
      col = (255, 255, 255) if self.wx_t < 150 else (190, 190, 200)
      blit_text(gs, small_font, "Weather: " + WEATHER_NAMES[k], col, (WIDTH // 2, 82), "center")

  def roll_quest(self):
    q = self.data.get('active_quest')
    if not q or q.get('done'):
      q = random.choice(BOUNTIES).copy()
      q['progress'] = 0
      q['done'] = False
      self.data['active_quest'] = q
      save_data(self.data)
    self.bounty = q

  def start_run(self):
    prewarm_dragon(self.selected)
    self.reset_run()
    self.compute_params()
    self.roll_quest()
    self.confirm_menu = False
    self.intro_t = 0
    self.state = "INTRO"

  def new_ember(self, anywhere=False):
    return [random.uniform(0, WIDTH), random.uniform(0, HEIGHT) if anywhere else HEIGHT + 5, random.uniform(0.4, 1.4), random.randint(2, 5), random.uniform(0, 6.28)]

  def shake_for(self, intensity, duration):
    self.shake_i, self.shake_t = intensity, max(self.shake_t, duration)

  def emit(self, x, y, vx, vy, size, color):
    if len(self.particles) < MAX_PARTICLES:
      self.particles.append([x, y, vx, vy, size, color])

  def burst(self, x, y, n, speed, smin, smax, color):
    for _ in range(n):
      self.emit(x, y, random.uniform(-speed, speed), random.uniform(-speed, speed), random.randint(smin, smax), color)

  def compute_params(self):
    up, sel = self.data['upgrades'], self.selected
    self.threat = 1 + self.score // 300
    self.scroll = BASE_SCROLL * 0.2 if self.boss else BASE_SCROLL + self.threat * 0.4
    self.scroll_px = int(math.ceil(self.scroll))
    self.gravity = 0.40 if sel == "BLUE" else BASE_GRAVITY
    self.breath_time = (380 if sel == "RED" else 240) + up['deep_lungs'] * 60
    self.score_mult = 1
    self.coin_val = 1.5 if sel == "CHINESE" else 1.0
    self.ts = 0.5 if (sel == "CHRONO" and self.breath) else 1.0
    self.slow_acc = getattr(self, 'slow_acc', 0.0) + self.ts
    self.tick = self.slow_acc >= 1.0
    if self.tick:
      self.slow_acc -= 1.0
    self.max_shields = 3 + up['thick_scales']
    self.magnet = 50 + up['coin_magnet'] * 60

  def bounty_add(self, kind):
    q = self.bounty
    if q and q['type'] == kind and not q.get('done'):
      q['progress'] += 1

  def spawn_scenery(self, x):
    t = random.choices(SCENERY_TYPES, SCENERY_WEIGHTS)[0]
    if t == "grass":
      t = "grass%d" % random.randint(0, 2)
    elif t == "flowers":
      t = "flowers%d" % random.randint(0, 1)
    self.scenery.append({'type': t, 'x': float(x), 'anim': random.uniform(0, 10), 'mod': random.uniform(0.8, 2.5)})

  def prefill_scenery(self):
    for _ in range(16):
      self.spawn_scenery(random.randint(0, WIDTH))

  def update_scenery(self, speed, interval):
    keep = []
    for s in self.scenery:
      if speed:
        s['anim'] += 0.2
        s['x'] -= speed + (s['mod'] if s['type'] in ("sheep", "deer", "knight", "dwarf") else 0)
      if s['x'] > -170:
        keep.append(s)
    self.scenery = keep
    self.scenery_t += 1
    if self.scenery_t > interval and speed:
      self.scenery_t = 0
      self.spawn_scenery(WIDTH)

  def run(self):
    while True:
      for e in pygame.event.get():
        if e.type == pygame.QUIT:
          self.quit()
        self.handle_event(e)
      self.mouse = self.map_pos(pygame.mouse.get_pos())
      self.update()
      self.draw()
      clock.tick(FPS)

  def quit(self):
    save_data(self.data)
    pygame.quit()
    sys.exit()

  def handle_event(self, e):
    st = self.state
    click = e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
    pos = self.map_pos(e.pos) if hasattr(e, 'pos') else (0, 0)
    key = e.key if e.type == pygame.KEYDOWN else None
    if key == pygame.K_F11:
      self.set_fullscreen(not self.fullscreen)
      self.data['fullscreen'] = self.fullscreen
      save_data(self.data)
      return
    if key == pygame.K_m or (click and st in ("MENU", "PAUSED") and SND_BTN.collidepoint(pos)):
      self.toggle_sound()
      return

    if st == "MENU":
      if key in (pygame.K_RETURN, pygame.K_SPACE):
        self.start_run()
      if click:
        for k, r in MENU_RECTS.items():
          if r.collidepoint(pos):
            self.menu_action(k)
    elif st == "OPTIONS":
      if (click and BACK_BTN.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = self.opt_from
      elif click:
        for k, r in OPT_RECTS.items():
          if k in ("weather", "difficulty") and self.opt_from == "PAUSED":
            continue
          if r.collidepoint(pos):
            self.option_action(k)
    elif st in ("QUESTS", "HOARD"):
      if (click and BACK_BTN.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = "MENU"
      elif click and st == "HOARD":
        for k, _t, _d, rect in UPGRADES:
          lvl = self.data['upgrades'][k]
          btn = pygame.Rect(rect.left + 20, rect.bottom - 50, 140, 35)
          if lvl < 3 and btn.collidepoint(pos) and self.data['coins'] >= UPGRADE_COSTS[lvl]:
            self.data['coins'] -= UPGRADE_COSTS[lvl]
            self.data['upgrades'][k] += 1
            save_data(self.data)
    elif st in ("SELECT", "RARE_SELECT"):
      boxes = SELECT_BOXES if st == "SELECT" else RARE_BOXES
      if click:
        if self.pending:
          if BUY_YES.collidepoint(pos):
            cost = DRAGON_PALETTES[self.pending]['cost']
            if self.data['coins'] >= cost:
              self.data['coins'] -= cost
              self.data['unlocked'].append(self.pending)
              self.selected = self.pending
              save_data(self.data)
            self.pending = None
          elif BUY_NO.collidepoint(pos):
            self.pending = None
        else:
          for k, r in boxes:
            if r.collidepoint(pos):
              if k in self.data['unlocked']:
                self.selected = k
              elif self.data['coins'] >= DRAGON_PALETTES[k]['cost']:
                self.pending = k
          if SEL_BACK_BTN.collidepoint(pos):
            self.state = "MENU" if st == "SELECT" else "SELECT"
          elif st == "SELECT" and RARE_BTN.collidepoint(pos):
            self.state = "RARE_SELECT"
      elif key == pygame.K_ESCAPE:
        self.pending = None
        self.state = "MENU" if st == "SELECT" else "SELECT"
    elif st == "INTRO":
      if click or key in (pygame.K_SPACE, pygame.K_RETURN):
        self.state = "PLAYING"
    elif st == "PLAYING":
      if click:
        if PAUSE_BTN.collidepoint(pos):
          self.pause()
        elif SHIELD_BTN.collidepoint(pos):
          self.use_shield()
        elif DASH_BTN.collidepoint(pos):
          self.try_dash()
        else:
          self.flap()
      elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
        self.flap()
      elif key in (pygame.K_p, pygame.K_ESCAPE):
        self.pause()
      elif key in (pygame.K_s, pygame.K_DOWN):
        self.use_shield()
      elif key in (pygame.K_d, pygame.K_RIGHT, pygame.K_LSHIFT, pygame.K_RSHIFT):
        self.try_dash()
    elif st == "PAUSED":
      if click:
        if not self.confirm_menu:
          if RESUME_BTN.collidepoint(pos):
            self.state = "PLAYING"
          elif OPT_BTN.collidepoint(pos):
            self.opt_from = "PAUSED"
            self.state = "OPTIONS"
          elif MENU_BTN.collidepoint(pos):
            self.confirm_menu = True
        else:
          if YES_BTN.collidepoint(pos):
            self.state = "MENU"
            self.confirm_menu = False
          elif NO_BTN.collidepoint(pos):
            self.confirm_menu = False
      elif key in (pygame.K_p, pygame.K_ESCAPE):
        self.state = "PLAYING"
    elif st == "GAMEOVER":
      if (click or key in (pygame.K_SPACE, pygame.K_RETURN)) and self.over_t > 25:
        self.state = "MENU"

  def option_action(self, k):
    AUDIO.play('click')
    d = self.data
    if k == "music":
      d['music'] = not d.get('music', True)
      AUDIO.set_music(d['music'])
    elif k == "sfx":
      d['sfx'] = not d.get('sfx', True)
      AUDIO.set_sfx(d['sfx'])
      if d['sfx']:
        AUDIO.play('click')
    elif k == "display":
      self.set_fullscreen(not self.fullscreen)
      d['fullscreen'] = self.fullscreen
    elif k == "difficulty":
      d['difficulty'] = 'hard' if d.get('difficulty', 'easy') == 'easy' else 'easy'
    elif k == "weather":
      d['weather'] = not d.get('weather', True)
      if not d['weather']:
        self.wx_kind, self.wx_parts, self.flash, self.bolt = "clear", [], 0, None
        self.day = ensure_day_assets()
      else:
        self.init_weather()
    save_data(d)

  def toggle_sound(self):
    on = not AUDIO.enabled
    self.data['sound'] = on
    save_data(self.data)
    AUDIO.set_enabled(on)
    AUDIO.play('click')

  def flap(self):
    if self.dash_state == 'out':
      return
    self.vel = FLAP_STRENGTH
    AUDIO.play('flap', 0.7)

  def menu_action(self, k):
    AUDIO.play('click')
    if k == "play":
      self.start_run()
    elif k == "roster":
      self.state = "SELECT"
    elif k == "hoard":
      self.state = "HOARD"
    elif k == "quests":
      self.state = "QUESTS"
    elif k == "options":
      self.opt_from = "MENU"
      self.state = "OPTIONS"
    elif k == "exit":
      self.quit()

  def map_pos(self, pos):
    """Touch/mouse position -> game coordinates (undoes letterboxing)."""
    sc, vx, vy = self.view
    if sc == 1.0 and not vx and not vy and self.view_sy == 1.0:
      return pos
    return (int((pos[0] - vx) / sc), int((pos[1] - vy) / self.view_sy))

  def display_is_full(self, surf):
    try:
      if surf.get_flags() & pygame.FULLSCREEN:
        return True
    except Exception:
      pass
    try:
      ww, wh = pygame.display.get_window_size()
      dw, dh = pygame.display.get_desktop_sizes()[0]
      return ww >= dw - 2 and wh >= dh - 2
    except Exception:
      return False

  def set_fullscreen(self, on, quiet=False):
    """Try a few fullscreen methods (phones are picky) and check which one really worked."""
    self.view = (1.0, 0, 0)
    self.view_sy = 1.0
    self.scale_buf = None
    if not on:
      try:
        self.surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
      except Exception:
        pass
      self.fullscreen = False
      return
    for size, flags in (((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN),
              ((0, 0), pygame.FULLSCREEN)):
      try:
        surf = pygame.display.set_mode(size, flags)
      except Exception:
        continue
      if self.display_is_full(surf):
        self.surface = surf
        self.fullscreen = True
        return
    try:
      self.surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    except Exception:
      pass
    self.fullscreen = False
    if not quiet:
      self.toast("Fullscreen isn't available here")

  def toast(self, msg):
    self.toast_msg, self.toast_t = msg, 150

  def present(self, ox, oy):
    surf = self.surface
    sw, sh = surf.get_size()
    if (sw, sh) == (WIDTH, HEIGHT):
      self.view = (1.0, 0, 0)
      self.view_sy = 1.0
      surf.blit(game_surface, (ox, oy))
    else:
      sc = min(sw / float(WIDTH), sh / float(HEIGHT))
      dw, dh = int(WIDTH * sc), int(HEIGHT * sc)
      vx, vy = (sw - dw) // 2, (sh - dh) // 2
      self.view = (sc, vx, vy)
      self.view_sy = sc
      buf = self.scale_buf
      if buf is None or buf.get_size() != (dw, dh):
        buf = self.scale_buf = pygame.Surface((dw, dh)).convert()
      try:
        pygame.transform.scale(game_surface, (dw, dh), buf)
      except Exception:
        buf = pygame.transform.scale(game_surface, (dw, dh))
      surf.blit(buf, (vx + int(ox * sc), vy + int(oy * sc)))
      if vx > 0 or vy > 0:
        try:
          if vx > 0:
            surf.blit(pygame.transform.scale(game_surface.subsurface((0, 0, 1, HEIGHT)), (vx, dh)), (0, vy))
            surf.blit(pygame.transform.scale(game_surface.subsurface((WIDTH - 1, 0, 1, HEIGHT)), (sw - vx - dw, dh)), (vx + dw, vy))
          if vy > 0:
            surf.blit(pygame.transform.scale(game_surface.subsurface((0, 0, WIDTH, 1)), (dw, vy)), (vx, 0))
            surf.blit(pygame.transform.scale(game_surface.subsurface((0, HEIGHT - 1, WIDTH, 1)), (dw, sh - vy - dh)), (vx, vy + dh))
        except Exception:
          surf.fill((0, 0, 0))
    pygame.display.flip()

  def pause(self):
    self.state = "PAUSED"
    self.confirm_menu = False

  def use_shield(self):
    if self.shields > 0 and not self.shield_active:
      self.shields -= 1
      self.shield_active = True
      self.shield_timer = 420
      AUDIO.play('shield')

  def try_dash(self):
    if self.dash_state != 'idle' or self.dash_cd > 0 or self.state != "PLAYING":
      return
    self.dash_state = 'out'
    self.dash_cd = DASH_COOLDOWN
    self.dash_boss = False
    self.dash_inv = 999
    self.vel = 0.0
    AUDIO.play('whoosh')
    AUDIO.play('roar', 0.5)
    self.shake_for(3, 6)

  def dash_target(self):
    return 150 + min(DASH_REACH, (WIDTH - 215) // 2)

  def update_dash(self):
    d = self.dragon
    if self.dash_cd > 0:
      self.dash_cd -= 1
    st = self.dash_state
    if st == 'idle':
      return
    tr = DRAGON_PALETTES[self.selected]['trail']
    if st == 'out':
      self.vel = 0.0
      for _ in range(3):
        self.emit(d.x + random.randint(0, 30), d.centery + random.randint(-18, 18), random.uniform(-6, -2), random.uniform(-1, 1), random.randint(8, 14), random.choice(tr))
      d.x += DASH_SPEED
      self.dash_sweep()
      if d.x >= self.dash_target():
        d.x = self.dash_target()
        self.dash_state = 'back'
        self.dash_inv = 45
    else:
      if self.dash_inv > 0:
        self.dash_inv -= 1
      d.x -= 3 if d.x - 150 > 60 else 2
      if d.x <= 150:
        d.x = 150
        self.dash_state = 'idle'
        self.dash_inv = 0

  def dash_sweep(self):
    d = self.dragon
    sw = pygame.Rect(d.x - 10, d.y - 22, d.w + 50, d.h + 44)
    hit = 0
    for name in GROUND_LISTS + ('enemies',):
      for o in getattr(self, name):
        if o.get('shattered') or not sw.colliderect(o['rect']):
          continue
        o['shattered'] = True
        hit += 1
        cx, cy = o['rect'].center
        self.burst(cx, cy, 22, 6, 6, 14, FIRE_CORE)
        self.burst(cx, cy, 14, 5, 4, 10, DRAGON_PALETTES[self.selected]['main'])
        self.score += 10 * self.score_mult
        self.dp += 4
        self.bounty_add('shatter')
    for p in self.fireballs + self.arrows + self.orbs:
      if not p.get('shattered') and sw.colliderect(pygame.Rect(int(p['x'] - 14), int(p['y'] - 14), 28, 28)):
        p['shattered'] = True
        self.burst(p['x'], p['y'], 8, 4, 3, 8, FIRE_CORE)
    for p in self.spears:
      if not p.get('shattered') and sw.colliderect(pygame.Rect(int(p['x'] - 30), int(p['y'] - 12), 60, 24)):
        p['shattered'] = True
        self.burst(p['x'], p['y'], 10, 5, 3, 9, FIRE_CORE)
    b = self.boss
    if b and b.get('fwaves'):
      for w in b['fwaves']:
        if sw.colliderect(pygame.Rect(int(w['x'] - 10), int(w['y'] - 55), 30, 110)):
          w['x'] = -999.0
          self.burst(w['x'] + 999, w['y'], 10, 5, 4, 9, (255, 150, 40))
    if b and b['state'] == 'fighting' and not b.get('ghost') and not self.dash_boss and sw.colliderect(self.boss_rect(b)):
      self.dash_boss = True
      if b.get('sh', 0) > 0:
        b['hp'] += 30
        self.burst(d.right + 20, d.centery, 20, 6, 4, 10, (255, 90, 70))
      b['hp'] -= 30
      b['flash'] = 10
      self.burst(d.right + 20, d.centery, 30, 7, 6, 14, (255, 220, 120))
      self.dash_state = 'back'
      self.dash_inv = 45
    if hit:
      AUDIO.play('shatter', 0.8)
      self.shake_for(6, 8)

  def update(self):
    st = self.state
    AUDIO.tick()
    if st != "PLAYING":
      AUDIO.set_loop('breath', None)
      AUDIO.set_loop('weather', None)
    if st == "PAUSED":
      return
    self.anim += 0.05
    if self.shake_t > 0:
      self.shake_t -= 1

    playing = st in ("PLAYING", "INTRO")
    self.far_x += self.scroll * 0.1 if playing else 0.05
    self.near_x += self.scroll * 0.2 if playing else 0.10
    self.mid_x += self.scroll * 0.4 if playing else 0.2
    for c in self.clouds:
      c[0] -= c[3] if playing else c[3] * 0.2
      if c[0] < -220:
        c[0], c[1] = WIDTH + 50, random.randint(20, 220)
    for m in self.mist:
      m[0] -= m[2] * self.scroll * 0.1 if playing else 0.5
      if m[0] < -60:
        m[0] = WIDTH + 10

    if st == "INTRO":
      self.update_intro()
      self.update_scenery(self.scroll_px, 10)
    elif playing:
      self.update_playing()
      self.update_scenery(self.scroll_px, max(4, 10 - self.threat // 2))
    elif st == "GAMEOVER":
      self.over_t += 1
      self.vel += BASE_GRAVITY
      self.dragon.y = min(self.dragon.y + int(self.vel), GROUND_Y - self.dragon.height + 8)
      self.update_scenery(0, 99)
    else:
      self.update_scenery(1, 24)
      if st == "MENU":
        self.update_menu_fx()
    self.update_particles()

  def update_intro(self):
    self.intro_t += 1
    self.update_weather()
    self.wing += 0.38
    self.dragon.y = HEIGHT // 2 + int(math.sin(self.intro_t * 0.07) * 14)
    self.vel = 0.0
    t = self.intro_t
    if t in (1, 61, 121):
      AUDIO.play('click')
    elif t == 181:
      AUDIO.play('roar', 0.8)
      self.shake_for(3, 12)
    if t >= INTRO_FRAMES:
      self.dragon.y = HEIGHT // 2
      self.state = "PLAYING"

  def update_menu_fx(self):
    for e in self.embers:
      e[1] -= e[2]
      e[0] += math.sin(self.anim * 2 + e[4]) * 0.4
      if e[1] < -10:
        e[:] = self.new_ember()
    self.menu_dragon_x += 2.2
    if self.menu_dragon_x > WIDTH + 140:
      self.menu_dragon_x = -140.0
    if int(self.anim * 20) % 2 == 0:
      tr = DRAGON_PALETTES[self.selected]['trail']
      my = 320 + math.sin(self.anim * 1.3) * 45
      self.emit(self.menu_dragon_x + 4, my + 24, random.uniform(-2.5, -0.5), random.uniform(-1, 1), random.randint(5, 9), random.choice(tr))

  def update_particles(self):
    alive = []
    for p in self.particles:
      p[0] += p[2]
      p[1] += p[3]
      p[4] -= 0.30
      if p[4] >= 1:
        alive.append(p)
    self.particles = alive

  def update_playing(self):
    sel, d = self.selected, self.dragon
    self.compute_params()
    sc = self.scroll_px
    self.vel += self.gravity + self.gust
    self.update_weather()
    AUDIO.set_loop('weather', WEATHER_LOOP.get(self.wx_kind))
    AUDIO.set_loop('breath', BREATH_LOOP.get(sel, 'fire') if self.breath else None)
    d.y += int(self.vel)
    self.update_dash()
    self.wing += 0.38
    self.pitch = max(-18.0, min(self.vel * 2.2, 28.0))
    self.dead = False
    self.bolts = []

    if not self.boss and not self.towers:
      if self.threat >= 3 and not self.b1:
        self.boss = {'type': 'griffin', 'x': WIDTH + 100.0, 'y': HEIGHT // 2, 'hp': 150.0, 'max_hp': 150.0, 'timer': 0.0, 'state': 'entering', 'atk': 'idle', 'at': 0, 'cool': 80, 'seq': 0, 'waves': []}
        AUDIO.play('roar')
      elif self.threat >= 6 and not self.b2:
        self.boss = {'type': 'demon', 'x': WIDTH + 150.0, 'y': HEIGHT // 2 - 60.0, 'hp': 520.0, 'max_hp': 520.0, 'timer': 0.0, 'state': 'entering', 'atk': 'idle', 'at': 0, 'cool': 60, 'sh': 0, 'fwaves': [], 'by': HEIGHT // 2 - 60.0, 'ghost': False, 'hurt': 0, 'flash': 0, 'dt': 0, 'seq': 0, 'alpha': 255}
        AUDIO.play('roar')

    if self.shield_active:
      self.shield_timer -= 1
      if self.shield_timer <= 0:
        self.shield_active = False
    if sel == "SKELETAL" and self.shields < self.max_shields:
      self.dp += 0.15
    if self.dp >= 100:
      if self.shields < self.max_shields:
        self.shields += 1
        self.dp -= 100
        self.shake_for(5, 10)
        self.burst(d.centerx, d.centery, 20, 5, 10, 15, ICE_BLUE)
      else:
        self.dp = 100

    hx, hy = d.x + 92, d.y + 4 - int(self.pitch * 0.4)
    if self.breath:
      self.breath_timer -= 1
      if self.breath_timer <= 0:
        self.breath = False
      if sel == "YELLOW":
        main = self.zig(hx, hy, hx + random.randint(300, 380), hy + random.randint(-40, 40), 7, 22)
        self.bolts.append((main, (255, 225, 70), 8))
        for p in random.sample(main[2:6], 3):
          self.bolts.append((self.zig(p[0], p[1], p[0] + random.randint(40, 100), p[1] + random.randint(-45, 45), 3, 12), (255, 238, 120), 5))
      else:
        cols = BREATH_COLORS.get(sel, DEFAULT_BREATH)
        for _ in range(0 if sel in ("RED", "BLUE", "GREEN", "SILVER") else 4):
          if sel == "SILVER":
            self.emit(hx, hy + random.randint(-20, 20), random.uniform(15, 25), random.uniform(-1, 1), random.randint(8, 14), random.choice(cols))
          else:
            self.emit(hx, hy + random.randint(-12, 18), random.uniform(10, 17), random.uniform(-3.5, 3.5), random.randint(10, 20), random.choice(cols))
    else:
      tr = DRAGON_PALETTES[sel]['trail']
      self.emit(d.x + 4, d.centery + 4 + int(self.pitch * 0.3), random.uniform(-3.5, -1), random.uniform(-1, 1), random.randint(6, 11), tr[0] if random.random() > 0.4 else tr[1])

    if not self.boss:
      self.spawn_t += 1
      if self.spawn_t > max(35, 75 - self.threat * 5):
        self.spawn_t = 0
        self.spawn_enemy()
    self.power_t += 1
    if self.power_t > 340:
      self.power_t = 0
      self.powerups.append({'rect': pygame.Rect(WIDTH, random.randint(120, 380), 34, 34), 't': 0.0, 'ry': 0})
    if random.random() < 0.02 and not self.boss:
      self.coins.append({'rect': pygame.Rect(WIDTH, random.randint(100, 400), 20, 20), 't': random.uniform(0, 5), 'ry': 0})

    self.update_items()
    if self.breath:
      self.update_breath()
    if sel in ("RED", "GREEN"):
      self.update_lava(hx, hy)
    self.update_boss()

    for name in GROUND_LISTS:
      for o in getattr(self, name):
        r, ost = o['rect'], o['state']
        if ost == 'blown':
          r.x += 15
          r.y -= 2
        else:
          r.x -= sc
        if ost == 'stasis':
          o['st'] = o.get('st', STASIS_FRAMES) - 1
          if o['st'] <= 0:
            o['state'] = ost = 'normal'
        if ost == 'normal' and not o.get('shattered') and r.x < WIDTH - 50:
          self.unit_ai(name, o)
        if ost == 'frozen' and not o.get('shattered') and d.colliderect(r):
          self.shatter_frozen(o)
        if ost == 'normal' and not o.get('shattered') and d.colliderect(r):
          self.hit_dragon(o, melee=True)
        if r.right < d.x and not o.get('passed'):
          o['passed'] = True
          self.score += 10 * self.score_mult
          self.bounty_add('dodge')

    for e in self.enemies:
      r, ost = e['rect'], e['state']
      if ost == 'blown':
        e['fx'] += 15
        r.y -= 2
      elif ost in STUCK_STATES:
        e['fx'] -= sc
        e['vy'] += BASE_GRAVITY * 1.5
        r.y += int(e['vy'])
        if r.bottom >= GROUND_Y:
          r.bottom = GROUND_Y
          e['vy'] = 0
          if ost == 'frozen':
            self.shatter_frozen(e)
      elif ost == 'stasis':
        e['st'] = e.get('st', STASIS_FRAMES) - 1
        if e['st'] <= 0:
          e['state'] = 'normal'
      else:
        sp = e['speed']
        ds = e.get('ds', -1)
        if ds == 0:
          if d.centerx + 260 < r.x < WIDTH - 140:
            e['ds'] = 1
            e['dt'] = 0.0
        elif ds == 1:
          e['dt'] += self.ts
          sp *= 0.25
          if e['dt'] > 42:
            e['ds'] = 2
            e['ty'] = d.centery - r.h // 2
            AUDIO.play('whoosh', 0.5)
        elif ds == 2:
          sp *= 2.0
          r.y += int((e['ty'] - r.y) * 0.06)
          self.emit(r.right, r.centery, random.uniform(1, 4), random.uniform(-1, 1), random.randint(5, 9), (255, 120, 60))
        e['fx'] -= sp * self.ts
      r.x = int(e['fx'])
      if ost == 'normal' and e.get('kind') == 'wyvern':
        e['age'] += self.ts
        r.y = int(e['by'] + math.sin(e['age'] * 0.12 + e['wph']) * 30)
      if ost == 'frozen' and not e.get('shattered') and d.colliderect(r):
        self.shatter_frozen(e)
      if ost == 'normal' and not e.get('shattered') and d.colliderect(r):
        self.hit_dragon(e, melee=True)
      if r.right < d.x and not e.get('passed'):
        e['passed'] = True
        self.score += (2 if e.get('kind') == 'wyvern' else (3 if e.get('foe') == 'imp' else 10)) * self.score_mult

    for o in self.orbs:
      ost = o['state']
      if ost == 'blown':
        o['x'] += 15
        o['y'] -= 2
      elif ost in STUCK_STATES:
        o['vy'] = o.get('vy', 0) + BASE_GRAVITY * 1.5
        o['y'] += int(o['vy'])
        o['shattered'] = o['y'] >= GROUND_Y
      elif ost == 'stasis':
        o['st'] = o.get('st', STASIS_FRAMES) - 1
        if o['st'] <= 0:
          o['state'] = 'normal'
      else:
        o['x'] += o['vx'] * self.ts
        if o['x'] > d.x and o.get('home', True):
          o['vy'] += (d.centery - o['y']) * 0.005 * self.ts
        o['y'] += o['vy'] * self.ts
      orr = int(o.get('r', 10) * 0.9)
      if ost == 'normal' and d.colliderect(pygame.Rect(int(o['x'] - orr), int(o['y'] - orr), orr * 2, orr * 2)):
        if not self.shield_active:
          self.dead = True
        else:
          o['shattered'] = True
      if self.state == "PLAYING" and not o.get('shattered'):
        self.emit(o['x'], o['y'], random.uniform(0, 2), random.uniform(-1, 1), random.randint(4, 8), o.get('col', MAGIC_PURPLE))

    for sp in self.spears:
      sp['x'] += sp['vx'] * self.ts
      sp['y'] += sp['vy'] * self.ts
      L = math.hypot(sp['vx'], sp['vy']) or 1.0
      for k in (0, 22, 44, 66):
        px, py = sp['x'] - sp['vx'] / L * k, sp['y'] - sp['vy'] / L * k
        if d.colliderect(pygame.Rect(int(px - 7), int(py - 7), 14, 14)):
          self.dead = True                    # unblockable
          break
      if sp['x'] < -120 or sp['y'] < -100 or sp['y'] > HEIGHT + 100:
        sp['shattered'] = True

    for lst, is_fire in ((self.fireballs, True), (self.arrows, False)):
      for p in lst:
        ost = p['state']
        if ost == 'blown':
          p['x'] += 15
          p['y'] -= 4
        elif ost in STUCK_STATES:
          p['vy'] = p.get('vy', 0) + BASE_GRAVITY * 1.5
          p['y'] += int(p['vy'])
          p['shattered'] = p['y'] >= GROUND_Y
        elif ost == 'stasis':
          p['st'] = p.get('st', STASIS_FRAMES) - 1
          if p['st'] <= 0:
            p['state'] = 'normal'
        else:
          ts = self.ts
          if is_fire:
            p['vx'] -= 0.02 * ts
            p['vy'] += FIREBALL_GRAVITY * ts
          elif p.get('kind') == 'boulder':
            p['vy'] += FIREBALL_GRAVITY * ts
            p['rot'] = p.get('rot', 0.0) + 0.25 * ts
          elif p.get('kind') != 'feather':
            p['vy'] += FIREBALL_GRAVITY * 0.5 * ts
          p['x'] += p['vx'] * ts
          p['y'] += p['vy'] * ts
        if is_fire and self.state == "PLAYING" and not p.get('shattered'):
          self.emit(p['x'], p['y'], random.uniform(1, 3), random.uniform(-1, 2), random.randint(6, 12), (240, random.randint(60, 130), 10))
        pr = pygame.Rect(int(p['x'] - 11), int(p['y'] - 11), 22, 22) if is_fire else (pygame.Rect(int(p['x'] - 9), int(p['y'] - 5), 18, 10) if p.get('kind') == 'feather' else (pygame.Rect(int(p['x'] - 17), int(p['y'] - 17), 34, 34) if p.get('kind') == 'boulder' else pygame.Rect(int(p['x'] - 15), int(p['y'] - 2), 30, 4)))
        if d.colliderect(pr) and ost == 'normal':
          if is_fire and sel == "RED":
            p['shattered'] = True
            self.score += 5
            self.emit(p['x'], p['y'], random.uniform(-3, 3), random.uniform(-3, 3), random.randint(8, 15), FIRE_CORE)
          elif not self.shield_active:
            self.dead = True
          else:
            p['shattered'] = True
        elif pr.right < d.x and not p.get('passed'):
          p['passed'] = True
          self.bounty_add('dodge')

    if self.hit_inv > 0:
      self.hit_inv -= 1
    if self.dash_inv > 0 or self.hit_inv > 0:
      self.dead = False
    elif self.dead and self.hearts > 0:
      self.take_heart()
    for name in GROUND_LISTS + ('enemies',):
      setattr(self, name, [o for o in getattr(self, name) if not o.get('shattered') and o['rect'].right > 0 and o['rect'].x < WIDTH + 400])
    self.arrows = [a for a in self.arrows if not a.get('shattered') and -50 < a['x'] < WIDTH + 400 and a['y'] < HEIGHT + 50]
    self.fireballs = [f for f in self.fireballs if not f.get('shattered') and f['y'] < HEIGHT + 50 and -100 < f['x'] < WIDTH + 400]
    self.orbs = [o for o in self.orbs if not o.get('shattered') and o['y'] < HEIGHT + 50 and -100 < o['x'] < WIDTH + 400]
    self.spears = [s for s in self.spears if not s.get('shattered')]

    q = self.bounty
    if q and q['progress'] >= q['target'] and not q.get('done'):
      q['done'] = True
      self.data['completed_quests'] += 1
      save_data(self.data)
      self.score += 100
      gold = quest_gold(q)
      self.data['coins'] += gold
      save_data(self.data)
      self.toast("BOUNTY COMPLETE!  +%d GOLD" % gold)
      AUDIO.play('quest')
      if self.shields < self.max_shields:
        self.shields += 1
      self.shake_for(5, 15)

    if d.top < -25 or d.bottom > GROUND_Y + 1:
      if not self.shield_active:
        if self.hearts > 0:
          if self.hit_inv <= 0:
            self.take_heart()
            self.dead = False
          if d.bottom > GROUND_Y + 1:
            d.bottom = GROUND_Y - 6
            self.vel = FLAP_STRENGTH
          if d.top < -25:
            d.top = -25
            self.vel = 0
        else:
          self.dead = True
      else:
        if d.bottom > GROUND_Y + 1:
          d.bottom = GROUND_Y + 1
          self.vel = FLAP_STRENGTH
        if d.top < -25:
          d.top = -25
          self.vel = 0

    if self.dead:
      self.die()

  def take_heart(self):
    self.hearts -= 1
    self.dead = False
    self.hit_inv = 100
    d = self.dragon
    self.burst(d.centerx, d.centery, 22, 6, 6, 12, (255, 60, 70))
    self.shake_for(8, 12)
    AUDIO.play('shatter', 0.8)

  def die(self):
    AUDIO.play('die')
    self.state = "GAMEOVER"
    self.over_t = 0
    data = self.data
    data['coins'] += int(self.run_coins)
    self.new_record = self.score > data['high_score']
    if self.new_record:
      data['high_score'] = self.score
    save_data(data)
    d = self.dragon
    self.burst(d.centerx, d.centery, 40, 7, 8, 16, DRAGON_PALETTES[self.selected]['main'])
    self.burst(d.centerx, d.centery, 20, 5, 6, 12, FIRE_CORE)
    self.shake_for(12, 20)
    self.bolts = []
    self.vel = -4.0

  def spawn_enemy(self):
    pool = ["tower", "catapult", "trebuchet", "enemy_dragon"]
    if self.threat >= 4:
      pool += ["mage", "ballista"]
    if self.threat >= 5:
      pool += ["archer", "archer"]
    if self.b1:
      pool += ["golem", "golem"]
    if self.threat >= 2:
      pool += ["swarm"]
    if self.threat >= 4:
      pool += ["swarm"]
    t = random.choice(pool)
    if t == "swarm":
      n = random.randint(3, 5)
      base = random.randint(130, GROUND_Y - 170)
      spd = 7 + self.threat * 0.3
      variant = random.randint(0, 1)
      for i in range(n):
        dy = 0 if i == 0 else (1 if i % 2 else -1) * ((i + 1) // 2) * 22
        dx = i * 42
        by = max(60, min(GROUND_Y - 110, base + dy))
        self.enemies.append({'rect': pygame.Rect(WIDTH + dx, by, 36, 30), 'fx': float(WIDTH + dx), 'kind': 'wyvern', 'variant': variant,
                                     'speed': spd, 'passed': False, 'state': 'normal', 'vy': 0.0, 'phase': i * 0.7, 'by': float(by), 'wph': i * 0.5, 'age': 0.0})
      return
    if t == "tower":
      h = random.randint(170, 340)
      self.towers.append({'rect': pygame.Rect(WIDTH, GROUND_Y - h, TOWER_WIDTH, h), 'passed': False, 'state': 'normal',
                'surf': build_tower(h, random.choice([BANNER_GOLD, BANNER_BLUE, CLOTH_RED]))})
    elif t == "catapult":
      self.catapults.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 40, 60, 40), 'fired': False, 'passed': False, 'state': 'normal', 'timer': 35})
    elif t == "trebuchet":
      self.trebuchets.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 55, 70, 55), 'fired': False, 'passed': False, 'state': 'normal', 'timer': 30})
    elif t == "enemy_dragon":
      foe = random.choice(('harpy', 'harpy', 'garg', 'imp', 'imp'))
      fw, fh = {'harpy': (40, 60), 'garg': (56, 56), 'imp': (36, 33)}[foe]
      if foe == 'imp':
        n = random.randint(3, 5)
        base = random.randint(110, GROUND_Y - 170)
        spd = random.randint(6, 8) + self.threat * 0.4
        for i in range(n):
          dy = 0 if i == 0 else (1 if i % 2 else -1) * ((i + 1) // 2) * 24
          dx = i * 46
          by = max(60, min(GROUND_Y - 110, base + dy))
          self.enemies.append({'rect': pygame.Rect(WIDTH + dx, by, fw, fh), 'fx': float(WIDTH + dx), 'foe': 'imp', 'speed': spd, 'passed': False, 'state': 'normal',
                                     'vy': 0.0, 'phase': i * 0.8, 'ds': -1, 'dt': 0.0, 'ty': 0})
        return
      self.enemies.append({'rect': pygame.Rect(WIDTH, random.randint(50, 340), fw, fh), 'fx': float(WIDTH), 'foe': foe,
                                 'speed': random.randint(6, 9) + self.threat * 0.5, 'passed': False, 'state': 'normal', 'vy': 0.0, 'phase': random.uniform(0, 6.28),
                                 'ds': 0 if (self.threat >= 4 and random.random() < 0.6) else -1, 'dt': 0.0, 'ty': 0})
    elif t == "golem":
      self.golems.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 72, 44, 72), 'timer': 45, 'wind': 0, 'passed': False, 'state': 'normal', 'ph': random.randint(0, 11)})
    elif t == "archer":
      self.archers.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 45, 30, 45), 'fired': False, 'passed': False, 'state': 'normal'})
    elif t == "mage":
      mk = random.choice(('pyro', 'wiz', 'skel'))
      mw, mh = {'pyro': (34, 66), 'wiz': (30, 60), 'skel': (36, 72)}[mk]
      self.mages.append({'rect': pygame.Rect(WIDTH, GROUND_Y - mh, mw, mh), 'timer': 0, 'passed': False, 'state': 'normal', 'kind': mk, 'ph': random.randint(0, 11)})
    elif t == "ballista":
      self.ballistas.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 40, 40, 40), 'timer': 35, 'passed': False, 'state': 'normal', 'mode': 'aiming'})

  def unit_ai(self, name, o):
    if not self.tick:                       # time is slowed: units act every other frame
      return
    r, d = o['rect'], self.dragon
    if name == 'catapults' or name == 'trebuchets':
      cat = name == 'catapults'
      if not o['fired']:
        o['timer'] -= 1                 # arm winds back while the timer runs down
        if o['timer'] <= 0:
          o['fired'] = True
          o['swing'] = 0
          o['launched'] = False
      elif not o.get('launched'):
        o['swing'] = o.get('swing', 0) + 1
        if o['swing'] >= 4:             # stone leaves the arm part-way through the swing
          o['launched'] = True
          self.fireballs.append({'x': r.centerx, 'y': r.top, 'vx': -8 if cat else -6, 'vy': -4 if cat else -14, 'state': 'normal'})
          self.shake_for(3, 5)
          AUDIO.play('launch')
          self.burst(r.centerx, r.top + 10, 6, 3, 4, 8, STONE_LIGHT)
      else:
        o['swing'] = min(o.get('swing', 0) + 1, 10)
    elif name == 'golems':
      if o['wind'] > 0:
        o['wind'] -= 1
        if o['wind'] == 5:
          sx, sy = float(r.left + 2), float(r.top + 12)
          T = max(38.0, min(70.0, abs(d.centerx - sx) / 8.0))
          g = FIREBALL_GRAVITY
          self.arrows.append({'x': sx, 'y': sy, 'vx': (d.centerx - sx) / T, 'vy': (d.centery - sy - 0.5 * g * T * T) / T, 'state': 'normal', 'kind': 'boulder', 'rot': 0.0})
          self.burst(sx, sy, 8, 3, 3, 7, (150, 150, 156))
          self.shake_for(3, 5)
          AUDIO.play('launch', 0.6)
        return
      if r.centerx < d.centerx + 90:
        return
      o['timer'] += 1
      if o['timer'] > 55:
        o['timer'] = -20
        o['wind'] = 13
    elif name == 'mages':
      if r.centerx < d.centerx + 30:
        return
      o['timer'] += 1
      mk = o.get('kind', 'skel')
      if mk == 'pyro' and o['timer'] > 40:
        o['timer'] = -80
        sx, sy = float(r.left + 2), float(r.top + 20)
        T = max(35.0, min(65.0, abs(d.centerx - sx) / 9.0))
        vx = (d.centerx - sx + 0.01 * T * T) / T
        vy = (d.centery - sy - 0.09 * T * T) / T
        self.fireballs.append({'x': sx, 'y': sy, 'vx': vx, 'vy': vy, 'state': 'normal'})
        self.burst(sx, sy, 8, 3, 3, 7, (255, 150, 30))
        AUDIO.play('launch', 0.6)
      elif mk == 'wiz' and o['timer'] > 35:
        o['timer'] = -115
        sx, sy = float(r.left + 4), float(r.top + 12)
        base = math.atan2(d.centery - sy, d.centerx - sx)
        for da in (-0.2, 0.0, 0.2):
          self.orbs.append({'x': sx, 'y': sy, 'vx': math.cos(base + da) * 8.0, 'vy': math.sin(base + da) * 8.0, 'state': 'normal', 'col': (100, 200, 255), 'r': 7, 'home': False})
        self.burst(sx, sy, 8, 3, 3, 6, (120, 210, 255))
        AUDIO.play('whoosh')
      elif mk == 'skel' and o['timer'] > 45:
        o['timer'] = -135
        sx, sy = float(r.left + 6), float(r.top + 2)
        dx, dy = d.centerx - sx, d.centery - sy
        dist = max(math.hypot(dx, dy), 1.0)
        spd = 3.4 + self.threat * 0.1
        self.orbs.append({'x': sx, 'y': sy, 'vx': dx / dist * spd, 'vy': dy / dist * spd, 'state': 'normal', 'col': (200, 60, 220), 'r': 13, 'home': True})
        self.burst(sx, sy, 8, 2, 3, 6, (200, 80, 230))
        AUDIO.play('whoosh')
    elif name == 'ballistas' and o['mode'] == 'aiming':
      o['timer'] -= 1
      if o['timer'] <= 0:
        o['mode'] = 'fired'
        hx, hy = float(r.x - 18), float(r.y - 11)
        dx, dy = d.centerx - hx, d.centery - hy
        ang = math.atan2(dy, -dx) if dx < 0 else 0.0
        ang = max(-0.7, min(0.2, ang))
        self.spears.append({'x': hx, 'y': hy, 'vx': -math.cos(ang) * 20, 'vy': math.sin(ang) * 20})
        self.burst(hx, hy, 6, 3, 3, 6, (255, 170, 50))
        self.shake_for(2, 3)
        AUDIO.play('whoosh')
    elif name == 'archers' and not o['fired']:
      dx, dy = d.centerx - r.centerx, d.centery - r.centery
      dist = max(math.hypot(dx, dy), 1)
      spd = 12 + self.threat * 0.3
      self.arrows.append({'x': float(r.centerx), 'y': float(r.centery - 10), 'vx': dx / dist * spd, 'vy': dy / dist * spd, 'state': 'normal'})
      o['fired'] = True

  def hit_dragon(self, o, melee):
    if not self.shield_active:
      self.dead = True
    else:
      o['shattered'] = True
      AUDIO.play('shatter')
      self.score += 10
      self.shake_for(6, 8)
      self.bounty_add('shatter')

  def update_items(self):
    d = self.dragon
    for lst, is_pu in ((self.powerups, True), (self.coins, False)):
      keep = []
      for it in lst:
        it['t'] += 0.14
        r = it['rect']
        dx, dy = d.centerx - r.centerx, d.centery - r.centery
        dist = math.hypot(dx, dy)
        if 0 < dist < self.magnet:
          r.x += int(dx / dist * 8)
          r.y += int(dy / dist * 8)
        else:
          r.x -= self.scroll_px
        it['ry'] = r.y + int(math.sin(it['t']) * 8)
        if d.colliderect(pygame.Rect(r.x, it['ry'], r.w, r.h)):
          if is_pu:
            self.breath, self.breath_timer = True, self.breath_time
            AUDIO.play('power')
            self.shake_for(6, 12)
            self.burst(r.x + 17, it['ry'] + 17, 20, 5, 6, 14, GOLD_BORDER)
          else:
            self.run_coins += self.coin_val
            self.bounty_add('collect')
            AUDIO.play('coin', 0.7)
            self.burst(r.x + 10, it['ry'] + 10, 5, 3, 4, 8, GOLD_BORDER)
        elif r.right >= 0:
          keep.append(it)
      lst[:] = keep

  def zig(self, x0, y0, x1, y1, n, amp):
    pts = [(x0, y0)]
    for i in range(1, n):
      t = i / float(n)
      pts.append((int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t + random.uniform(-amp, amp))))
    pts.append((x1, y1))
    return pts

  def update_lava(self, hx, hy):
    if self.breath and random.random() < 0.12 and len(self.globs) < 8:
      self.globs.append([float(hx), float(hy), random.uniform(5, 10), random.uniform(-3, 0)])
    keep = []
    for g in self.globs:
      g[0] += g[2]
      g[1] += g[3]
      g[3] += 0.55
      if g[1] >= GROUND_Y - 4:
        self.burst(g[0], GROUND_Y - 6, 6, 3, 3, 7, (255, 150, 30) if self.selected == "RED" else (150, 255, 90))
        for p in self.lava:
          if abs(p['x'] - g[0]) < 30:
            p['life'] = max(p['life'], 260)
            break
        else:
          if len(self.lava) < 8:
            self.lava.append({'x': g[0], 'life': 260})
      elif g[0] < WIDTH + 40:
        keep.append(g)
    self.globs = keep
    pools = []
    for p in self.lava:
      p['x'] -= self.scroll_px
      p['life'] -= 1
      if p['life'] > 0 and p['x'] > -50:
        pools.append(p)
    self.lava = pools
    for p in pools:
      zone = pygame.Rect(int(p['x'] - 34), GROUND_Y - 22, 68, 26)
      if random.random() < 0.3:
        self.emit(p['x'] + random.randint(-28, 28), GROUND_Y - 6, random.uniform(-0.6, 0.6), random.uniform(-2.4, -0.8), random.randint(4, 7), random.choice(BREATH_COLORS[self.selected][:3]))
      for name in ('towers', 'catapults', 'trebuchets', 'archers', 'mages', 'ballistas', 'golems'):
        for o in getattr(self, name):
          if o.get('state', 'normal') == 'normal' and zone.colliderect(o['rect']):
            o['burn'] = o.get('burn', 0) + 1
            if o['burn'] % 4 == 0:
              self.emit(o['rect'].centerx + random.randint(-10, 10), o['rect'].bottom - random.randint(4, 30), random.uniform(-1, 1), random.uniform(-3, -1), random.randint(5, 8), random.choice(BREATH_COLORS[self.selected][:3]))
            if o['burn'] >= (40 if name == 'towers' else 24):
              self.apply_breath(o, 20, (255, 120, 20))

  def update_breath(self):
    d, sel = self.dragon, self.selected
    beam = pygame.Rect(d.right, d.y - 45, 400, 130)
    targets = ((self.towers, 15, STONE_DARK), (self.catapults, 25, WOOD_BROWN), (self.trebuchets, 25, WOOD_BROWN), (self.enemies, 35, (100, 100, 100)),
                   (self.archers, 20, CLOTH_DARK), (self.mages, 20, MAGIC_PURPLE), (self.ballistas, 30, WOOD_DARK), (self.golems, 40, STONE_DARK))
    for lst, pts, col in targets:
      for o in lst:
        if beam.colliderect(o['rect']):
          self.apply_breath(o, pts, col)
    for fb in self.fireballs:
      if beam.colliderect(pygame.Rect(int(fb['x'] - 11), int(fb['y'] - 11), 22, 22)):
        self.apply_breath(fb, 5, (255, 100, 0))
    for o in self.orbs:
      if beam.colliderect(pygame.Rect(int(o['x'] - 10), int(o['y'] - 10), 20, 20)):
        self.apply_breath(o, 5, MAGIC_PURPLE)
    for a in self.arrows:
      if beam.colliderect(pygame.Rect(int(a['x'] - 15), int(a['y'] - 2), 30, 4)):
        self.apply_breath(a, 2, STONE_LIGHT)
    b = self.boss
    if b and b['state'] == 'fighting' and b.get('atk') != 'dive' and not b.get('ghost') and beam.colliderect(self.boss_rect(b)):
      if b.get('sh', 0) > 0:
        if random.random() < 0.5:
          self.emit(b['x'] + 5, b['y'] + random.randint(10, 140), random.uniform(-3, 0), random.uniform(-2, 2), random.randint(4, 8), (255, 120, 90))
        return
      b['hp'] -= 1.2 if sel in ("RED", "CHINESE", "GREEN") else 0.8
      b['hurt'] = b.get('hurt', 0) + 1
      if b['hurt'] % 14 == 1:
        b['flash'] = 3
      self.emit(b['x'] + random.randint(0, 50), b['y'] + random.randint(0, 50), random.uniform(-2, 2), random.uniform(-2, 2), random.randint(5, 10), (255, 50, 50))

  def shatter_frozen(self, o):
    if o.get('shattered'):
      return
    o['shattered'] = True
    cx, cy = o['rect'].center if 'rect' in o else (o['x'], o['y'])
    self.burst(cx, cy, 26, 6, 3, 9, random.choice(((210, 248, 255), (150, 226, 246), (255, 255, 255))))
    self.burst(cx, cy, 12, 4, 3, 7, (66, 140, 190))
    AUDIO.play('shatter', 0.7)
    self.shake_for(8, 10)
    self.score += 10 * self.score_mult
    self.bounty_add('shatter')

  def apply_breath(self, o, pts, color):
    if o.get('state', 'normal') != 'normal':
      return
    new_state = BREATH_STATE.get(self.selected)
    if new_state:
      o['state'] = new_state
      if new_state == 'frozen':
        o['vy'] = 0.0
        self.burst(*((o['rect'].center) if 'rect' in o else (o['x'], o['y'])), 8, 3, 3, 6, (210, 248, 255))
      if new_state == 'stasis':
        o['st'] = STASIS_FRAMES
        self.burst(*( (o['rect'].center) if 'rect' in o else (o['x'], o['y']) ), 6, 3, 3, 6, (255, 225, 120))
    else:
      o['shattered'] = True
      self.shake_for(10, 12)
      AUDIO.play('shatter', 0.7)
      cx, cy = o['rect'].center if 'rect' in o else (o['x'], o['y'])
      self.burst(cx, cy, 24, 6, 8, 16, SHATTER_TINT.get(self.selected, color))
      self.bounty_add('shatter')
      if 'rect' in o:
        self.score += int(pts * self.score_mult)
    self.dp += pts

  def griffin_ai(self, b):
    d = self.dragon
    atk = b.setdefault('atk', 'idle')
    b['at'] = b.get('at', 0) + 1
    at = b['at']
    pushed = False
    for w in b['waves']:
      w['x'] -= 11
      w['h'] = min(170, w['h'] + 3)
      if abs(w['x'] - d.centerx) < 34 and abs(d.centery - w['y']) < w['h']:
        pushed = True
    b['waves'] = [w for w in b['waves'] if w['x'] > -40]
    if pushed:
      d.x = max(40, d.x - 5)
    elif d.x < 150:
      d.x = min(150, d.x + 2)
    if b.get('stun', 0) > 0:
      b['stun'] -= 1
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    b['fi'] = [0, 1, 2, 3][(at // 7) % 4]
    b['tilt'] = 0
    if atk == 'idle':
      b['cool'] = b.get('cool', 70) - 1
      if b['cool'] <= 0:
        seq = ['volley', 'gust', 'volley', 'volley', 'dive'] if b['hp'] <= b['max_hp'] / 2 else ['volley', 'volley', 'volley', 'dive']
        nxt = seq[b.get('seq', 0) % len(seq)]
        b['seq'] = b.get('seq', 0) + 1
        b['atk'] = {'volley': 'volley', 'gust': 'gust_warn', 'dive': 'dive_warn'}[nxt]
        b['at'] = 0
        if nxt != 'volley':
          AUDIO.play('roar', 0.7)
    elif atk == 'volley':
      if at < 20:
        b['fi'] = 0
      elif at < 24:
        b['fi'] = 3
      elif at < 28:
        b['fi'] = 2
      else:
        b['fi'] = [3, 2][(at // 5) % 2]
      if 24 <= at <= 34 and (at - 24) % 2 == 0:
        k = (at - 24) // 2
        px, py = WING_PTS[2][k]
        sx, sy = b['x'] - 14 + px * 2, b['y'] - 12 + py * 2
        base = math.atan2(d.centery - sy, d.centerx - sx)
        ang = base + (k - 2.5) * 0.11
        sp = 8.5
        self.arrows.append({'x': float(sx), 'y': float(sy), 'vx': math.cos(ang) * sp, 'vy': math.sin(ang) * sp, 'state': 'normal', 'kind': 'feather'})
      if at >= 46:
        b['atk'] = 'idle'
        b['cool'] = 70
    elif atk == 'dive_warn':
      b['fi'] = [0, 1][(at // 6) % 2]
      b['flash'] = 3 if at % 12 < 6 else 0
      if at == 26:
        b['ty'] = max(10, min(GROUND_Y - 100, d.centery - 50))
      if at >= 40:
        b['atk'] = 'dive'
        b['at'] = 0
        b['sx'], b['sy'] = b['x'], b['y']
        b['ty'] = b.get('ty', b['y'])
        b['hit'] = False
    elif atk == 'dive':
      u = min(1.0, at / 22.0)
      b['x'] = b['sx'] - (b['sx'] + 170) * u
      b['y'] = b['sy'] + (b['ty'] - b['sy']) * min(1.0, u * 1.4)
      b['fi'] = 2
      b['tilt'] = -18 if b['ty'] > b['sy'] else 18
      if not b['hit'] and d.colliderect(pygame.Rect(int(b['x']) + 8, int(b['y']) + 16, 84, 70)):
        if self.shield_active:
          b['hit'] = True
        else:
          self.dead = True
      if at >= 24:
        b['atk'] = 'recover'
        b['at'] = 0
        b['x'] = WIDTH + 120.0
    elif atk == 'recover':
      b['x'] -= 7
      if b['x'] <= BOSS_X:
        b['x'] = BOSS_X
        b['atk'] = 'idle'
        b['cool'] = 110
        b['stun'] = 90
    elif atk == 'gust_warn':
      b['fi'] = 0
      b['flash'] = 3 if at % 8 < 4 else 0
      if at >= 30:
        b['atk'] = 'gust'
        b['at'] = 0
    elif atk == 'gust':
      b['fi'] = [2, 3][(at // 4) % 2]
      if at in (2, 12, 22):
        b['waves'].append({'x': b['x'] + 10.0, 'y': b['y'] + 50.0, 'h': 60.0})
      if at >= 40:
        b['atk'] = 'idle'
        b['cool'] = 80

  def boss_rect(self, b):
    if b['type'] == 'demon':
      return pygame.Rect(int(b['x']), int(b['y']), 150, 150)
    return pygame.Rect(int(b['x']), int(b['y']), 100, 100)

  def demon_ai(self, b):
    d = self.dragon
    b['at'] += 1
    at = b['at']
    atk = b['atk']
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    if b.get('sh', 0) > 0:
      b['sh'] -= 1
    for w in b['fwaves']:
      w['x'] -= 10.5 * self.ts
      w['fr'] += 0.3
      w['y'] += w.get('vy', 0.0) * self.ts
      if self.tick and random.random() < 0.5:
        self.emit(w['x'] + 14, w['y'] + random.randint(-45, 45), random.uniform(1, 3), random.uniform(-1, 1), random.randint(4, 8), random.choice(((255, 140, 30), (255, 210, 90), (220, 60, 20))))
      if d.colliderect(pygame.Rect(int(w['x'] - 10), int(w['y'] - 55), 30, 110)):
        w['x'] = -999.0
        if not self.shield_active:
          self.dead = True
        else:
          self.burst(d.centerx, d.centery, 14, 5, 4, 9, (255, 150, 40))
          AUDIO.play('shatter', 0.5)
    b['fwaves'] = [w for w in b['fwaves'] if w['x'] > -60]
    if atk != 'phase':
      b['y'] = b['by'] + math.sin(b['timer'] * 1.3) * 28
    if atk == 'idle':
      b['cool'] -= 1
      if b['hurt'] > 30 and b['cool'] < 50:
        b['cool'] = 0
        b['seq'] = 1 if b['seq'] % 2 else 3
      if b['cool'] <= 0:
        b['hurt'] = 0
        nxt = ('slash', 'phase', 'slash', 'guard')[b['seq'] % 4]
        b['seq'] += 1
        if nxt == 'guard':
          b['sh'] = 170
          b['cool'] = 150
          AUDIO.play('shield')
          self.burst(b['x'] + 75, b['y'] + 75, 24, 6, 4, 10, (255, 110, 80))
        else:
          b['atk'] = nxt
          b['at'] = 0
        if nxt == 'phase':
          AUDIO.play('whoosh', 0.7)
    elif atk == 'slash':
      if at in (18, 38, 58):
        k = (58, 38, 18).index(at)
        off = (0, -95, 95)[k] if k else 0
        ty = d.centery + off
        ty = max(80, min(GROUND_Y - 70, ty))
        self.shake_for(3, 5)
        AUDIO.play('whoosh')
        sx, sy = float(b['x'] + 5), float(b['y'] + 112)
        trav = max(10.0, (sx - d.centerx) / 10.5)
        b['fwaves'].append({'x': sx, 'y': sy, 'vy': (ty - sy) / trav, 'fr': 0.0})
        self.burst(sx, sy, 12, 5, 4, 9, (255, 150, 40))
      if at >= 66:
        b['atk'] = 'idle'
        b['cool'] = 55
        b['at'] = 0
    elif atk == 'phase':
      if at < 24:
        b['alpha'] = int(255 * (1 - at / 24.0))
        if at >= 6:
          b['ghost'] = True
      elif at == 24:
        b['alpha'] = 0
        ny = b['by']
        for _ in range(8):
          ny = random.uniform(100, GROUND_Y - 150)
          if abs(ny - b['y']) > 110:
            break
        b['by'] = ny
        b['y'] = ny
        b['x'] = BOSS_X + random.uniform(-70, 70)
        self.burst(b['x'] + 50, b['y'] + 60, 26, 5, 4, 10, (255, 150, 40))
      elif at < 50:
        b['alpha'] = int(255 * ((at - 24) / 26.0))
        if at % 3 == 0:
          self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(0, 110), random.uniform(-2, 2), random.uniform(-3, -1), random.randint(5, 9), random.choice(((255, 140, 30), (255, 210, 90))))
        if at >= 44:
          b['ghost'] = False
      else:
        b['alpha'] = 255
        b['ghost'] = False
        b['atk'] = 'idle'
        b['cool'] = 60
        b['at'] = 0
      if at < 24 and at % 3 == 0:
        self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(0, 110), random.uniform(-2, 2), random.uniform(-3, -1), random.randint(5, 9), random.choice(((255, 140, 30), (255, 210, 90))))

  def update_boss(self):
    b = self.boss
    d = self.dragon
    if not b:
      if d.x < 150:
        d.x = min(150, d.x + 2)
      return
    b['timer'] += 0.05
    if b['state'] == 'entering':
      b['x'] -= 6 if b['x'] > BOSS_X + 120 else 2
      if b['x'] <= BOSS_X:
        b['state'] = 'fighting'
    elif b['state'] == 'fighting':
      if b['type'] == 'demon':
        pass
      elif b.get('atk') not in ('dive', 'dive_warn_lock'):
        if b['type'] != 'griffin' or b.get('atk') != 'dive':
          b['y'] = HEIGHT // 2 - 50 + math.sin(b['timer']) * (100 if b['type'] == 'griffin' else 150)
      if b['hp'] <= 0:
        b['state'] = 'dying'
        b['tilt'] = 0
        b['fi'] = None
        b['atk'] = 'idle'
        b['waves'] = []
        b['fwaves'] = []
        b['ghost'] = False
        b['alpha'] = 255
        self.shake_for(15, 30)
        self.score += 300
        if b['type'] == 'griffin':
          self.b1 = True
        else:
          self.b2 = True
      elif b['type'] == 'griffin':
        self.griffin_ai(b)
      elif b['type'] == 'demon':
        self.demon_ai(b)
      elif b['type'] == 'zeppelin' and random.random() < 0.04:
        self.fireballs.append({'x': float(b['x']), 'y': float(b['y'] + 50), 'vx': -8, 'vy': 0, 'state': 'normal'})
        self.fireballs.append({'x': float(b['x'] + 50), 'y': float(b['y'] + 80), 'vx': -2, 'vy': 5, 'state': 'normal'})
    elif b['type'] == 'demon':  # dying
      b['dt'] += 1
      b['y'] = min(b['y'] + 3, GROUND_Y - 150.0)
      if b['dt'] % 3 == 0:
        self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(20, 100), random.uniform(-3, 3), random.uniform(-4, -1), random.randint(8, 16), random.choice(((255, 100, 0), (255, 200, 60), (200, 40, 20))))
      if b['dt'] > 110:
        self.boss = None
    else:  # dying
      b['y'] += 4
      self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(0, 100), random.uniform(-4, 4), random.uniform(-4, 4), random.randint(10, 25), (255, 100, 0))
      if b['y'] > HEIGHT:
        self.boss = None
