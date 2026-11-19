# Miku v2 style bible

Everything drawn for Miku v2 is checked against this page.

## Character and size

- **Design authority:** the six-pose sheet (`assets/reference/miku_poses.png`). P1 is the master front frame.
- **Size:** 67 pixels from crown to boot soles, on a 74×72 canvas, with the soles on row 67 and a 3-row ground shadow below. That's 36 terminal rows in half-block rendering.
- **Proportions:** every view keeps P1's proportions. The head runs from the crown to the chin at about row 31, the torso to row 44, the skirt to row 54, and the legs below. The twin tails are a big mass that nearly reaches the boots.

## Palette

The shared 18-colour body palette from the model sheet (see `MIKU_V2_REFERENCE.md`), in ramps of two or three steps per material:

| Material | Colours |
|---|---|
| hair | highlight, cyan, teal shadow |
| top | light grey, grey, shade |
| skirt and sleeves | grey, shadow |
| skin | skin, shade, blush |
| leek | pale stalk, green, shadow green |
| mouth | red, inside |
| socks, boots, iris | dark slate |

The terminal adds two colours: a slate for the outer outline, and a dim grey for the ground shadow. No colours have been added for the profile views.

## Lines

- **Inside the silhouette:** navy, 1 pixel, everywhere.
- **Outer edge:** slate, so she stays readable on dark terminals.
- **Never:** doubled corners or gaps. Limbs and cloth should avoid long straight outline runs (the stiffness flag warns above 5 pixels).

## Shading

Each material has a flat base, one shadow and one highlight:
- hair: a highlight band, base, and teal shadow on the inner side
- skirt: lighter pleat lines and a cyan hem trim
- top: grey with a lighter collar and a cyan tie.

## Drawing rules

- **Cloth, limbs and hands** are hand-placed pixel clusters, never geometric primitives.
- **Hair masses** may start from primitives but get hand-placed highlight and strand strokes.
- **Twin tails** are procedural chains hung from the hair tie: shrinking discs, shaded with the hair ramp and outlined. Every frame stores the tail points.
- **Poses** keep a line of action, weight on one leg, tilted hips and shoulders, tapering limbs, and cloth that folds and flares. Nothing is straightened or mirrored into symmetry.

## Faces

Drawn once and reused:
- **From the sheet:** smile (P1), wink (P2), smug (P3), squeezed shut (P4), excited (P5), sleepy (P6).
- **Side and 3/4 views:** P1's eye in profile, and a 3/4 face with a narrow far eye.
- **Derived at the clip stage:** surprised, panting and blink.

## Timing

- 12 fps (1 tick = 1/12 s).
- Keys are held for 2 ticks or more, and the smallest action frames are 1–2 ticks.
- Every clip has an exposure sheet in `tools/miku/xsheets/`, written before its frames.

## Secondary motion

- The tails lag body motion by 1–2 ticks: their swing is driven by an earlier tick's phase.
- The skirt hem lags 1 tick behind the hips.
- In side view, the far tail is behind the body and the near tail in front.

## Facing

- She faces the way she moves, and every change of direction plays a turn.
- She never flips straight from one profile to the other, and never moonwalks.
- The walk cycle plays only in profile.
- She turns to the front when stopping and toward the next target when leaving.
