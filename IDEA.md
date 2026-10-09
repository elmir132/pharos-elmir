# PharOS: the idea in one page

**One line:** PharOS is a lighthouse for city intersections. It shows where people get hurt in Manhattan, lets you open the live camera at each corner, and finds candidate near misses in street footage, with the numbers behind every flag.

## The problem
Cities learn about dangerous intersections after someone is hurt. Hundreds of cameras exist, but nobody can watch them all, and crash records only say where harm already happened.

## What PharOS does
1. **Home page: a tilted 3D map of Manhattan.** A heatmap of real injury and death records shows the dangerous areas. A walkthrough flies the camera to the highest-risk corners.
2. **Click any camera node** (377 NYC traffic cameras): live image, risk percentile, collisions by hour, the causes police recorded, and **preventable next steps** (for example a leading pedestrian interval, daylighting the corner, curb extensions).
3. **City panel:** most common causes, the intersections to look at first.
4. **Watch panel:** candidate near misses from street footage. For each one: distance, closing speed, time to collision, a scene description, and cues such as a phone in hand, headphones, dark clothing at dusk or running (shown as conditions that raise risk, never as a judgement of a person).
5. **Reckless vehicle idea:** speed above what the street expects plus a projected path into a crosswalk that is occupied or about to be (future conflict, not just present distance).

## How it works
VAST stores the video and the YOLO11 detections. We track people and vehicles, measure distance and time to collision, and rank events. Cosmos describes each scene. A Weights & Biases model writes a one-sentence note, accepted only if every number in it was measured. Cursor built it.

## Name and look
Pharos, the lighthouse of Alexandria: it does not stop storms, it shows the rocks early and leaves the decision to the person at the wheel. The mark is a three-tier tower (square, octagon, circle), meaning sense, measure, warn. Palette: night blue, beacon amber, ember for danger, sea green for safe. Details in `design/README.md`.

## What is real and what is not yet
- Real: 3D map, crash heatmap, camera nodes with live images, per-intersection insights, walkthrough, near-miss candidates on VAST footage.
- Not built: trajectory projection to future crosswalks, a Cosmos yes/no check (no GPU endpoint URL), live detection on NYC cameras (they serve stills, not video), merge with the teammates' version.
- Known weakness: some candidates are false because of perspective (a person in the foreground, a car behind). Accuracy has not been measured.

## Questions for Codex
1. What would you add that most increases real usefulness for a city traffic engineer, within a few hours?
2. How would you cut false near misses without extra data, and how would you measure precision on a small hand-labelled set?
3. How would you build the trajectory projection and the crosswalk-conflict check?
4. What would make the 3-minute demo stronger?
5. What in the design or code would you change?

Repo: github.com/elmir132/pharos-elmir (private). Start with `README.md`, then `AGENTS.md`.
