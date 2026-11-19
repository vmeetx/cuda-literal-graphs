"""Design-time: the tile-set style sheet, rendered by the real drawer and the screenshot tool."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "spike"), str(ROOT / "tools")]

import boxdraw  # noqa: E402
import screenshot  # noqa: E402

K = "kernel"
DATA = {"nodes": [
    {"index": 0, "node_type": "memset", "kernel_name": None, "dependencies": []},
    {"index": 1, "node_type": K, "kernel_name": "ampere_bf16_s1688gemm_bf16_128x128", "dependencies": [0]},
    {"index": 2, "node_type": K, "kernel_name": "gemv2T_kernel_val", "dependencies": [1]},
    {"index": 3, "node_type": "event_record", "kernel_name": None, "dependencies": [1]},
    {"index": 4, "node_type": K, "kernel_name": "vectorized_elementwise_kernel_CUDAFunctor_add",
     "dependencies": [1]},
    {"index": 5, "node_type": K, "kernel_name": "softmax_warp_forward", "dependencies": [2, 3, 4]},
    {"index": 6, "node_type": K, "kernel_name": "unrolled_elementwise_kernel_silu", "dependencies": [5]},
    {"index": 7, "node_type": K, "kernel_name": "elementwise_kernel_BinaryFunctor_mul", "dependencies": [6]},
]}


def main(out=str(ROOT / "findings/graph_fix/style_sheet.png")):
    parts = ["\x1b[1mTile set\x1b[0m  heavy = GEMM-type, light = other kernel, rounded = memset/memcpy/event",
             "edges: orthogonal, autotiled junctions (fork ├/┬, join ┤/┴), arrowheads ▶ ▼, stream tags s1 s2 s3", ""]
    for orient in ("LR", "TB"):
        lay, _, _, _ = boxdraw.layout(DATA, ["proj"], width=200, prefer=(orient,))
        parts += [f"\x1b[2m{orient}\x1b[0m", boxdraw.to_ansi(lay), ""]
    txt = "\n".join(parts)
    sc = screenshot.screen_of(txt.encode(), 100, 200)
    screenshot.render(sc, out)
    print(boxdraw.to_text(lay))


if __name__ == "__main__":
    main(*sys.argv[1:])
