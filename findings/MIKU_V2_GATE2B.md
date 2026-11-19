# Miku v2: GATE 2b, surgical fixes

These are the fixes from your notes on the walk and walk_tired contact sheets, plus your earlier requests: a smiling, cheerful walk with the leek spinning in circles, and the side hair fixed in both walks. The dragged leek, the closed line eyes and the leek jump during the turn are kept. Everything else was left as it was.

"Before" is the GATE 2 package (commit 803e3c9). Each panel shows before and after at 1× and 8× (4× for the full-figure onion comparisons).

## The root cause of the tails on the wrong side

The tail chain measured its angle so that the setting meant to trail the tails behind her actually pushed them forward (+x). That's why the near tail kept showing up ahead of her chest. The chain now uses an explicit angle from vertical and an explicit backward direction. A new test checks every profile frame: no tail pixel is further forward than the body's leading edge.

## Each fix

| # | Fix | Result | Panel |
|---|---|---|---|
| 1 | No tail pixel ahead of her front edge | Done, with a test over every profile frame | `miku_v2/gate2b/fix_01.png` |
| 2 | Tails arc back and down from the tie, clear of her back, tips lag | Done. The far tail is a shade darker. The critic says the cheerful walk's arc now overshoots: too far back, not enough down | `fix_02.png` |
| 3 | Rounded crown and back, bangs forward, near-side hair tie | Mostly done. The crown and the larger near tie read; the bangs sweep is modest | `fix_03.png` |
| 4 | Far side one shade darker | Done, with a test: far-side colours are never lighter than near-side ones, for legs, arms and tails. Painting the far leg in outline navy erased its shape, so a dedicated far-side slate (#1a2a40) was added to the palette for the far sock and boot. The critic finds it too close to the near slate on dark terminals | `fix_04.png` |
| 5 | Grey halo | Diagnosed and removed from review. It was the onion skin's 30% ghost of the previous frame, not the outline treatment. The frames are clean on white and on dark | `fix_05.png` |
| 6 | Pale blob in frame 2 | Gone. It was the onion ghost of frame 1's forward-swinging far arm, and that lobe no longer exists. No smear was added: I couldn't make one read at 1× | `fix_06.png` |
| 7 | Smile and bright eyes throughout | The bright open eye is done. The open mouth (red rim, dark inside) still reads as a red block on the profile edge, per the critic | `fix_07.png` |
| 8 | Spinning leek in the leading hand, nothing strapped to her back | Done. The angle follows time: an even full turn each second, passing behind her head | `fix_08.png` |
| 9 | Keep the tired eyes, droop and dragged leek | Kept | `fix_09.png` |
| 10 | Tired: near arm hangs limp in front; far arm drags the leek | Done. The critic says the two dark sleeves read a little like a vest and the near hand is small | `fix_10.png` |
| 11 | Tired tails hang heavily down and back, close, little sway | Done | `fix_11.png` |

Also fixed: transparent holes trapped inside the silhouette, between the side lock and the neck, are now filled with the surrounding colour.

## Critic (fresh subagent, 1–5)

| Dimension | GATE 2 final | GATE 2b, first run | GATE 2b, final frames |
|---|---|---|---|
| likeness / P1 | 3 | 3 | 3 |
| silhouette | 3 | 3 | 3 |
| consistency across frames | 3 | 4 | 3 |
| pose readability | 3 | 3 | 3 |
| timing | 4 | 3 | 4 |
| pixel discipline | 3 | 3 | 3 |
| dark-terminal contrast | 4 | 3 | 4 |
| gesture | 2 | 3 | 2 |
| asymmetry and weight | 2 | 2 | 3 |
| taper and flow | 2 | 3 | 3 |
| appeal | 2 | 3 | 3 |
| **total (of 55)** | 34 | 33 | **34** |

Appeal, taper and weight each moved from 2 to 3. Gesture is still 2.

## What the critic still flags (not done; this gate stops here as planned)

- **Spin:** the whole arm windmills from the shoulder. It should be a forearm or wrist circle near the chest, and the leaves fan out like a claw.
- **Cheerful tails:** too long and too horizontal for walking pace. Bring them down to about 30–40° with the tips near the knees.
- **Profile face:** it has no nose or chin, and the mouth needs a smile shape set inside the edge.
- **Cheerful walk:** it still lacks forward lean and bounce, and the far arm is hard to see.
- **Tired walk:** the stride isn't shortened enough, and the droop needs a head tilt, not a drop.
- **Far-side slate:** too close in value to the near slate on dark terminals.

## Other changes

- The walk exposure sheet now describes the cheerful spin.
- The palette gained one colour, the far-side slate, for the reason given in fix 4.
- The GIFs (`miku_v2/gate2/walk_both_ways.gif` and `walk_tired.gif`) were re-recorded from the final clips and rendered with agg.
- All Miku v2 tests pass (20, including the two new ones).
