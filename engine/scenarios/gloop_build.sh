#!/bin/bash
# gloop_build.sh <scenario.py> <out.mp4>   (needs /tmp/tts kokoro files)
set -e
SC=$(dirname $(readlink -f $0))
SCN=$(readlink -f $1); OUT=$(readlink -f -m $2); D=/tmp/w/$(basename $SCN .py); mkdir -p $D; cd $D
if [ -z "$SKIPV" ] || [ ! -s v.mp4 ]; then python3 $SCN v.mp4 ev.json; fi
python3 $SC/gloop_sfx.py ev.json sfx.wav
python3 - $SCN <<'PY'
import json, sys, re
ev = json.load(open('ev.json')); src = open(sys.argv[1]).read()
say = re.search(r"^SAY\s*=\s*'([^']*)'", src, re.M).group(1)
json.dump([[0.2, f"Will Gloop survive {say}?", 1.0], [ev['outro'] + 0.1, "See you next challenge!", 1.0]], open('lines.json', 'w'))
open('dur', 'w').write(str(ev['dur']))
PY
python3 $SC/../vo.py /tmp/tts lines.json vo.wav am_michael $(cat dur)
CRF=24
while true; do
ffmpeg -v error -y -i v.mp4 -i sfx.wav -i vo.wav -filter_complex "[2:a]aresample=44100,asplit=2[v1][v2];[1:a]volume=0.7[s];[s][v1]sidechaincompress=threshold=0.03:ratio=6:attack=5:release=250[d];[d][v2]amix=inputs=2:weights='1 1.6':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset veryfast -crf $CRF -pix_fmt yuv420p -r 30 -c:a aac -b:a 128k -movflags +faststart -shortest out.mp4
SZ=$(stat -c %s out.mp4)
if [ $SZ -lt 4500000 ] || [ $CRF -ge 34 ]; then break; fi
CRF=$((CRF+2))
done
cp out.mp4 $OUT
echo "$(basename $OUT) size=$SZ crf=$CRF dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4)"
