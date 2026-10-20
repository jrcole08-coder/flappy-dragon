import base64
import math
import zlib
import pygame

GW, GH = 63, 62
GPAL = "1016261e2c48c7cfddffffff92a1b9385278131313bf6f4ac424304a5266e69c69282e3c5d2c288a4836fcfff16573921a1c282e324254729a"
GDATA = "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"
WING_PTS = {2: [(32, 23), (36, 22), (41, 22), (45, 22), (50, 22), (54, 24)], 3: [(32, 24), (36, 20), (40, 17), (44, 17), (48, 15), (52, 26)]}
GCACHE = {}
FEATHER_ROWS = (0, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 0)


def griffin_frames():
  if "f" in GCACHE:
    return GCACHE["f"]
  pal = [None] + [tuple(int(GPAL[i + k:i + k + 2], 16) for k in (0, 2, 4)) for i in range(0, len(GPAL), 6)]
  raw = zlib.decompress(base64.b64decode(GDATA))
  frames = []
  for f in range(4):
    s = pygame.Surface((GW, GH), pygame.SRCALPHA)
    base = f * GW * GH
    for i in range(GW * GH):
      v = raw[base + i]
      if v:
        s.set_at((i % GW, i // GW), pal[v] + (255,))
    frames.append(pygame.transform.scale(s, (GW * 2, GH * 2)))
  GCACHE["f"] = frames
  return frames


def tinted_frame(fi, kind):
  k = ("t", fi, kind)
  s = GCACHE.get(k)
  if s is None:
    s = griffin_frames()[fi].copy()
    s.fill((150, 0, 0) if kind == "red" else (110, 110, 130), special_flags=pygame.BLEND_RGB_ADD)
    GCACHE[k] = s
  return s


def feather_sprite(theta):
  b = int(round(math.degrees(theta) / 15.0)) % 24
  k = ("fe", b)
  s = GCACHE.get(k)
  if s is None:
    f = pygame.Surface((12, 5), pygame.SRCALPHA)
    for x, h in enumerate(FEATHER_ROWS):
      for y in range(2 - h, 3 + h):
        f.set_at((x, y), (18, 26, 46) if (abs(y - 2) == h and h > 0) else (44, 66, 104))
      if 1 <= x <= 8:
        f.set_at((x, 2), (150, 184, 220))
    f.set_at((9, 2), (238, 230, 214))
    f.set_at((10, 2), (238, 230, 214))
    f.set_at((0, 2), (210, 226, 244))
    f = pygame.transform.scale(f, (24, 10))
    s = GCACHE[k] = pygame.transform.rotate(f, -b * 15.0 - 180)
  return s


def draw_feather(surface, p):
  s = feather_sprite(math.atan2(p.get('vy', 0), p.get('vx', -1)))
  surface.blit(s, (int(p['x'] - s.get_width() / 2), int(p['y'] - s.get_height() / 2)))


def draw_gust_waves(surface, waves):
  for w in waves:
    h = int(w['h'])
    for wd, col in ((8, (110, 160, 214)), (5, (196, 224, 248)), (2, (255, 255, 255))):
      pygame.draw.arc(surface, col, (int(w['x'] - 22), int(w['y'] - h), 44, h * 2), 1.92, 4.36, wd)
    for k in range(5):
      yy = int(w['y'] - h * 0.8 + k * h * 0.4)
      pygame.draw.line(surface, (232, 244, 255), (int(w['x'] + 14), yy), (int(w['x'] + 14 + 30 + k * 5), yy), 2)


def draw_griffin_boss(surface, b):
  atk = b.get('atk', 'idle')
  fi = b.get('fi')
  if fi is None:
    fi = int(b['timer'] * 3) % 4
  kind = None
  if b.get('flash') and b['flash'] > 0:
    kind = "red" if atk == "dive_warn" else "white"
  spr = tinted_frame(fi, kind) if kind else griffin_frames()[fi]
  x, y = int(b['x']) - 14, int(b['y']) - 12
  if b.get('tilt'):
    r = pygame.transform.rotate(spr, b['tilt'])
    x -= (r.get_width() - spr.get_width()) // 2
    y -= (r.get_height() - spr.get_height()) // 2
    spr = r
  surface.blit(spr, (x, y))
  bx, by = int(b['x']), int(b['y'])
  if atk == "dive_warn" and b['at'] % 10 < 6:
    pygame.draw.polygon(surface, (255, 50, 40), [(bx + 50, by - 46), (bx + 72, by - 8), (bx + 28, by - 8)])
    pygame.draw.polygon(surface, (255, 255, 255), [(bx + 50, by - 46), (bx + 72, by - 8), (bx + 28, by - 8)], 2)
    pygame.draw.rect(surface, (255, 255, 255), (bx + 48, by - 34, 5, 14))
    pygame.draw.rect(surface, (255, 255, 255), (bx + 48, by - 16, 5, 5))
  if b.get('stun', 0) > 0:
    for k in range(3):
      a = b['at'] * 0.25 + k * 2.1
      pygame.draw.circle(surface, (255, 230, 60), (int(bx + 40 + math.cos(a) * 26), int(by - 16 + math.sin(a) * 6)), 4)
  draw_gust_waves(surface, b.get('waves', []))


def draw_griffin(surface, x, y, anim):
  surface.blit(griffin_frames()[int(anim * 3) % 4], (int(x) - 14, int(y) - 12))
