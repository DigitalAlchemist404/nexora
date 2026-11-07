"""Genera los recursos ficticios de demo/recursos (dibujos hechos por código). Ya vienen incluidos: no hace falta correrlo.
Requiere Pillow y ffmpeg. Uso: python3 demo/generar_recursos.py demo/recursos"""
import math, random, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
W, H = 1280, 960
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
def font(size, mono=False):
    try: return ImageFont.truetype(MONO if mono else FONT, size)
    except OSError: return ImageFont.load_default()

def grad(d, box, top, bottom):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        k = (y - y0) / max(1, y1 - y0)
        d.line([(x0, y), (x1, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(top, bottom)))

def ruido(im, seed):
    r = random.Random(seed); px = im.load()
    for _ in range(9000):
        x, y = r.randrange(im.width), r.randrange(im.height); c = px[x, y]; v = r.randint(-12, 12)
        px[x, y] = tuple(max(0, min(255, ch + v)) for ch in c)
    return im.filter(ImageFilter.GaussianBlur(0.6))

def playa(seed):
    r = random.Random(seed); im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    hz = 470 + r.randint(-40, 40)
    grad(d, (0, 0, W, hz), (255, 140 + r.randint(-20, 20), 80), (255, 210, 150))
    sx = r.randint(250, 1000); d.ellipse([sx - 80, hz - 120, sx + 80, hz + 40], fill=(255, 235, 120))
    grad(d, (0, hz, W, 700), (40, 110, 170), (70, 160, 200))
    for i in range(14):
        y = hz + 20 + i * 16; ax = r.randint(-200, 1000); d.arc([ax, y, ax + r.randint(200, 600), y + 30], 200, 340, fill=(220, 240, 255), width=3)
    d.polygon([(0, 700), (W, 650), (W, H), (0, H)], fill=(235, 205, 150))
    px = r.choice([180, 1050]); d.line([(px, 900), (px + 40, 470)], fill=(110, 70, 40), width=26)
    for a in range(0, 360, 50):
        e = (px + 40 + 170 * math.cos(math.radians(a)), 470 + 90 * math.sin(math.radians(a)) + 40)
        d.line([(px + 40, 470), e], fill=(40, 120, 50), width=22)
    if r.random() < .7:
        ux = r.randint(450, 850); d.pieslice([ux - 150, 640, ux + 150, 820], 180, 360, fill=(220, 60, 60))
        d.line([(ux, 730), (ux, 880)], fill=(90, 90, 90), width=8)
    return ruido(im, seed)

def cumple(seed):
    r = random.Random(seed); im = Image.new('RGB', (W, H), (250, 230, 240)); d = ImageDraw.Draw(im)
    grad(d, (0, 0, W, 620), (255, 225, 235), (245, 200, 220)); d.rectangle([0, 620, W, H], fill=(150, 100, 70))
    for i in range(6):
        bx, by = r.randint(80, 1200), r.randint(60, 300); c = r.choice([(240, 70, 90), (70, 140, 240), (250, 200, 60), (120, 200, 120)])
        d.ellipse([bx - 50, by - 65, bx + 50, by + 65], fill=c); d.line([(bx, by + 65), (bx + r.randint(-30, 30), by + 260)], fill=(90, 90, 90), width=2)
    cx = W // 2 + r.randint(-80, 80); d.ellipse([cx - 330, 760, cx + 330, 860], fill=(240, 240, 240))
    d.rectangle([cx - 260, 560, cx + 260, 800], fill=(250, 240, 220)); d.ellipse([cx - 260, 520, cx + 260, 600], fill=(255, 150, 180))
    d.ellipse([cx - 260, 760, cx + 260, 840], fill=(250, 240, 220)); d.rectangle([cx - 260, 640, cx + 260, 670], fill=(255, 150, 180))
    for i in range(r.randint(3, 6)):
        x = cx - 150 + i * 70; d.rectangle([x - 9, 450, x + 9, 560], fill=r.choice([(80, 160, 240), (240, 90, 120), (250, 210, 70)]))
        d.ellipse([x - 14, 405, x + 14, 452], fill=(255, 190, 40)); d.ellipse([x - 6, 420, x + 6, 446], fill=(255, 250, 200))
    d.text((W // 2, 360), '¡FELIZ CUMPLE!', font=font(70), fill=(200, 40, 90), anchor='mm')
    return ruido(im, seed)

def futbol(seed):
    r = random.Random(seed); im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    grad(d, (0, 0, W, 260), (120, 180, 240), (190, 220, 250))
    for i in range(10): d.polygon([(0, 260 + i * 70), (W, 260 + i * 70), (W, 330 + i * 70), (0, 330 + i * 70)], fill=(60, 150, 60) if i % 2 else (75, 170, 70))
    d.line([(0, 600), (W, 560)], fill='white', width=6); d.ellipse([480, 500, 800, 660], outline='white', width=6)
    gx = r.randint(250, 900); d.rectangle([gx - 220, 220, gx + 220, 380], outline='white', width=10)
    for i in range(0, 440, 30): d.line([(gx - 220 + i, 220), (gx - 220 + i, 380)], fill=(230, 230, 230), width=1)
    for i in range(r.randint(3, 6)):
        px, py = r.randint(100, 1180), r.randint(420, 800); c = r.choice([(220, 40, 40), (30, 60, 200)])
        d.ellipse([px - 18, py - 110, px + 18, py - 74], fill=(240, 200, 160)); d.rectangle([px - 28, py - 74, px + 28, py - 10], fill=c)
        d.line([(px - 12, py - 10), (px - 22, py + 50)], fill=(30, 30, 30), width=12); d.line([(px + 12, py - 10), (px + 26, py + 50)], fill=(30, 30, 30), width=12)
    bx, by = r.randint(300, 1000), r.randint(650, 860); d.ellipse([bx - 45, by - 45, bx + 45, by + 45], fill='white', outline='black', width=3)
    d.regular_polygon((bx, by, 16), 5, fill='black')
    for a in range(0, 360, 72): d.regular_polygon((bx + 30 * math.cos(math.radians(a - 90)), by + 30 * math.sin(math.radians(a - 90)), 9), 5, fill='black')
    return ruido(im, seed)

def montana(seed):
    r = random.Random(seed); im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    grad(d, (0, 0, W, 560), (110, 170, 230), (210, 230, 250))
    for k, col in enumerate([(120, 120, 150), (90, 100, 130)]):
        x = -100
        while x < W + 100:
            w = r.randint(300, 520); h = r.randint(260, 420) - k * 60; base = 600 + k * 40
            d.polygon([(x, base), (x + w // 2, base - h), (x + w, base)], fill=col)
            d.polygon([(x + w // 2 - 50, base - h + 70), (x + w // 2, base - h), (x + w // 2 + 50, base - h + 70)], fill='white'); x += w - 120
    grad(d, (0, 620, W, 760), (70, 130, 180), (110, 170, 210)); d.rectangle([0, 760, W, H], fill=(70, 120, 60))
    for i in range(14):
        tx = r.randint(0, W); ty = r.randint(780, 940); d.polygon([(tx - 30, ty), (tx, ty - 110), (tx + 30, ty)], fill=(30, 80, 40))
    return ruido(im, seed)

def pizza(seed):
    r = random.Random(seed); im = Image.new('RGB', (W, H), (180, 130, 90)); d = ImageDraw.Draw(im)
    for i in range(0, W, 80): d.line([(i, 0), (i, H)], fill=(165, 118, 80), width=3)
    d.ellipse([240, 80, 1040, 880], fill=(245, 245, 245)); d.ellipse([300, 140, 980, 820], fill=(200, 140, 60))
    d.ellipse([330, 170, 950, 790], fill=(220, 70, 40))
    for _ in range(40): x, y = r.randint(380, 900), r.randint(220, 740); d.ellipse([x - 30, y - 22, x + 30, y + 22], fill=(250, 225, 150))
    for _ in range(14):
        a, rr = r.uniform(0, 6.28), r.uniform(0, 250); x, y = 640 + rr * math.cos(a), 480 + rr * math.sin(a)
        d.ellipse([x - 32, y - 32, x + 32, y + 32], fill=(170, 40, 40))
    for _ in range(12): x, y = r.randint(400, 880), r.randint(250, 720); d.ellipse([x - 12, y - 7, x + 12, y + 7], fill=(40, 130, 40))
    return ruido(im, seed)

def ciudad(seed):
    r = random.Random(seed); im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    grad(d, (0, 0, W, H), (10, 15, 50), (60, 40, 90)); d.ellipse([1000, 80, 1110, 190], fill=(240, 240, 210))
    for _ in range(80): x, y = r.randint(0, W), r.randint(0, 400); d.point((x, y), fill='white')
    x = 0
    while x < W:
        w, h = r.randint(70, 160), r.randint(250, 650); d.rectangle([x, H - h, x + w, H], fill=(25, 25, 40))
        for wy in range(H - h + 20, H - 20, 34):
            for wx in range(x + 12, x + w - 16, 26):
                if r.random() < .55: d.rectangle([wx, wy, wx + 12, wy + 18], fill=(255, 220, 120))
        x += w + r.randint(4, 20)
    return ruido(im, seed)

def gato(seed):
    r = random.Random(seed); im = Image.new('RGB', (W, H), (235, 225, 210)); d = ImageDraw.Draw(im)
    d.rectangle([0, 700, W, H], fill=(150, 110, 80)); c = r.choice([(230, 150, 70), (90, 90, 90), (40, 40, 40)])
    d.ellipse([440, 560, 840, 900], fill=c); d.ellipse([460, 260, 820, 600], fill=c)
    d.polygon([(480, 340), (500, 170), (600, 290)], fill=c); d.polygon([(800, 340), (780, 170), (680, 290)], fill=c)
    for ex in (565, 715): d.ellipse([ex - 38, 380, ex + 38, 450], fill=(120, 200, 90)); d.ellipse([ex - 10, 385, ex + 10, 445], fill='black')
    d.polygon([(625, 480), (655, 480), (640, 500)], fill=(240, 130, 150))
    for s in (-1, 1):
        for k in range(3): d.line([(640 + s * 40, 505 + k * 10), (640 + s * 200, 480 + k * 25)], fill=(250, 250, 250), width=3)
    d.arc([700, 700, 1000, 920], 200, 330, fill=c, width=40)
    return ruido(im, seed)

def captura_codigo(seed):
    im = Image.new('RGB', (1600, 1000), (30, 32, 40)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1600, 50], fill=(50, 52, 62)); [d.ellipse([20 + i * 34, 15, 40 + i * 34, 35], fill=c) for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)])]
    d.text((800, 25), 'lista_enlazada.py', font=font(22, True), fill=(200, 200, 200), anchor='mm')
    code = ['class Nodo:', '    def __init__(self, valor):', '        self.valor = valor', '        self.siguiente = None', '',
            'class ListaEnlazada:', '    def __init__(self):', '        self.cabeza = None', '', '    def agregar(self, valor):',
            '        nuevo = Nodo(valor)', '        if self.cabeza is None:', '            self.cabeza = nuevo', '            return',
            '        actual = self.cabeza', '        while actual.siguiente:', '            actual = actual.siguiente', '        actual.siguiente = nuevo']
    for i, line in enumerate(code):
        col = (198, 120, 221) if line.strip().startswith(('class', 'def', 'if', 'while', 'return')) else (220, 220, 220)
        d.text((40, 80 + i * 48), f'{i + 1:>2}', font=font(28, True), fill=(110, 110, 130)); d.text((110, 80 + i * 48), line, font=font(28, True), fill=col)
    return im

def horario(seed):
    im = Image.new('RGB', (1240, 1754), (250, 250, 245)); d = ImageDraw.Draw(im)
    d.text((620, 120), 'HORARIO DE CLASES', font=font(54), fill=(30, 30, 30), anchor='mm')
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']; filas = ['7:00', '8:30', '10:00', '11:30', '13:00', '14:30']
    mat = ['Matemáticas', 'Física', 'Programación', 'Inglés', 'Historia', '—']
    r = random.Random(seed)
    for j, dname in enumerate(dias): d.text((260 + j * 200, 260), dname, font=font(26), fill=(30, 30, 30), anchor='mm')
    for i, h in enumerate(filas):
        y = 320 + i * 180; d.text((90, y + 80), h, font=font(26), fill=(30, 30, 30), anchor='mm'); d.line([(160, y), (1180, y)], fill=(120, 120, 120), width=2)
        for j in range(5): d.text((260 + j * 200, y + 80), r.choice(mat).replace(' ', '\n', 1), font=font(20), fill=(40, 40, 90), anchor='mm', align='center')
    im = im.rotate(1.2, fillcolor=(200, 200, 195)); return ruido(im, seed)

def guardar(im, nombre, fecha=None, q=82):
    p = OUT / nombre
    if fecha:
        ex = Image.Exif(); ex[0x0110] = 'Telefono Demo'; ex[0x0132] = fecha
        ex.get_ifd(0x8769)[0x9003] = fecha; im.save(p, 'JPEG', quality=q, exif=ex)
    elif p.suffix == '.png': im.save(p, 'PNG', optimize=True)
    else: im.save(p, 'JPEG', quality=q)
    return p

plan = []
for i in range(10): plan.append((playa, 100 + i, f'playa_{i:02d}.jpg', f'2024:07:{12 + i // 4:02d} {16 + i % 4:02d}:{10 + i * 3:02d}:00'))
for i in range(7): plan.append((cumple, 200 + i, f'cumple_{i:02d}.jpg', f'2025:03:08 {19 + i // 4:02d}:{5 + i * 6:02d}:00'))
for i in range(8): plan.append((futbol, 300 + i, f'futbol_{i:02d}.jpg', f'2025:09:{6 + i // 3:02d} 10:{12 + i * 4:02d}:00'))
for i in range(5): plan.append((montana, 400 + i, f'montana_{i:02d}.jpg', f'2023:12:{27 + i // 3:02d} 08:{20 + i * 7:02d}:00'))
for i in range(2): plan.append((pizza, 500 + i, f'pizza_{i:02d}.jpg', f'2025:06:14 20:{30 + i:02d}:00'))
for i in range(3): plan.append((ciudad, 600 + i, f'ciudad_{i:02d}.jpg', f'2024:11:02 21:{40 + i * 2:02d}:00'))
for i in range(3): plan.append((gato, 700 + i, f'gato_{i:02d}.jpg', f'2026:01:{10 + i:02d} 09:15:00'))
for fn, seed, nombre, fecha in plan: guardar(fn(seed), nombre, fecha)
guardar(captura_codigo(1), 'captura_codigo.png'); guardar(horario(2), 'horario_escaneado.jpg', None, 70)
guardar(futbol(399).resize((1280, 720)), 'miniatura_video.png')

# Videos cortos (zoom lento sobre un dibujo) y audio (melodía sintética)
def video(img, nombre, seg=4):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', str(OUT / img), '-vf',
                    f"scale=1280:960,zoompan=z='min(zoom+0.0015,1.15)':d={seg * 25}:s=640x480:fps=25", '-t', str(seg),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '30', '-preset', 'veryfast', '-an', str(OUT / nombre)], check=True)
video('playa_03.jpg', 'video_playa.mp4'); video('cumple_02.jpg', 'video_cumple.mp4'); video('futbol_05.jpg', 'video_gol.mp4')
notas = '+'.join(f"sin(2*PI*{f}*t)*between(mod(t,4),{i*0.5},{i*0.5+0.45})" for i, f in enumerate([523, 587, 659, 698, 784, 698, 659, 587]))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', "aevalsrc=exprs='0.25*(" + notas + ")':s=44100:d=12", '-c:a', 'libmp3lame', '-b:a', '96k', str(OUT / 'melodia.mp3')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anoisesrc=d=6:c=pink:a=0.08', '-c:a', 'aac', '-b:a', '64k', str(OUT / 'nota_de_voz.m4a')], check=True)
print('listo', sum(f.stat().st_size for f in OUT.iterdir()) // 1024, 'KiB', len(list(OUT.iterdir())), 'archivos')
