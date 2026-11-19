"""Command-line entry point."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
import traceback
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from cgviz import io, show

DEFAULT_COLS = 160
DEFAULT_ROWS = 48
DEFAULT_SIZES = (256, 512, 1024, 2048, 4096)
DEFAULT_NCU_KERNEL = "gemm"


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--renderer", choices=show.RENDERERS, default=None, help="default: best available"
    )
    common.add_argument("--cols", type=int, default=DEFAULT_COLS)
    common.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    common.add_argument("--fit", action="store_true", help="use the terminal size")
    common.add_argument("--out", type=Path, default=None, help="output base directory")

    p = argparse.ArgumentParser(prog="cgviz", description="Draw CUDA graphs as graphs.")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", parents=[common], help="capture and draw the built-in diamond")
    d = sub.add_parser("draw", parents=[common], help="capture and draw path.py:function")
    d.add_argument("target", help="path.py:function")
    sub.add_parser("time", parents=[common], help="eager vs graph replay over a size sweep")
    sub.add_parser("vs-ncu", parents=[common], help="this timer vs Nsight Compute")
    sub.add_parser("env", help="print environment versions")
    return p


def resolve_size(args: argparse.Namespace) -> tuple[int, int]:
    if args.fit:
        ts = shutil.get_terminal_size((args.cols, args.rows))
        return ts.columns, max(ts.lines - 1, 1)
    return args.cols, args.rows


def resolve_renderer(args: argparse.Namespace) -> str:
    return args.renderer or show.best_renderer()


def load_target(target: str) -> Callable[..., Any]:
    """Load `function` from `path.py:function`. The function must return
    (workload, static_inputs)."""
    path, sep, func = target.rpartition(":")
    if not sep or not path or not func:
        raise ValueError(f"expected path.py:function, got {target!r}")
    file = Path(path)
    if not file.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(file.stem, file)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func)


def _out_dir(args: argparse.Namespace) -> Path:
    return io.make_out_dir(args.command, base=args.out or "out")


def _render_and_write(args: argparse.Namespace, fig: Any, out: Path) -> None:
    io.write_figure_png(fig, out / "figure.png")
    cols, rows = resolve_size(args)
    chars, colours = show.render(fig, cols, rows, resolve_renderer(args))
    io.write_grid_txt(chars, out / "grid.txt")
    io.write_grid_ans(chars, colours, out / "grid.ans")
    show.print_grid(chars, colours)
    print(f"wrote {out}")


def _graph_pipeline(args: argparse.Namespace, workload: Any, inputs: Any) -> None:
    from cgviz import capture, draw, graphdata, layout

    graph = capture.capture(workload, inputs)
    if not capture.check_replay(graph, workload, inputs):
        raise RuntimeError("graph replay does not match eager output")
    out = _out_dir(args)
    dot = capture.dump_dot(graph, out / "graph.dot")
    g = graphdata.to_digraph(dot)
    io.write_graph_json(g, out / "graph.json")
    fig = draw.draw_graph(g, layout.layered_layout(g))
    _render_and_write(args, fig, out)


def _plot_pipeline(args: argparse.Namespace, rows: Sequence[Any], csv_name: str) -> None:
    from cgviz import plots

    out = _out_dir(args)
    io.write_csv(rows, out / csv_name)
    _render_and_write(args, plots.plot_rows(rows), out)


def cmd_demo(args: argparse.Namespace) -> None:
    from cgviz import demo

    workload, inputs = demo.diamond()
    _graph_pipeline(args, workload, inputs)


def cmd_draw(args: argparse.Namespace) -> None:
    workload, inputs = load_target(args.target)()
    _graph_pipeline(args, workload, inputs)


def cmd_time(args: argparse.Namespace) -> None:
    from cgviz import demo, measure

    rows = measure.time_sweep(demo.diamond, DEFAULT_SIZES)
    _plot_pipeline(args, rows, "timing.csv")


def cmd_vs_ncu(args: argparse.Namespace) -> None:
    from cgviz import profile

    rows = profile.ncu_sweep(DEFAULT_NCU_KERNEL, DEFAULT_SIZES)
    _plot_pipeline(args, rows, "ncu.csv")


def cmd_env(args: argparse.Namespace) -> None:
    from cgviz import env

    env.print_env()


COMMANDS: dict[str, Callable[[argparse.Namespace], None]] = {
    "demo": cmd_demo,
    "draw": cmd_draw,
    "time": cmd_time,
    "vs-ncu": cmd_vs_ncu,
    "env": cmd_env,
}


def _origin(exc: BaseException) -> str:
    """Return `module.function` where the exception was raised."""
    tb = traceback.extract_tb(exc.__traceback__)
    if not tb:
        return "?"
    frame = tb[-1]
    return f"{Path(frame.filename).stem}.{frame.name}"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        COMMANDS[args.command](args)
    except NotImplementedError as e:
        print(f"not implemented yet: {_origin(e)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
