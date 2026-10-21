# Spy Academy Advanced

A standalone browser spy adventure with **24 operations**, maths from the first level, towers from 8 to 24 floors, and playable vehicle escapes. The complete game is in **`index.html`**: no build, server backend, Python runtime, external assets, accounts or API keys.

The maths generators are based on selected topics in the user's uploaded worksheets. This is a first curriculum release, not a transcription of every supplied problem. See [CURRICULUM.md](CURRICULUM.md) for the sequence and authoring contract and [SOURCES.md](SOURCES.md) for the source mapping and remaining material.

## Play and deploy

Open `index.html` directly in a modern browser, including offline. Progress is local to that browser/device and the site's origin. Changing from a local file to a hosted URL starts a separate save.

**GitHub Pages:** in this repository, open **Settings → Pages**, choose **Deploy from a branch**, then **main / (root)** and Save. The expected address after GitHub finishes deployment is `https://vorontzov.github.io/Spy-Academy-Advanced/`. This address works only after Pages has been enabled and deployed.

**Vercel:** import `Vorontzov/Spy-Academy-Advanced`, select **Other**, leave the build command empty, and use the repository root for the output. Deploy. No environment variables are needed. Future pushes to `main` can deploy automatically through that Vercel project.

For development, run `python -m http.server 8000 --bind 127.0.0.1` in this checkout. This server is only a local development tool; the published game remains static.

## Controls

| Input       | Action                                                            |
| ----------- | ----------------------------------------------------------------- |
| A/D or ←/→  | Move; steer during escapes                                        |
| W/S or ↑/↓  | Call/ride lifts; use a marked stair landing; steer during escapes |
| E or ↑      | Open a mission case; launch an escape                             |
| Space       | Jump; boost a vehicle (except parachute)                          |
| X or Z      | Fire                                                              |
| Q           | Cycle pulse pistol, scatter blaster and arc launcher              |
| C           | Close-range takedown                                              |
| V           | Cycle cloak, EMP and grapple                                      |
| G           | Activate selected gadget; shield during escapes                   |
| P or Escape | Pause/resume                                                      |
| M / F       | Sound / fullscreen                                                |

Touch controls appear below the game on smaller screens. Equipment buttons also support touch and keyboard activation. The field manual explains the mechanics.

## Missions and learning

Recover every mission case, then reach floor 01 extraction. Cases contain keycards, microchips, a cipher lens, blueprints and a black box. Every required case is a maths gate. Optional intel, medkits, shields and batteries help along the route. Stairs and grapples provide alternatives to elevators; later operations introduce faster and armored patrols. EMP barrels produce area stun explosions.

Environments include academy headquarters, dungeons, rooftop outposts, laboratories, a harbor, a citadel and a skybase. Every infiltration is followed by a playable car, motorcycle, helicopter, plane or parachute escape. These are compact scrolling stages: steer, clear hazards, collect beacons and reach the end of the route. They are arcade interpretations, not vehicle simulators.

There is no countdown. The action freezes during maths. Wrong answers do not cost hearts. “Walk me through it” hides the main answer choices and requires a correct input for each step before revealing the next. Only after all steps are checked does the complete solution appear. Fractions accept equivalent fractions or decimals; symbolic formula steps accept the requested expression with flexible spacing and minus-sign notation. They do not perform general symbolic algebra equivalence checking.

Progress, selected equipment, escape distance, scratch work and checked steps are saved locally. Continue restores lives and preserves recovered items. Storage failure falls back to a playable session. The Advanced game uses its own `spyacademy.advanced.*` keys. Practice Record reports independent and assisted work and retains the last 40 completed problems. All operations can also be selected directly.

## Verification

The game requires no test packages to play. The optional developer checks require Node and Python with Playwright plus Chromium:

```sh
node tests/math_bank.cjs
python tests/browser_game.py
python tests/mobile_offline.py
```

If needed for a fresh test environment: `python -m pip install playwright` and `python -m playwright install chromium`. The test scripts use `CHROMIUM_PATH`, a system `chromium`, or Playwright's installed Chromium. Each browser test starts and stops its own HTTP server.

The maths suite checks 10,200 seeded variants against independent answer calculations and 38,700 guided inputs. Browser checks cover a full mission through actual controls, maths gating and saved steps, all 51 template/tier forms, weapons and gadgets, all five escape types, phone input and scrolling, blocked/corrupt storage, and offline rendering of the complete HTML without a network connection. The managed test browser blocks `file://` navigation by policy, so that URL scheme is not covered by the automated checks.

Rendering, sound and game logic are procedural and contained in the HTML. The documentation and tests are development aids; only `index.html` needs to be served.
