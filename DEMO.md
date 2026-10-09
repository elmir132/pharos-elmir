# PharOS demo: 3 minutes, three acts

Goal: show a useful tool and be exact about what each part is. Say what is measured, what is a still, and what is a candidate that needs a person.

Setup before presenting
- Mac: `cd web/pharos && python3 -m http.server 8099`, open http://127.0.0.1:8099 in a visible tab, wait until the heatmap and dots appear (about 30 seconds on a fresh load).
- VM: the review queue and clips only work on the workshop VM (see README). Have that browser window ready, and a screen recording of the same steps as a fallback.
- Check the data row on the City panel: collisions through 2026-06-11, 377 cameras.

## Act 1: where people were hurt (60 s)
Show: the 3D map, the heatmap, then press W for the walkthrough for a few seconds.
Say: "This is Manhattan. The glow is where NYC's own records show people injured or killed since 2024, through June 2026. The dots are NYC traffic cameras, coloured by the crash history within 120 metres. It is history, not a prediction, and it is not adjusted for how much traffic passes."
Show the row of sources: "If a source fails the tool says unavailable. It never shows zero."

## Act 2: one camera area (60 s)
Show: click one of the top areas (for example Delancey St @ Bowery St). Point at the latest still, the hour chart, the recorded causes, and the countermeasures list.
Say: "This is a still image from the city's camera, not video, and the time shown is when we asked for it. Around this camera there were 116 collisions and 13 pedestrians hurt. The most common recorded cause is driver inattention. For engineers to evaluate: a leading pedestrian interval, which studies associate with roughly 10 to 19 percent fewer pedestrian-vehicle crashes, daylighting the corner, curb extensions."
Do not say: "dangerous intersection" or "risk score". Say "crash history".

## Act 3: candidates a person must review (50 s)
Show: on the VM, the Review tab. Play one clip, point at distance, closing speed and time to collision, then mark it Real, False or Unsure.
Say: "Separately, we analysed street footage from VAST: YOLO tracks people and vehicles, we measure distance and closing speed, Cosmos describes the scene, and a model writes one sentence that is only accepted if every number in it was measured. These clips are not tied to the camera I just showed; VAST does not publish their location. Each one is only a candidate. Reviewers mark them so we can measure how often the detector is right. We have a precision script ready and, if we have labels by then, one number with its interval."
If there is no precision number yet, say so: "We have not measured accuracy yet."

## Close (10 s)
"PharOS is a lighthouse: it shows the rocks early and leaves the decision to the people steering. The next step is a pilot camera with video and labelled clips, then trajectory projection into crosswalks, which is designed but not built."

## Do not claim
- Live detection on the NYC cameras (they are stills).
- That the Review clips are from the selected intersection or from Manhattan for certain.
- Any accuracy figure that has not been measured on labelled clips.
- That a person is at fault because of a phone or clothing in a caption.
