# PharOS: submission text (draft)

Fill the bracketed parts. Edit anything that is not true by the time you submit.

## Project name
PharOS

## One line
A lighthouse for city intersections: it shows where people were hurt in Manhattan, opens the latest camera still at each corner, and finds candidate near misses in street footage with the measurements behind each one.

## What we built
- A 3D map of Manhattan with a crash-history heatmap from NYC Open Data (collisions 2024 to 2026-06-11), 377 NYC DOT camera locations, and a panel per camera area: latest still image, collisions by hour, recorded causes, countermeasures to evaluate, and a plain-text brief an engineer can copy.
- A near-miss detector for street footage: it tracks vehicles and pedestrians or cyclists, measures approximate distance, closing speed and time to collision, and ranks candidate events.
- A review workflow: reviewers mark each candidate real, false or unsure, export labels, and a script reports precision with a confidence interval, so accuracy is measured and not claimed.
- Honest behaviour: every data source can fail alone, unknown is never shown as zero, stills are labelled as stills, and a language model's sentence is only accepted if every number in it was measured.
- [Add what Divyesh and Pranav built: live observatory on 511NY video, recorded evidence search, forecast lab.]

## Sponsor tools used (be exact)
- VAST Data: AI OS stores the video, the YOLO detections and the search index; we read detections, captions and search through its backend.
- NVIDIA Cosmos: Cosmos Reason scene descriptions and Cosmos Embed search, used through the VAST pipeline. [Add a direct Cosmos call only if it is actually working.]
- CoreWeave GPUs: serve YOLO11 and Cosmos for the pipeline.
- Weights & Biases: serverless inference writes a one-sentence note for each candidate, checked against the measured numbers. [Do not claim Weave unless it is used.]
- Cursor: built the code.

## What is not done (say it)
- Trajectory projection into crosswalks is designed, not built.
- NYC DOT cameras provide still images, not video, so live measurement runs only on video sources.
- The camera location of the analysed footage is unknown, so near-miss clips are not tied to a map location.
- Detector accuracy: [number with its interval and sample size, or "not yet measured"].

## Links
- Code: https://github.com/elmir132/pharos-elmir
- Demo video: [link]
- Live app: [link, if any]

## Team
[Names and the email each person signs in to Cursor with]
