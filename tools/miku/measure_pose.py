"""Dev-only: head and hip centres of a side-view drawing, measured on the body alone (before
tails and props are drawn), for the posture check and the reference strip.

head centre = mean x of body pixels in the head rows (crown to chin);
hip centre  = mean x of body pixels in the hip band (the skirt from the waist down 8 rows).
Leek pixels (b, I, X) are ignored wherever they are.
"""

PROP = set("bIX")


def centres(canvas, bob=0, head_rows=(2, 30), hip_rows=(44, 52)):
    def cx(y0, y1):
        xs = [x for y in range(y0 + bob, y1 + bob + 1) for x in range(canvas.w)
              if 0 <= y < canvas.h and canvas.g[y][x] not in PROP and canvas.g[y][x] != "."]
        return round(sum(xs) / len(xs), 2) if xs else None

    return cx(*head_rows), cx(*hip_rows)
