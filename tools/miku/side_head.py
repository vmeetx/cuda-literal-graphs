"""Dev-only: the side-view head, hand-placed (facing right), with face alternatives.

Head box 34 x 34, placed so the crown and chin line up with P1 (crown at canvas row ~2,
chin at ~31). Rows 0-17 are full hand-typed rows (dome, hair tie, highlight strokes, fringe);
rows 18-33 are back hair (cols 0-12) + side lock (13-16) + face (17-33). The face is about
16 px wide, close to half of P1's frontal face, and the eye is P1's 5 x 7 eye in profile.
Alternatives replace only eye / fringe / mouth rows of the face part.
"""

from __future__ import annotations

TOP = [
    "............BBBBBBBB..............",
    ".........BBBAAAAAAAABBB...........",
    ".......BBAAAAAAAAAAAAAABB.........",
    "......BAAAAAAGGGGGAAAAAAAB........",
    ".....BAAAAAGGAAAAAAAAAAAAAB.......",
    "....BAAAAAGAAAAAAAAAAAAAAAAB......",
    "..BBBBAAAAAAAAAAAAAAAAAAAAAAB.....",
    "..BSBBCAAAAAAAAAAAAAAAAGGAAAAB....",
    "..BBSBCAAAAAAAAAAAAAAAAAAGGAAAB...",
    "..BSBSCCAAAAAAAAAAAAAAAAAAAAAAAB..",
    "..BBSBCCAAAAAAAAAAAAAAAAAAAAAAAB..",
    "..BSBBCAAAAAAAAAAAAAAAAAAAAAAAAAB.",
    "..BBBBCAAAAAAAAAAAAAAAAAAAAAAAAAB.",
    "...BCCAAAAAAAAAAAAAAAAAAAAAAAAAAB.",
    "...BCAAAAAAAAAAACAAAAAACAAAAAAAAAB",
    "..BCCAAAAAAAAAAACAAAAACAAAAAACAAAB",
    "..BCAAAAAAAAAAACAAAACAAAACAAAAAAB.",
    "..BCAAAAAAAAACAAAACEEAACEEAAACAAB.",
]

BACK = {
    18: "..BCAAAAAAAAA", 19: "..BCAAAAAAAAA", 20: "..BCAAAAAAAAA", 21: "..BCAAAAAAAAA",
    22: "...BCAAAAAAAA", 23: "...BCAAAAAAAA", 24: "....BCAAAAAAA", 25: "....BCAAAAAAA",
    26: ".....BCAAAAAA", 27: "......BCCAAAA", 28: ".......BBCCAA", 29: ".........BBBB",
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
    "three_quarter": {   # turned toward the viewer: near eye large, far eye narrow, mouth centred
        18: "EEACEEEEACEAAAAB.",
        19: "EBBBBBBEEBBBBAAB.",
        20: "EBFFFFBEEBFFBECB.",
        21: "EFGLCFEEEFGCFEEB.",
        22: "EFGCCFEEEFCCFEEB.",
        23: "ECCCCCEEECCCEEEB.",
        24: "ECAAACEEECAACEEEB",
        25: "EEAACEEEEEACEEEB.",
        26: "EEBBBEEEEEBBEEEB.",
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
FRINGE = {  # rows 14-16, cols 14-33
    14: "ACAAAAACAAAAACAAAAAB",
    15: "AACAAAAACAAAAACAAAAB",
    16: "AAACAAAAACAAAAACAAB.",
}
FRINGE_FACE = {  # rows 17-20, cols 17-33 (applied before the alternative's overrides)
    17: "ACEAAAACEAAAACAB.",
    18: "CEEEEAACEAAAAAAB.",
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
    bad = [(i, len(r)) for i, r in enumerate(rows) if len(r) != 34]
    assert not bad, bad
    return rows


TIE_ANCHOR = (3, 12)
