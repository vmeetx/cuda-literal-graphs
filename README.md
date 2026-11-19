# cuda-literal-graphs (cgviz)

I thought CUDA graphs were graphs, so I made them graphs.

![demo](TODO.gif)

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
