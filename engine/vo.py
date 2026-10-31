import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro(sys.argv[1] + '/kokoro-v1.0.int8.onnx', sys.argv[1] + '/voices-v1.0.bin')
lines = json.load(open(sys.argv[2])); voice = sys.argv[4]
SR = 24000; dur = float(sys.argv[5]) if len(sys.argv) > 5 else 23.0; out = np.zeros(int(dur * SR))
for t, txt, spd in lines:
    a, sr = k.create(txt, voice=voice, speed=spd, lang='en-us')
    nz = np.nonzero(np.abs(a) > 0.01)[0]; a = a[nz[0]:nz[-1] + 1]
    print(f'{t:5.2f} {len(a)/sr:4.2f}s {txt}')
    i = int(t * SR); j = min(len(out), i + len(a)); out[i:j] += a[:j - i]
sf.write(sys.argv[3], out / max(1e-6, np.abs(out).max()) * 0.95, SR)
