"""Dev-only: cut an asciicast v2 file just before the program leaves the alternate screen,
so a GIF rendered from it (agg) ends on the last animation frame, not a blank screen."""
import json
import sys

src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding="utf-8").read().splitlines()
head, events = lines[0], [json.loads(l) for l in lines[1:]]
out = []
for t, kind, data in events:
    if "\x1b[?1049l" in data:
        data = data.split("\x1b[?1049l")[0]
        if data:
            out.append([t, kind, data])
        break
    out.append([t, kind, data])
with open(dst, "w", encoding="utf-8") as fh:
    fh.write(head + "\n")
    for e in out:
        fh.write(json.dumps(e) + "\n")
print(f"{len(out)} events kept of {len(events)}")
