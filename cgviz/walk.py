"""Miku walks the graph: a pure, frame-by-frame simulation (no terminal I/O here).

Rules
- Walkers only ever stand on edge cells (the drawn path of an edge) or node cells (a box's
  border). Inside a box they walk along its outline, so they never cut through it.
- Each node is visited exactly once, in execution order: one walker per edge.
- At a node with k outgoing edges the walker splits into k walkers at the node's out-port.
- At a node with k incoming edges, walkers wait just before their paths first overlap until
  all k have arrived, then merge into one, which walks on into the node.
- At each node the walker stops (idle bob) and the box is highlighted; the caption names it.
- At the last node she plays the victory frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FPS = 12
STOP_FRAMES = 14       # time standing at a node, at --speed 1
VICTORY_FRAMES = 30
WAIT_BACK = 13         # cells before the meeting point where walkers wait at a join
SPRITE_GAP = 13        # cells a walker gets ahead before its sibling leaves a fork
HOP = (0, 0, -1, -2, -3, -3, -2, -1, 0, 0, 0, 0)  # victory hop, pixels
BOB = (0, 0, 0, -1, -1, -1, 0, 0, 0, 1, 1, 1)  # pixel offsets over one bob cycle


@dataclass
class Walker:
    id: int
    pos: tuple[int, int]
    state: str = "stop"            # stop | walk | wait | done | victory
    cells: list = field(default_factory=list)   # remaining cells to walk
    node: int | None = None        # node being stopped at / walked to
    edge: tuple | None = None      # edge being walked
    timer: float = 0.0
    facing: int = 1                # +1 right, -1 left
    steps: int = 0                 # cells walked (drives the walk-frame alternation)
    then: str = ""                 # what to do when cells run out: arrive | split | wait


@dataclass
class Frame:
    walkers: list                  # [(id, pos, sprite, facing, dy)]
    highlight: frozenset           # node ids whose box is highlighted
    caption: str
    event: str = ""                # "", "split", "merge", "victory"


def caption_for(nd: dict) -> str:
    n = nd["members"][0]
    if len(nd["members"]) > 1:
        return (f"#{n}-{nd['members'][-1]}  {nd['label']}  ·  "
                f"{len(nd['members'])} tiny kernels squashed into one box")
    if nd.get("op") == "splitK":
        return f"#{n}  {nd['label']}  ·  cuBLAS split this GEMM in two"
    from cgviz.draw import short_name

    kind = "gemm" if nd.get("op") in ("gemm", "splitK") else nd["kind"]
    return f"#{n}  {nd['label']}  ·  {kind}  ·  {short_name(nd['full'])}"


def _dedupe(cells):
    out = []
    for c in cells:
        if not out or out[-1] != c:
            out.append(c)
    return out


def _line(a, b):
    """Cells from a to b inclusive, along one axis."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    out, x, y = [(x0, y0)], x0, y0
    while (x, y) != (x1, y1):
        x, y = x + dx, y + dy
        out.append((x, y))
    return out


def node_route(box, orient):
    """(entry, stop, exit) cells on a box's border.

    TB: enter at the top port, walk the top border to the right side, stop at the middle of
    the right border, leave down the right side and along the bottom border to the port.
    LR: enter at the left port, go up and along the top border, stop at its middle, then on
    along the top and down the right side to the out-port.
    """
    x0, y0, x1, y1 = box
    if orient == "TB":
        px, cy = (x0 + x1) // 2, (y0 + y1) // 2
        entry = _line((px, y0), (x1, y0)) + _line((x1, y0), (x1, cy))[1:]
        stop = (x1, cy)
        exit_ = _line((x1, cy), (x1, y1))[1:] + _line((x1, y1), (px, y1))[1:]
    else:
        cx, py = (x0 + x1) // 2, (y0 + y1) // 2
        entry = _line((x0, py), (x0, y0)) + _line((x0, y0), (cx, y0))[1:]
        stop = (cx, y0)
        exit_ = _line((cx, y0), (x1, y0))[1:] + _line((x1, y0), (x1, py))[1:]
    return entry, stop, exit_


class Walk:
    def __init__(self, lay, nodes, edges, speed: float = 1.0):
        self.lay, self.nodes, self.edges = lay, nodes, set(edges)
        self.speed = max(speed, 0.1)
        self.stop_frames = max(2, round(STOP_FRAMES / self.speed))
        self.succ, self.pred = {}, {}
        for u, v in sorted(self.edges):
            self.succ.setdefault(u, []).append(v)
            self.pred.setdefault(v, []).append(u)
        self.path = {(u, v): _dedupe(cells) for u, v, cells in lay.paths}
        self.route = {n: node_route(lay.boxes[n], lay.orient) for n in nodes}
        # order the branches of each fork across the screen (left-to-right or top-to-bottom)
        axis = 0 if lay.orient == "TB" else 1
        for u in self.succ:
            self.succ[u].sort(key=lambda v: (self.path[(u, v)][0][axis] if self.path[(u, v)]
                                              else 0, self.path[(u, v)][-1][axis], v))
        # where each incoming walker waits at a join: just before its path first overlaps
        # another incoming path of the same node
        self.wait_at, self.shared = {}, {}
        for v, ps in self.pred.items():
            if len(ps) < 2:
                continue
            for u in ps:
                others = set()
                for w in ps:
                    if w != u:
                        others |= set(self.path[(w, v)])
                cells = self.path[(u, v)]
                i = next((k for k, c in enumerate(cells) if c in others), len(cells))
                self.shared[(u, v)] = min(i, len(cells) - 1)
                # wait a sprite-width back from the meeting cell so the walkers stand apart
                self.wait_at[(u, v)] = max(min(i - WAIT_BACK, i - 1), 0)
        self.final = max(n for n in nodes if not self.succ.get(n))
        self.walkers: list[Walker] = []
        self.next_id = 0
        self.arrived: dict[int, list[Walker]] = {}
        self.visits: list[int] = []
        self.caption = ""
        self.trace: list[tuple[int, tuple]] = []   # (walker id, pos) for every frame
        self.splits: dict[int, int] = {}           # node -> walkers it split into
        self.merges: list[tuple[int, int]] = []    # (node, walkers that had arrived)

    # ------------------------------------------------------------- helpers
    def _new(self, pos):
        w = Walker(self.next_id, pos)
        self.next_id += 1
        self.walkers.append(w)
        return w

    def _arrive(self, w, n):
        w.state, w.node, w.timer, w.edge = "stop", n, self.stop_frames, None
        w.pos = self.route[n][1]
        self.visits.append(n)
        self.caption = caption_for(self.nodes[n])

    def _leave(self, w):
        n = w.node
        if not self.succ.get(n):
            w.state = "victory" if n == self.final else "done"
            if w.state == "victory":
                w.timer = VICTORY_FRAMES
            return
        w.state, w.cells, w.then = "walk", list(self.route[n][2]), "split"

    def _split(self, w):
        """At the out-port: one walker per outgoing edge, all leaving together."""
        n = w.node
        kids = []
        gap = max(1, round(SPRITE_GAP / self.speed))
        for i, v in enumerate(self.succ[n]):
            k = w if i == 0 else self._new(w.pos)
            k.facing, k.steps = w.facing, w.steps
            self._send(k, n, v)
            if i > 0:   # siblings leave one after another, a sprite-width apart
                k.state, k.timer = "hold", i * gap
            kids.append(k)
        self.splits[n] = len(kids)
        return "split" if len(kids) > 1 else ""

    def _send(self, w, u, v):
        cells = self.path[(u, v)]
        w.edge, w.node, w.state = (u, v), v, "walk"
        if (u, v) in self.wait_at:
            i = self.wait_at[(u, v)]
            w.cells, w.then = cells[: i + 1], "wait"
            w.rest = cells[i + 1:]
        else:
            w.cells, w.then = cells + self.route[v][0], "arrive"

    def _step(self, w):
        nxt = w.cells.pop(0)
        if nxt[0] != w.pos[0]:
            w.facing = 1 if nxt[0] > w.pos[0] else -1
        if nxt != w.pos:
            w.steps += 1
        w.pos = nxt

    # ------------------------------------------------------------- simulation
    def frames(self, limit=20000):
        out = []
        for s in [n for n in sorted(self.nodes) if not self.pred.get(n)]:
            w = self._new(self.route[s][1])
            self._arrive(w, s)
        frame_no = 0
        budget = 0.0
        while frame_no < limit:
            event = ""
            budget += self.speed
            moves = int(budget)
            budget -= moves
            for w in list(self.walkers):
                if w.state == "stop":
                    w.timer -= 1
                    if w.timer <= 0:
                        self._leave(w)
                elif w.state == "victory":
                    w.timer -= 1
                elif w.state == "hold":
                    w.timer -= 1
                    if w.timer <= 0:
                        w.state = "walk"
                        continue
                if w.state == "walk":
                    for _ in range(moves):
                        if w.cells:
                            self._step(w)
                        if not w.cells:
                            break
                    if not w.cells:
                        if w.then == "split":
                            event = self._split(w) or event
                        elif w.then == "arrive":
                            self._arrive(w, w.node)
                        elif w.then == "wait":
                            w.state = "wait"
                            self.arrived.setdefault(w.node, []).append(w)
                        elif w.then == "vanish":
                            self.walkers.remove(w)      # merged into the surviving walker
            # joins: once every incoming walker has arrived, they all walk in to the meeting
            # cell; the extras vanish there and one walks on into the node
            for v, ws in list(self.arrived.items()):
                if len(ws) == len(self.pred[v]):
                    self.merges.append((v, len(ws)))
                    keep = min(ws, key=lambda x: x.id)
                    for x in ws:
                        if x is keep:
                            continue
                        u = x.edge[0]
                        cells = self.path[(u, v)]
                        x.state, x.then = "walk", "vanish"
                        x.cells = cells[self.wait_at[(u, v)] + 1: self.shared[(u, v)] + 1] or [x.pos]
                    keep.state, keep.cells, keep.then = "walk", keep.rest + self.route[v][0], "arrive"
                    del self.arrived[v]
                    event = "merge"
            snap = []
            for w in self.walkers:
                self.trace.append((w.id, w.pos))
                if w.state == "victory":
                    sprite, dy = "victory_1", HOP[frame_no % len(HOP)]
                elif w.state in ("stop", "wait", "done", "hold"):
                    sprite, dy = "idle_1", BOB[frame_no % len(BOB)]
                else:
                    sprite, dy = ("walk_1" if (w.steps // 2) % 2 == 0 else "walk_2"), 0
                snap.append((w.id, w.pos, sprite, w.facing, dy))
            hl = frozenset(w.node for w in self.walkers if w.state in ("stop", "victory"))
            if any(w.state == "victory" for w in self.walkers) and not event:
                event = "victory"
            caption = self.caption
            if not hl:   # everyone is on the move: say where they are heading, and from where
                heading: dict[str, list[str]] = {}
                for w in sorted(self.walkers, key=lambda x: x.id):
                    if w.node is not None and w.state in ("walk", "hold", "wait"):
                        src = heading.setdefault(self.nodes[w.node]["label"], [])
                        if w.edge and self.nodes[w.edge[0]]["label"] not in src:
                            src.append(self.nodes[w.edge[0]]["label"])
                if heading:
                    caption = "→ " + "  ·  ".join(
                        f"{t} (from {', '.join(f)})" if f else t for t, f in heading.items())
            out.append(Frame(snap, hl, caption, event))
            frame_no += 1
            if all(w.state in ("done", "victory") for w in self.walkers) and all(
                    w.timer <= 0 for w in self.walkers if w.state == "victory"):
                break
        return out
