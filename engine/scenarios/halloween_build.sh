#!/bin/bash
# build.sh N  -> /tmp/w/out/vN.mp4
set -e
N=$1; D=/tmp/w/b$N; mkdir -p $D /tmp/w/out; cd $D
SC=/home/claude/gloop-videos/engine/scenarios
python3 $SC/2026-10-31_v$N.py v.mp4 ev.json
python3 $SC/halloween_sfx.py ev.json sfx.wav
python3 - <<PY
import json
ev=json.load(open('ev.json')); P=json.load(open('/tmp/w/plan.json'))[$N-1]
json.dump([[0.2, f"Will Gloop survive {P['say']}?", 1.0],[ev['outro']+0.1, "See you next challenge!", 1.0]], open('lines.json','w'))
open('dur','w').write(str(ev['dur']))
PY
python3 /home/claude/gloop-videos/engine/vo.py /tmp/tts lines.json vo.wav am_michael $(cat dur)
CRF=24
while true; do
ffmpeg -v error -y -i v.mp4 -i sfx.wav -i vo.wav -filter_complex "[2:a]aresample=44100,asplit=2[v1][v2];[1:a]volume=0.7[s];[s][v1]sidechaincompress=threshold=0.03:ratio=6:attack=5:release=250[d];[d][v2]amix=inputs=2:weights='1 1.6':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset veryfast -crf $CRF -pix_fmt yuv420p -r 30 -c:a aac -b:a 128k -movflags +faststart -shortest out.mp4
SZ=$(stat -c %s out.mp4)
if [ $SZ -lt 4500000 ] || [ $CRF -ge 34 ]; then break; fi
CRF=$((CRF+2))
done
cp out.mp4 /tmp/w/out/v$N.mp4
echo "v$N size=$SZ crf=$CRF dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4)"
