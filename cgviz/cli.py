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

from cgviz import io, show, term

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

    p = argparse.ArgumentParser(prog="cgviz", description="Draw captured CUDA graphs as graphs.")
    sub = p.add_subparsers(dest="command", required=True)
    anim = argparse.ArgumentParser(add_help=False)
    anim.add_argument("--no-miku", action="store_true", help="static graph only")
    anim.add_argument("--speed", type=float, default=1.0, help="walk/stop speed multiplier")
    anim.add_argument("--miku-size", choices=("auto", "full", "compact", "small"), default="auto",
                      help="sprite size (auto: the largest that fits the terminal; small is "
                           "the 12-cell v1 sprite)")
    anim.add_argument("--no-panel", action="store_true", help="no portrait side panel")
    anim.add_argument("--full-names", action="store_true", help="untruncated kernel names")
    for name, desc in (("diamond", "two branches on two streams, joined"),
                       ("decode", "one transformer layer, 1 token"),
                       ("prefill", "one transformer layer, 512 tokens")):
        sub.add_parser(name, parents=[common, anim], help=f"capture and draw: {desc}")
    sub.add_parser("demo", parents=[common, anim], help="capture and draw the built-in diamond")
    d = sub.add_parser("draw", parents=[common, anim], help="capture and draw path.py:function")
    d.add_argument("target", help="path.py:function")
    sh = sub.add_parser("show", parents=[common, anim],
                        help="replay a saved capture (out/.../graph_data.json); no GPU needed")
    sh.add_argument("path", type=Path, help="graph_data.json written by an earlier run")
    sh.add_argument("--labels", choices=("diamond", "decode", "prefill"),
                    help="name the GEMMs as that preset does (Q, K, V, ...)")
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


def _graph_pipeline(args: argparse.Namespace, workload: Any, inputs: Any,
                    roles: list[str] | None = None, title: str = "") -> None:
    from cgviz import capture

    graph = capture.capture(workload, inputs)
    if not capture.check_replay(graph, workload, inputs):
        raise RuntimeError("graph replay does not match eager output")
    out = _out_dir(args)
    capture.save_data(graph, out / "graph_data.json")
    try:
        capture.dump_dot(graph, out / "graph.dot")
    except RuntimeError:
        pass
    show_graph(args, graph.data, roles, title or args.command, out, graph.provenance)


def layout_width(args: argparse.Namespace) -> int:
    """Draw to the real terminal width unless --cols was given explicitly."""
    cols, _ = resolve_size(args)
    if not args.fit and cols == DEFAULT_COLS and sys.stdout.isatty():
        cols = shutil.get_terminal_size((cols, args.rows)).columns
    return cols


def show_graph(args: argparse.Namespace, data: dict, roles: list[str] | None, title: str,
               out: Path | None = None, prov=None) -> str:
    """Draw the captured graph (and, in a terminal, let Miku walk it). Returns the static
    text, which starts with the provenance header."""
    from cgviz import draw, provenance, walk

    width = layout_width(args)
    lay, nodes, cn, ce = draw.layout(data, roles, width)
    tty = sys.stdout.isatty()
    pic = draw.to_ansi(lay) if tty else draw.to_text(lay)
    lst = draw.node_list(nodes, cn, width, full=getattr(args, "full_names", False))
    head = (prov or provenance.Provenance()).header()
    static = head + "\n\n" + pic + "\n\n" + provenance.KERNEL_NOTE + "\n" + lst
    if out is not None:
        (out / "graph.txt").write_text(head + "\n\n" + draw.to_text(lay) + "\n\n"
                                       + provenance.KERNEL_NOTE + "\n" + lst + "\n",
                                       encoding="utf-8")
    if not getattr(args, "no_miku", True) and show.can_animate():
        from cgviz import miku_walk

        size = shutil.get_terminal_size((width, args.rows))
        alay, acn, frames, sprites = miku_walk.walk(
            data, roles, width, lay.orient, size.columns, size.lines,
            speed=args.speed, size=getattr(args, "miku_size", "auto"))
        show.play(alay, acn, frames, title=f"cgviz {title} · captured graph",
                  panel=not args.no_panel, sprites=sprites)
    show.print_static(static)
    return static


def cmd_preset(args: argparse.Namespace) -> None:
    from cgviz import presets

    workload, inputs = presets.get(args.command)
    _graph_pipeline(args, workload, inputs, presets.ROLES.get(args.command), args.command)


def _plot_pipeline(args: argparse.Namespace, rows: Sequence[Any], csv_name: str) -> None:
    from cgviz import plots

    out = _out_dir(args)
    io.write_csv(rows, out / csv_name)
    _render_and_write(args, plots.plot_rows(rows), out)


def cmd_demo(args: argparse.Namespace) -> None:
    from cgviz import demo

    from cgviz import presets

    workload, inputs = demo.diamond()
    _graph_pipeline(args, workload, inputs, presets.ROLES["diamond"], "diamond")


def cmd_draw(args: argparse.Namespace) -> None:
    workload, inputs = load_target(args.target)()
    _graph_pipeline(args, workload, inputs)


def cmd_show(args: argparse.Namespace) -> None:
    import json

    from cgviz import presets

    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise RuntimeError(f"can't read {args.path}: {e}") from e
    from cgviz import provenance

    roles = presets.ROLES.get(args.labels) if args.labels else None
    prov = None                       # the capture's own header, saved beside it
    side = args.path.with_name("provenance.json")
    if side.is_file():
        try:
            prov = provenance.Provenance.from_dict(json.loads(side.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            prov = None
    title = args.path.parent.name if args.path.name == "graph_data.json" else args.path.stem
    show_graph(args, data, roles, title, prov=prov)


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
    "diamond": cmd_preset,
    "decode": cmd_preset,
    "prefill": cmd_preset,
    "demo": cmd_demo,
    "draw": cmd_draw,
    "show": cmd_show,
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
    term.utf8_stdout()
    try:
        COMMANDS[args.command](args)
    except NotImplementedError as e:
        print(f"not implemented yet: {_origin(e)}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"cgviz: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
