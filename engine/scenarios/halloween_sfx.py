"""Synth SFX for the Halloween engine. usage: python3 halloween_sfx.py events.json out.wav"""
import numpy as np, json, sys, wave
ev = json.load(open(sys.argv[1])); SR = 44100
n = int(ev['dur'] * SR); out = np.zeros(n); t = np.arange(n) / SR
rng = np.random.default_rng(1)
def add(start, sig, gain=1.0):
    i = int(start * SR); j = min(n, i + len(sig))
    if 0 <= i < n: out[i:j] += gain * sig[:j - i]
def env(d, a=0.005, decay=None):
    tt = np.arange(int(d * SR)) / SR; e = np.minimum(1, tt / a)
    return tt, e * (np.exp(-tt / decay) if decay else np.ones_like(tt))
def lp(x, k=0.05):
    y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)): acc += k * (x[i] - acc); y[i] = acc
    return y
def hp(x): return x - lp(x, 0.3)
def tone(f, d, dec, g, at):
    tt, e = env(d, 0.002, dec); add(at, np.sin(2 * np.pi * f * tt) * e, g)
def noise(d, k): return lp(rng.standard_normal(int(d * SR)), k)
# spooky soft drone (minor-ish pad)
for f, g in ((55, 0.03), (65.4, 0.018), (82.4, 0.012)):
    out += g * np.sin(2 * np.pi * f * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t + f))
out += 0.006 * np.sin(2 * np.pi * 220 * t + 3 * np.sin(2 * np.pi * 5 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t))
# damage hits: soft thumps
for s in ev['acts']:
    if s == ev['break'] and ev['fail']: continue
    tt, e = env(0.25, 0.003, 0.07); add(s, np.sin(2 * np.pi * (140 - 60 * tt) * tt) * e, 0.45)
    tt, e = env(0.04, 0.001, 0.008); add(s + 0.01, hp(rng.standard_normal(len(tt))) * e, 0.12)
# threat sounds at attacks
th = ev['threat']
for a in ev['attacks']:
    if th == 'pumpkin':
        tt, e = env(0.4, 0.002, 0.09); add(a, np.sin(2 * np.pi * (90 - 30 * tt) * tt) * e, 0.7)
        tt, e = env(0.06, 0.001, 0.012); add(a, hp(rng.standard_normal(len(tt))) * e, 0.3)
    elif th == 'cauldron':
        for k in range(5):
            tt, e = env(0.12, 0.004, 0.04); add(a - 0.5 + k * 0.11, np.sin(2 * np.pi * (180 + 260 * tt / 0.12) * tt) * e, 0.25)
        d = 0.7; tt = np.arange(int(d * SR)) / SR; add(a - 0.2, noise(d, 0.08) * np.sin(np.pi * tt / d), 0.5)
    elif th == 'hands':
        for k in range(6):
            tt, e = env(0.03, 0.001, 0.006); add(a - 0.5 + k * 0.09, hp(rng.standard_normal(len(tt))) * e, 0.35)
            tone(1800 + 300 * (k % 3), 0.04, 0.01, 0.06, a - 0.5 + k * 0.09)
    elif th == 'ghost':
        d = 1.1; tt = np.arange(int(d * SR)) / SR
        add(a - 0.6, noise(d, 0.04) * np.sin(np.pi * tt / d), 0.6)
        f = 330 - 80 * tt / d + 12 * np.sin(2 * np.pi * 5 * tt)
        add(a - 0.4, 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 2, 0.18)
    elif th == 'bats':
        d = 1.3; tt = np.arange(int(d * SR)) / SR
        add(a - 0.7, noise(d, 0.15) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 18 * tt))) * np.sin(np.pi * tt / d), 0.4)
        for k in range(4): tone(3000 + 400 * k, 0.05, 0.015, 0.04, a - 0.4 + k * 0.17)
    elif th == 'spider':
        for k in range(10):
            tt, e = env(0.02, 0.001, 0.004); add(a - 0.6 + k * 0.06, hp(rng.standard_normal(len(tt))) * e, 0.25)
        tt, e = env(0.3, 0.002, 0.08); add(a, np.sin(2 * np.pi * (110 - 40 * tt) * tt) * e, 0.5)
# timer start beep, last-5s ticks (only while timer runs)
tone(880, 0.25, 0.08, 0.2, ev['start'])
stop = ev['fail_t'] if ev['fail'] else ev['end']
for k in range(5, 0, -1):
    tk = ev['end'] - k
    if tk < stop - 0.05: tone(1200 if k > 2 else 1500, 0.12, 0.03, 0.22, tk)
# break sound
b = ev['break']; sp = ev['support']
if sp == 'bubble':
    tt, e = env(0.15, 0.001, 0.03); add(b, np.sin(2 * np.pi * (600 + 2400 * tt) * tt) * e, 0.5)
else:
    tt, e = env(0.2, 0.001, 0.04); add(b, hp(rng.standard_normal(len(tt))) * e, 0.7)
    tt, e = env(0.5, 0.003, 0.15); add(b, np.sin(2 * np.pi * (75 - 30 * tt) * tt) * e, 0.5)
if ev['fail']:
    c = ev['catch']
    if th in ('pumpkin', 'cauldron'):
        tt, e = env(0.5, 0.003, 0.15); add(c, np.sin(2 * np.pi * (220 - 300 * tt) * tt) * e, 0.6)   # gulp / sploosh
        if th == 'cauldron': add(c, noise(0.5, 0.1) * np.exp(-np.arange(int(0.5 * SR)) / SR / 0.15), 0.6)
        s_ = ev['spit']; tt, e = env(0.35, 0.003, 0.12); add(s_, np.sin(2 * np.pi * (200 + 900 * tt) * tt) * e, 0.45)  # boing out
        tt, e = env(0.2, 0.002, 0.05); add(s_ + 0.55, np.sin(2 * np.pi * (120 - 50 * tt) * tt) * e, 0.5)
    else:
        for k in range(6):
            d = 0.12; tt = np.arange(int(d * SR)) / SR; add(c + k * 0.1, noise(d, 0.2) * np.sin(np.pi * tt / d), 0.3)
    # sad "wah wah" (soft triangle-ish)
    for i, (f0, d) in enumerate(((392, 0.35), (370, 0.35), (349, 0.35), (330, 0.8))):
        tt = np.arange(int(d * SR)) / SR; ff = f0 * (1 + (0.02 * np.sin(2 * np.pi * 6 * tt) if i == 3 else 0))
        ph = 2 * np.pi * np.cumsum(ff) / SR
        sig = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * np.minimum(1, tt / 0.02) * np.minimum(1, (d - tt) / 0.08)
        add(ev['res'] + 0.05 + i * 0.36, sig, 0.13)
else:
    for i, fq in enumerate([784, 1046, 1568]): tone(fq, 0.8, 0.3, 0.2, ev['end'] + i * 0.07)
# claw whir in / out, clank
for st, d, f0, f1 in ((ev['claw_in'], 1.2, 300, 220), (ev['lift'], 1.8, 220, 340)):
    tt = np.arange(int(d * SR)) / SR; f = f0 + (f1 - f0) * tt / d
    sig = 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    add(st, sig * np.minimum(1, tt / 0.1) * np.minimum(1, (d - tt) / 0.2), 0.06)
tt, e = env(0.3, 0.001, 0.06); add(ev['grab'], (np.sin(2 * np.pi * 900 * tt) + np.sin(2 * np.pi * 1350 * tt)) * e, 0.18)
for i, fq in enumerate([523, 659, 784]): tone(fq, 0.5, 0.18, 0.15, ev['outro'] + i * 0.1)
out = out / np.max(np.abs(out)) * 0.9
w = wave.open(sys.argv[2], 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
