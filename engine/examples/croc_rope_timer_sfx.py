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
def hp(x, k=0.9):
    y = np.zeros_like(x); prev = 0
    for i in range(1, len(x)): prev = k * (prev + x[i] - x[i - 1]); y[i] = prev
    return y
def tone(f, d, dec, g, at):
    tt, e = env(d, 0.002, dec); add(at, np.sin(2 * np.pi * f * tt) * e, g)
out += 0.035 * np.sin(2 * np.pi * 55 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * t))
for s in ev['bounces']:
    tt, e = env(0.25, 0.003, 0.07); add(s, np.sin(2 * np.pi * (140 - 60 * tt) * tt) * e, 0.45)
    tt, e = env(0.03, 0.001, 0.006); add(s + 0.01, hp(rng.standard_normal(len(tt))) * e, 0.18)
for c in ev['chomps']:
    tt, e = env(0.35, 0.002, 0.08); add(c, np.sin(2 * np.pi * 85 * tt) * e, 0.7)
    tt, e = env(0.05, 0.001, 0.01); add(c, hp(rng.standard_normal(len(tt))) * e, 0.5)
# timer start beep, last-5s ticks
tone(880, 0.25, 0.08, 0.2, ev['start'])
for k in range(5, 0, -1):
    tone(1200 if k > 2 else 1500, 0.12, 0.03, 0.22, ev['end'] - k)
# time up ding
for i, fq in enumerate([784, 1046, 1568]):
    tone(fq, 0.8, 0.3, 0.2, ev['end'] + i * 0.07)
# claw whir in / out, clank
for st, d, f0, f1 in ((ev['claw_in'], 1.4, 300, 220), (ev['lift'], 1.8, 220, 340)):
    tt = np.arange(int(d * SR)) / SR; f = f0 + (f1 - f0) * tt / d
    sig = 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    add(st, sig * np.minimum(1, tt / 0.1) * np.minimum(1, (d - tt) / 0.2), 0.06)
tt, e = env(0.3, 0.001, 0.06); add(ev['grab'], (np.sin(2 * np.pi * 900 * tt) + np.sin(2 * np.pi * 1350 * tt)) * e, 0.18)
# rope snap
b = ev['break']
tt, e = env(0.2, 0.001, 0.04); add(b, hp(rng.standard_normal(len(tt))) * e, 0.8)
tt, e = env(0.6, 0.003, 0.2); add(b, np.sin(2 * np.pi * (70 - 30 * tt) * tt) * e, 0.6)
# outro chime
for i, fq in enumerate([523, 659, 784]): tone(fq, 0.5, 0.18, 0.15, ev['outro'] + i * 0.1)
out = out / np.max(np.abs(out)) * 0.9
w = wave.open(sys.argv[2], 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
