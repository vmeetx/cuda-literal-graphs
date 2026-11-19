"""Dev-only: hand-placed side-view body parts (facing right) and the side pose composer.

Canvas columns: the head box sits at x=HX (34 wide), so the neck is at x=HX+19..21 and the
body's centre line is about x=40. Rows follow P1: chin ~31, torso 32-44, skirt 44-54, legs
54-67 (soles on BASELINE 67). Every part is typed pixel by pixel; nothing here is a primitive.
Leg shapes use o=outline, s=sock, c=cyan band, b=boot, and are coloured near/far at paste time.
"""

from __future__ import annotations

import side_head
import tails
from build import BASELINE, Canvas

HX, HY = 20, 1

TORSO = [  # x0 = 32, rows 32..44: neck, collar, grey top, tie hanging in front of the chest
    "......BEEEB...",
    ".....BLLLLAB..",
    "....BKNLLLAAB.",
    "...BKNNNNNLAAB",
    "...BKNNNNNNLAB",
    "...BKNNNNNNNAB",
    "...BKNNNNNNNAB",
    "...BKNNNNNNNAB",
    "...BKNNNNNNNNB",
    "...BKNNNNNNNNB",
    "...BKKNNNNNNNB",
    "....BKKNNNNNB.",
    "....BBBBBBBBB.",
]

# P3's carry, in profile: shoulder skin, detached grey sleeve with a cyan cuff, the forearm
# raised so the hand grips the stalk at the front of the shoulder. x0 = 35, rows 34..43.
CARRY_ARM = [
    "..BEEB.....",
    "..BEEB..BB.",
    ".BDDDB.BEEB",
    ".BDDMDBBEPB",
    ".BDDDMDBEEB",
    ".BDDDDMDBB.",
    "..BDDDDDB..",
    "..BAAADDB..",
    "...BAAAB...",
    "....BBB....",
]

# leek resting on the near shoulder, angled back and up behind the head; drawn before the
# head and tails so it sits behind them. Stalk pale (b) with a light edge, leaves green.
LEEK = [  # x0 = 14, rows 16..37
    "BBB.................................",
    "BIIB.BB.............................",
    "BXIIBIIB............................",
    ".BXIIIIB.BB.........................",
    "..BXIIIIBIIB........................",
    "...BXIIIIIIB........................",
    "....BXIIIIB.........................",
    ".....BXIIIIB........................",
    "......BBXIIB........................",
    "........BbbbB.......................",
    ".........BbbbB......................",
    "..........BbbbB.....................",
    "...........BbbbB....................",
    "............BbbbB...................",
    ".............BbbbB..................",
    "..............BbbbB.................",
    "...............BbbbB................",
    "................BbbbB...............",
    ".................BbbbB..............",
    "..................BbbbBB............",
    "...................BBbbbB...........",
    ".....................BBBB...........",
]

# tired: the near arm hangs and drags the leek behind on the ground (P6)
DRAG_ARM = [  # x0 = 33, rows 34..45
    "..BEEB.", "..BEEB.", ".BDDDB.", ".BDDMB.", ".BDDMB.", ".BDDMB.", ".BDDMB.", ".BDDMB.",
    ".BAAAB.", "..BEEB.", ".BEPEB.", "..BBB..",
]
LIMP_ARM = [  # x0 = 35, rows 34..44: the near arm hanging limp (sleeve, cuff, small hand)
    "..BEEB.", "..BEEB.", ".BDDDB.", ".BDDMB.", "..BDDMB", "..BDDMB", "..BDDMB",
    "..BAAAB", "...BEEB", "...BEPB", "....BB.",
]
FAR_DRAG_ARM = [  # x0 = 29, rows 35..46: the far arm behind her, shadow colours, gripping the stalk
    "..BMB.", ".BMMB.", ".BMMB.", ".BMMB.", ".BMMB.", ".BMMB.", ".BMMB.",
    ".BCCB.", ".BPPB.", ".BPPB.", "..BB..",
]
DRAG_LEAVES = [  # x0 = 8, rows 61..67: leaves splayed on the ground behind her
    "......BB.....BB.",
    ".....BIIB...BIIB",
    "..BBBXIIIBBBXIB.",
    ".BIIIXXIIIIIIB..",
    "BIIIIIIXXIIIIIBB",
    ".BBXIIIIIIIIIIbb",
    "...BBBBBBBBBBBBB",
]


def drag_stalk(c, x0, y0, x1, y1, bob):
    """The dragged stalk from the hand down to the leaves (a prop, not a limb)."""
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n) + bob
        for dx, ch in ((-1, "B"), (0, "b"), (1, "b"), (2, "B")):
            if c.get(x + dx, y) in ".":
                c.set(x + dx, y, ch)


FAR_ARM = {  # the far arm, behind the body, swinging against the legs
    # far side, so in the shadow colours: sleeve shadow grey, teal cuff, shaded hand
    "fwd": (42, 38, [".BMMB..", ".BMMMB.", "..BMMMB", "...BMMB", "...BCCB", "....BPB", "....BB."]),
    "back": (27, 38, ["..BMMB.", ".BMMMB.", "BMMMB..", "BMMB...", "BCCB...", "BPB....", ".BB...."]),
    "mid": None,
}
ARM_FOR = {"contact_r": "fwd", "down_r": "fwd", "pass_r": "mid", "up_r": "back",
           "contact_l": "back", "down_l": "back", "pass_l": "mid", "up_l": "fwd",
           "side_stand": "mid", "_pass": "mid"}

SKIRT = [  # x0 = 28, rows 44..55: flare, pleat lines, back side shaded, cyan hem trim
    "......BMDDDDDDB.....",
    ".....BMDDKDDDDDB....",
    ".....BMDDKDDDKDB....",
    "....BMDDKDDDDKDDB...",
    "....BMDKDDDDDKDDB...",
    "...BMDDKDDDDDDKDDB..",
    "...BMDKDDDDDDDKDDB..",
    ".BMMDDKDDDDDDDDKDDB.",
    "BMAAAAAAAAAAAAAAAAB.",
    "BAALAAALAAALAAALABB.",
    "BBAAAAAAAAAAAABBBB..",
    ".BBBBBBBBBBBBB......",
]

LEGS = {  # 12 wide x 13 tall; hip roughly at columns 1-4 of the box
    "front_contact": [
        "occco.......", "osssso......", ".osssso.....", ".osssso.....", "..osssso....",
        "..osssso....", "...osssso...", "...osssso...", "....osssso..", "....obbbbo..",
        "....obbbbbo.", "....obbbbbbo", "....oooooooo"],
    "back_contact": [
        ".....occco..", ".....ossso..", "....ossso...", "....ossso...", "...ossso....",
        "...ossso....", "..ossso.....", "..ossso.....", ".obbbbo.....", ".obbbbo.....",
        "obbbbbo.....", "obbbbo......", "oooooo......"],
    "front_down": [
        "occco.......", "osssso......", ".osssso.....", "..osssso....", "..osssso....",
        "..ossso.....", "..ossso.....", "..ossso.....", "..obbbo.....", "..obbbbo....",
        "..obbbbbo...", "..oooooooo..", "............"],
    "back_down": [
        ".....occco..", ".....ossso..", "....ossso...", "...ossso....", "..ossso.....",
        "..ossso.....", "..osssso....", "...obbbbo...", "..obbbbo....", ".obbbbbo....",
        ".obbbbo.....", ".oooooo.....", "............"],
    "support": [
        "..occco.....", "..ossso.....", "..ossso.....", "..ossso.....", "..ossso.....",
        "..ossso.....", "..ossso.....", "..ossso.....", "..ossso.....", "..obbbo.....",
        "..obbbbo....", "..obbbbbo...", "..oooooooo.."],
    "swing_back": [
        "..occco.....", "..ossso.....", "..ossso.....", "..osssso....", "...osssso...",
        "..ossssso...", ".ossssso....", "obbbbso.....", "obbbbo......", "ooooo.......",
        "............", "............", "............"],
    "swing_back_high": [
        "..occco.....", "..ossso.....", "..osssso....", "...osssso...", "...ossssso..",
        "..osssssso..", ".obbsssso...", "obbbbsso....", "obbbbo......", "oooooo......",
        "............", "............", "............"],
    "support_up": [
        "..occco.....", "..ossso.....", "..ossso.....", "..ossso.....", "..ossso.....",
        "..ossso.....", "..ossso.....", "..ossso.....", "..ossso.....", "..obbbo.....",
        "...obbbo....", "...obbbbo...", "...ooooo...."],
    "swing_front": [
        "..occco.....", "..osssso....", "...osssso...", "....osssso..", "....osssso..",
        "....ossso...", "...ossso....", "...obbbo....", "...obbbbo...", "...oooooo...",
        "............", "............", "............"],
}
NEAR = {"o": "B", "s": "F", "c": "A", "b": "F"}
FAR = {"o": "B", "s": "B", "c": "C", "b": "B"}   # far leg: one step darker on each ramp (F->B, A->C)

# walk drawings: (front-leg shape, back-leg shape, which leg is near, bob, skirt lag)
# "near" = the leg on the viewer's side. R = right (near) leg forward.
WALK = {
    "contact_r": ("front_contact", "back_contact", "front", 0, 0),
    "down_r":    ("front_down", "back_down", "front", 2, -1),
    "pass_r":    ("support", "swing_back", "back", 0, -1),
    "up_r":      ("swing_front", "support_up", "back", -2, 0),
    "contact_l": ("front_contact", "back_contact", "back", 0, 0),
    "down_l":    ("front_down", "back_down", "back", 2, -1),
    "pass_l":    ("support", "swing_back", "front", 0, -1),
    "up_l":      ("swing_front", "support_up", "front", -2, 0),
}
WALK["side_stand"] = ("support", "support", "front", 0, 0)
LEG_X = {"front": 41, "back": 30}
STAND_X = {"front": 38, "back": 35}   # box x of each leg shape (front leg ahead of the back leg)


def paste_leg(c, shape, x0, y0, palette):
    rows = LEGS[shape]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".":
                c.set(x0 + i, y0 + j, palette[ch])
        if palette is NEAR:            # a lighter shin edge so the leg reads on dark terminals
            front = max((i for i, ch in enumerate(r) if ch == "s"), default=None)
            if front is not None:
                c.set(x0 + front, y0 + j, "D")


def skirt_rows(lag):
    rows = list(SKIRT)
    if lag:
        for j in range(5, 11):          # the hem lags behind the hips by one pixel
            r = rows[j]
            rows[j] = (r[1:] + ".") if lag < 0 else ("." + r[:-1])
    return rows


PASS_ALTS = {  # passing-pose alternatives for the thumbnail round
    "A": dict(),
    "B": dict(back="swing_back_high"),
    "C": dict(lean=1),
    "D": dict(back="swing_back_high", lean=1, slag=-2, swing=0.35),
}
PASS_NOTES = {
    "A": "upright, swing foot low behind",
    "B": "swing foot kicked higher, sharper knee",
    "C": "A with a 1 px forward lean above the waist",
    "D": "B + lean, stronger skirt lag, tails swing out",
}


def lean_rows(rows, lean, waist, neck=31):
    """Graded lean into the walk: the head moves `lean + 1` px forward, the torso `lean` px,
    the hips stay. Gives the drawing a line of action instead of a vertical post."""
    if not lean:
        return rows
    out = []
    for y, r in enumerate(rows):
        k = lean + 1 if y < neck else (lean if y < waist else 0)
        out.append(("." * k + r[:-k]) if k else r)
    return out


# cheerful walk: the near arm reaches forward and the hand spins the leek in circles
SPIN_ARM = [  # x0 = 37, rows 34..39; hand at columns 49-50, rows 37-38
    "..BEEB.........",
    ".BDDDDBBBBB....",
    ".BMDDDDDDDDBBB.",
    "..BMMMDDDDAAEEB",
    "...BBBBBBBAAEPB",
    "..........BBBB.",
]
SPIN_HAND = (50, 37)


def spin_leek(c, k, bob, protect):
    """The leek at angle k*45 degrees around the hand: pale stalk, then fanned leaves, all
    outlined. A prop, so it is drawn procedurally; it never paints over `protect` cells."""
    import math
    hx, hy = SPIN_HAND[0], SPIN_HAND[1] + bob
    a = math.radians(k * 45 - 90)                      # k=0 points straight up
    cells = {}
    for r in range(1, 10):                             # stalk, 2 px thick
        x, y = hx + r * math.cos(a), hy + r * math.sin(a)
        for dx, dy in ((0, 0), (round(-math.sin(a)), round(math.cos(a)))):
            cells[(round(x) + dx, round(y) + dy)] = "b"
    for off in (-0.32, 0.0, 0.32):                     # three leaves fanning out
        for r in range(9, 16):
            x, y = hx + r * math.cos(a + off * (r - 8) / 7), hy + r * math.sin(a + off * (r - 8) / 7)
            cells[(round(x), round(y))] = "I" if off == 0 or r < 14 else "X"
    for (x, y), ch in cells.items():
        if (x, y) not in protect:
            c.set(x, y, ch)
    for (x, y) in list(cells):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in cells and c.get(*n) == ".":
                c.set(n[0], n[1], "B")


def pose_side(drawing="contact_r", head="A", lag_prev=0.0, swing=0.0, alt=None, tired=False,
              lean=None, spin=None):
    """One side-view drawing facing right. Returns (rows, metadata).
    drawing: a walk drawing, "side_stand", or "three_quarter" (standing, head turned)."""
    three_q = drawing == "three_quarter"
    if three_q:
        drawing, head = "side_stand", "three_quarter"
    if tired:
        head = "sleepy"
    elif spin is not None:
        head = "cheery"
    front, back, near, bob, slag = WALK[drawing]
    lean = lean or 0
    if alt:
        o = PASS_ALTS[alt]
        back = o.get("back", back)
        lean = o.get("lean", 0)
        slag = o.get("slag", slag)
        swing = o.get("swing", swing)
    c = Canvas()
    # back-to-front: far tail, far leg, leek, torso/skirt, near leg, head, near tail, arm
    tie = (HX + side_head.TIE_ANCHOR[0], HY + side_head.TIE_ANCHOR[1] + bob)
    # two tails arcing back and down from the hair tie, clear of her back; the far one wider
    # and a shade darker. Tired: both hang heavily down and close, with little sway.
    if tired:
        far_pts = tails.chain((tie[0] - 1, tie[1]), lag=0.2, swing=0.0, back=-1,
                              curl=0.25, splay=0.38)
        near_pts = tails.chain((tie[0] + 1, tie[1] + 1), lag=0.2, swing=0.0, back=-1,
                               curl=0.2, splay=0.28)
    else:
        far_pts = tails.chain((tie[0] - 1, tie[1]), lag=lag_prev, swing=swing, back=-1,
                              curl=0.85, splay=1.0)
        near_pts = tails.chain((tie[0] + 1, tie[1] + 1), lag=lag_prev * 0.8, swing=swing * 0.6,
                               back=-1, curl=0.75, splay=0.8)
    body = Canvas()
    legs_y = 54 + bob
    far_leg, near_leg = (back, front) if near == "front" else (front, back)
    far_key = "back" if near == "front" else "front"
    near_key = "front" if near == "front" else "back"
    xs = STAND_X if drawing == "side_stand" else LEG_X
    if tired and drawing != "side_stand":
        xs = {"front": LEG_X["front"] - 1, "back": LEG_X["back"] + 1}   # shorter stride
    if tired:
        body.patch(29, 35 + bob, FAR_DRAG_ARM)   # behind the torso and skirt
    arm = FAR_ARM.get(ARM_FOR.get(drawing, "mid"))
    if arm and not tired:
        ax, ay, rows_a = arm
        body.patch(ax, ay + bob, rows_a)
    paste_leg(body, far_leg, xs[far_key], legs_y, FAR)
    if not tired and spin is None:
        body.patch(14, 16 + bob, LEEK)
    body.patch(32, 32 + bob, TORSO)
    body.patch(28, 44 + bob, skirt_rows(slag))
    paste_leg(body, near_leg, xs[near_key], legs_y, NEAR)
    head_rows = side_head.head_rows(head)
    for j, r in enumerate(head_rows):
        for i, ch in enumerate(r):
            if ch != ".":
                body.set(HX + i, HY + bob + j, ch)
    if tired:
        body.patch(35, 34 + bob, LIMP_ARM)      # near arm hangs limp in front of her
    elif spin is not None:
        body.patch(37, 34 + bob, SPIN_ARM)
    else:
        body.patch(35, 34 + bob, CARRY_ARM)
    rows_now = lean_rows(["".join(r) for r in body.g], lean, 44 + bob, neck=31 + bob)
    if tired:   # head 2 px lower and 1 px forward, shoulders 1 px lower: a rounded back
        def sh(r, k):
            return ("." * k + r[:-k]) if k else r
        new = []
        for y in range(len(rows_now)):
            if y < 31 + bob:
                src = rows_now[y - 2] if y >= 2 else "." * len(rows_now[0])
                new.append(sh(src, 2))
            elif y < 44 + bob:
                new.append(rows_now[y - 1])
            else:
                new.append(rows_now[y])
        rows_now = new
    body.g = [list(r) for r in rows_now]
    if tired:   # the far arm, behind her, drags the leek: stalk down to leaves on the ground
        drag_stalk(body, 31, 46, 20, 64, bob)
        body.patch(6, 61, DRAG_LEAVES)
    body_front_x = max(x for y in range(c.h) for x in range(c.w)
                       if body.g[y][x] != "." and y <= BASELINE)
    # tails: far tail behind everything, near tail in front of the body
    tails.draw(c, far_pts, far=True)
    for y in range(c.h):
        for x in range(c.w):
            if body.g[y][x] != ".":
                c.g[y][x] = body.g[y][x]
    near_meta = tails.draw(c, near_pts)
    if spin is not None and not tired:   # the spinning leek, in front; never over her face
        head = {(x, y) for y in range(c.h) for x in range(c.w)
                if y < 33 + bob and c.g[y][x] != "."}          # the leek passes behind her head
        spin_leek(c, spin, bob, head)
    # ground shadow under the feet (same dim colour and shape as the front poses)
    for dy, half in ((1, 18), (2, 22), (3, 16)):
        y = BASELINE + dy
        for x in range(40 - half, 40 + half + 1):
            if c.get(x, y) == ".":
                c.set(x, y, "Z")
    meta = {"view": "three_quarter" if three_q else "side", "facing": "right",
            "drawing": "three_quarter" if three_q else drawing, "bob": bob,
            "tie_anchor": tie, "tail_far": [list(p) for p in far_pts],
            "leek_angle": None if spin is None else spin * 45,
            "body_front_x": body_front_x,
            "tail_front_x": max(x for x, _ in c.tail_cells) if getattr(c, "tail_cells", None) else None,
            "tail_near": near_meta}
    return c.rows(), meta
