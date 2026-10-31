import numpy as np, json, sys, wave
ev = json.load(open(sys.argv[1])); SR = 44100; FPS = ev['fps']
n = int(ev['dur'] * SR); out = np.zeros(n); t = np.arange(n) / SR
rng = np.random.default_rng(3)
def add(st, sig, g=1.0):
    i = int(st * SR); j = min(n, i + len(sig))
    if 0 <= i < n: out[i:j] += g * sig[:j - i]
def env(d, a=0.003, dec=None):
    tt = np.arange(int(d * SR)) / SR; e = np.minimum(1, tt / a)
    return tt, e * (np.exp(-tt / dec) if dec else 1)
def tone(f, d, dec, g, at):
    tt, e = env(d, 0.002, dec); add(at, np.sin(2 * np.pi * f * tt) * e, g)
def noise(d, dec, g, at, smooth=1):
    tt, e = env(d, 0.001, dec); x = rng.standard_normal(len(tt))
    if smooth > 1: x = np.convolve(x, np.ones(smooth) / smooth, 'same')
    add(at, x * e, g)
spot = ev['spot']; stop = spot if spot else ev['end']
# ambience + soft beam hum
out += 0.03 * np.sin(2 * np.pi * 55 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t))
out += 0.012 * np.sin(2 * np.pi * 120 * t + 2 * np.sin(2 * np.pi * 0.5 * t))
# detection whine while seen (per frame)
seen = ev['seen']; ph = 0; det = 0
for f, s in enumerate(seen):
    if f / FPS < ev['start'] or f / FPS >= stop: continue
    if s:
        i0 = int(f / FPS * SR); i1 = min(n, int((f + 1) / FPS * SR)); fr = 420 + 6 * f % 1
        tt = np.arange(i1 - i0) / SR
        freq = 380 + 400 * min(1, (f / FPS - ev['start']) / 16)
        out[i0:i1] += 0.05 * np.sin(2 * np.pi * freq * tt + ph); ph += 2 * np.pi * freq * (i1 - i0) / SR
# "!" blips
for s in ev['seen_starts']:
    if s <= stop: tone(900, 0.08, 0.03, 0.25, s); tone(1400, 0.12, 0.05, 0.25, s + 0.07)
# hop squish
for h0, h1 in ev['hops']:
    k = int(np.ceil(h0 * 7)); 
    while k / 7 < h1:
        tt, e = env(0.15, 0.003, 0.04); add(k / 7, np.sin(2 * np.pi * (260 + 200 * tt / 0.15) * tt) * e, 0.18); k += 1
# ticks last 5 s
for k in range(5, 0, -1):
    at = ev['end'] - k
    if at < stop: tone(1200 if k > 2 else 1500, 0.1, 0.03, 0.2, at)
# can tips: clang + lid clatter
tip = ev['tip'] + 0.35
for fr, g in ((523, .25), (1180, .15), (1730, .1), (2410, .07)): tone(fr, 0.9, 0.25, g, tip)
for k in range(4): noise(0.06, 0.015, 0.12, tip + 0.25 + k * 0.11)
if spot:
    # alarm siren
    for k in range(4):
        for j, fr in enumerate((700, 950)):
            tt, e = env(0.22, 0.01); sig = np.sign(np.sin(2 * np.pi * fr * tt)) * 0.5 + np.sin(2 * np.pi * fr * tt) * 0.5
            add(spot + k * 0.44 + j * 0.22, sig * np.minimum(1, (0.22 - tt) / 0.02), 0.07)
    # cage slam
    at = ev['cage'] + 0.35
    tt, e = env(0.5, 0.002, 0.1); add(at, np.sin(2 * np.pi * (90 - 30 * tt) * tt) * e, 0.8)
    for fr, g in ((780, .12), (1430, .08), (2210, .05)): tone(fr, 1.0, 0.3, g, at)
    # sad wah-wah
    for k, f0 in enumerate((392, 370, 349)):
        tt = np.arange(int(0.35 * SR)) / SR; f = f0 + 6 * np.sin(2 * np.pi * 6 * tt)
        sig = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
        add(ev['text'] + k * 0.35, sig * np.minimum(1, tt / 0.03) * np.minimum(1, (0.35 - tt) / 0.08), 0.12)
    tt = np.arange(int(0.8 * SR)) / SR; f = 330 - 60 * tt / 0.8 + 8 * np.sin(2 * np.pi * 6 * tt)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    add(ev['text'] + 1.05, sig * np.minimum(1, tt / 0.03) * np.exp(-tt / 0.5), 0.12)
else:
    for i, fq in enumerate([784, 1046, 1568]): tone(fq, 0.8, 0.3, 0.2, ev['end'] + i * 0.07)
# claw
for st, d, f0, f1 in ((ev['claw_in'], ev['grab'] - ev['claw_in'], 300, 220), (ev['lift'], 1.6, 220, 340)):
    tt = np.arange(int(d * SR)) / SR; f = f0 + (f1 - f0) * tt / d
    sig = 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    add(st, sig * np.minimum(1, tt / 0.1) * np.minimum(1, (d - tt) / 0.2), 0.06)
tt, e = env(0.3, 0.001, 0.06); add(ev['grab'], (np.sin(2 * np.pi * 900 * tt) + np.sin(2 * np.pi * 1350 * tt)) * e, 0.16)
for i, fq in enumerate([523, 659, 784]): tone(fq, 0.5, 0.18, 0.15, ev['outro'] + i * 0.1)
out = out / np.max(np.abs(out)) * 0.9
w = wave.open(sys.argv[2], 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
