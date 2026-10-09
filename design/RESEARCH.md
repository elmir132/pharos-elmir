# How people see crashes before they happen

Written Oct 9, 2026 during the build. Sources are linked; claims that come from general knowledge rather than a source are marked.

## 1. What practitioners do, ranked by how much they change risk

1. **Look where people already got hurt (network screening).** Agencies rank intersections by crash history and fix the worst first. It is the most used method and the easiest to act on. Weakness: it waits for harm, and a few years of data on one corner is noisy. PharOS does this on the map heat and the ranked list, using the NYC collision file.
2. **Measure close calls instead of waiting for crashes (traffic conflict technique).** Video analysis counts near misses with *surrogate safety measures*:
   - **Time to collision (TTC):** how long until two road users collide if both keep their path and speed.
   - **Post-encroachment time (PET):** the gap between one road user leaving a conflict point and the next arriving.
   - **Deceleration rate to avoid a crash (DRAC):** how hard someone must brake to avoid it.
   Research on 139 signalized intersections found these measures relate most strongly to low-severity crashes, and that severe outcomes need extra context such as speed and road design. They explain rear-end and left-turn crashes best.
   Sources: [FHWA, Algorithms for Surrogate Measures of Safety at Intersections](https://www.fhwa.dot.gov/publications/research/safety/03050/07.cfm); [Kittelson, Breaking Down Video-Based Conflict Monitoring](https://www.kittelson.com/ideas/breaking-down-video-based-conflict-monitoring/); [Real-time pedestrian risk from predicted PET (arXiv 2404.15635)](https://arxiv.org/pdf/2404.15635); [Can surrogate safety measures explain crash patterns at signalized intersections (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0022437526000654).
3. **Fix the thing that is known to work.** Example: a leading pedestrian interval gives walkers a head start before turning cars move. Studies in the FHWA clearinghouse report roughly 10 to 19 percent fewer pedestrian-vehicle crashes, with one outlier study much higher. Source: [FHWA CMF Clearinghouse](https://cmfclearinghouse.fhwa.dot.gov/detail.php?facid=9903).
4. **Manage speed.** General knowledge: speed decides how severe a crash is, which is why street redesign and speed enforcement sit at the centre of Vision Zero programmes. PharOS does not yet measure vehicle speed on live NYC cameras.
5. **Watch driver and pedestrian attention.** In the NYC collision file since 2024, "Driver Inattention/Distraction" is the most common recorded cause by a wide margin (see the City panel). Cues such as a phone in hand are therefore worth surfacing as conditions that raise risk.

## 2. What would give the earliest warning

- **Trajectory, not position.** A car at 40 km/h that will reach a crosswalk in 1.5 seconds with someone in it is dangerous even if the two are still 25 metres apart. Straight-line projection of tracked vehicles and pedestrians for two to three seconds, and a check against the crosswalk polygon, flags future conflicts. This is how PharOS describes a "reckless vehicle": speed above what the street expects, and a projected path into a crossing that is occupied or about to be. Status: designed, not yet running on live feeds.
- **Interaction measures** (TTC, PET, DRAC) between each vehicle and each person, as in section 1. Status: TTC and distance run on analysed footage; PET and DRAC are planned.
- **Context that changes severity:** dusk and night, rain, sightlines blocked by parked vehicles or trucks, turning movements across a crosswalk.
- **Pedestrian cues** (phone, headphones, dark clothing at dusk, running, crossing against the signal) from a vision-language model description of the scene. These are weak signals and are shown as cues, never as a score on a person.

## 3. Real-time and open data options

| Source | What it gives | Notes from testing |
|--------|---------------|--------------------|
| [NYC DOT traffic cameras](https://webcams.nyctmc.org/map) | Still images from about 1,000 cameras; 377 in Manhattan were listed as online | Image changes between requests a few seconds apart. Not video, so time to collision cannot be measured reliably from it. The camera list API does not allow browser cross-origin requests, so PharOS ships the list as a file. |
| [NYC Open Data, Motor Vehicle Collisions](https://data.cityofnewyork.us/resource/h9gi-nx95) | Every police-reported crash with location, injuries and contributing factors | On Oct 9, 2026 the newest record was June 11, 2026, and the dataset notes that its automatic update was paused. The City panel states the date. |
| [NYC DOT Traffic Speeds](https://data.cityofnewyork.us/resource/i4gi-tjb9) | Live link speeds and travel times | Latest record at check time was Oct 9, 2026 08:11. Useful to add a "traffic is faster than usual" signal. Not wired in yet. |
| VAST Builders Challenge index | 5-second street-camera segments with Cosmos captions and YOLO11 detections, searchable by words | Works only from the workshop VM. This is where near-miss measurement runs today. |

Open question for a next step: a true real-time near-miss detector needs video at several frames per second. The NYC DOT feed offers stills, so a city-wide live detector would need either higher-rate video access from the city or placing a small camera node at chosen corners.

## 4. What PharOS does today

| Capability | Status |
|------------|--------|
| 3D Manhattan map, camera nodes, crash heatmap, ranked intersections | Working on real data |
| Per-intersection live image, history by hour, recorded causes, suggested fixes | Working on real data |
| Walkthrough of the highest-risk intersections | Working |
| Candidate near misses from analysed footage with distance, closing speed, time to collision, Cosmos scene description, pedestrian cue tags | Working on the VM; accuracy not measured |
| Trajectory projection to future crosswalk conflicts | Designed, not built |
| Live detection on NYC DOT cameras | Not possible from stills; needs video |

## 5. Limits to state out loud

- Distances are approximate metres from the ground point of each box, scaled by typical object height, with no camera calibration.
- The near-miss thresholds were tuned on synthetic tracks and checked by eye on a handful of clips. No precision figure exists yet.
- Contributing factor is the first factor recorded by police; about half of reports list it as unspecified.
