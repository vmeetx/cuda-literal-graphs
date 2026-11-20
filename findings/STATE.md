# Where things stand (2026-11-20, end of day)

## Done, committed as WIP on `feature/miku-v2`

- **Whole graph on screen.** Tall graphs fold into side-by-side columns (newspaper style), so the whole graph fits the terminal. Decode fits 120x40 and prefill 120x42; a wide graph like the 4-expert one goes left to right instead.
- **Two new workloads**, captured on the GPU and saved as fixtures:
  - `examples/mlp.py`: one stream, so a plain chain
  - `examples/experts.py`: four streams, so a 4-way fork and join
- **Walk accuracy, checked by tests on all five graphs:**
  - a box lights up only after everything it depends on is done
  - each branch of a fork gets its own walker
  - a join waits for all of its branches
  - with the small default sprite, all branches leave a fork on the same frame
- **Labels:** GELU shows as `gelu`, and multiply kernels show `[mul]` (it used to say `[gpu]`).
- **README:** how the walk maps to the graph, the examples, and the size options.

## Not right yet

- **The default sprite is wrong.** `--miku-size tiny` (the default) is a 9x10 sprite drawn from scratch. It is not the approved Miku, and it has to go.
- **The five GIFs** in `findings/whole_graph/` use that sprite. They are not committed.
- **The mini tier is started but not usable.** `tools/miku/mini.py` halves the approved compact Miku to 18x18 px. Plain halving keeps the hair and silhouette but loses the eyes, torso, arms, legs and stride. It needs the same treatment compact got: halve with those parts left out, then draw them by hand at mini size.

## The user's latest direction

The user wants the two approved designs as the options: **compact** (37x36 px) and **full** (74x72 px). Demo GIFs of decode with each are recording into `findings/size_options/`:
- `compact_decode_120x40.gif`
- `full_decode_160x50.gif`

Show those first, then ask:
1. Should compact replace the tiny sprite as the default?
2. Is the mini tier still wanted?
3. Should compact and full use the whole-graph view, with her walking over the boxes, or the spread-out map with the camera following her?

## Rules still in force

- Never push. Keep `master` and `feature/v1` untouched.
- Commit locally in small steps, and stop at gates for review.
- Show images; don't describe them.
- Before any delete, a review agent confirms it, and paths use `-LiteralPath`.
- Run heavy WSL jobs one at a time.
