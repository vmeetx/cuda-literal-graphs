"""Design-time: render a fixture with boxdraw to ANSI + screenshot.  gf_render.py PRESET OUT_STEM [WIDTH]"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "spike"), str(ROOT / "tools")]

import boxdraw  # noqa: E402
import screenshot  # noqa: E402

ROLES = {"diamond": ["gemm1", "gemm2"],
         "decode": ["Q", "K", "V", "QK", "PV", "out", "gate", "up", "down"],
         "prefill": ["Q", "K", "V", "QK", "PV", "out", "gate", "up", "down"]}


def main(preset, stem, width=120):
    width = int(width)
    data = json.loads((ROOT / "tests/fixtures/graphs" / f"{preset}.json").read_text())
    lay, nodes, cn, _ = boxdraw.layout(data, ROLES.get(preset), width)
    txt = boxdraw.to_ansi(lay) + "\n\n" + boxdraw.node_list(nodes, cn, width) + "\n"
    Path(stem + ".ans").write_text(txt, encoding="utf-8")
    sc = screenshot.screen_of(txt.encode(), width, 400)
    screenshot.render(sc, stem + ".png")
    print(preset, "tried", lay.tried, "size", lay.width, "x", lay.height)
    print(boxdraw.to_text(lay))


if __name__ == "__main__":
    main(*sys.argv[1:])
