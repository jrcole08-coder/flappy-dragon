"""
Flappy Dragon  --  optimised + visual refresh

Performance notes
  * Backgrounds (sky, stars, moon, mountains, hills, clouds, mist, ground) are pre-rendered once.
  * Towers, scenery, enemy dragons, siege engines, coins, shields, ice/acid overlays are cached sprites.
  * Text and panels are cached; glows are additive-blended cached sprites.
  * Particle count is capped and updated with a single pass (no list.remove in loops).
  * Off-screen scenery is now removed (the old version leaked it forever).
  * One central event loop instead of a pygame.event.get() per screen.
"""
import pygame
import random
import sys
import math
import json
import os

pygame.init()

def _wide_width():
  w = h = 0
  try:
    w, h = pygame.display.get_desktop_sizes()[0]
  except Exception:
    pass
  if not (w and h):
    try:
      info = pygame.display.Info()
      w, h = info.current_w, info.current_h
    except Exception:
      w = h = 0
  a = w / float(h) if (w and h) else 4 / 3.0
  if a < 1.34:
    a = 4 / 3.0
  return max(800, min(1600, int(round(600 * a / 8.0)) * 8))

WIDTH, HEIGHT = _wide_width(), 600
XO = (WIDTH - 800) // 2
BOSS_X = min(WIDTH - 200, 560)
FPS = 60
INTRO_FRAMES = 280
INTRO_FADE = 255
BASE_GRAVITY = 0.48
FLAP_STRENGTH = -8.5
BASE_SCROLL = 5
TOWER_WIDTH = 95
FIREBALL_GRAVITY = 0.18
GROUND_H = 32
GROUND_Y = HEIGHT - GROUND_H
MAX_PARTICLES = 260

DUSK_TOP = (4, 6, 14)
DUSK_BOTTOM = (45, 25, 40)
MOON_LIGHT = (255, 254, 240)
MOON_SHADOW = (220, 215, 195)
STAR_WHITE = (255, 255, 255)
MOUNTAIN_FAR = (18, 20, 32)
MOUNTAIN_NEAR = (28, 30, 45)
HILL_MID = (35, 65, 35)
HILL_MID_LIGHT = (45, 80, 40)
HILL_FG = (25, 50, 25)

GOLD_BORDER = (218, 165, 32)
IRON_GRAY = (45, 48, 52)
STONE_WALL = (95, 100, 105)
STONE_DARK = (55, 58, 62)
STONE_LIGHT = (130, 135, 142)
IVY_GREEN = (34, 110, 45)
BANNER_GOLD = (230, 175, 20)
BANNER_BLUE = (25, 75, 160)
WOOD_BROWN = (100, 58, 24)
WOOD_DARK = (45, 25, 10)
FIRE_CORE = (255, 245, 180)
LEAF_GREEN = (25, 115, 25)
PINE_GREEN = (15, 75, 30)
TERRA_BROWN = (40, 28, 18)
PARCHMENT = (235, 225, 205)
BONE_WHITE = (240, 240, 235)
ICE_BLUE = (150, 230, 255)
SKIN_COLOR = (240, 190, 160)
CLOTH_RED = (180, 40, 40)
CLOTH_BLUE = (40, 60, 150)
CLOTH_DARK = (30, 35, 40)
MAGIC_PURPLE = (180, 50, 255)
PANEL_DARK = (16, 17, 24)

DRAGON_PALETTES = {
  "RED": {'main': (62, 48, 54), 'dark': (26, 18, 22), 'belly': (255, 150, 40), 'eye': (255, 235, 70), 'trail': [(255, 120, 20), (60, 50, 55)], 'cost': 0, 'title': "Magma Dragon", 'desc': "Molten breath leaves burning ground. Immune to fire!"},
  "BLUE": {'main': (122, 212, 236), 'dark': (40, 100, 150), 'belly': (222, 250, 255), 'eye': (255, 110, 200), 'trail': [(150, 226, 246), (235, 252, 255)], 'cost': 150, 'title': "Ice Dragon", 'desc': "Freezes foes solid. Frozen foes shatter!"},
  "GREEN": {'main': (38, 198, 152), 'dark': (18, 92, 96), 'belly': (255, 216, 72), 'eye': (255, 70, 50), 'trail': [(176, 240, 70), (255, 170, 50)], 'cost': 300, 'title': "Acid Dragon", 'desc': "Acid globs burn the ground and shatter foes."},
  "CHRONO": {'main': (25, 105, 125), 'dark': (10, 42, 62), 'belly': (240, 210, 110), 'eye': (255, 235, 130), 'trail': [(120, 230, 255), (240, 210, 110)], 'cost': 600, 'title': "Chrono Wyrm", 'desc': "Breath slows time and freezes foes."},
  "YELLOW": {'main': (248, 204, 52), 'dark': (150, 96, 24), 'belly': (255, 246, 200), 'eye': (70, 200, 255), 'trail': [(120, 220, 255), (255, 236, 90)], 'cost': 450, 'title': "Stormcaller", 'desc': "Forked lightning stuns and grounds enemies."},
  "SILVER": {'main': (150, 138, 168), 'dark': (58, 50, 78), 'belly': (236, 226, 212), 'eye': (255, 216, 60), 'trail': [(200, 236, 255), (255, 255, 255)], 'cost': 750, 'title': "Wind Owl-Drake", 'desc': "Crescent air blades blow enemies away."},
  "CHINESE": {'main': (200, 30, 40), 'dark': (140, 20, 20), 'belly': (240, 200, 50), 'eye': (0, 255, 150), 'trail': [(255, 200, 50), (220, 40, 40)], 'cost': 5000, 'title': "Celestial", 'desc': "Fire breath + 50% extra gold."},
  "SKELETAL": {'main': (220, 225, 215), 'dark': (60, 65, 60), 'belly': (160, 165, 160), 'eye': (10, 255, 50), 'trail': [(40, 40, 40), (10, 255, 10)], 'cost': 5000, 'title': "Bone Reaper", 'desc': "Death breath + Auto shield regen."},
}

BREATH_COLORS = {
  "RED": [(255, 236, 110), (255, 176, 44), (255, 96, 20), (70, 40, 34)],
  "BLUE": [(200, 240, 255), (150, 200, 255), (255, 255, 255)],
  "SILVER": [(220, 220, 220), (200, 200, 200), (255, 255, 255)],
  "GREEN": [(100, 255, 50), (50, 200, 20), (150, 255, 100)],
  "SKELETAL": [(40, 40, 40), (10, 255, 10), (100, 0, 255)],
  "CHRONO": [(255, 225, 120), (120, 230, 255), (255, 255, 255)],
}
DEFAULT_BREATH = [FIRE_CORE, (255, 160, 20), (255, 70, 0), (80, 80, 85)]
BREATH_BAR = {"RED": (255, 110, 20), "BLUE": ICE_BLUE, "YELLOW": (255, 220, 0), "SILVER": (200, 200, 200), "GREEN": (100, 255, 50), "SKELETAL": (40, 255, 40), "CHRONO": (120, 230, 255)}
BREATH_GLOW = {"RED": (140, 55, 6), "BLUE": (30, 80, 130), "YELLOW": (110, 100, 20), "SILVER": (70, 70, 80), "GREEN": (30, 100, 20), "SKELETAL": (10, 90, 20), "CHRONO": (20, 80, 100)}
DEFAULT_GLOW = (120, 50, 5)
BREATH_STATE = {"BLUE": "frozen", "YELLOW": "stunned", "SILVER": "blown", "CHRONO": "stasis"}
STASIS_FRAMES = 220
SHATTER_TINT = {"BLUE": (190, 235, 255), "GREEN": (110, 255, 60)}   # shard colour when ice / acid shatters something
WEATHER_KINDS = ["clear", "rain", "storm", "fog", "wind", "snow"]
WEATHER_WEIGHTS = [2, 3, 2, 2, 2, 2]
WEATHER_NAMES = {"rain": "Heavy Rain", "storm": "Thunderstorm", "fog": "Thick Fog", "wind": "Gale Winds", "snow": "Snowfall"}
STUCK_STATES = ("frozen", "stunned", "melted")
HOLD_STATES = ("stasis",)

ENEMY_COLORS = [((20, 85, 190), (10, 35, 110)), ((30, 140, 50), (10, 70, 20)), ((120, 30, 150), (60, 10, 90))]
UPGRADE_COSTS = [500, 1500, 3000]
BOUNTIES = [
  {"type": "collect", "target": 10, "desc": "Collect 10 Coins", "gold": 40},
  {"type": "collect", "target": 20, "desc": "Collect 20 Coins", "gold": 90},
  {"type": "collect", "target": 35, "desc": "Collect 35 Coins", "gold": 190},
  {"type": "shatter", "target": 5, "desc": "Shatter 5 Defenses", "gold": 50},
  {"type": "shatter", "target": 8, "desc": "Shatter 8 Defenses", "gold": 100},
  {"type": "shatter", "target": 15, "desc": "Shatter 15 Defenses", "gold": 230},
  {"type": "dodge", "target": 3, "desc": "Dodge 3 Fireballs", "gold": 40},
  {"type": "dodge", "target": 5, "desc": "Dodge 5 Fireballs", "gold": 90},
  {"type": "dodge", "target": 10, "desc": "Dodge 10 Fireballs", "gold": 210},
]
QUEST_GOLD_PER = {"collect": 4, "shatter": 12, "dodge": 18}


def quest_gold(q):
  return int(q.get("gold") or QUEST_GOLD_PER.get(q.get("type"), 10) * q.get("target", 5))


screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("Flappy Dragon")
game_surface = pygame.Surface((WIDTH, HEIGHT)).convert()
clock = pygame.time.Clock()

title_font = pygame.font.SysFont("serif", 80, bold=True)
hud_font = pygame.font.SysFont("serif", 38, bold=True)
button_font = pygame.font.SysFont("serif", 28, bold=True)
small_font = pygame.font.SysFont("serif", 20, bold=True)
tiny_font = pygame.font.SysFont("serif", 16, bold=True)

SAVE_FILE = os.path.join(os.environ.get("ANDROID_PRIVATE", "."), "dragon_save_v6.json")

def load_data():
  default = {
    "high_score": 0, "coins": 0, "unlocked": ["RED"],
    "upgrades": {"thick_scales": 0, "deep_lungs": 0, "coin_magnet": 0},
    "completed_quests": 0, "active_quest": None,
    "music": True, "sfx": True, "fullscreen": True, "weather": True, "difficulty": "easy",
  }
  if os.path.exists(SAVE_FILE):
    try:
      with open(SAVE_FILE, "r") as f:
        data = json.load(f)
      for k, v in default.items():
        data.setdefault(k, v)
      for k, v in default["upgrades"].items():
        data["upgrades"].setdefault(k, v)
      if "VOID" in data["unlocked"]:           # Abyssal dragon became the Chrono Wyrm
        data["unlocked"] = ["CHRONO" if u == "VOID" else u for u in data["unlocked"]]
      return data
    except (OSError, ValueError):
      pass
  return default

def save_data(data):
  try:
    with open(SAVE_FILE, "w") as f:
      json.dump(data, f)
  except OSError:
    pass

_text_cache, _glow_cache, _panel_cache, SPRITE_CACHE, _dim_cache = {}, {}, {}, {}, {}

def text(font, s, color):
  key = (id(font), s, color)
  img = _text_cache.get(key)
  if img is None:
    if len(_text_cache) > 500:
      _text_cache.clear()
    img = _text_cache[key] = font.render(s, True, color)
  return img

def blit_text(surf, font, s, color, pos, anchor="topleft", shadow=True):
  img = text(font, s, color)
  r = img.get_rect(**{anchor: pos})
  if shadow:
    surf.blit(text(font, s, (0, 0, 0)), r.move(2, 2))
  surf.blit(img, r)
  return r

def glow(radius, color):
  """Black-background radial glow, meant for BLEND_RGB_ADD."""
  key = (radius, color)
  g = _glow_cache.get(key)
  if g is None:
    g = pygame.Surface((radius * 2, radius * 2))
    for r in range(radius, 0, -2):
      k = (1 - r / radius) ** 2
      pygame.draw.circle(g, (int(color[0] * k), int(color[1] * k), int(color[2] * k)), (radius, radius), r)
    _glow_cache[key] = g.convert()
    g = _glow_cache[key]
  return g

def add_glow(surf, cx, cy, radius, color):
  surf.blit(glow(radius, color), (cx - radius, cy - radius), special_flags=pygame.BLEND_RGB_ADD)

def lighten(c, n):
  return tuple(min(255, v + n) for v in c)

def panel(surf, rect, fill=PANEL_DARK, alpha=215, border=GOLD_BORDER, bw=3, radius=10):
  key = (rect.w, rect.h, fill, alpha, border, bw, radius)
  s = _panel_cache.get(key)
  if s is None:
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*fill, alpha), s.get_rect(), border_radius=radius)
    sheen = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(sheen, (255, 255, 255, 16), (bw + 1, bw + 1, rect.w - 2 * bw - 2, max(2, rect.h // 2 - bw)), border_radius=max(2, radius - 2))
    s.blit(sheen, (0, 0))
    if bw:
      pygame.draw.rect(s, border, s.get_rect(), bw, border_radius=radius)
    s = s.convert_alpha()
    _panel_cache[key] = s
  surf.blit(s, rect.topleft)

def draw_button(surf, rect, label, color=PARCHMENT, hover=False, bg=IRON_GRAY, border=GOLD_BORDER, font=None):
  font = font or button_font
  panel(surf, rect, lighten(bg, 22) if hover else bg, 240, lighten(border, 40) if hover else border, 3, 9)
  img = text(font, label, color)
  surf.blit(img, img.get_rect(center=rect.center))

def dim(surf, alpha, rect=None):
  rect = rect or surf.get_rect()
  key = (rect.w, rect.h, alpha)
  s = _dim_cache.get(key)
  if s is None:
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    _dim_cache[key] = s = s.convert_alpha()
  surf.blit(s, rect.topleft)

KEY = (255, 0, 255)

def ck(surf):
  """Convert an opaque-with-transparent-background surface to a fast colorkey surface."""
  out = pygame.Surface(surf.get_size()).convert()
  out.fill(KEY)
  out.blit(surf, (0, 0))
  out.set_colorkey(KEY, pygame.RLEACCEL)
  return out

def cached_sprite(key, w, h, ox, oy, draw_fn):
  """Pre-render draw_fn(surface, ox, oy) into a sprite. Returns (surface, ox, oy)."""
  spr = SPRITE_CACHE.get(key)
  if spr is None:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    draw_fn(s, ox, oy)
    spr = SPRITE_CACHE[key] = (ck(s), ox, oy)
  return spr

MENU_ITEMS = [
  ("play", "ENTER REALM", PARCHMENT, IRON_GRAY, GOLD_BORDER),
  ("roster", "DRAGON ROSTER", PARCHMENT, IRON_GRAY, GOLD_BORDER),
  ("hoard", "THE HOARD", BANNER_GOLD, WOOD_DARK, GOLD_BORDER),
  ("quests", "QUESTS", ICE_BLUE, STONE_DARK, GOLD_BORDER),
  ("options", "OPTIONS", PARCHMENT, IRON_GRAY, GOLD_BORDER),
  ("exit", "ABANDON SIEGE", PARCHMENT, IRON_GRAY, GOLD_BORDER),
]
SND_BTN = pygame.Rect(14, 14, 50, 40)
OPT_KEYS = ["music", "sfx", "display", "weather", "difficulty"]
OPT_RECTS = {k: pygame.Rect(WIDTH // 2 - 190, 140 + i * 66, 380, 52) for i, k in enumerate(OPT_KEYS)}
MENU_RECTS = {k: (pygame.Rect(WIDTH // 2 - 175, 214, 350, 66) if k == "play" else pygame.Rect(WIDTH // 2 - 140, 294 + (i - 1) * 50, 280, 42)) for i, (k, *_r) in enumerate(MENU_ITEMS)}

SELECT_BOXES = [("RED", pygame.Rect(XO + 140, 100, 160, 160)), ("BLUE", pygame.Rect(XO + 320, 100, 160, 160)), ("GREEN", pygame.Rect(XO + 500, 100, 160, 160)),
        ("CHRONO", pygame.Rect(XO + 140, 280, 160, 160)), ("YELLOW", pygame.Rect(XO + 320, 280, 160, 160)), ("SILVER", pygame.Rect(XO + 500, 280, 160, 160))]
RARE_BOXES = [("CHINESE", pygame.Rect(XO + 190, 160, 200, 200)), ("SKELETAL", pygame.Rect(XO + 410, 160, 200, 200))]
UPGRADES = [("thick_scales", "Thick Scales", "Max Shields +1", pygame.Rect(XO + 100, 125, 180, 250)),
      ("deep_lungs", "Deep Lungs", "Breath Duration +1s", pygame.Rect(XO + 310, 125, 180, 250)),
      ("coin_magnet", "Coin Magnet", "Pulls Nearby Coins", pygame.Rect(XO + 520, 125, 180, 250))]

BACK_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 80, 260, 45)
SEL_BACK_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 55, 260, 40)
RARE_BTN = pygame.Rect(WIDTH - 165, HEIGHT - 55, 150, 40)
PAUSE_BTN = pygame.Rect(WIDTH - 110, GROUND_Y - 46, 95, 35)
SHIELD_BTN = pygame.Rect(15, 480, 140, 50)
DASH_BTN = pygame.Rect(15, 424, 140, 50)
DASH_COOLDOWN = 600
DASH_SPEED = 30
DASH_REACH = 400
RESUME_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 - 20, 260, 45)
OPT_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 40, 260, 45)
MENU_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 100, 260, 45)
YES_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 20, 110, 45)
NO_BTN = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 20, 110, 45)
BUY_YES = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 10, 110, 45)
BUY_NO = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 10, 110, 45)

GROUND_LISTS = ('towers', 'catapults', 'trebuchets', 'archers', 'mages', 'ballistas', 'golems')
SCENERY_TYPES = ["oak", "pine", "birch", "bush", "grass", "flowers", "rock", "smith", "knight", "dwarf", "fg_hill"]
SCENERY_WEIGHTS = [13, 13, 8, 16, 22, 10, 6, 5, 2, 2, 5]
