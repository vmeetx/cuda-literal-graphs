# cuda-literal-graphs (cgviz)

I thought CUDA graphs were graphs, so I made them graphs.

![Miku walking a captured diamond graph in an 80x24 terminal](findings/miku_v2/walk_v2/diamond_80x24.gif)

`cgviz` captures a PyTorch workload as a CUDA graph, then draws that graph in your terminal as real boxes and arrows, labelled with the actual kernel names, and a pixel-art Miku walks across it.

How it came about, and everything learned along the way: [JOURNEY.md](JOURNEY.md).

## What you're looking at

`cgviz` draws a **captured graph**: the CUDA graph PyTorch recorded while running a workload once, with every kernel, memset and dependency in it.

- **Unfused, one kernel per op.** In eager mode each PyTorch op launches its own kernel. An RMSNorm written in plain PyTorch is 8 kernels. Runs of small elementwise kernels are folded into one box (`norm x8`) so the graph stays readable; the node list below the drawing names every member.
- **cuBLAS picks only the matmul kernels.** Matmuls go to cuBLAS, which picks a GEMM, GEMV or split-K kernel for that shape on your GPU. Softmax, concat and elementwise ops are PyTorch's own kernels. The names shown are the ones picked at capture.
- **Provenance header.** Every run starts with the stream count measured during capture, the GPU, the CUDA and cuBLAS versions, and the main GEMM shapes.
- **A fork means independent**, not parallel: neither branch waits for the other. That is what lets the GPU overlap them, but the graph records only dependencies. A workload issued on a single stream captures as a plain chain, and no fork can appear.
- **No time axis.** The walk shows structure, not timing. Miku walks at the same pace everywhere.

### How the walk maps to the graph

| On screen | In the captured graph |
|---|---|
| a box lights up while she stands at it | that kernel's turn: everything it depends on is done |
| she splits into k Mikus at a box, all leaving together | a fork: k kernels that depend only on this one, all ready at once |
| a Miku stops before a box and waits for the others | a join: a kernel that waits for every branch |
| one Miku walking a straight line of boxes | a single stream: each kernel waits for the one before it |
| which branch arrives first | nothing: the graph records dependencies, not durations |

## Commands

| Command | What it does |
|---|---|
| `cgviz diamond` | capture and draw two branches on two streams, joined |
| `cgviz decode` | one transformer layer, 1 token (bf16) |
| `cgviz prefill` | the same layer, 512 tokens |
| `cgviz demo` | the built-in diamond |
| `cgviz draw path.py:function` | your own workload (see below) |
| `cgviz draw examples/mlp.py:make` | a 3-layer MLP on one stream: a plain chain |
| `cgviz draw examples/experts.py:make` | four experts on four streams: a 4-way fork and join |
| `cgviz show path/graph_data.json` | replay a saved capture; no GPU needed |
| `cgviz env` | print environment versions |
| `cgviz time`, `cgviz vs-ncu` | not implemented yet |

Options for the drawing commands:

| Option | Meaning |
|---|---|
| `--speed 1.5` | walk speed multiplier |
| `--miku-size tiny\|small\|compact\|full\|auto` | sprite size. `tiny` (default) is about one box, and the whole graph stays on screen. `small` is the original 12-cell sprite. `compact` and `full` are the big Miku: the map is spread out for her and the camera follows her. `auto` picks the largest size that still shows the whole graph. |
| `--no-miku` | static drawing only |
| `--full-names` | untruncated kernel names in the node list |
| `--no-panel` | no portrait side panel (small sprite) |
| `--labels diamond\|decode\|prefill` | `show` only: name the GEMMs as that preset does (Q, K, V, ...) |
| `--out DIR` | output base directory (default `out/`) |

### Your own workload

`cgviz draw my_model.py:make` imports `my_model.py` and calls `make()`. It must return `(step, inputs)`: `step(*inputs)` is captured. An optional `ROLES` list in the file names the GEMMs in execution order. The files in `examples/` show the pattern, including `cgviz.presets.fork` for putting independent work on separate streams. Everything inside `step` has to be capturable: a CPU readback such as `.item()`, `.cpu()` or `print(tensor)` breaks capture.

## Requirements

**Capture** (`diamond`, `decode`, `prefill`, `demo`, `draw`):
- an NVIDIA GPU, on Linux or WSL2
- Python 3.10
- torch 2.14.1 built for CUDA 13.0. Older torch can't list the nodes of a captured graph; cgviz says so and stops.
- `c++filt` (binutils) to demangle kernel names

```bash
pip install -r requirements.txt
```

```bash
pip install -e .
```

**Replay** (`show`) works anywhere, including native Windows, with any recent Python plus networkx, numpy and matplotlib. Run it from a checkout:

```bash
python -m cgviz show tests/fixtures/graphs/decode.json --labels decode
```

Windows Terminal and PowerShell work. Colour falls back to 256 colours where the terminal lacks 24-bit; set `CGVIZ_COLOR` to override.

## Output files

Each capture writes to `out/<command>-<YYYYmmdd-HHMMSS>/`:

| File | Contents |
|---|---|
| `graph_data.json` | the captured graph: nodes, kernel names (raw and demangled), dependencies. `cgviz show` reads it. |
| `provenance.json` | the header: streams, GPU, CUDA, cuBLAS, GEMM shapes |
| `graph.dot` | NVIDIA's own DOT dump, with launch configs |
| `graph.txt` | the drawing and node list as plain text |

## Caveats

- Tested on one GPU (RTX 3050 Laptop) with cuBLAS. Kernel choices differ between GPUs and library versions.
- Small graphs only: around 30 nodes after folding stays readable.
- With the default tiny sprite, a tall graph is folded into side-by-side columns so all of it fits. Decode fits a 120x40 terminal and prefill fits 120x42; in a smaller terminal the camera follows her.
- Folding hides the individual elementwise kernels inside a box. The node list keeps them.

## License and credits

The code is MIT; see [LICENSE](LICENSE).

**Hatsune Miku © Crypton Future Media, INC. www.piapro.net**

The Miku sprite art (`cgviz/assets/miku/` and the drawings under `findings/` and `assets/`) is fan art of a character owned by Crypton Future Media. It is **not** covered by the MIT license. It is shared for non-commercial use under the [Piapro Character License](https://piapro.net/intl/en_for_creators.html). Don't use it commercially. If you need a commercially usable build, `--no-miku` draws the graph alone.
