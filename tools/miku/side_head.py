"""Dev-only: the side-view head, hand-placed (facing right), with face alternatives.

Head box 34 x 34, placed so the crown and chin line up with P1 (crown at canvas row ~2,
chin at ~31). Rows 0-17 are full hand-typed rows (dome, hair tie, highlight strokes, fringe);
rows 18-33 are back hair (cols 0-12) + side lock (13-16) + face (17-33). The face is about
16 px wide, close to half of P1's frontal face, and the eye is P1's 5 x 7 eye in profile.
Alternatives replace only eye / fringe / mouth rows of the face part.
"""

from __future__ import annotations

TOP = [  # rounded crown and back of the head (no flat top), widest at rows 11-13
    "..............BBBBB...............",
    "...........BBBAAAAABBB............",
    ".........BBAAAAAAAAAAABB..........",
    "........BAAAAAAGGGGGAAAAB.........",
    ".......BAAAAAGGAAAAAAAAAAB........",
    "......BAAAAAGAAAAAAAAAAAAAB.......",
    ".....BAAAAAAAAAAAAAAAAAAAAAB......",
    "....BAAAAAAAAAAAAAAAAAGGAAAAB.....",
    "...BCAAAAAAAAAAAAAAAAAAAGGAAAB....",
    "..BCCAAAAAAAAAAAAAAAAAAAAAAAAAB...",
    "..BCAAAAAAAAAAAAAAAAAAAAAAAAAAAB..",
    ".BCCAAAAAAAAAAAAAAAAAAAAAAAAAAAAB.",
    ".BCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB.",
    ".BCCAAAAAAAAAAAAAAAAAAAAAAAAAAAAB.",
    ".BCCCAAAAAAAAAACAAAAAACAAAAAAAAAB",
    ".BCCCAAAAAAAAAACAAAAACAAAAAACAAAB",
    ".BCCAAAAAAAAAACAAAACAAAACAAAAAAB.",
    ".BCCAAAAAAAAACAAAACEEAACEEAAACAAB.",
]

NEAR_TIE = [   # the near-side hair tie: a dark block with red diagonal stripes (cols 5-9)
    ".BBB.",
    "BSBBB",
    "BBSBB",
    "BSBSB",
    "BBSBB",
    "BSBBB",
    ".BBB.",
]

BACK = {  # layered locks with teal strand lines; the nape ends in points, not a helmet curve
    18: "..BCAAACAAAAA", 19: "..BCAAAACAAAA", 20: "..BCAAAAACAAA", 21: "..BCCAAAAACAA",
    22: "...BCAAAAAACA", 23: "...BCCAAAAAAC", 24: "....BCAAAAAAA", 25: "....BCCAAAAAA",
    26: ".....BCAACAAA", 27: "....BCAB.BCAA", 28: "....BAB..BBCA", 29: ".....B....BBB",
    30: ".............", 31: ".............", 32: ".............", 33: ".............",
}
LOCK = {y: "BCAB" for y in range(18, 23)}               # steps back, then tapers to a point
LOCK.update({23: "BCAB", 24: ".BCB", 25: ".BCB", 26: ".BCB", 27: ".BAB", 28: ".BAB",
             29: "..BB", 30: "..BB", 31: "...B", 32: "....", 33: "...."})

FACE_A = {
    18: "EEEEEACEEEEAAAAB.",
    19: "EEEEEEBBBBBBBAAB.",
    20: "EEEEEEEFFFFBBEEB.",
    21: "EEEEEEEFGLCFEEEB.",
    22: "EEEEEEEFGCCFEEEB.",
    23: "EEEEEEECCCCCEEEB.",
    24: "EEEEEEECAAACEEEEB",
    25: "EEEEEEEEAACEEEEB.",
    26: "EEEEEEEEBBBEEEEB.",
    27: "EEUUUUEEEEEEEEEB.",
    28: "EEEEEEEEEEEEEESB.",
    29: "EEEEEEEEEEEEEEB..",
    30: "BAEEEEEEEEEEEB...",
    31: ".BEEEEBBBBBBB....",
    32: ".BEEEB...........",
    33: ".BEEEB...........",
}

ALTS = {
    "A": {},
    "B": {   # almond eye, 4 wide, with a lash flick at the front corner
        19: "EEEEEEEBBBBBAACB.",
        20: "EEEEEEEEFFFBBECB.",
        21: "EEEEEEEEGLCFEEEB.",
        22: "EEEEEEEEGCCFEEEB.",
        23: "EEEEEEEECCCCEEEB.",
        24: "EEEEEEEECAACEEEEB",
        25: "EEEEEEEEEBBEEEEB.",
        26: "EEEEEEEEEEEEEEEB.",
    },
    "C": {   # P5's bright open eye and open smile
        19: "EEEEEEBBBBBBAACB.",
        20: "EEEEEEBFFFFFBECB.",
        21: "EEEEEEEFGLCFEEEB.",
        22: "EEEEEEEFGLCFEEEB.",
        23: "EEEEEEECCCCCEEEB.",
        24: "EEEEEEECAAACEEEEB",
        25: "EEEEEEECAAACEEEB.",
        26: "EEEEEEEEBBBEEEEB.",
        28: "EEEEEEEEEEEEESSB.",
        29: "EEEEEEEEEEEEEVB..",
    },
    "D": {   # longer fringe: the middle lock hangs over the top of the eye
        18: "CEEEEAAACAAAAAAB.",
        19: "EEEEEEBAACBBAACB.",
        20: "EEEEEEEFCFFBBECB.",
    },
}

# faces that are not thumbnail alternatives
EXTRA = {
    "sleepy": {   # P6: eye closed to a lash line, small mouth
        19: "EEEEEEEEEEEEAACB.",
        20: "EEEEEEEEEEEEEECB.",
        21: "EEEEEEEEEEEEEEEB.",
        22: "EEEEEEEEEEEEEEEB.",
        23: "EEEEEEBBBBBBEEEB.",
        24: "EEEEEEEBEEEEEEEEB",
        25: "EEEEEEEEEEEEEEEB.",
        26: "EEEEEEEEEEEEEEEB.",
    },
    "cheery": {   # bright open eye (P5) with two highlights, wide open happy mouth, blush
        19: "EEEEEEBBBBBBAACB.",
        20: "EEEEEEBFFFFFBECB.",
        21: "EEEEEEEFGLCFEEEB.",
        22: "EEEEEEEFGLCFEEEB.",
        23: "EEEEEEECCCCCEEEB.",
        24: "EEEEEEECAAGCEEEEB",
        25: "EEEEEEECAAACEEEB.",
        26: "EUUUUEEEBBBEEEEB.",
        27: "EEEEEEEEEEEEEUEB.",
        28: "EEEEEEEEEEEUUEEB.",
        29: "EEEEEEEEEEEEEEB..",
    },
    "three_quarter": {   # turned toward the viewer: near eye large, far eye narrow, mouth centred
        18: "EEACEEEEACEAAAAB.",
        19: "EBBBBBBEEEEBBBAB.",
        20: "EBFFFFBEEEEEFBCB.",
        21: "EFGLCFEEEEEEGFEB.",
        22: "EFGCCFEEEEEECFEB.",
        23: "ECCCCCEEEEEECCEB.",
        24: "ECAAACEEEEEEACEEB",
        25: "EEAACEEEEEEEEAEB.",
        26: "EEBBBEEEEEEEEBEB.",
        27: "UUUEEEEEEEEEUUEB.",
        28: "EEEEEEEESEEEEEB..",
        29: "EEEEEEEEEEEEEB...",
        30: "BAEEEEEEEEEEB....",
        31: ".BEEEEBBBBBB.....",
    },
}

NOTES = {
    "A": "P1's round eye in profile, 5x7",
    "B": "almond eye, 4 wide, lash flick",
    "C": "P5's bright open eye, open smile",
    "D": "longer fringe over the eye",
}


# fringe: three locks swept forward, separation lines stepping forward one px per row,
# tips at increasing depth (back lock shortest, front lock over the eye's front corner)
FRINGE = {  # rows 14-16, cols 14-33: strand lines at uneven spacing and length, two highlights
    14: "AACAAAAAGCAAAACAAAAB",
    15: "AAACAAAAGACAAAACAAAB",
    16: "AAAACAAAAAACAAACAAAB",
}
FRINGE_FACE = {  # rows 17-20, cols 17-33 (applied before the alternative's overrides)
    17: "ACEAAAACEAAAACAAB",
    18: "CEEEEAACEAAAAAACB",
    19: "EEEEEEBBBBBBAACB.",
    20: "EEEEEEEFFFFBBECB.",
}


def head_rows(alt: str = "A") -> list[str]:
    face = dict(FACE_A)
    face.update({y: r for y, r in FRINGE_FACE.items() if y != 17})
    face.update(ALTS[alt] if alt in ALTS else EXTRA[alt])
    rows = list(TOP)
    for y, seg in FRINGE.items():
        rows[y] = rows[y][:14] + seg
    rows[17] = rows[17][:13] + "BCAB" + (ALTS[alt] if alt in ALTS else EXTRA[alt]).get(17, FRINGE_FACE[17])
    for y in range(18, 34):
        rows.append(BACK[y] + LOCK[y] + face[y])
    for j, r in enumerate(NEAR_TIE):          # near-side hair tie on top of the hair
        y = 6 + j
        rows[y] = "".join(ch if ch == "." else ch for ch in rows[y])
        rows[y] = rows[y][:5] + "".join(t if t != "." else o for t, o in zip(r, rows[y][5:10])) + rows[y][10:]
    bad = [(i, len(r)) for i, r in enumerate(rows) if len(r) != 34]
    assert not bad, bad
    return rows


TIE_ANCHOR = (7, 12)   # bottom of the near hair tie
