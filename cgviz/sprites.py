"""Miku sprite frames as text pixel maps. Standard library only.

One letter per pixel, '.' transparent. Walker frames are 12x16, portraits 32x48.
Colours: the canonical character palette (the provided references were monochrome
ASCII art, so they set pose and proportion only).
"""

PALETTE = {
    "T": (57, 197, 187),   # hair, tie, trim
    "D": (22, 110, 120),   # eyes, hair shadow
    "G": (196, 202, 208),  # top
    "K": (36, 36, 46),     # sleeves, skirt, boots, headset
    "S": (255, 222, 204),  # skin
    "L": (112, 196, 72),   # leek leaves
    "W": (240, 242, 232),  # leek stalk
}

# ---- walker 12x16 -----------------------------------------------------------
# idle_1 is the style anchor. Rows 0-9 (head and torso) are shared by every walker frame;
# walk frames change only rows 10-15 (skirt, legs) and the tail tips.

WALK_TOP = [
    "....TTTT....",
    "..TTTTTTTT..",
    ".KTTTTTTTTK.",
    ".KTTTTTTTTK.",
    ".TTSTSSTSTT.",
    ".TTSDSSDSTT.",
    "TT..SSSS..TT",
    "TD.KGTTGK.DT",
    "TD.KGGTGK.DT",
    "TD.SGGTGS.DT",
]

# ---- tiny walker 9x10: about the size of one graph box ------------------------
# Front view. Walk frames look toward the travel side (mirrored when facing left).

TINY_HEAD = ["..TTTTT..", ".TTTTTTT."]
TINY_BODY = ["T.KGTGK.T", "T.SGGGS.T", "T.KKKKK.T", "T.TTTTT.T"]

TINY = {
    "idle_1": TINY_HEAD + ["TTSDSDSTT", "TTSSKSSTT"] + TINY_BODY + ["D..S.S..D", "...K.K..."],
    # stride: legs apart, tail tips out
    "walk_1": TINY_HEAD + ["TTSSDSDTT", "TTSSSSSTT"] + TINY_BODY + ["D.S...S.D", ".K.....K."],
    # passing: legs together, tail tips in
    "walk_2": TINY_HEAD + ["TTSSDSDTT", "TTSSSSSTT"] + TINY_BODY + [".D.S.S.D.", "...K.K..."],
    # leek raised in the right hand
    "victory_1": ["..TTTTT.L", ".TTTTTTTW", "TTSDSDSTS", "TTSSKSSTK", "T.KGTGKKT", "T.SGGG..T",
                  "T.KKKKK.T", "T.TTTTT.T", "D..S.S..D", "...K.K..."],
}

FRAMES = {
    "idle_1": WALK_TOP + [
        "TD.KKKKKKW.T",
        "TDKKKKKKKW.T",
        "T..TTTTTTL..",
        "T..SS..SS...",
        "...TT..TT...",
        "...KK..KK...",
    ],
    # stride: legs apart, tail tips swing in
    "walk_1": WALK_TOP + [
        "TD.KKKKKKW.T",
        "TDKKKKKKKW.T",
        ".T.TTTTTTL..",
        "..SS....SS..",
        "..TT....TT..",
        "..KK....KK..",
    ],
    # passing: legs together, back foot lifted, tail tips swing out
    "walk_2": WALK_TOP + [
        "TD.KKKKKKW.T",
        "TDKKKKKKKW.T",
        "T..TTTTTTL..",
        "T...SS.SS...",
        "....TT.KK...",
        "....KK......",
    ],
    # leek raised overhead in the right hand
    "victory_1": [
        "....TTTT..LL",
        "..TTTTTTTT.L",
        ".KTTTTTTTTKW",
        ".KTTTTTTTTKS",
        ".TTSTSSTSTTK",
        ".TTSDSSDSTTK",
        "TT..SSSS..TK",
        "TD.KGTTGKK.T",
        "TD.KGGTGG.DT",
        "TD.SGGTGG.DT",
        "TD.KKKKKK.DT",
        "TDKKKKKKKKDT",
        "T..TTTTTT..T",
        "T...S..S...T",
        "....T..T....",
        "...KK..KK...",
    ],
    "portrait_idle": [
        "................................",
        "................................",
        "................................",
        ".............TTTTTT.............",
        "...........TTTTTTTTTT...........",
        "..........TTTTTTTTTTTT..........",
        ".........TTTTTTTTTTTTTT.........",
        ".........TTTTTTTTTTTTTTT........",
        "........TTTTTTTTTTTTTTTT........",
        ".......TTTTTTTTTTTTTTTTTT....L..",
        "......TTTTTTTTTTTTTTTTTTTTL..L..",
        ".....TTTTTTTTSTTSSTTSSTTTTLLLL..",
        ".....TTKKTTTSSSSSSTSSSTKKTLLLL..",
        ".....TTKKTSSSSSSSSSSSSTKKTLLLL..",
        "....TTTKKTSSWDSSSSWDSSTKKTTLL...",
        "....TTDKKTSSDDSSSSDDSSTKKDTLL...",
        "....TTDTKTSSSDSSSSDSSSTTTDTLL...",
        "....TTDTTKTSSSSDSSSSSTTTTDTLL...",
        "....TTDTTTKTSSSSSSSST.TTTTWW....",
        "....TTTTTT...SSSSSS...TTTTWT....",
        "....TDTTTT..GGGTTGGG..TTTWWTT...",
        "...TTDTTTTKKGGGTTGGGKKTTTWWTT...",
        "...TTDTTTTKKGGGTTGGGKKKTTWDTT...",
        "...TTDTTTKKKGGGTTGGGKKKTWWDTT...",
        "...TTDTTTKKKGGGTTGGGKKKTWTDTT...",
        "...TTDTTTKKKGGGGTGGGKKKWWTDTT...",
        "...TTDTTTKKKGGGGTGGGKKKWTTTTTT..",
        "..TTTTTTTKKKKKKKKKKKKKKWTTTDTT..",
        "..TTDTTTTKKKKKKKKKKKKKWWTTTDTT..",
        "..TTDTTT.TTKKKKKKKKKKTW.TTTDTT..",
        "..TTDTTT.SSKKKKKKKKKKSW.TTTDTT..",
        "..TTDTTT.SSKKKKKKKKKKSS.TTTDTT..",
        "..TTDTTT..TTTTTTTTTTTT...TTDTTT.",
        "..TTDTT......SS..SS......TTTTTT.",
        ".TTTTTT......SS..SS......TTTDTT.",
        ".TTDTTT......SS..SS......TTTDTT.",
        ".TTDTTT......SS..SS.......TTDTT.",
        ".TTDTT.......TS..ST.......TTDTT.",
        ".TTDTT.......TTT.TT.......TTDTT.",
        ".TTDTT.......KKK.KK.......TTDTT.",
        ".TTTTT.......KKK.KK........TTTT.",
        "..TTT........KKK.KK........TTT..",
        ".............KKK.KK.............",
        ".............KKK.KK.............",
        ".............KKK.KK.............",
        "................................",
        "................................",
        "................................",
    ],
    "portrait_victory": [
        "............................LL.L",
        "............................LL.L",
        ".............................LLL",
        ".............TTTTTT..........LLL",
        "...........TTTTTTTTTT........LL.",
        "..........TTTTTTTTTTTT.......W..",
        ".........TTTTTTTTTTTTTT.....WW..",
        ".........TTTTTTTTTTTTTTT....WW..",
        "........TTTTTTTTTTTTTTTT...WW...",
        ".......TTTTTTTTTTTTTTTTTT..WW...",
        "......TTTTTTTTTTTTTTTTTTTTTSS...",
        ".....TTTTTTTTSTTSSTTSSTTTTTTT...",
        ".....TTKKTTTSSSSSSTSSSTKKKTT....",
        ".....TTKKTSSSSSSSSSSSSTKKKK.....",
        "....TTTKKTSSWDSSSSWDSSTKKKTT....",
        "....TTDKKTSSDDSSSSDDSSTKKKTT....",
        "....TTDTKTSSSDSSSSDSSSTKKDTT....",
        "....TTDTTKTSSSSDSSSSSTKKKDTT....",
        "....TTDTTTKTSSSSSSSST.KKTTTT....",
        "....TTTTTT...SSSSSS..KKTTTDT....",
        "....TDTTTT..GGGTTGGGKKKTTTDTT...",
        "...TTDTTTTKKGGGTTGGGKKTTTTDTT...",
        "...TTDTTTTKKGGGTTGGG..TTTTDTT...",
        "...TTDTTTKKKGGGTTGGG...TTTDTT...",
        "...TTDTTTKKKGGGTTGGG...TTTDTT...",
        "...TTDTTTKKKGGGGTGGG...TTTDTT...",
        "...TTDTTTKKKGGGGTGGG...TTTTTTT..",
        "..TTTTTTTKKKKKKKKKKK...TTTTDTT..",
        "..TTDTTTTKKKKKKKKKKKK...TTTDTT..",
        "..TTDTTT.TTKKKKKKKKKK...TTTDTT..",
        "..TTDTTT.SSKKKKKKKKKK...TTTDTT..",
        "..TTDTTT.SSKKKKKKKKKKK..TTTDTT..",
        "..TTDTTT..TTTTTTTTTTTT...TTDTTT.",
        "..TTDTT......SS..SS......TTTTTT.",
        ".TTTTTT......SS..SS......TTTDTT.",
        ".TTDTTT......SS..SS......TTTDTT.",
        ".TTDTTT......SS..SS.......TTDTT.",
        ".TTDTT.......TS..ST.......TTDTT.",
        ".TTDTT.......TTT.TT.......TTDTT.",
        ".TTDTT.......KKK.KK.......TTDTT.",
        ".TTTTT.......KKK.KK........TTTT.",
        "..TTT........KKK.KK........TTT..",
        ".............KKK.KK.............",
        ".............KKK.KK.............",
        ".............KKK.KK.............",
        "................................",
        "................................",
        "................................",
    ],
}
