# Beta: Miku walks the graph

## Branches

- The scaffold's branch is **`master`**. The brief calls it "main", but `git branch -a` shows only `master`, `spike` and the new `feature/v1`.
- `feature/v1` was created off `master`. Nothing was merged or pushed. `spike` is unchanged.

## What was built

### Part 1: the port

After `pip install -e .` (verified in the WSL venv), `cgviz diamond`, `cgviz decode` and `cgviz prefill` each capture the preset on the GPU, check that replay matches eager, save the graph data and the `.dot` dump, draw the graph, and then play the walk. The older subcommands (`demo`, `draw`, `time`, `vs-ncu`, `env`) are kept. `demo` and `draw` now use the same pipeline.

The prototype now lives in these package modules:

| Module | What it holds |
|---|---|
| `presets` | the three workloads and the GEMM label table |
| `capture` | capture, replay check, dot dump, saving graph data |
| `graphdata` | classify, load, collapse, transitive reduction, plus the scaffold's `to_digraph` |
| `layout` | layering, crossing reduction, grid placement, plus the scaffold's `layered_layout` |
| `draw` | box-drawing tiles, labels, node list |
| `braille` | the legacy braille drawer and its golden test |
| `walk` | the simulation |
| `show` | the player |
| `cli` | commands and flags |

- **Flags:** `--no-miku`, `--speed`, `--no-panel` and `--full-names`, alongside the existing `--cols`, `--rows`, `--fit` and `--out`.
- **Tests:** every spike test and golden file was carried over and passes. Two scaffold tests asserted that `demo` and `draw` were still stubs; I updated them to assert the new behaviour. The layout and capture scaffold tests now pass, so their xfail marks were removed. The matplotlib `draw_graph` stub remains, with its xfail test.

### Part 2: the walk

- **Walking the graph.** The walk is planned frame by frame, separately from drawing.
  - Each edge is walked by exactly one walker, so each node is visited exactly once, in execution order.
  - Walkers stand only on edge cells or on box borders. Inside a box they walk its outline, so they never cut through it.
  - At each node she stops, plays the idle bob (the same frame shifted one pixel up and down) and the box is highlighted. The highlighted box is drawn on top of her so the stop always shows, and every box label stays readable on top of sprites.
- **Captions.** A stop's caption shows the node's number, label, kind and short kernel name. splitK reads "cuBLAS split this GEMM in two", and collapsed runs read "N tiny kernels squashed into one box". While everyone is walking, the caption shows where each walker is heading and from where, e.g. "→ cat (from Q, K, V)".
- **Forks.** The walker splits into one walker per outgoing edge at the node's out-port. Siblings leave one after another, a sprite-width apart, so they never pile up.
- **Joins.** Walkers wait about a sprite-width before their paths meet. Once all have arrived they walk in together; the extras vanish at the meeting point and one walks on.
- **Ending.** At the last node she plays the victory frame with a small hop, standing on top of the final box. The portrait in the side panel switches to its victory pose.
- **Sprite placement.** On vertical runs she is centred on the line with her feet on it. On horizontal runs she stands centred just above it. The offset eases between the two so corners don't jump, and she is mirrored when walking left.
- **Camera.** It follows the walkers and keeps them in the middle third of the view. It moves at most 3 cells per frame, but never so slowly that she leaves the view. When the walkers are split, it frames all of them, or follows the leftmost if they don't fit. A 3-row margin is kept below the last box for the ending.
- **Side panel.** The 32×48 portrait appears when the terminal fits the graph plus 34 columns and has at least 26 rows.
- **Rendering.**
  - Runs in the alternate screen with the cursor hidden.
  - Redraws by diff: only changed cells are sent, about 1–1.7 KB per walking frame, and nothing at all on unchanged idle frames.
  - Runs at about 12 fps; `--speed` scales both walking and stop time.
  - Restores the terminal on normal exit, Ctrl-C and SIGTERM (attributes, cursor, line wrap, main screen, echo).
  - After the animation, the static graph and node list are printed, so they stay in your scrollback.
  - When output isn't a terminal, or the terminal is smaller than 40×16, or with `--no-miku`, only the static graph and node list are printed.
- **Dependencies:** the runtime uses only the standard library. plotille isn't even needed now.

### Part 3: verification

- **Tests:** 94 pass, plus the existing skip and the matplotlib xfail. The new animation tests check that:
  - the route visits every node exactly once and respects execution order
  - walkers stand only on edge or node cells and never inside a box
  - each fork's split count equals its out-degree
  - a join merges only after all of its branches arrive
  - the walker count goes 1, then up to the widest fork, then back to 1
  - it ends in victory at the last node
  - transparent sprite pixels never change a graph cell
  - every frame fits the viewport and keeps the walkers in view at 100×30, 60×20 and 160×50
  - the camera moves smoothly
  - the diff redraw sends nothing for an unchanged frame
  - the special captions appear
  - the keyframe goldens match: first frame, first fork, first join and final frame, for diamond and decode
  - a real pseudo-terminal is restored after SIGINT and SIGTERM.
- **Real-terminal check:**
  - Keyframe screenshots go through tools/screenshot.py: pyte plus DejaVu Sans Mono, fed with the exact escape sequences the player sends.
  - The GIFs come from recordings of the real `cgviz` command in a pseudo-terminal. GPU captures ran one at a time.

## Deliverables in findings/beta/

- `demo_decode.gif` (recorded at `--speed 1.5`, 33 s) and `demo_diamond.gif` (speed 1, 18 s), each with its asciicast v2 recording (`.cast`) and a stills sheet of five frames sampled across it.
- Keyframes `{diamond,decode}_{first,fork,join,final}_100x30.png` and `decode_*_160x48.png`.
- `prefill_end_120x40.png`: the end of a real `cgviz prefill` run.

### How the GIFs were made

The brief asked for asciinema and agg. Neither was installed, and agg would have meant downloading a prebuilt binary, which I didn't do without asking. Instead:
- `tools/record.py` records the real command in a pseudo-terminal and writes a standard asciicast v2 file, so asciinema and agg can still be used on it later.
- It renders the GIF by replaying that recording through pyte and DejaVu Sans Mono, the same path as the screenshots.
- The GIF starts when the program enters the alternate screen (the GPU capture is trimmed off) and ends on the victory frame.

## Critic rounds (fresh subagent each time; checklist items 0–2)

| Item | Round 1 | Round 2 | Round 3 |
|---|---|---|---|
| Miku recognisable while walking | 2 | 2 | 2 |
| Visibly stays on edges | 1 | 1 | 1 |
| Caption readable at each stop | 2 | 2 | 2 |
| Split at forks obvious | 1 | 2 | 2 |
| Camera never loses her | 2 | 2 | 2 |
| No flicker | 1 | 2 | 2 |
| Ending lands | 2 | 1 | 1 |
| **Total** | **11** | **12** | **12** |

- **Round 1 flagged:**
  - Sprites hid the box being visited. Fixed: the visited box is drawn in front of her.
  - Walkers overlapped at forks. Fixed: siblings leave staggered.
  - She floated beside the line. Fixed: she is now centred on it.
  - The caption went stale while walking. Fixed: it now shows where walkers are heading.
  - The victory was small. Fixed: added a hop.
- **Round 2 flagged:**
  - Waiting walkers hid labels at the QKV join. Fixed: labels are drawn over sprites.
  - She still read as floating. Fixed: moved down a row, so the line runs through her shins.
  - The ending was cramped. Fixed: a bottom margin.
  - The hop didn't show in stills. Fixed: it is now 3 pixels tall.
  - The caption didn't say which walker was which. Fixed: "(from X)".
- **Round 3 flagged:**
  - The victory pose was hidden behind the final box. Fixed after the round: she now stands on top of it. This and the grouped caption ("→ cat (from Q, K, V)") were applied after the last allowed round, so no critic has re-checked them.
  - Not addressed: "drift off the lines" and labels split by her hair. Both come from the size mismatch below.
- **Flicker:** the critics judged it from stills only. In the recordings, frames arrive at an even 83 ms and only changed cells are sent.

## Known limitations

- **She's bigger than the graph.** The sprite is 12×8 cells while a box is 3 rows tall with 2-row gaps, so she always covers parts of nearby boxes. Labels and the visited box are drawn over her to compensate. This is why "stays on edges" never got above 1.
- **Wider spacing in the animation.** The animation re-lays out the graph with wider sibling gaps (15 columns top-to-bottom, 10 rows left-to-right) so walkers fit beside branches. The static graph printed afterwards keeps the compact spacing, so the two pictures differ slightly.
- **Run length.** Decode takes about 40 s at speed 1 (about 25 nodes with stops) and prefill about 50 s. Use `--speed 2` or `3` for a quick look.
- **Resizing.** Mid-animation resizes are handled by rebuilding the scene and doing a full redraw. That path isn't covered by a test.
- **Platforms.** Terminal restore uses termios and signals, so it's POSIX only (fine on WSL and Linux). On Windows the terminal-restore tests are skipped.
- **GIF speed.** The decode GIF is recorded at speed 1.5 to keep it around 5 MB.

## Decisions for you

1. **Tool setup:** should I install asciinema and download agg so the GIFs come from the exact tools you named? The `.cast` files are ready for it.
2. **Sprite size:** keep the 12×16 walker, or use a smaller one (e.g. 8×12) in the animation so she overlaps the graph less? A smaller one would likely fix the "stays on edges" score.
3. **Default speed:** keep 1, or make 1.5 the default since decode runs about 40 s?
4. **Character IP**, still open from the sprite round: decide before the repo goes public.
5. **The `pyproject` dependency pins** (img2unicode, matplotlib, cuda-bindings) came from the scaffold. The new path doesn't need them. Trim them, or keep them for the planned `time`/`vs-ncu` commands?
