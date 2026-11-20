# the journey

okay so i was thinking. hey, i want to see a decode step, unfused, as an actual visible graph. like a real boxes-and-arrows graph. because CUDA graphs are called graphs, and they aren't really graphs, not in any way you can look at. you capture one, you replay it, it's faster, and the "graph" part is a black box handle you never see.

so the joke was: i thought CUDA graphs were graphs, so i made them graphs. and then a pixel-art Miku walks across it in the terminal, because why not.

this is how that went. it took about two days (19 to 20 November 2026), around 40 commits, and an embarrassing number of rounds arguing with a critic about a cartoon girl's mouth. i built it pairing with Claude (Claude Code), with review agents playing "critic" and "art director" at the gates.

## 0. what a CUDA graph actually is

quick version, because this is the whole point.

when PyTorch runs a model in eager mode, every op launches its own kernel. a matmul goes to cuBLAS, which picks a GEMM kernel for that shape on that GPU. an RMSNorm written in plain PyTorch is not one kernel, it's eight: copy, pow, mean, add eps, rsqrt, mul, a bf16 copy, mul. nothing gets fused unless you ask a compiler to fuse it.

a CUDA graph records all those launches once, with the dependencies between them, so the GPU can replay the whole thing without the CPU launching each kernel again. that record is a real graph: nodes are kernels and memsets, edges are "this has to finish before that starts". you just never get to see it.

## 1. the spike: can we even get the graph out

first question: can you get the graph back out of PyTorch at all, without a profiler?

yes, with a recent enough torch (2.14 with cu130, in WSL on my laptop's RTX 3050). capture with the graph kept, instantiate it, and `get_graph_data()` hands you a dict: every node, its type, its kernel name, and who it depends on. no parsing needed. NVIDIA's DOT dump has the same graph with launch configs too, but reading it was a trap: networkx's DOT reader silently returns an empty graph, because everything sits inside a cluster subgraph. no error, just 0 nodes. fun.

stuff the spike taught me:

- **my diamond had 6 nodes, not 4.** cuBLAS slipped a memset in front of each fp32 GEMM (split-K workspace). you cannot predict node counts from the model code.
- **kernel names come out of the capture.** cuBLAS names are readable (`ampere_sgemm_128x64_nn`). PyTorch and CUTLASS names are mangled C++ and need c++filt. even demangled, every elementwise kernel has the same base name, so the useful bit (add? rsqrt? silu?) has to be dug out of template arguments.
- **"GEMV for decode, GEMM for prefill" is only half true.** for 1 token, cuBLAS picked tensor-core CUTLASS GEMMs for the 1024x1024 projections and split-K plus a reduce for the down projection. GEMV shows up only for attention and the wide gate/up projections. that table alone was worth the whole spike.
- **stream joins add redundant edges.** drawn naively they run straight through a box, so there's a transitive reduction before drawing.
- **a 36-node decode layer, drawn uncollapsed, is a column of slivers.** you could read the numbers but not the graph. folding runs of small elementwise kernels into one box ("norm x8") brought it down to something you can actually read, with the Q/K/V three-way fork and the gate/up fork right there.
- **only about a third of the nodes are cuBLAS.** concat, softmax and elementwise kernels outnumber the GEMMs. "cuBLAS picks the kernels" is true only for the matmuls.

and the big one, the reason the joke works: **a single-stream capture is just a chain.** if everything is on one stream, every kernel depends on the one before it, and the "graph" is a straight line. forks show up only when work goes onto several streams. so the presets put independent branches on separate streams on purpose, and the tool says so.

the first drawings were braille (plotille). they worked, but box-drawing characters ended up much more readable, so v1 went with those.

## 2. feature/v1: Miku walks the graph

the spike scripts got ported into a proper package (`cgviz`): presets, capture, graph loading, layering with crossing reduction, a box-drawing renderer, and a walk simulation. `cgviz decode` captures one transformer layer on the GPU, checks the replay matches eager exactly, saves the graph data, draws it, and then a small sprite walks it:

- she starts at the first node, walks the edges, pauses at each box while it highlights
- at a fork she splits into one walker per branch
- at a join, whoever arrives first waits for the others
- at the end there's a little victory hop

then came the beta critic rounds, with a reviewer agent picking at recordings frame by frame: boxes drawn in front of sprites, labels hidden under her, feet floating off the line, the fork looking like a race, the victory landing in the wrong place. round by round those got fixed.

### honesty pass

somewhere in here i realised the walk was quietly lying. she walked at different paces, so it looked like a timeline, and a fork looked like "these run in parallel". neither is what a captured graph tells you. so:

- every run now starts with a **provenance header**: how many streams were actually used during capture (measured, not assumed), the GPU, CUDA and cuBLAS versions, and the main GEMM shapes
- the fork caption says "independent: neither waits for the other", which is what a fork means. whether the GPU actually overlaps them is a different question that the graph can't answer
- she walks at the same pace everywhere. the walk shows structure, not time
- it's called a "captured graph" everywhere, because that's what it is

## 3. Miku v2: the art rabbit hole

the v1 sprite was tiny and blocky. v2 was supposed to be "a bit nicer". it turned into most of the project.

- **gate 1:** extract a pixel grid from a reference image. the first attempt built her torso, arms and skirt out of rectangles and looked like a robot, so it was rejected. the redo samples six poses straight from a pose sheet, normalises them to one height and one baseline, and only ever edits pixels, never redraws from rectangles. then a cleanup pass took specks from 109 down to 4, checkerboard mixing from 62 to 1, and outline gaps from 74 to 0.
- **gate 2:** side-view head and body, procedural twin tails, a walk cycle, a tired walk, turn clips, and a **facing planner**: she never moonwalks, never walks in front view, turns to the side before her first step, and turns through the front before reversing. also a style bible, so later fixes didn't drift.
- **gate 2b and 2c:** tails arc behind her instead of through her head (there was an angle bug), the far side of her body is darker, a spinning leek, and an upright chibi walk with her head over her hips.
- **gate 2d:** the art director wanted her turned diagonally, like chibi Miku walking in the anime. so the cheerful walk became a 3/4 view: open arms, leek aloft, tails flaring. the side walk was kept as the best earlier version.
- **gate 2e, the hair flicker:** recordings showed dark specks flickering on her hair. the sprite data was clean, and so were compositing and the diff redraw. the cause was the GIF recorder: it decoded each pty read on its own, so a 3-byte half-block character split across two reads became two garbage glyphs. one cast had 108 of them. the fix was an incremental UTF-8 decoder, plus a regression test that chops the byte stream into 7-byte chunks and replays it through a terminal emulator. after that: a flowy skirt with a lagging hem, an elbow on the leek arm, and a 3/4 tired walk. three critic rounds; the fourth made things worse and got reverted, because the rule is you only keep a change if it scores at least as well as the best so far. for the tired walk i picked option B out of three side-by-side.

## 4. making it run in the terminal you already have

a gorgeous 74x72-pixel Miku is useless if you need a 160x50 terminal to see her.

- **terminal support:** truecolor when the terminal says it has it, otherwise nearest xterm-256 (every pair of palette colours stays distinct, and that's tested); synchronized output so frames don't tear; VT mode switched on in Windows consoles, falling back to the static view if that fails.
- **size tiers:** a compact Miku at half size for a normal 80x24 terminal. the first idea was redrawing her small from scratch (thumbnail B), and it was rejected because it didn't look like her anymore. what worked was halving the approved drawings, then fixing by hand the parts halving destroys: torso, arms, leek, mouths, eyes, legs. six critic rounds, best score 35/35. along the way: a '^' for cheerful eyes, a 'v' smile that read as an open mouth and got reverted, and hand-drawn half-size legs because halving kept eating the far leg.
- **PowerShell:** the Windows console echoed keypresses into the animation, so the console's echo and line input are switched off while she walks (and restored after). stdout is forced to UTF-8 when piped.

## 5. v2 walks the real graph

up to here, v2 only walked in a demo. wiring her into the real graph walk broke all the old assumptions, because v1 was 12 cells wide and compact v2 is 37x20:

- the layout now spaces siblings a sprite-width apart and layers a sprite-height apart
- fork and join tracks moved next to the target boxes, so she has open space to stand in
- she stands beside a box on its right side, or under it on its bottom border, never on top of the label
- the facing rules hold on the graph too (tested on all three fixture graphs, at three sizes and three speeds): turns happen standing still, and the walk cycle advances one tick per cell walked, so at any `--speed` her feet keep pace with the ground
- the tier is picked from your terminal size, and the v1 sprite comes back when the terminal is too small

## 6. `cgviz show`: replay anywhere

capture needs a recent torch on Linux/WSL. but the graph data is just JSON, so `cgviz show out/.../graph_data.json` replays a saved capture on any machine, no GPU needed, including native Windows. kernel names are now demangled at capture time and saved, because Windows has no c++filt. and if your torch is too old to list graph nodes, you get a clear error instead of a traceback.

## so what is this, actually

what it does: you pick a workload (a preset, or your own `file.py:function`). PyTorch runs it once in eager mode. each op dispatches to its kernel: matmuls go to cuBLAS (which picks a GEMM kernel for that shape on your GPU), and everything else goes to PyTorch's own kernels, one per op, unfused. the capture records every kernel and memset and what each one waits on. cgviz draws that as a graph, labels it with the real kernel names, and Miku walks it.

who it helps:

- people learning why `torch.compile` and fused kernels matter. seeing RMSNorm as eight separate boxes says it better than any blog post.
- people curious what cuBLAS actually picks for their shapes: GEMV vs GEMM vs split-K, and the tile sizes.
- anyone who thought a CUDA graph gives you parallelism for free. a single stream gives you a chain, and the drawing shows it.

what it isn't: a profiler. there's no timing in the drawing. graphs past about 30 nodes get long and folded. and it started as a joke that got out of hand.

## what's left

- an `--unfold` flag to show every kernel instead of folded runs
- a menu to pick a workload instead of typing a subcommand
- long walks: decode takes about 70 s at `--speed 1.5`
- `time` and `vs-ncu` are still stubs
- grab/rappel, pants, reactions and a dance were deferred, and are still deferred
