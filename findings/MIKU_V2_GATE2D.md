# Miku v2: GATE 2d, the diagonal (3/4) walk

The art director asked us to look at how comfortably chibi Miku walks in the anime "Shopping! Shopping!" frames, and to turn our sprite diagonally a little, the same way. The cheerful walk is now a 3/4 view. The side-profile walk from GATE 2c is kept as the best-so-far version, but nothing at runtime uses it.

## What the reference frames do

- **Turned slightly toward the viewer.** The body faces mostly front, angled a little toward travel. The face sits a bit off-centre toward travel, and the far side of the face is narrower.
- **Upright and relaxed.** The head sits over the hips, with no lean.
- **Open arms.** The travel-side hand holds the leek up, with the arm out wide. The other arm is out low and back, palm down.
- **Small, easy steps.** The knees stay close and the feet stay under the skirt.
- **Tails swing wide**, on both sides.
- **Happy face:** closed eyes and an open smile.

## The new walk

![side vs diagonal](miku_v2/gate2d/old_vs_new.png)

Top row: the GATE 2c side walk. Bottom row: the new diagonal walk. Each shows all 8 drawings at 1×, contact and passing at 8×, and a real terminal in dark and light.

![contact sheet](miku_v2/gate2d/contact_walk.png)

![onion skin](miku_v2/gate2d/onion_walk.png)

![terminal stills](miku_v2/gate2d/walk_diagonal_stills.png)

The stills come from the terminal recording: idle in front view, the turn, walking right, walking left, then back to front. The full recording is in [walk_diagonal.gif](miku_v2/gate2d/walk_diagonal.gif).

## How it is built

- **Head:** the approved front pose, turned by a column warp. The outline and near tie stay one-to-one; the rest of the head is stretched on the near side and squeezed on the far side, so the face moves about 4 px toward travel and the far eye and far tie narrow. On top of that sit closed "^ ^" eyes, a blush and an open D-shaped smile.
- **Tails:** the clean hand-drawn tail from the front pose, used on both sides (mirrored for the near one, since the front pose's near tail has the leek over it). The far tail is one step darker on the hair ramp. The far tail tucks 3 px behind the head. The two tails flare outward together twice per cycle, one tick behind the bob, with the most movement at the tips.
- **Body:** new hand-placed grids:
  - torso, with the tie turned toward travel
  - raised leek arm, its fist around the stalk
  - low back arm, palm down
  - flared skirt with cyan hem
  - four leg shapes: planted, reaching forward, on the toe behind, and passing with the knee up
- **Far leg:** skin shade on the thigh and the darker far-side slate on the sock. The near leg crosses in front on the left-foot steps.
- **Bob:** the body drops 1 px at contact and down, and rises 1 px at passing and up. The planted foot stays on the ground. The skirt hem and the leek leaves lag by a pixel.
- **Posture:** head centre minus hip centre is about −1.5 px in every drawing, so the head is over or slightly behind the hips, never ahead. The upright test still passes.

## Turns

- **Cheerful walk:** she turns from front straight to the 3/4 standing pose, then walks. That's one in-between instead of two, because 3/4 sits between front and side.
- **Tired walk:** keeps its side profile and slouch, and now has its own side-view turns, so a tired stroll never pops between views. The facing planner picks the right turns for each walk, and switching between the two styles always goes through the front.

## Tests

All 133 pass (1 skipped, 1 expected failure). New tests:
- a tired walk uses the side-view turns, and the plan still obeys every facing rule
- in every diagonal drawing at least one foot is on the ground and nothing is below it

## Critic

Two rounds, with a fresh reviewer each time and the same rubric.

**Round 1** found that the mood was right but the 3/4 turn didn't read: the face was centred and both tails were locked. I then strengthened the head turn and tucked the far tail behind the head. The first warp smeared the near hair tie, so the outline now stays one-to-one. The tails now flare outward together on each bounce.

**Round 2** verdict: partly. The mood is right: happy face, leek up, open arms, upright chibi stack, and a clear step up from the stiff side profile. But the diagonal is still shallow. It reads as front-facing and bouncing more than strolling at 3/4.

| Item | Verdict |
|---|---|
| 3/4 turn reads | partly |
| Upright stack | yes |
| Open arms with leek aloft | yes |
| Small steps read as walking | partly |
| Bounce | partly |
| Tail swing | partly |
| Happy face | yes |
| Far-side depth | yes |
| Turn transitions | partly |

Scores, 1–5:

| Area | Score |
|---|---|
| Likeness | 4 |
| Silhouette | 3 |
| Consistency | 4 |
| Pose readability | 3 |
| Timing | 3 |
| Pixel discipline | 3 |
| Dark-terminal contrast | 3 |
| Gesture | 3 |
| Asymmetry and weight | 2 |
| Taper and flow | 3 |
| Appeal | 4 |

Remaining issues, not addressed this round:
- **Major:** deepen the turn. The far tie should be smaller or partly hidden, and the far side of the torso and skirt narrower.
- **Major:** the contact pose is a straddle. Offset the legs in depth (near foot lower and forward) and angle the feet toward travel.
- **Moderate:** the leek arm is a rigid bar with dotted pixels near the shoulder, and it nearly vanishes against the far tail on dark.
- **Moderate:** the tails need a bigger flare, and the bounce more travel.
- **Moderate:** the turn from front pops: the eyes go from open to closed and the leek from low to high, so it needs one in-between drawing.
- **Minor:** the skirt is static.
- **Minor:** the far boot is hard to separate at contact on dark.
- **Minor:** check the stray specks beside the sprite in the terminal stills.
