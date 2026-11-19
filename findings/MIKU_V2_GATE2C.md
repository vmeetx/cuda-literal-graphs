# Miku v2: GATE 2c, walk posture

GATE 2b is not approved yet. This round fixes the hunch in the cheerful walk and the critic's leftover items 5–8. The tired walk keeps its slouch.

## 1. Study: reference strip

![reference strip](miku_v2/gate2c/reference_strip.png)

There are five side-view walk cycles, all CC0 from OpenGameArt. I used them for study only: nothing was copied or traced, and no pixels from them ship. The files are r4t4's pixel girl walk, Junko (chibi pixel girl with long hair), the chibi walking bases, "Girl walking side" and the cartoon female walk. On each figure, a red line marks the head centre and a blue line marks the hip centre. The number under each frame is head minus hip toward the direction of travel, scaled to our 67 px height.

What the references do that we didn't:
- **Head stacked over the hips.** The chibi bases and the cartoon female keep the two lines within about 1 px in every frame. Our old walk led with the head by +1.1 to +1.8 px. A forward-tilted torso carried the head ahead of the hips, and that was the hunch.
- **Short stride, feet under the body.** Chibi proportions leave little leg, so the feet never reach far past the hip line. Our old stride was a full-size stride on chibi legs.
- **Vertical bounce, steady torso.** The body only rises and falls. It doesn't tip toward the step.
- **Chest up, chin level.** No reference drops its head into the walk.

A caveat on the measurements: the r4t4 and Junko numbers (+4 and +15 px) are contaminated. Long hair and the swinging arms pull the "head" and "hip" bands off-centre. Both figures look upright by eye, so read those two rows by eye, not by number.

## 2. Posture: old vs new

![old vs new](miku_v2/gate2c/old_vs_new.png)

The image shows all eight drawings at 1×, then contact and passing at 8×, then a real terminal in dark and light.

Head centre minus hip centre per frame (body pixels only; tails and leek excluded):

| Frame | Old (GATE 2b) | New |
|---|---|---|
| contact | +1.1 to +1.8 | −0.89 / −0.67 |
| down | | −0.45 / −0.23 |
| pass | | −0.31 / −0.31 |
| up | | −0.67 / −0.89 |

Every new frame has the head slightly behind, or over, the hips, never ahead. An automatic test now enforces this on every cheerful-walk frame: head minus hip must be at most 1 px toward travel. The test does not apply to walk_tired.

## 3. What changed

- **Upright stack:** the cheerful walk has zero forward lean, with spine vertical and chest up.
- **Chibi gait:** new short leg shapes keep the feet under her body. The two feet sit only 2 px apart at the hip, and the planted foot stays on the ground while the body moves.
- **Bounce:** down 1 px at contact and down, up 1 px at passing and up.
- **Head:** chin level; the cheerful face keeps a bright open eye.
- **Leek spin (item 5):** the upper arm hangs at her side, the forearm points forward, and the leek is shorter, twirling at the hand.
- **Tails (item 6):** angled down and back from the ties instead of near-horizontal. They bounce one beat behind her bob.
- **Profile face (item 7):** the mouth is a 1–2 px light-pink smile with an upturn, inside the face rather than a red block on the edge. The nose bump and chin stay on the silhouette.
- **Far side (item 8):** the far-side slate is darker on the same ramp, so the far leg separates from the near leg.

For walk_tired, the slouch is unchanged and so is its posture. The darker far side applies through the shared palette. The face change applies only to the cheerful face.

GIFs, recorded in a real terminal: [cheerful walk](miku_v2/gate2c/walk_cheerful.gif), [tired walk](miku_v2/gate2c/walk_tired.gif). Contact sheets: [walk](miku_v2/gate2/contact_walk.png), [walk_tired](miku_v2/gate2/contact_walk_tired.png).

## 4. Critic (fresh reviewer, same rubric)

The verdict on the hunch was **fixed**. The new frames stand upright and match the upright chibi references.

Requirements:

| Item | Verdict |
|---|---|
| Posture | yes |
| Head and chin | yes |
| Chibi gait | partly: the stride is now so short that contact reads close to standing, and the bob is subtle |
| Leek spin | partly/no: at passing the arm still reads as reaching out from the shoulder |
| Tails | partly: about 25–30°, the shallow edge, a stiff plank, and the bounce is not visible |
| Profile face | partly: the chin and nose are fine, but the mouth sits near the jaw edge and can read as blush |
| Far vs near legs | partly: they separate, but the value gap is still small on dark |

Scores, 1–5:

| Area | Score |
|---|---|
| Likeness | 4 |
| Silhouette | 3 |
| Consistency | 4 |
| Pose readability | 3 |
| Timing | 3 |
| Pixel discipline | 4 |
| Dark-terminal contrast | 3 |
| Gesture | 2 |
| Asymmetry and weight | 2 |
| Taper and flow | 2 |
| Appeal | 3 |

Remaining issues the critic flagged, not addressed this round (stopped as asked):
- **Major:** the tails need about 35–45°, a taper and an S-curve with a tip flick.
- **Major:** the leek elbow should be pinned at the waist so only the forearm turns.
- **Moderate:** widen contact by 1–2 px and make the bob a clear 1–2 px.
- **Moderate:** add a little weight shift, such as a 1 px chest or skirt sway.
- **Moderate:** a bigger near/far leg value gap.
- **Minor:** the mouth should sit 1 px further in, with a clear corner pixel.
