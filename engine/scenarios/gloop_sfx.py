"""Generic synthesized sfx for 2026-11-01+ scenarios. Usage: gloop_sfx.py events.json out.wav
events: [t, kind, extra?]. Ambience from ev['amb']: drone (Hz), wind (gain), rumble (gain)."""
import numpy as np, json, sys, wave
ev = json.load(open(sys.argv[1])); SR = 44100
n = int(ev['dur'] * SR); out = np.zeros(n); t = np.arange(n) / SR
rng = np.random.default_rng(7)
def add(st, sig, g=1.0):
    i = int(st * SR); j = min(n, i + len(sig))
    if 0 <= i < n: out[i:j] += g * sig[:j - i]
def env(d, a=0.003, dec=None):
    tt = np.arange(int(d * SR)) / SR; e = np.minimum(1, tt / a)
    return tt, e * (np.exp(-tt / dec) if dec else 1)
def tone(f, d, dec, g, at):
    tt, e = env(d, 0.002, dec); add(at, np.sin(2 * np.pi * f * tt) * e, g)
def sweep(f0, f1, d, g, at, dec=None, h2=0.0):
    tt, e = env(d, 0.005, dec); f = f0 + (f1 - f0) * tt / d; ph = 2 * np.pi * np.cumsum(f) / SR
    add(at, (np.sin(ph) + h2 * np.sin(2 * ph)) * e * np.minimum(1, (d - tt) / 0.03), g)
def lp(x, k):
    return np.convolve(x, np.ones(k) / k, 'same') if k > 1 else x
def noise(d, dec, g, at, smooth=1, a=0.001):
    tt, e = env(d, a, dec); add(at, lp(rng.standard_normal(len(tt)), smooth) * e, g)
amb = ev.get('amb', {})
out += 0.03 * np.sin(2 * np.pi * amb.get('drone', 55) * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t))
if amb.get('wind'):
    w = lp(rng.standard_normal(n), 60); w = lp(w, 30)
    out += amb['wind'] * w / (np.abs(w).max() + 1e-9) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * t))
if amb.get('rumble'):
    r = lp(rng.standard_normal(n), 200); out += amb['rumble'] * r / (np.abs(r).max() + 1e-9)
for e in ev['events']:
    at, k = e[0], e[1]; x = e[2] if len(e) > 2 else None
    if k == 'tick': tone(1500 if x else 1200, 0.1, 0.03, 0.2, at)
    elif k == 'thump':
        g = x or 1.0; tt, en = env(0.35, 0.002, 0.07); add(at, np.sin(2 * np.pi * (110 - 50 * tt) * tt) * en, 0.45 * g)
        noise(0.08, 0.02, 0.08 * g, at, 8)
    elif k == 'hop':
        tt, en = env(0.15, 0.003, 0.04); add(at, np.sin(2 * np.pi * (260 + 200 * tt / 0.15) * tt) * en, 0.16)
    elif k == 'blip': tone(900, 0.08, 0.03, 0.22, at); tone(1400, 0.12, 0.05, 0.22, at + 0.07)
    elif k == 'whoosh':
        tt, en = env(0.45, 0.15, None); w = lp(rng.standard_normal(len(tt)), 12) * np.sin(np.pi * tt / 0.45); add(at, w, 0.14)
    elif k == 'crash':
        tt, en = env(0.6, 0.002, 0.12); add(at, np.sin(2 * np.pi * (70 - 25 * tt) * tt) * en, 0.7); noise(0.5, 0.12, 0.25, at, 4)
    elif k == 'clink':
        for fr, g in ((1650, .14), (2480, .09), (3300, .05)): tone(fr, 0.5, 0.12, g, at)
    elif k == 'clang':
        for fr, g in ((523, .22), (1180, .14), (1730, .09), (2410, .06)): tone(fr, 0.9, 0.25, g, at)
    elif k == 'sizzle': noise(0.5, 0.2, 0.06, at, 2, 0.02)
    elif k == 'crackle':
        for j in range(6): noise(0.03, 0.008, 0.14, at + j * 0.05 + rng.uniform(0, 0.03), 1)
    elif k == 'snore':
        tt = np.arange(int(1.1 * SR)) / SR; en = np.sin(np.pi * tt / 1.1) ** 2
        add(at, lp(rng.standard_normal(len(tt)), 40) * en * (0.6 + 0.4 * np.sin(2 * np.pi * 28 * tt)), 0.18)
    elif k == 'creak': sweep(180, 330, 0.35, 0.09, at, None, 0.6)
    elif k == 'noise_hit':  # generic noisy landing
        noise(0.12, 0.04, 0.18 * (x or 1), at, 6); tone(170, 0.2, 0.05, 0.2 * (x or 1), at)
    elif k == 'roar':
        d = 1.0; tt = np.arange(int(d * SR)) / SR; f = 90 + 30 * np.sin(2 * np.pi * 7 * tt)
        sig = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 + lp(rng.standard_normal(len(tt)), 6) * 0.7
        add(at, lp(sig, 5) * np.minimum(1, tt / 0.05) * np.exp(-tt / 0.5), 0.35)
    elif k == 'siren':
        for j in range(4):
            sweep(700, 950, 0.22, 0.06, at + j * 0.44); sweep(950, 700, 0.22, 0.06, at + j * 0.44 + 0.22)
    elif k == 'slam':
        tt, en = env(0.5, 0.002, 0.1); add(at, np.sin(2 * np.pi * (90 - 30 * tt) * tt) * en, 0.8)
        for fr, g in ((780, .12), (1430, .08), (2210, .05)): tone(fr, 1.0, 0.3, g, at)
    elif k == 'pop': sweep(500, 1400, 0.09, 0.25, at); noise(0.05, 0.015, 0.12, at, 2)
    elif k == 'heart': sweep(660, 330, 0.3, 0.16, at, None, 0.3)
    elif k == 'freeze':
        for j, fr in enumerate((1800, 2400, 3100, 2000)): tone(fr, 0.6, 0.2, 0.08, at + j * 0.06)
        noise(0.4, 0.15, 0.1, at, 1)
    elif k == 'splash': noise(0.7, 0.2, 0.3, at, 3); tone(140, 0.3, 0.08, 0.3, at)
    elif k == 'rumble':
        d = x or 0.8; tt = np.arange(int(d * SR)) / SR
        add(at, lp(rng.standard_normal(len(tt)), 120) * np.sin(np.pi * tt / d) * 8, 0.25)
    elif k == 'win':
        for i, fq in enumerate([784, 1046, 1568]): tone(fq, 0.8, 0.3, 0.2, at + i * 0.07)
    elif k == 'wah':
        for j, f0 in enumerate((392, 370, 349)):
            tt = np.arange(int(0.35 * SR)) / SR; f = f0 + 6 * np.sin(2 * np.pi * 6 * tt)
            sig = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
            add(at + j * 0.35, sig * np.minimum(1, tt / 0.03) * np.minimum(1, (0.35 - tt) / 0.08), 0.12)
        tt = np.arange(int(0.8 * SR)) / SR; f = 330 - 60 * tt / 0.8 + 8 * np.sin(2 * np.pi * 6 * tt)
        sig = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
        add(at + 1.05, sig * np.minimum(1, tt / 0.03) * np.exp(-tt / 0.5), 0.12)
    elif k in ('claw_in', 'claw_lift'):
        d = x; f0, f1 = (300, 220) if k == 'claw_in' else (220, 340)
        tt = np.arange(int(d * SR)) / SR; f = f0 + (f1 - f0) * tt / d
        sig = 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
        add(at, sig * np.minimum(1, tt / 0.1) * np.minimum(1, (d - tt) / 0.2), 0.06)
    elif k == 'grab':
        tt, en = env(0.3, 0.001, 0.06); add(at, (np.sin(2 * np.pi * 900 * tt) + np.sin(2 * np.pi * 1350 * tt)) * en, 0.16)
    elif k == 'outro':
        for i, fq in enumerate([523, 659, 784]): tone(fq, 0.5, 0.18, 0.15, at + i * 0.1)
out = out / np.max(np.abs(out)) * 0.9
w = wave.open(sys.argv[2], 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
