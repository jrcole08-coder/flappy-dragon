"""Flappy Dragon screens and rendering."""
from fd_core import *
from fd_foes import foe_frame
from fd_satyr import satyr_frame
from fd_extra import extra_frame
from fd_mages import mage_frame, mage_frames
from fd_art import *
from fd_sound import AUDIO

BOLT_CACHE = {}


def bolt_sprite(deg):
  spr = BOLT_CACHE.get(deg)
  if spr is None:
    base = pygame.Surface((100, 30), pygame.SRCALPHA)
    cy = 15
    pygame.draw.rect(base, (105, 65, 32), (20, cy - 3, 76, 6))
    pygame.draw.line(base, (150, 100, 55), (20, cy - 2), (96, cy - 2), 1)
    for k in range(3):
      fx = 92 - k * 10
      pygame.draw.polygon(base, (190, 60, 30), [(fx, cy - 3), (fx + 12, cy - 3), (fx + 16, cy - 10), (fx + 4, cy - 10)])
      pygame.draw.polygon(base, (190, 60, 30), [(fx, cy + 3), (fx + 12, cy + 3), (fx + 16, cy + 10), (fx + 4, cy + 10)])
    pygame.draw.polygon(base, (70, 72, 80), [(0, cy), (24, cy - 10), (24, cy + 10)])
    pygame.draw.polygon(base, (255, 170, 50), [(6, cy), (24, cy - 6), (24, cy + 6)])
    pygame.draw.polygon(base, (255, 245, 200), [(12, cy), (24, cy - 3), (24, cy + 3)])
    spr = BOLT_CACHE[deg] = pygame.transform.rotate(base, -deg)
  return spr


BOSSBAR_CACHE = {}
CRESCENTS = {}
SCALED = {}


def scaled_frame(kind, fr, k):
  key = (kind, fr, k)
  spr = SCALED.get(key)
  if spr is None:
    src = extra_frame(kind, fr)
    spr = SCALED[key] = pygame.transform.scale(src, (int(src.get_width() * k), int(src.get_height() * k)))
  return spr


def fire_crescent(fr):
  spr = CRESCENTS.get(fr)
  if spr is None:
    H, W = 120, 56
    spr = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(fr * 5 + 1)
    cols = ((190, 36, 14), (235, 92, 18), (255, 160, 30), (255, 226, 110))
    R = H * 0.62
    cx = W + R * 0.35 - 4
    n = 18
    for li, col in enumerate(cols):
      th = 1.0 - li * 0.2
      outer, inner = [], []
      for k in range(n + 1):
        a = -math.radians(62) * th + math.radians(124) * th * k / n
        j = 1 + rnd.uniform(-0.04, 0.04)
        outer.append((int(cx - math.cos(a) * R * j), int(H / 2 + math.sin(a) * R * j)))
      wid = 30 - li * 7
      for k in range(n, -1, -1):
        a = -math.radians(62) * th + math.radians(124) * th * k / n
        ri = R - wid * math.sin(math.pi * (k / float(n))) ** 0.7 - 1
        inner.append((int(cx - math.cos(a) * ri), int(H / 2 + math.sin(a) * ri)))
      pygame.draw.polygon(spr, col, outer + inner)
    for _ in range(14):
      spr.set_at((int(rnd.uniform(W * 0.45, W - 1)), int(rnd.uniform(8, H - 9))), rnd.choice(cols[1:]))
    CRESCENTS[fr] = spr
  return spr


def draw_heart(gs, cx, cy, full):
  col, hi, dk = ((226, 40, 52), (255, 140, 150), (110, 14, 24)) if full else ((52, 40, 48), (80, 68, 76), (30, 22, 28))
  pts = [(cx, cy + 12), (cx - 13, cy), (cx - 13, cy - 6), (cx - 8, cy - 11), (cx - 3, cy - 11), (cx, cy - 7), (cx + 3, cy - 11), (cx + 8, cy - 11), (cx + 13, cy - 6), (cx + 13, cy)]
  pygame.draw.polygon(gs, dk, [(x, y + 1) for x, y in pts])
  pygame.draw.polygon(gs, col, pts)
  pygame.draw.polygon(gs, dk, pts, 2)
  pygame.draw.circle(gs, hi, (cx - 6, cy - 5), 2)

class GameDraw:
  def draw(self):
    gs = game_surface
    self.draw_background()
    st = self.state
    if st == "MENU":
      self.draw_menu()
    elif st == "QUESTS":
      self.draw_quests()
    elif st == "OPTIONS":
      self.draw_options()
    elif st == "HOARD":
      self.draw_hoard()
    elif st in ("SELECT", "RARE_SELECT"):
      self.draw_select()
    elif st == "INTRO":
      self.draw_intro()
    else:
      self.draw_game()
    if st not in ("PLAYING", "PAUSED", "GAMEOVER", "INTRO"):
      gs.blit(VIGNETTE, (0, 0))
    ox = oy = 0
    if self.shake_t > 0 and self.shake_i:
      ox, oy = random.randint(-self.shake_i, self.shake_i), random.randint(-self.shake_i, self.shake_i)
    if self.toast_t > 0:
      self.toast_t -= 1
      img = text(small_font, self.toast_msg, PARCHMENT)
      tr = img.get_rect(center=(WIDTH // 2, GROUND_Y - 70)).inflate(34, 16)
      panel(gs, tr, PANEL_DARK, 240, GOLD_BORDER, 2, 8)
      gs.blit(img, img.get_rect(center=tr.center))
    self.present(ox, oy)

  def draw_background(self):
    gs = game_surface
    if self.day:
      gs.blit(DAY['sky'], (0, 0))
      gs.blit(DAY['sun'], (WIDTH - 240, -10))
    else:
      gs.blit(SKY, (0, 0))
      for x, y, ph in self.twinkle:
        r = 1 + int((math.sin(self.anim * 3 + ph) + 1) * 0.9)
        pygame.draw.circle(gs, STAR_WHITE, (x, y), r)
      gs.blit(MOON, (WIDTH - 240, -10))
    self.blit_layer(FAR_LAYER, 250, self.far_x)
    for c in self.clouds:
      gs.blit(CLOUDS[c[2]], (int(c[0]), int(c[1])))
    self.blit_layer(NEAR_LAYER, 330, self.near_x)
    self.blit_layer(HILL_LAYER, 430, self.mid_x)
    for m in self.mist:
      gs.blit(MIST, (int(m[0]), int(m[1])))
    if self.day:
      gs.fill(DAY_LIFT, special_flags=pygame.BLEND_RGB_ADD)

  def lift_ground(self, gs):
    if self.day:
      gs.fill((38, 44, 30), (0, GROUND_Y, WIDTH, GROUND_H), special_flags=pygame.BLEND_RGB_ADD)

  def blit_layer(self, layer, y0, x):
    o = int(x) % WIDTH
    game_surface.blit(layer, (-o, y0))
    game_surface.blit(layer, (-o + WIDTH, y0))

  def draw_backdrop_ground(self):
    self.draw_scenery()
    game_surface.blit(GROUND, (0, GROUND_Y))
    self.lift_ground(game_surface)

  def draw_scenery(self):
    gs = game_surface
    for s in self.scenery:
      t, x = s['type'], int(s['x'])
      if t == "fg_hill":
        gs.blit(SPRITE_CACHE["fg_hill"][0], (x - 50, GROUND_Y - 16))
      elif t in ("smith", "peasant"):
        spr = extra_frame('smith', int(s['anim'] * 0.6))
        gs.blit(spr, (x, GROUND_Y + 4 - spr.get_height()))
      elif t in ("knight", "dwarf"):
        spr = scaled_frame(t, int(s['anim'] * 0.8), 1.4) if t == "knight" else extra_frame(t, int(s['anim'] * 0.8))
        gs.blit(spr, (x, GROUND_Y + 4 - spr.get_height()))
      elif t in ("sheep", "deer"):
        spr = ENV.runner_sprite(t, 0, int(s['anim'] * 0.7) % 4)
        gs.blit(spr, (x, GROUND_Y + 4 - spr.get_height()))
      else:
        spr, ox, oy = SPRITE_CACHE[t]
        gs.blit(spr, (x - ox, GROUND_Y + 4 - oy))

  def draw_particles(self):
    gs = game_surface
    for p in self.particles:
      pygame.draw.circle(gs, p[5], (int(p[0]), int(p[1])), int(p[4]))

  def draw_sound_btn(self):
    gs = game_surface
    r = SND_BTN
    panel(gs, r, PANEL_DARK, 220, GOLD_BORDER, 2, 8)
    on = AUDIO.ok and AUDIO.enabled
    c = PARCHMENT if on else (140, 120, 120)
    pygame.draw.polygon(gs, c, [(r.x + 10, r.y + 15), (r.x + 18, r.y + 15), (r.x + 27, r.y + 8), (r.x + 27, r.y + 32), (r.x + 18, r.y + 25), (r.x + 10, r.y + 25)])
    if on:
      pygame.draw.arc(gs, c, (r.x + 24, r.y + 13, 10, 14), -1.1, 1.1, 2)
      pygame.draw.arc(gs, c, (r.x + 27, r.y + 8, 14, 24), -1.1, 1.1, 2)
    else:
      pygame.draw.line(gs, (230, 80, 70), (r.x + 30, r.y + 13), (r.x + 42, r.y + 27), 3)
      pygame.draw.line(gs, (230, 80, 70), (r.x + 42, r.y + 13), (r.x + 30, r.y + 27), 3)

  def draw_coin_panel(self):
    gs = game_surface
    panel(gs, pygame.Rect(WIDTH - 160, 14, 146, 40), PANEL_DARK, 220, GOLD_BORDER, 2, 8)
    draw_coin(gs, WIDTH - 138, 34)
    blit_text(gs, button_font, str(self.data['coins']), PARCHMENT, (WIDTH - 118, 20), shadow=False)

  def draw_menu(self):
    gs = game_surface
    a = self.anim
    for x, y, vy, size, ph in self.embers:
      pygame.draw.circle(gs, (255, 190, 80), (int(x), int(y)), max(1, size // 3))
    self.draw_backdrop_ground()
    self.draw_particles()
    my = 320 + math.sin(a * 1.3) * 45
    draw_any_dragon(gs, self.selected, int(self.menu_dragon_x), int(my), int(math.cos(a * 1.3) * 6), a * 7)

    bounce = int(math.sin(a) * 5)
    art = ENV.menu_art()
    crest = pygame.Rect(WIDTH // 2 - 300, 22 + bounce, 600, 140)
    add_glow(gs, WIDTH // 2, crest.centery, 150, (46, 18, 6))
    for i, tx in enumerate((crest.left - 16, crest.right + 16)):             # torches
      pygame.draw.rect(gs, WOOD_DARK, (tx - 3, crest.centery + 4, 6, 30))
      fl = 3 * math.sin(a * 9 + i * 2)
      add_glow(gs, tx, crest.centery - 4, 38, (130, 60, 8))
      pygame.draw.polygon(gs, (255, 120, 20), [(tx - 7, crest.centery + 4), (tx, crest.centery - 20 - fl), (tx + 7, crest.centery + 4)])
      pygame.draw.polygon(gs, FIRE_CORE, [(tx - 3, crest.centery + 4), (tx, crest.centery - 8 - fl), (tx + 3, crest.centery + 4)])
    if art.get('title') is not None:
      gs.blit(art['crest'], crest.topleft)
      gs.blit(art['title'], art['title'].get_rect(center=(crest.centerx, crest.centery - 6)))
      k = (math.sin(a * 3) + 1) / 2
      for sx, sy, ph in ((-200, -34, 0.0), (130, -40, 1.7), (222, 6, 3.1)):
        r = int(2 + 6 * ((math.sin(a * 3 + ph) + 1) / 2))
        cx, cy = crest.centerx + sx, crest.centery + sy
        pygame.draw.line(gs, (255, 244, 190), (cx - r, cy), (cx + r, cy), 1)
        pygame.draw.line(gs, (255, 244, 190), (cx, cy - r), (cx, cy + r), 1)
    else:
      panel(gs, crest, (12, 12, 20), 225, GOLD_BORDER, 4, 14)
      img = text(title_font, "Flappy Dragon", (228, 58, 28))
      tr = img.get_rect(center=(WIDTH // 2, crest.centery))
      gs.blit(text(title_font, "Flappy Dragon", (70, 10, 6)), tr.move(4, 4))
      gs.blit(img, tr)

    rec = pygame.Rect(WIDTH // 2 - 150, 172, 300, 30)
    panel(gs, rec, PANEL_DARK, 215, GOLD_BORDER, 2, 8)
    blit_text(gs, small_font, "REALM RECORD: %d" % self.data['high_score'], PARCHMENT, rec.center, "center", shadow=False)

    for k, label, col, bg, border in MENU_ITEMS:
      r = MENU_RECTS[k]
      if k == "play" and art.get('play') is not None:
        pulse = (math.sin(a * 3) + 1) / 2
        add_glow(gs, r.centerx, r.centery, 125 + int(pulse * 20), (110 + int(pulse * 40), 30, 8))
        gs.blit(art['playh'] if r.collidepoint(self.mouse) else art['play'], r.topleft)
        continue
      draw_button(gs, r, label, col, r.collidepoint(self.mouse), bg, border)
    blit_text(gs, tiny_font, "Click / SPACE flap  |  S shield  |  D dash  |  P pause", (150, 140, 130), (WIDTH // 2, HEIGHT - 26), "center", shadow=False)
    self.draw_coin_panel()
    self.draw_sound_btn()

  def draw_options(self):
    gs = game_surface
    self.draw_backdrop_ground()
    blit_text(gs, hud_font, "OPTIONS", ICE_BLUE, (WIDTH // 2, 62), "center")
    pnl = pygame.Rect(WIDTH // 2 - 230, 100, 460, 390)
    panel(gs, pnl, PANEL_DARK, 225, STONE_LIGHT, 4, 12)
    d = self.data
    rows = {
      "music": ("MUSIC", d.get('music', True)),
      "sfx": ("SOUND EFFECTS", d.get('sfx', True)),
      "display": ("DISPLAY", self.fullscreen),
      "weather": ("WEATHER", d.get('weather', True)),
      "difficulty": ("DIFFICULTY", d.get('difficulty', 'easy') == 'easy'),
    }
    for k, r in OPT_RECTS.items():
      if k in ("weather", "difficulty") and self.opt_from == "PAUSED":
        continue
      name, on = rows[k]
      hov = r.collidepoint(self.mouse)
      if k == "display":
        val, vcol = ("FULLSCREEN" if on else "WINDOWED"), BANNER_GOLD
      elif k == "difficulty":
        val, vcol = ("EASY" if on else "HARD"), (LEAF_GREEN if on else CLOTH_RED)
      else:
        val, vcol = ("ON" if on else "OFF"), (LEAF_GREEN if on else CLOTH_RED)
      panel(gs, r, lighten(IRON_GRAY, 22) if hov else IRON_GRAY, 240, lighten(GOLD_BORDER, 40) if hov else GOLD_BORDER, 3, 9)
      blit_text(gs, button_font, name, PARCHMENT, (r.left + 20, r.centery), "midleft")
      blit_text(gs, button_font, val, vcol, (r.right - 20, r.centery), "midright")
    if self.opt_from != "PAUSED":
      blit_text(gs, tiny_font, "Easy: 3 hearts  |  Hard: one hit and you fall", (150, 140, 130), (WIDTH // 2, pnl.bottom - 14), "center", shadow=False)
    draw_button(gs, BACK_BTN, "RETURN", PARCHMENT, BACK_BTN.collidepoint(self.mouse))

  def draw_quests(self):
    gs = game_surface
    self.draw_backdrop_ground()
    blit_text(gs, hud_font, "REALM QUESTS", ICE_BLUE, (WIDTH // 2, 55), "center")
    pnl = pygame.Rect(WIDTH // 2 - 220, 110, 440, 320)
    panel(gs, pnl, PANEL_DARK, 225, STONE_LIGHT, 4, 12)
    blit_text(gs, button_font, "Completed Quests: %d" % self.data['completed_quests'], BANNER_GOLD, (WIDTH // 2, 150), "center")
    pygame.draw.line(gs, STONE_DARK, (pnl.left + 20, 185), (pnl.right - 20, 185), 3)
    q = self.data['active_quest']
    blit_text(gs, button_font, "Current Bounty", PARCHMENT, (WIDTH // 2, 220), "center")
    blit_text(gs, small_font, q['desc'], MOON_LIGHT, (WIDTH // 2, 270), "center")
    blit_text(gs, tiny_font, "Reward: %d gold" % quest_gold(q), BANNER_GOLD, (WIDTH // 2, 292), "center")
    bar = pygame.Rect(pnl.left + 50, 310, pnl.w - 100, 22)
    pygame.draw.rect(gs, (30, 10, 10), bar, border_radius=6)
    frac = min(1.0, q['progress'] / q['target'])
    if frac > 0:
      pygame.draw.rect(gs, LEAF_GREEN if q.get('done') else CLOTH_RED, (bar.x, bar.y, int(bar.w * frac), bar.h), border_radius=6)
    pygame.draw.rect(gs, GOLD_BORDER, bar, 2, border_radius=6)
    blit_text(gs, tiny_font, "%d / %d" % (min(q['progress'], q['target']), q['target']), PARCHMENT, bar.center, "center")
    if q.get('done'):
      blit_text(gs, small_font, "Complete! %d gold claimed. New bounty next run." % quest_gold(q), LEAF_GREEN, (WIDTH // 2, 365), "center")
    draw_button(gs, BACK_BTN, "RETURN", PARCHMENT, BACK_BTN.collidepoint(self.mouse))

  def draw_upgrade_icon(self, key, cx, cy):
    gs = game_surface
    if key == "thick_scales":
      pts = [(cx - 16, cy - 18), (cx + 16, cy - 18), (cx + 16, cy + 2), (cx, cy + 20), (cx - 16, cy + 2)]
      pygame.draw.polygon(gs, (110, 160, 215), pts)
      pygame.draw.polygon(gs, PARCHMENT, pts, 2)
      pygame.draw.line(gs, PARCHMENT, (cx, cy - 16), (cx, cy + 16), 2)
    elif key == "deep_lungs":
      pygame.draw.polygon(gs, (255, 110, 20), [(cx, cy - 22), (cx + 15, cy + 4), (cx, cy + 20), (cx - 15, cy + 4)])
      pygame.draw.polygon(gs, FIRE_CORE, [(cx, cy - 6), (cx + 7, cy + 6), (cx, cy + 15), (cx - 7, cy + 6)])
    else:
      pygame.draw.arc(gs, CLOTH_RED, (cx - 16, cy - 18, 32, 32), 0, math.pi, 7)
      pygame.draw.line(gs, CLOTH_RED, (cx - 14, cy - 2), (cx - 14, cy + 16), 7)
      pygame.draw.line(gs, CLOTH_RED, (cx + 13, cy - 2), (cx + 13, cy + 16), 7)
      pygame.draw.rect(gs, BONE_WHITE, (cx - 18, cy + 12, 8, 7))
      pygame.draw.rect(gs, BONE_WHITE, (cx + 9, cy + 12, 8, 7))

  def draw_hoard(self):
    gs = game_surface
    self.draw_backdrop_ground()
    blit_text(gs, hud_font, "THE DRAGON'S HOARD", BANNER_GOLD, (WIDTH // 2, 55), "center")
    self.draw_coin_panel()
    for key, title, desc, rect in UPGRADES:
      lvl = self.data['upgrades'][key]
      panel(gs, rect, PANEL_DARK, 225, GOLD_BORDER if lvl < 3 else LEAF_GREEN, 4, 10)
      blit_text(gs, button_font, title, BANNER_GOLD, (rect.centerx, rect.top + 28), "center")
      self.draw_upgrade_icon(key, rect.centerx, rect.top + 85)
      blit_text(gs, tiny_font, desc, PARCHMENT, (rect.centerx, rect.top + 125), "center", shadow=False)
      for i in range(3):
        c = LEAF_GREEN if i < lvl else STONE_DARK
        pygame.draw.circle(gs, c, (rect.left + 40 + i * 50, rect.top + 160), 15)
        pygame.draw.circle(gs, PARCHMENT, (rect.left + 40 + i * 50, rect.top + 160), 15, 2)
      if lvl < 3:
        cost = UPGRADE_COSTS[lvl]
        btn = pygame.Rect(rect.left + 20, rect.bottom - 50, 140, 35)
        ok = self.data['coins'] >= cost
        draw_button(gs, btn, "BUY: %d" % cost, PARCHMENT if ok else (150, 50, 50), ok and btn.collidepoint(self.mouse), IRON_GRAY, GOLD_BORDER if ok else STONE_DARK, small_font)
      else:
        blit_text(gs, button_font, "MAXED", LEAF_GREEN, (rect.centerx, rect.bottom - 32), "center")
    draw_button(gs, BACK_BTN, "RETURN", PARCHMENT, BACK_BTN.collidepoint(self.mouse))

  def draw_select(self):
    gs = game_surface
    rare = self.state == "RARE_SELECT"
    boxes = RARE_BOXES if rare else SELECT_BOXES
    self.draw_backdrop_ground()
    blit_text(gs, hud_font, "MYTHIC BEASTS" if rare else "DRAGON ROSTER", BANNER_GOLD if rare else PARCHMENT, (WIDTH // 2, 55), "center")
    self.draw_coin_panel()
    hovered = self.selected if self.selected in [b[0] for b in boxes] else boxes[0][0]
    for key, rect in boxes:
      if rect.collidepoint(self.mouse) and not self.pending:
        hovered = key
      unlocked = key in self.data['unlocked']
      bc = (BANNER_GOLD if rare else GOLD_BORDER) if self.selected == key else STONE_DARK
      if not unlocked:
        bc = (150, 50, 50)
      panel(gs, rect, (50, 15, 15) if rare else PANEL_DARK, 225, bc, 6 if rare else 4, 10)
      if self.selected == key:
        add_glow(gs, rect.centerx, rect.centery, rect.w // 2 + 20, (40, 30, 6))
      draw_any_dragon(gs, key, rect.centerx - 25, rect.top + (70 if key in ("CHINESE", "SKELETAL") else 50), 0, self.anim, False)
      if not unlocked:
        dim(gs, 90, rect.inflate(-8, -8))
      pal = DRAGON_PALETTES[key]
      blit_text(gs, small_font, pal['title'], BANNER_GOLD if rare else PARCHMENT, (rect.centerx, rect.bottom - 40), "center")
      if unlocked:
        blit_text(gs, tiny_font, "UNLOCKED", LEAF_GREEN, (rect.centerx, rect.bottom - 17), "center", shadow=False)
      else:
        blit_text(gs, tiny_font, "%d COINS" % pal['cost'], (255, 100, 100), (rect.centerx, rect.bottom - 17), "center", shadow=False)
    pr = pygame.Rect(WIDTH // 2 - 230, HEIGHT - 112, 460, 42)
    panel(gs, pr, (50, 15, 15) if rare else STONE_DARK, 225, STONE_LIGHT, 2, 6)
    blit_text(gs, small_font, DRAGON_PALETTES[hovered]['desc'], PARCHMENT, pr.center, "center", shadow=False)
    draw_button(gs, SEL_BACK_BTN, "RETURN", PARCHMENT, SEL_BACK_BTN.collidepoint(self.mouse), font=button_font)
    if not rare:
      draw_button(gs, RARE_BTN, "RARE", BANNER_GOLD, RARE_BTN.collidepoint(self.mouse), (60, 20, 20), BANNER_GOLD)
    if self.pending:
      dim(gs, 160)
      pop = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 100, 440, 180)
      panel(gs, pop, PARCHMENT, 255, WOOD_DARK, 6, 12)
      pal = DRAGON_PALETTES[self.pending]
      blit_text(gs, small_font, "Unlock %s for %d?" % (pal['title'], pal['cost']), WOOD_DARK, (pop.centerx, pop.top + 50), "center", shadow=False)
      draw_button(gs, BUY_YES, "YES", PARCHMENT, BUY_YES.collidepoint(self.mouse))
      draw_button(gs, BUY_NO, "NO", PARCHMENT, BUY_NO.collidepoint(self.mouse))

  def draw_intro(self):
    gs = game_surface
    t = self.intro_t
    self.draw_game()
    if t < 180:
      n = 3 - t // 60
      loc = (t % 60) / 60.0
      img = ENV.fire_text(str(n), 150)
      sc = 1.0 + 0.55 * max(0.0, 1 - loc * 5)
      im = pygame.transform.smoothscale(img, (int(img.get_width() * sc), int(img.get_height() * sc)))
      if loc > 0.8:
        im.set_alpha(int(255 * (1 - loc) / 0.2))
      add_glow(gs, WIDTH // 2, 170, 120, (90, 40, 8))
      gs.blit(im, im.get_rect(center=(WIDTH // 2, 170)))
    else:
      loc = t - 180
      img = ENV.fire_text("REIGN TERROR", 72)
      if img.get_width() > WIDTH - 40:
        img = pygame.transform.smoothscale(img, (WIDTH - 40, int(img.get_height() * (WIDTH - 40) / float(img.get_width()))))
      sc = 1.0 + 0.6 * max(0.0, 1 - loc / 12.0)
      im = pygame.transform.smoothscale(img, (int(img.get_width() * sc), int(img.get_height() * sc)))
      add_glow(gs, WIDTH // 2, 170, 200, (90, 40, 8))
      gs.blit(im, im.get_rect(center=(WIDTH // 2, 170)))

  def draw_game(self):
    gs, d, st = game_surface, self.dragon, self.state
    self.draw_scenery()
    self.draw_particles()

    for name in ('towers', 'mages', 'archers', 'catapults', 'trebuchets', 'ballistas', 'golems', 'enemies'):
      for o in getattr(self, name):
        if o.get('shattered'):
          continue
        ost = o['state']
        r = o['rect'].copy()
        if ost == 'stunned':
          r.x += random.randint(-4, 4)
          r.y += random.randint(-4, 4)
        if name == 'towers':
          gs.blit(o['surf'], (r.x, r.y - 15))
        elif name == 'golems':
          if o['wind'] > 0:
            fi = 12 + min(2, (18 - o['wind']) // 6)
          else:
            fi = (int(self.wing * 0.4) + o['ph']) % 12
          spr = extra_frame('golem', fi)
          gs.blit(spr, (r.centerx - spr.get_width() // 2, r.bottom + 2 - spr.get_height()))
        elif name == 'mages':
          mk = o.get('kind', 'skel')
          spr = mage_frame(mk, (int(self.wing * 1.2) + o.get('ph', 0)) % mage_frames(mk))
          gs.blit(spr, (r.centerx - spr.get_width() // 2, r.bottom + 4 - spr.get_height()))
        elif name == 'archers':
          spr = satyr_frame(int(self.wing * 0.45) + o.setdefault('ph', random.randint(0, 11)))
          gs.blit(spr, (r.centerx - spr.get_width() // 2, r.bottom + 3 - spr.get_height()))
        elif name == 'catapults':
          ang, ld = siege_pose(o, 'cat')
          qa = int(round(ang / 6.0)) * 6
          spr, ox, oy = cached_sprite(("catapult", qa, ld), 120, 120, 30, 40, lambda s_, x_, y_, qa=qa, ld=ld: draw_catapult(s_, x_, y_, qa, ld))
          gs.blit(spr, (r.x - ox, r.y - oy))
        elif name == 'trebuchets':
          ang, ld = siege_pose(o, 'treb')
          qa = int(round(ang / 6.0)) * 6
          spr, ox, oy = cached_sprite(("trebuchet", qa, ld), 160, 160, 45, 60, lambda s_, x_, y_, qa=qa, ld=ld: draw_trebuchet(s_, x_, y_, qa, ld))
          gs.blit(spr, (r.x - ox, r.y - oy))
        elif name == 'ballistas':
          m = o['mode']
          spr, ox, oy = cached_sprite(("ballista", m), 100, 110, 30, 40, lambda s, x, y, m=m: draw_ballista(s, x, y, m))
          gs.blit(spr, (r.x - ox, r.y - oy))
        elif o.get('kind') == 'wyvern':
          wf = int(((self.wing * 1.6 + o['phase']) % (2 * math.pi)) / (2 * math.pi) * 6) % 6
          gs.blit(foe_frame('eye', wf), (r.x - 8, r.y - 8))
        else:
          frame = int(((self.wing * 0.8 + o['phase']) % (2 * math.pi)) / (2 * math.pi) * 6) % 6
          if o.get('foe') == 'imp':
            gs.blit(extra_frame('imp', int(self.wing * 0.5 + o['phase'] * 2)), (r.x - 2, r.y - 1 + int(math.sin(self.anim * 6 + o['phase']) * 3)))
          elif o.get('foe') == 'garg':
            gs.blit(foe_frame('garg', frame), (r.x - 12, r.y - 14))
          else:
            gs.blit(foe_frame('harpy', frame), (r.x - 7, r.y - 10))
        if name == 'enemies' and o.get('ds') == 1:
          pulse = 120 + int(100 * abs(math.sin(o['dt'] * 0.5)))
          add_glow(gs, r.centerx, r.centery, 46, (pulse, 10, 10))
          blit_text(gs, button_font, "!", (255, 90, 60), (r.centerx, r.top - 18), "center")
        elif name == 'enemies' and o.get('ds') == 2:
          for k in range(3):
            pygame.draw.line(gs, (255, 150, 90), (r.right + 4, r.y + 8 + k * (r.h - 16) // 2), (r.right + 34 + k * 8, r.y + 8 + k * (r.h - 16) // 2), 2)
        if ost == 'stasis':
          draw_stasis(gs, r)
        if ost == 'frozen':
          gs.blit(ice_sprite(r.w, r.h), (r.x - 5, r.y - 5))
        elif ost == 'melted':
          gs.blit(acid_sprite(r.w, r.h, (pygame.time.get_ticks() // 120) % 2), (r.x - 5, r.y - 5))
        elif ost == 'stunned':
          for _ in range(4):
            pygame.draw.circle(gs, (255, 255, 100), (r.x + random.randint(0, r.w), r.y + random.randint(0, r.h)), random.randint(2, 4))

    for sp in self.spears:
      L = math.hypot(sp['vx'], sp['vy']) or 1.0
      ux, uy = sp['vx'] / L, sp['vy'] / L
      hx, hy = int(sp['x']), int(sp['y'])
      add_glow(gs, hx + 4, hy, 30, (150, 60, 8))
      for i in range(12):
        t = i / 12.0
        tx, ty = sp['x'] - ux * (66 + i * 4) + random.uniform(-3, 3), sp['y'] - uy * (66 + i * 4) + random.uniform(-4, 4) * (0.4 + t)
        pygame.draw.circle(gs, (255, int(210 - 170 * t), int(70 - 60 * t)), (int(tx), int(ty)), int(5 * (1 - t)) + 1)
      spr = bolt_sprite(int(round(math.degrees(math.atan2(-sp['vy'], -sp['vx'])) / 6.0)) * 6)
      cx, cy = sp['x'] - ux * 38, sp['y'] - uy * 38
      gs.blit(spr, (int(cx - spr.get_width() / 2), int(cy - spr.get_height() / 2)))

    for o in self.orbs:
      if not o.get('shattered'):
        ox_, oy_ = int(o['x']), int(o['y'])
        oc = o.get('col', MAGIC_PURPLE)
        orr = o.get('r', 12)
        add_glow(gs, ox_, oy_, int(orr * 2.2), (oc[0] // 3, oc[1] // 3, oc[2] // 3))
        if not o.get('home', True):
          ol = math.hypot(o['vx'], o['vy']) or 1.0
          pygame.draw.line(gs, oc, (ox_, oy_), (int(ox_ - o['vx'] / ol * 22), int(oy_ - o['vy'] / ol * 22)), 3)
        pygame.draw.circle(gs, oc, (ox_, oy_), orr)
        pygame.draw.circle(gs, (min(255, oc[0] + 90), min(255, oc[1] + 90), min(255, oc[2] + 90)), (ox_, oy_), max(2, orr * 2 // 3))
        pygame.draw.circle(gs, (255, 255, 255), (ox_, oy_), max(2, orr // 3))

    for a in self.arrows:
      if not a.get('shattered') and a.get('kind') == 'feather':
        draw_feather(gs, a)
      elif not a.get('shattered') and a.get('kind') == 'boulder':
        spr = scaled_frame('boulder', int(a.get('rot', 0.0)) % 8, 1.5)
        gs.blit(spr, (int(a['x']) - 18, int(a['y']) - 18))
      elif not a.get('shattered'):
        ax, ay = int(a['x']), int(a['y'])
        ang = math.atan2(a.get('vy', 0), a.get('vx', 1))
        ex, ey = ax + math.cos(ang) * 15, ay + math.sin(ang) * 15
        ca, sa = math.cos(ang), math.sin(ang)
        add_glow(gs, int(ex), int(ey), 24, (150, 60, 8))
        for i in range(8):
          t = i / 8.0
          pr = int(5 * (1 - t)) + 1
          pygame.draw.circle(gs, (255, int(200 - 150 * t), int(60 - 50 * t)), (int(ax - ca * (8 + i * 4) + random.uniform(-2, 2)), int(ay - sa * (8 + i * 4) + random.uniform(-2, 2))), pr)
        pygame.draw.line(gs, WOOD_BROWN, (ax - ca * 15, ay - sa * 15), (ex, ey), 3)
        pygame.draw.polygon(gs, (255, 225, 110), [(ex + ca * 9, ey + sa * 9), (ex - sa * 5, ey + ca * 5), (ex + sa * 5, ey - ca * 5)])
        pygame.draw.circle(gs, (255, 255, 230), (int(ex + ca * 3), int(ey + sa * 3)), 2)

    for fb in self.fireballs:
      if not fb.get('shattered'):
        add_glow(gs, int(fb['x']), int(fb['y']), 34, (130, 50, 5))
        pygame.draw.circle(gs, (255, 120, 10), (int(fb['x']), int(fb['y'])), 15)
        pygame.draw.circle(gs, FIRE_CORE, (int(fb['x']), int(fb['y'])), 9)

    for coin in self.coins:
      gs.blit(coin_sprite(), (coin['rect'].x - 2, coin['ry'] - 2))
    for pu in self.powerups:
      add_glow(gs, pu['rect'].x + 17, pu['ry'] + 17, 30 + int(math.sin(pu['t'] * 2) * 5), (110, 30, 10))
      gs.blit(powerup_sprite(), (pu['rect'].x - 3, pu['ry'] - 3))

    b = self.boss
    if b:
      if b['type'] == 'griffin':
        draw_griffin_boss(gs, b)
      elif b['type'] == 'demon':
        self.draw_demon(gs, b)
      else:
        draw_zeppelin(gs, int(b['x']), int(b['y']), b['timer'])

    for pts, col, w in self.bolts:
      pygame.draw.lines(gs, (150, 130, 30), False, pts, w + 6)
      pygame.draw.lines(gs, col, False, pts, w)
      pygame.draw.lines(gs, (255, 255, 240), False, pts, max(1, w - 4))

    gs.blit(GROUND, (0, GROUND_Y))
    self.lift_ground(gs)
    if self.lava:
      fr = int(self.anim * 12)
      for p in self.lava:
        pool = (lava_pool_sprite if self.selected == "RED" else acid_pool_sprite)((fr + int(p['x'])) % 4)
        if p['life'] < 50 and (p['life'] // 4) % 2 == 0:
          continue
        gs.blit(pool, (int(p['x']) - 40, GROUND_Y - 38))

    if self.dash_state == 'out':
      add_glow(gs, d.centerx + 20, d.centery, 90, (120, 60, 12))
      for k in range(5):
        yy = d.y + 4 + k * 8
        pygame.draw.line(gs, (255, 230, 170), (d.x - 20 - k * 6, yy), (d.x - 90 - k * 14, yy), 2)
    if self.hit_inv <= 0 or (self.hit_inv // 4) % 2 == 0:
      draw_any_dragon(gs, self.selected, d.x, d.y, int(self.vel * 0.8), self.wing, self.breath)
    if self.breath:
      hx, hy = d.x + 92, d.y + 4 - int(self.pitch * 0.4)
      add_glow(gs, hx, hy + 6, 70, BREATH_GLOW.get(self.selected, DEFAULT_GLOW))
      if self.selected in ("RED", "BLUE", "GREEN", "SILVER"):
        fr = int(self.anim * 14)
        gs.blit(({"RED": lava_stream_sprite, "BLUE": frost_stream_sprite, "GREEN": acid_stream_sprite, "SILVER": blade_stream_sprite}[self.selected])(fr % 4), (hx - 6, hy + 3 - 64))
    for g in self.globs:
      gx, gy = int(g[0]), int(g[1])
      if self.selected == "GREEN":
        pygame.draw.circle(gs, (60, 160, 76), (gx, gy), 7)
        pygame.draw.circle(gs, (140, 238, 120), (gx, gy), 5)
        pygame.draw.circle(gs, (255, 255, 255), (gx - 2, gy - 2), 2)
      else:
        pygame.draw.circle(gs, (255, 96, 20), (gx, gy), 7)
        pygame.draw.circle(gs, (255, 176, 44), (gx, gy), 5)
        pygame.draw.circle(gs, (255, 236, 110), (gx - 1, gy - 1), 2)
    if self.shield_active:
      sr = 50 + int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 3)
      gs.blit(shield_sprite(sr), (d.centerx - sr, d.centery - sr))

    self.draw_weather(gs)
    if st in ("PLAYING", "PAUSED"):
      self.draw_hud()
    elif st == "GAMEOVER":
      self.draw_gameover()
    if st == "PAUSED":
      self.draw_pause()

  def draw_hud(self):
    gs = game_surface
    sel = self.selected
    gx, gy, gw, gh = 15, 100, 44, 310
    panel(gs, pygame.Rect(gx, gy, gw, gh), PANEL_DARK, 215, GOLD_BORDER, 3, 8)
    inner = pygame.Rect(gx + 10, gy + 15, gw - 20, gh - 30)
    pygame.draw.rect(gs, (40, 10, 10), inner, border_radius=4)
    fh = int(min(self.dp, 100) / 100.0 * inner.h)
    if fh > 0:
      pygame.draw.rect(gs, ICE_BLUE, (inner.x, inner.bottom - fh, inner.w, fh), border_radius=4)
      pygame.draw.rect(gs, (230, 255, 255), (inner.x + 2, inner.bottom - fh, 4, fh), border_radius=2)
    v = SPRITE_CACHE.get("shield_lbl")
    if v is None:
      v = SPRITE_CACHE["shield_lbl"] = pygame.transform.rotate(text(small_font, "SHIELD CHARGE", MOON_LIGHT), 90)
    gs.blit(v, (gx + gw // 2 - v.get_width() // 2, gy + gh // 2 - v.get_height() // 2))

    draw_button(gs, PAUSE_BTN, "PAUSE", PARCHMENT, PAUSE_BTN.collidepoint(self.mouse), font=small_font)

    if self.shield_active:
      panel(gs, SHIELD_BTN, (20, 40, 80), 235, ICE_BLUE, 3, 12)
      s_txt = text(small_font, "ACTIVE: %ds" % (self.shield_timer // 60 + 1), MOON_LIGHT)
    elif self.shields > 0:
      panel(gs, SHIELD_BTN, (10, 25, 40), 235, MAGIC_PURPLE, 3, 12)
      add_glow(gs, SHIELD_BTN.centerx, SHIELD_BTN.centery, 60, (24, 8, 40))
      s_txt = text(small_font, "SHIELD: %d/%d" % (self.shields, self.max_shields), ICE_BLUE)
    else:
      panel(gs, SHIELD_BTN, (40, 40, 40), 235, STONE_DARK, 3, 12)
      s_txt = text(small_font, "SHIELD: 0/%d" % self.max_shields, (100, 100, 100))
    gs.blit(s_txt, s_txt.get_rect(center=SHIELD_BTN.center))

    if self.dash_state == 'out':
      panel(gs, DASH_BTN, (60, 24, 10), 235, (255, 200, 60), 3, 12)
      add_glow(gs, DASH_BTN.centerx, DASH_BTN.centery, 60, (40, 18, 4))
      d_txt = text(small_font, "DASHING!", (255, 240, 180))
    elif self.dash_cd > 0:
      panel(gs, DASH_BTN, (40, 40, 40), 235, STONE_DARK, 3, 12)
      d_txt = text(small_font, "DASH %ds" % (self.dash_cd // 60 + 1), (120, 120, 120))
    else:
      panel(gs, DASH_BTN, (10, 25, 40), 235, (255, 150, 40), 3, 12)
      add_glow(gs, DASH_BTN.centerx, DASH_BTN.centery, 60, (40, 18, 4))
      d_txt = text(small_font, "DASH: READY", (255, 210, 120))
    gs.blit(d_txt, d_txt.get_rect(center=DASH_BTN.center))
    if self.dash_cd > 0:
      frac = 1.0 - self.dash_cd / float(DASH_COOLDOWN)
      pygame.draw.rect(gs, (255, 150, 40), (DASH_BTN.x + 8, DASH_BTN.bottom - 9, int((DASH_BTN.w - 16) * frac), 4), border_radius=2)

    panel(gs, pygame.Rect(15, 15, 300, 50), PANEL_DARK, 215, GOLD_BORDER, 3, 8)
    blit_text(gs, hud_font, "SCORE: %d" % self.score, MOON_LIGHT, (35, 18))
    panel(gs, pygame.Rect(330, 15, 100, 50), PANEL_DARK, 215, GOLD_BORDER, 3, 8)
    draw_coin(gs, 355, 40)
    blit_text(gs, button_font, str(int(self.run_coins)), MOON_LIGHT, (375, 25))
    hot = min(1.0, (self.threat - 1) / 8)
    panel(gs, pygame.Rect(WIDTH - 180, 15, 165, 50), (70 + int(60 * hot), 20, 20), 225, (200, 50, 50), 3, 8)
    blit_text(gs, small_font, "THREAT: %d" % self.threat, PARCHMENT, (WIDTH - 180 + 82, 40), "center")

    if self.data.get('difficulty', 'easy') == 'easy':
      hp = pygame.Rect(WIDTH - 180, 72, 165, 34)
      panel(gs, hp, PANEL_DARK, 215, GOLD_BORDER, 2, 8)
      for i in range(3):
        draw_heart(gs, hp.x + 34 + i * 48, hp.centery, i < self.hearts)

    q = self.bounty
    if q:
      br = pygame.Rect(434, 15, 182, 50)
      panel(gs, br, PARCHMENT, 245, WOOD_DARK, 3, 5)
      if q.get('done'):
        blit_text(gs, small_font, "+%d GOLD!" % quest_gold(q), (200, 130, 10), br.center, "center", shadow=False)
      else:
        blit_text(gs, tiny_font, q['desc'], WOOD_DARK, (br.centerx, br.top + 16), "center", shadow=False)
        blit_text(gs, small_font, "%d/%d" % (q['progress'], q['target']), CLOTH_RED, (br.centerx, br.top + 35), "center", shadow=False)

    b = self.boss
    if b and b['state'] != 'dying':
      self.draw_boss_bar(b)

    if self.breath:
      panel(gs, pygame.Rect(15, 75, 300, 18), IRON_GRAY, 230, GOLD_BORDER, 2, 5)
      pygame.draw.rect(gs, BREATH_BAR.get(sel, (255, 80, 0)), (17, 77, max(0, int(self.breath_timer / self.breath_time * 296)), 14), border_radius=4)

  def draw_demon(self, gs, b):
    if b['state'] == 'dying':
      fi = 15 + min(5, b['dt'] // 12)
    elif b['atk'] == 'slash':
      fi = 8 + min(5, b['at'] // 6)
    elif b.get('flash', 0) > 0:
      fi = 14
    else:
      fi = int(b['timer'] * 9) % 8
    spr = scaled_frame('demon', fi, 1.5)
    al = b.get('alpha', 255)
    if al < 255:
      spr = spr.copy()
      spr.set_alpha(max(0, al))
    if al > 0:
      add_glow(gs, int(b['x']) + 75, int(b['y']) + 80, 120, (50, 18, 4))
      gs.blit(spr, (int(b['x']) - 30, int(b['y']) - 24))
      if b.get('sh', 0) > 0 and (b['sh'] > 40 or (b['sh'] // 4) % 2 == 0):
        sr = 108 + int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 4)
        gs.blit(red_shield_sprite(sr), (int(b['x']) + 75 - sr, int(b['y']) + 78 - sr))
    for w in b.get('fwaves', []):
      gs.blit(fire_crescent(int(w['fr']) % 4), (int(w['x']) - 28, int(w['y']) - 60))
      add_glow(gs, int(w['x']), int(w['y']), 50, (90, 30, 6))

  def draw_boss_bar(self, b):
    gs = game_surface
    bw, bh = 400, 22
    x0, y0 = WIDTH // 2 - bw // 2, 120
    pct = max(0.0, min(1.0, b['hp'] / float(b['max_hp'])))
    key = ("bossbar", int(pct * bw))
    spr = BOSSBAR_CACHE.get(key)
    if spr is None:
      if len(BOSSBAR_CACHE) > 400:
        BOSSBAR_CACHE.clear()
      spr = pygame.Surface((bw + 40, bh + 24), pygame.SRCALPHA)
      pygame.draw.rect(spr, (30, 22, 18), (4, 0, bw + 32, bh + 24), border_radius=8)
      pygame.draw.rect(spr, GOLD_BORDER, (4, 0, bw + 32, bh + 24), 3, border_radius=8)
      pygame.draw.rect(spr, (50, 12, 12), (20, 8, bw, bh), border_radius=5)
      fw = int(pct * bw)
      for i in range(bh):
        k = i / float(bh)
        col = (255, 150, 110) if k < 0.15 else (int(230 - 80 * k), int(50 - 30 * k), int(40 - 20 * k))
        if fw > 6:
          pygame.draw.line(spr, col, (23, 8 + i), (20 + fw - 3, 8 + i))
      pygame.draw.rect(spr, (120, 80, 20), (20, 8, bw, bh), 2, border_radius=5)
      for i in range(1, 10):
        pygame.draw.line(spr, (20, 8, 6), (20 + bw * i // 10, 8 + bh - 5), (20 + bw * i // 10, 8 + bh - 1))
      for cx in (8, bw + 32):
        pygame.draw.polygon(spr, (220, 170, 50), [(cx, 20 - 12), (cx + 10, 20), (cx, 20 + 12), (cx - 10, 20)])
        pygame.draw.polygon(spr, (60, 30, 10), [(cx, 20 - 12), (cx + 10, 20), (cx, 20 + 12), (cx - 10, 20)], 1)
      BOSSBAR_CACHE[key] = spr
    gs.blit(spr, (x0 - 20, y0 - 8))
    nm = {"griffin": "GRIFFIN", "demon": "FIRE DEMON"}.get(b['type'], "SKY FORTRESS")
    blit_text(gs, small_font, nm, (255, 226, 150), (WIDTH // 2, y0 - 26), "center")
    blit_text(gs, tiny_font, "%d%%" % int(pct * 100 + 0.5), (255, 240, 220), (WIDTH // 2, y0 + bh // 2), "center")

  def draw_gameover(self):
    gs = game_surface
    dim(gs, 120)
    pnl = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 130, 440, 260)
    panel(gs, pnl, PARCHMENT, 252, WOOD_DARK, 6, 12)
    blit_text(gs, hud_font, "SIEGE CASUALTY", (190, 40, 20), (pnl.centerx, pnl.top + 45), "center", shadow=False)
    blit_text(gs, button_font, "Score: %d" % self.score, WOOD_DARK, (pnl.centerx, pnl.top + 100), "center", shadow=False)
    if self.new_record:
      pulse = 180 + int(75 * math.sin(self.anim * 6))
      blit_text(gs, small_font, "NEW REALM RECORD!", (pulse, int(pulse * 0.6), 20), (pnl.centerx, pnl.top + 132), "center", shadow=False)
    else:
      blit_text(gs, small_font, "Record: %d" % self.data['high_score'], (110, 80, 40), (pnl.centerx, pnl.top + 132), "center", shadow=False)
    blit_text(gs, small_font, "Coins Pillaged: %d" % int(self.run_coins), (180, 120, 10), (pnl.centerx, pnl.top + 165), "center", shadow=False)
    if self.over_t > 25 and (self.over_t // 30) % 2 == 0:
      blit_text(gs, button_font, "Tap to Return to Menu", WOOD_DARK, (pnl.centerx, pnl.top + 218), "center", shadow=False)

  def draw_pause(self):
    gs = game_surface
    dim(gs, 150)
    if not self.confirm_menu:
      self.draw_sound_btn()
      blit_text(gs, title_font, "PAUSED", PARCHMENT, (WIDTH // 2, HEIGHT // 2 - 85), "center")
      draw_button(gs, RESUME_BTN, "RESUME", PARCHMENT, RESUME_BTN.collidepoint(self.mouse))
      draw_button(gs, OPT_BTN, "OPTIONS", PARCHMENT, OPT_BTN.collidepoint(self.mouse))
      draw_button(gs, MENU_BTN, "MAIN MENU", PARCHMENT, MENU_BTN.collidepoint(self.mouse))
    else:
      cp = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 80, 400, 160)
      panel(gs, cp, PARCHMENT, 255, WOOD_DARK, 6, 12)
      blit_text(gs, hud_font, "Abandon Siege?", WOOD_DARK, (cp.centerx, cp.top + 40), "center", shadow=False)
      draw_button(gs, YES_BTN, "YES", PARCHMENT, YES_BTN.collidepoint(self.mouse))
      draw_button(gs, NO_BTN, "NO", PARCHMENT, NO_BTN.collidepoint(self.mouse))
