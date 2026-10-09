# PharOS design notes

PharOS is a lighthouse for city intersections. This file explains the name, the mark, the colours and the interaction design, and why each choice was made. Facts about the code and data are in the main README; research behind the method is in `RESEARCH.md`.

## 1. Why a lighthouse

The Pharos of Alexandria stood on an island at the mouth of the harbour of Alexandria from about the third century BC. It became so famous that in French (*phare*), Spanish and Italian (*faro*) the word for a lighthouse is still its name.

A lighthouse does not stop storms. It does three quieter things:

1. **It watches** a place nobody else can watch all at once.
2. **It tells you early**, while there is still time to steer.
3. **It leaves the decision to the person at the wheel.**

That is the product. A city has hundreds of intersections and a few people who can look at them. PharOS watches the cameras and the crash records, shows where the hidden rocks are, and leaves the choice (change the signal, paint the corner, slow the street) to the people responsible. It is a warning light, not an autopilot.

The name carries the idea of an operating system for street safety: the **OS** is set in beacon colour because it is the part that runs.

## 2. The mark

![mark](logo-mark.svg)

The tower follows the historical Pharos, which was described as three stacked forms: a **square** base, an **octagonal** middle and a **cylindrical** top. Each tier is also a stage of the product.

| Tier | Shape | Product stage | Why this shape |
|------|-------|---------------|----------------|
| Base | Square, 36 wide | **Sense**: cameras and crash records | Four sides, stable, the part that must not move |
| Middle | Octagon, 24 wide | **Measure**: tracks, distance, time to collision | Eight directions of travel, the way traffic actually meets at a corner |
| Top | Circle, 9 radius | **Warn**: the light a person sees | The one soft, open shape; it is where the system speaks to a human |

Read bottom to top the corners are removed one step at a time: square, octagon, circle. Raw data gets rounded into something a person can act on.

Proportions (viewBox 96 by 96):
- Base is 36 wide, the octagon 24 wide (a 3 to 2 step), the lantern 18 across, which is half the base.
- The two beams leave the lantern at about 21 degrees above and below the horizontal, a 42 degree fan. A narrow fan reads as a searchlight, not as a broadcast antenna.
- A thin ring around the lantern is the "range" of the light, echoing a radar sweep without copying one.
- The door arch in the base gives the tower scale and a human reference.

Beams are soft at the tips (gradient to transparent) because the warning is probabilistic: it fades with distance and uncertainty rather than ending at a hard edge.

## 3. Colour

Colours come from the harbour at night: deep water, a warm light, and one hot colour for danger.

| Token | Hex | Meaning |
|-------|-----|---------|
| Night | `#0A1022` | Water at night, main background |
| Harbor | `#121C36` | Cards and panels |
| Fog | `#E9EEF7` | Tower stone, main text |
| Mute | `#93A1BA` | Secondary text |
| Beacon | `#FFB703` | The light: brand accent, selection, highlights |
| Ember | `#FB5607` | Higher risk |
| Sea | `#2EC4B6` | Lower risk, "clear water" |
| Crimson | `#B1003D` | Highest risk only |

The risk scale runs sea, beacon, ember, crimson. It is used for the map dots, the heat layer and the legend, and it always travels with a second signal (dot size, or a number) so that colour is never the only carrier.

Contrast, computed from the WCAG formula, on Night:

| Pair | Ratio |
|------|-------|
| Fog text | 16.2 to 1 |
| Mute text | 7.2 to 1 |
| Beacon | 10.8 to 1 |
| Ember | 5.8 to 1 |
| Sea | 8.7 to 1 |

All are above the 4.5 to 1 level for normal text. The palette has not been checked with a colour-vision simulator; the redundancy rule above is the safeguard.

## 4. Interaction design (HCI choices)

**One question per level.** The page answers three questions in order and never mixes them.
1. *City:* where should I look first? (heat, ranked list, common causes)
2. *Intersection:* what is happening here, and has it before? (live camera, history, causes)
3. *Watch:* what is about to go wrong right now? (candidate near misses with evidence)

**Map first.** The home screen is a tilted 3D map of Manhattan because the problem is spatial and people already read cities that way. The tilt lets tall blocks show why a corner is hard to see around. A walkthrough (key W) flies the camera to the highest-risk intersections in turn so a viewer can take in the pattern without learning controls. Dragging the map stops it.

**Progressive disclosure.** Numbers appear when asked for. The side panel starts with four totals, then causes, then a ranked list. Clicking a camera opens its own panel with the live image first because the picture is what people trust.

**Show the work.** Every flag carries the measurement behind it (distance, closing speed, time to collision). Sentences written by a language model are only accepted if every number in them was measured.

**Calm, not alarming.** There is no flashing and no red banner. Events are called candidates for review. The aim is to avoid alert fatigue, which makes people ignore the one alert that matters.

**Honest about uncertainty.** The first panel states the date the public collision file runs to. Distances are described as approximate. Cause is the first factor on the police report, and about half of reports leave it unspecified; the panel says so.

**Accessibility.** Text contrast above 4.5 to 1, visible keyboard focus, keyboard shortcuts (W walkthrough, H heat, T tilt), buttons are real buttons, the live image has an alt text, motion respects `prefers-reduced-motion`, and the panel becomes a bottom sheet on a phone.

**Language.** Plain words: "people injured", not "KSI". Numbers are rounded to what the data supports.

## 5. Ethics and privacy

- PharOS never identifies a person. It does not do face recognition or read plates.
- Pedestrian cues (phone in hand, headphones, dark clothing at dusk, running) are treated as **conditions that raise the chance of a conflict**, the same way fog or a blocked sightline does. They are never used to blame or to rank people.
- Camera images are shown live from the public NYC traffic-camera network and are not stored by PharOS.
- Every suggested fix is an idea for engineers to evaluate, not a diagnosis.

## 6. Files

- `logo-mark.svg` the mark alone
- `logo.svg` mark and wordmark on Night
- `RESEARCH.md` what is known about detecting crashes before they happen, and data sources
