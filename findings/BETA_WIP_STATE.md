# Beta work: paused state (2026-11-19)

The work was paused by the user mid-port. Resume from here.

## Branches

- **master:** the scaffold. The brief called it "main", but here it is `master`. Untouched.
- **spike:** the prototype, unchanged. The last commit is aefc1c5, the box-drawing graph fix.
- **feature/v1:** created off master and holds this WIP commit. Nothing is pushed or merged.
- The untracked `capture.py` at the repo root predates this work. It was left alone.

## Done so far on feature/v1 (Part 1: port, partial)

A one-off script split the spike drawers into package modules:
- `cgviz/graphdata.py`: classify, load, collapse and transitive reduction from spike/graphdraw.py, plus `read_graph_data` and `to_digraph` (the scaffold API, now implemented).
- `cgviz/layout.py`: layering, dummies and crossing reduction from graphdraw; `dwidth`, `cut`, `Layout`, `plan` and `dims` from boxdraw; plus `layered_layout` (the scaffold API, implemented). `plan` takes a `node_gap` argument.
- `cgviz/draw.py`: tiles, labels, short names, `draw_plan`, stream tags, legend, `layout()` (which now takes `node_gap`), text and ANSI output, and the node list. `draw_graph` remains the scaffold's matplotlib stub.
- `cgviz/braille.py`: the legacy braille raster and render (spike v2), kept for its golden test.

These modules are **not yet verified to import or run**. Last known state: `cgviz/draw.py` still uses `gd.` references. That is intended, because draw imports graphdata as gd. But draw.py must also import `layers_of`, `with_dummies` and `reduce_crossings` if it uses them; check this.

## Remaining (in order)

1. **Finish the port:**
   - Create `cgviz/presets.py`: the diamond, decode and prefill workloads plus the ROLES table, from spike/lab.py.
   - Implement `cgviz/capture.py`: capture, check_replay and dump_dot, plus a helper returning (graph_data, ok, maxerr), from spike/lab.py's capture().
   - Implement `cgviz/demo.py` `diamond()` via presets.
   - In `cgviz/cli.py`, add the `diamond`, `decode` and `prefill` subcommands with the flags `--no-miku`, `--speed`, `--no-panel` and `--full-names`. Keep the existing subcommands.
   - Copy the tests and goldens from spike: test_boxdraw.py, test_graph_golden.py, tests/golden/*, tests/fixtures/graphs/*. Repoint them at cgviz.draw and cgviz.braille.
   - Check that `pip install -e .` and `cgviz decode` work in the WSL venv at /home/vmeetx/cudagraph-term/.venv.
2. **Part 2 (animation), planned design:**
   - Add `cgviz/walk.py`, a pure simulation: one walker per edge, split at forks, wait at joins (at the first shared path cell), and merge.
   - Routes run along the box outline:
     - TB: in at the top port, along the top border to the right border's midpoint (the stop), then down and along the bottom border to the port.
     - LR: in at the left port, up the left border and along the top to its midpoint (the stop), then on to the right port.
   - Placing the sprite beside the path:
     - TB: to the right of the path, 2 cells out.
     - LR: above the path.
   - The animation layout uses a wider `node_gap` so sprites fit beside branches.
   - Bob: pad the frame to 18 rows and shift it by one pixel.
   - Mirror the frame when moving left.
   - Add the animation player to `cgviz/show.py`:
     - alternate screen, diff-based redraw, about 12 fps
     - the camera keeps walkers in the middle third and moves at most 2 cells per frame
     - a portrait side panel when the terminal is wide enough
     - restores the terminal on exit, on Ctrl-C and on SIGTERM
     - prints the static graph after leaving the alternate screen
     - falls back to static output when not a TTY or when the terminal is too small.
3. **Part 3:**
   - Tests: route, cell occupancy, splits, joins, transparency, viewport, and keyframe goldens.
   - Screenshots via tools/screenshot.py (copy it from spike).
   - GIFs via asciinema and agg.
   - Up to three critic rounds.
   - findings/BETA.md.

## Environment notes

- WSL Ubuntu-22.04, venv at /home/vmeetx/cudagraph-term/.venv. pyte, wcwidth and fonttools are installed as design-time tools.
- Run GPU captures one preset at a time. Prefill once crashed WSL when run back to back with others; run it on its own. The WSL restart also wiped /tmp, so recreate /tmp/gf and /tmp/cgout.
- Run WSL commands from a script file via PowerShell (`wsl -d Ubuntu-22.04 -- bash "/mnt/d/..."`). Inline quoting breaks.
- Never write regex `\b` through a Python heredoc: it turns into backspace characters.
