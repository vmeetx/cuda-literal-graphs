# cuda-literal-graphs (cgviz)

I thought CUDA graphs were graphs, so I made them graphs.

![demo](TODO.gif)

## What you're looking at

`cgviz` draws a **captured graph**: the CUDA graph PyTorch recorded while running a workload once, with every kernel, memset and dependency it contains. Each run starts with a provenance header naming the stream count during capture, the GPU, the CUDA and cuBLAS versions and the main GEMM shapes. Kernel names are the ones chosen at capture for those shapes on that GPU.

A fork in the captured graph means its branches are independent: neither waits for the other. That is what makes it possible for the GPU to run them in parallel, but the captured graph only records the dependencies. If the workload issued everything on a single stream, the capture is a plain chain and no parallelism can appear in it.

The walk has no time axis: it shows structure, not timing. Miku walks at the same pace everywhere, and where she pauses depends only on what kind of node it is and where it sits.

## What it does

- `cgviz demo`: TODO
- `cgviz draw <path.py:function>`: TODO
- `cgviz time`: TODO
- `cgviz vs-ncu`: TODO

## Install

`pip install -r requirements.txt` (uses `--extra-index-url https://download.pytorch.org/whl/cu130` for torch), then `pip install -e .`.

Optional: `pip install -e ".[fast]"` adds n2 for the gamma and braille renderers. Without it, only the block renderer is available.

## Usage

TODO

## Output files

- `graph.json`: TODO
- `grid.txt`: TODO
- `grid.ans`: TODO
- `*.csv`: TODO
- `figure.png`: TODO

## Caveats

- Tested on cuBLAS only.
- Small graphs only (about 20-30 nodes).
- ncu disagrees with wall-clock timing by design: launch overhead is excluded.

## Environment

Run `cgviz env`.

## License

MIT. See LICENSE.
