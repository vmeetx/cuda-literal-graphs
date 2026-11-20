# Miku v2: GATE 2e (hair flicker, flowy skirt, 3/4 tired walk)

This gate continues from commit 889e275. The approved items are unchanged except where a fix needed a change, and those changes are shown below. The skirt and torso keep their full width.

## 1. Hair flicker

**Cause:** the GIF recorder decoded each pty read on its own. A half-block character (3 bytes in UTF-8) split across two reads turned into two U+FFFD replacement glyphs, and agg drew them as dark specks on her hair. The recorded cast had 108 of them.

I checked each layer in turn:

| Layer | Finding |
|---|---|
| Sprite data | Clean. The lint found no outline pixels walled in by hair, in any frame. Once the bob is undone, the top of her head is pixel-identical in every walk frame. |
| Compositing order | Clean. No tail, tie, leek or arm layer reaches into the head region. |
| Half-block rendering | The demo compositor wrote a transparent half with no background, so the terminal default showed instead of the scene underneath. That had no visible effect on the dark default, but it was wrong, so it is fixed too: a sprite cell now keeps the background of the cell it covers. |
| Diff redraw | Clean. Every changed cell is rewritten in full, with its colours reset. |

**Fix:** the recorder now uses an incremental UTF-8 decoder that carries unfinished bytes over to the next read. New recordings contain 0 replacement glyphs.

**Regression test:** every frame of every clip, in both facings, is composited over a graph box on a dark and a light background. The real diff redraw renders it, the byte stream is cut into 7-byte chunks that split characters, and the chunks are decoded the way the recorder decodes them. A terminal emulator (pyte) replays the result. Every cell of the sprite's rectangle must then match the scene exactly: no replacement glyph, no outline pixel the frame doesn't contain, no stale cell, and the scene background behind every transparent half. A second test pins the cause: chunk-by-chunk decoding produces U+FFFD, and the fix doesn't.

Head crops from consecutive GIF frames, before and after:

![before](miku_v2/gate2e/flicker_heads_before.png)

![after](miku_v2/gate2e/flicker_heads_after.png)

GIFs: [before](miku_v2/gate2e/flicker_before.gif), [after](miku_v2/gate2e/flicker_after.gif).

## 2. Flowy skirt

The waist (rows 45–47) moves with the body. Below it, the hem comes from four hand-drawn states, S0–S3, all asymmetric, with the trailing side on the left. Each state is a pair of hem edges plus a per-column offset string.

| State | Drawing it comes from | What it does |
|---|---|---|
| S0 | contact | drops over the front leg |
| S1 | down | flares out behind |
| S2 | passing | swings back |
| S3 | up | settles, with a flick at the front |

The walk shows the state of the drawing before (cheerful) or two drawings before (tired), which puts the hem 1–2 ticks behind the hips.

- **Wave down the skirt:** the rows between waist and hem ease from the waist edges to the hem edges, so the movement travels down.
- **Pleats and trim:** the pleat lines bend toward the hem, and the cyan trim follows the hem as one continuous stepped line.
- **Settles last:** in the turns, the waist is still while the hem keeps moving for one more drawing (`stand_settle`, then `stand`). The turn into the walk starts with the hem trailing (`stand_go`).
- **Full width:** at rest the skirt is exactly the approved width. A test checks that no frame is ever narrower; sway only flares a side outward.
- **Lint:** no straight run longer than 5 px on any hem outline, in any walk frame.

![skirt before/after](miku_v2/gate2e/skirt_before_after.png)

![old vs new, 1x, 8x and terminal](miku_v2/gate2e/old_vs_new.png)

GIF: [cheerful walk with the new skirt](miku_v2/gate2e/walk_cheerful.gif).

**Changes to approved turns:** the cheerful turn to front gained one tick, where the hem settles (`stand_settle` 2, `stand` 1, front 2). The turn to the walk now starts with the hem trailing. The feet, face, head turn and posture are unchanged.

## 3. Tired walk in 3/4 view

**Exposure sheets came first.** `walk_tired` is 20 ticks, with keys held 3 ticks and in-betweens 2.

**Thumbnails:** three options for the contact key, at 1x, 6x and in a terminal (dark and light).

| Option | Head | Leek drag |
|---|---|---|
| A (pick) | 1 px forward, 3 px down | long, leaves well behind her |
| B | 2 px forward, 3 px down | short, leaves close |
| C | 1 px forward, 1 px down | arm stretched back, leaves far behind |

Every critic round preferred A. B and C stay in the code and swap in with one setting.

![tired thumbnails](miku_v2/gate2e/tired_thumbnails.png)

**Design:**
- **Face:** closed line eyes and a flat mouth.
- **Posture:** rounded shoulders, with the head 1 px forward and 3 px down.
- **Gait:** a short shuffle:
  - the leading foot is 3 px ahead and the trailing foot is flat behind
  - the heel peels up on the down drawings
  - the foot lifts 1 px on passing
  - bob is 0–1 px, and on the down drawings only the body dips, not the head
- **Arms:** the near arm hangs limp (sleeve, cuff, small hand). The far hand reaches back and drags the leek: a pale root at the hand, a green stalk, and three blades that scrape between two states.
- **Tails:** they hang heavy and close, with a quarter of the cheerful sway.
- **Skirt:** half the wave, lagging two drawings.
- **Leg depth:** matches the cheerful walk.
- **Head over hips:** this check is exempt for the tired walk, and the test says so.
- **Not done:** the sweat drop (optional).

![tired contact sheet](miku_v2/gate2e/contact_walk_tired.png)

![tired onion skin](miku_v2/gate2e/onion_walk_tired.png)

GIF: [tired walk](miku_v2/gate2e/walk_tired.gif).

## 4. Transitions

| Clip | Length | What happens |
|---|---|---|
| `walk_to_tired` (on the way to a rest) | 16 drawings, 28 ticks | eyes go "^ ^" → half-lidded → lines; the leek lowers (up → out → at her side → dragged); the up-bounce dies first, then the down-bob; the skirt calms; the second cycle takes on the tired holds and steps |
| `walk_from_tired` (walking off after the rest) | same length | the reverse |
| Tired turns | | the 3/4 tired stand settles its hem, then a tired front view (the front pose with line eyes and a flat mouth); she holds that tired front through the rest |

The facing planner picks all of these automatically, and the facing-rule tests cover the full sequence.

![walk_to_tired](miku_v2/gate2e/contact_walk_to_tired.png)

![walk_from_tired](miku_v2/gate2e/contact_walk_from_tired.png)

![rest sequence stills](miku_v2/gate2e/rest_transitions_stills.png)

GIF: [cheerful → tired → tired turn → rest → tired turn → walking it off](miku_v2/gate2e/rest_transitions.gif).

The side-view tired walk and its turns are kept as fallbacks, renamed with a `_side` suffix. Nothing uses them now.

## 5. Leek arm

The upper arm comes out from the shoulder, bends at the elbow, and the forearm rises at about 45°. The sleeve tapers from 5 px to 3 px at the cuff, then a small fist. The open outline under the shoulder, which caused the broken pixels, is closed. The leek's angle and the raised hand are unchanged.

![leek arm before/after](miku_v2/gate2e/leek_arm_before_after.png)

## 6. Critic and tests

Four rounds, each with a fresh reviewer, the same rubric, and the 1x PNGs, terminal screenshots and text grids. Scores are cheerful / tired; GATE 2d had no tired 3/4 walk.

| Area | GATE 2d | Round 1 | Round 2 | Round 3 (kept) | Round 4 (reverted) |
|---|---|---|---|---|---|
| Likeness | 4 | 4 / 4 | 5 / 4 | 5 / 4 | 5 / 4 |
| Silhouette | 3 | 4 / 3 | 4 / 3 | 4 / 3 | 4 / 3 |
| Consistency | 4 | 4 / 3 | 4 / 3 | 4 / 3 | 4 / 3 |
| Pose readability | 3 | 3 / 3 | 5 / 3 | 5 / 3 | 5 / 3 |
| Timing | 3 | 3 / 2 | 4 / 4 | 4 / 3 | 4 / 3 |
| Pixel discipline | 3 | 3 / 3 | 4 / 3 | 4 / 4 | 4 / 4 |
| Dark-terminal contrast | 3 | 3 / 3 | 4 / 3 | 4 / 3 | 4 / 3 |
| Gesture | 3 | 3 / 2 | 5 / 3 | 5 / 3 | 5 / 3 |
| Asymmetry & weight | 2 | 3 / 3 | 4 / 3 | 4 / 4 | 4 / 4 |
| Taper & flow | 3 | 4 / 3 | 4 / 3 | 4 / 4 | 4 / 3 |
| Appeal | 4 | 4 / 3 | 5 / 4 | 5 / 4 | 5 / 4 |
| Skirt follow-through | – | 4 | 4 | 4 | 4 |

- **Cheerful walk:** every dimension is 4 or higher.
- **Tired walk:** silhouette, consistency, pose readability, timing, contrast and gesture are still 3.
- **Round 4** scored lower on tired taper and flow (4 → 3) and nothing improved, so it was reverted and the round-3 version is kept as the best.

Remaining issues the critics raised, not fixed at this gate:
- **Major:** the end of the tired turn jumps. The tired front view is the approved front pose, with the leek held crosswise and the legs crossed. It needs its own drawing that keeps the leek dragging, with a flat, parallel stance.
- **Moderate:** the tired legs change little between drawings, so at 20 ticks the walk reads close to a slide.
- **Moderate:** the limp near arm sinks into the dark skirt on a dark terminal.
- **Minor:** the dragged blades can read as grass at 1x.
- **Minor:** the dashed trim can speckle at 1x.

Tests: 163 pass (1 skipped, 1 expected failure). The checks cover:
- palette, strays, ground line, region-diff intent
- facing rules, tails behind the body (side clips)
- far side darker than near side, head over hips (cheerful only)
- the hair-flicker terminal regression test
- the hem straight-run lint, full skirt width, hem lag, and the waist settling before the hem
- the tired gait
- the rest sequence in the planner
