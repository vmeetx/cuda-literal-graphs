"""Dev-only: enlarge P2's raised hand by 2 px so it reads as a fist gripping the leek.

The fist becomes 5x4 skin (with a shade column and one finger-separation line), outlined,
with the stalk leaving through its top-left. Rows 12-17, columns 11-20 only; '.' in the patch
means "keep the existing pixel". The wink, the kick and the leek angle are untouched.
"""

import json
import shutil
from pathlib import Path

REF = Path(__file__).resolve().parent / "ref"
PATCH = {  # columns 11..20; the hand grips the lower end of the stalk (rows 18-20 originally)
    17: "...BEEbEPB",      # knuckles wrap the stalk: 1 px taller on top, stalk shows through
    21: "...BEEEEPB",      # palm: 1 px taller below, above the cuff
}


def main():
    poses = json.loads((REF / "poses.json").read_text())
    before = REF / "poses_before_p2hand.json"
    if not before.exists():
        shutil.copy(REF / "poses.json", before)
    g = [list(r) for r in json.loads(before.read_text())["P2"]]   # always from the original
    for y, row in PATCH.items():
        for i, ch in enumerate(row):
            if ch == "-":
                g[y][11 + i] = "."
            elif ch != ".":
                g[y][11 + i] = ch
    poses["P2"] = ["".join(r) for r in g]
    (REF / "poses.json").write_text(json.dumps(poses, indent=0))
    for y in range(10, 20):
        print(y, poses["P2"][y][8:24])


if __name__ == "__main__":
    main()
