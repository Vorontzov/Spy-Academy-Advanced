# Spy Academy Advanced

A standalone browser spy adventure with **96 operations**, maths from the first level, towers from 8 to 34 floors, and playable vehicle escapes. The complete game is in **`index.html`**: no build, server backend, Python runtime, external assets, accounts or API keys.

The maths generators are based on selected topics in the user's uploaded worksheets. This is an expanding curriculum, not a transcription of every supplied problem. See [CURRICULUM.md](CURRICULUM.md) for the sequence and authoring contract and [SOURCES.md](SOURCES.md) for the source mapping and remaining material.

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
| X or Z      | Fire (takedown when unarmed)                                      |
| Q           | Cycle collected weapons                                           |
| C           | Takedown; unlocked spinning kick or aerial strike                 |
| V           | Cycle cloak, EMP and grapple                                      |
| G           | Activate selected gadget; shield during escapes                   |
| B           | Call recruited ally support (Eclipse Pact / Jade Current)         |
| P or Escape | Pause/resume                                                      |
| M / F       | Sound / fullscreen                                                |

Touch controls appear below the game on smaller screens. Equipment buttons also support touch and keyboard activation. The field manual explains the mechanics.

## Missions and learning

Recover every mission case, then reach floor 01 extraction. Cases contain keycards, microchips, a cipher lens, blueprints and a black box. Every required case is a maths gate. Optional intel, medkits, shields and batteries help along the route. Stairs and grapples provide alternatives to elevators; later operations introduce faster and armored patrols. EMP barrels produce area stun explosions.

Environments include academy headquarters, dungeons, rooftop outposts, laboratories, a harbor, a citadel and a skybase. Every infiltration is followed by a playable car, motorcycle, boat, helicopter, plane or parachute escape. These are compact scrolling stages: steer, clear hazards, collect beacons and reach the end of the route. They are arcade interpretations, not vehicle simulators.

**Shadow Atlas (operations 25–36)** adds Arctic bunkers, Venetian palazzos, desert outposts, jungle temples, underwater stations and a volcanic fortress. Each mission has five named objectives: obtain an access item, recover evidence or rescue a contact, disable defenses, secure an artifact, and transmit the evidence. The on-screen tracker gives the next destination and floor. Rescues trigger an extraction beacon; they do not require escorting an NPC.

Objectives have prerequisites. The override disables timed floor traps and removes the villain’s shield. Artifacts restore one heart and refill energy. Defeat the local villain before unlocking the final transmission. Rangers fire three-shot volleys, duelists telegraph a charge, and engineers call up to two reinforcements. Brawlers fight at close range; snipers show an aiming line before a faster shot. Ice adds braking distance in the Arctic; other locations have different scenery and the shared warning/active/off trap cycle.

Operations 27 and 31 start unarmed: **C**, **X** or **Z** performs a takedown until a weapon is recovered. Other Shadow Atlas missions start with the pulse pistol. Four optional caches contain the scatter blaster, ion rail, ricochet disc and arc launcher. The ion rail penetrates guards and costs 8 energy; the disc rebounds once and costs 6. Energy regenerates, and **Q** cycles only the weapons recovered during the mission. The first 24 operations retain their original three-weapon loadout and infiltration progression.

**Phantom Circuit (operations 37–60)** adds 24 adventures across eight settings: Prague's clockwork museum, Tokyo's neon bazaar, Istanbul's grand exchange, Singapore's sky gardens, a Swiss mountain rail terminal, a Scottish storm citadel, an Atacama observatory and a stratospheric relay. Recover an orrery key, a covert camera, a depth compass and other named artifacts; rescue contacts, disable defenses and confront each location's villain. These missions build on the five-objective chains, acquired weapons and three villain styles introduced in Shadow Atlas. Operations 37, 44, 49 and 56 begin unarmed. Towers grow from 14 to 30 floors, with villain armor capped at 14 pulse-pistol hits.

Each new operation introduces one problem family at three tiers, interleaved with two review gates: **120 additional required maths tasks**. The sequence moves through fraction conversions, percent applications, tax and discounts, commissions, profit, means and weighted averages, signed numbers, distributed and fractional equations, literal equations, elimination, factorable quadratics and checking radical solutions. Money questions state their rounding rules; radical guides require checking a candidate in the original equation. A chapter-grouped mission selector makes the expanded campaign easier to browse. Existing operation definitions, seeded questions and save keys are preserved.

**Eclipse Pact (operations 61–78)** adds 18 missions across Luxor's Meridian Pyramid, Jaipur's Mirror Palace, the Paris catacombs, a Bhutanese monastery, Cappadocia's buried observatory and the Eclipse airship above the Aegean. The three lowest floors become cellar galleries or lower decks. The final tower has 32 floors. Recover artifacts including a Sun Compass, Mirror Mask and Dawn Core to stop the Eclipse network from jamming emergency communications. These stakes are part of the story; there is still no mission deadline.

The second objective recruits a companion who stays with you for that mission. **Nova**, your partner and field engineer, supplies an ion rail; **B** grants five seconds of protection and 45 gadget energy. **Ibis**, a scout, supplies a ricochet disc and grants six seconds of cloak, highlighting the path to the next maze objective while underground. **Rook**, a rival in a temporary alliance, supplies a scatter blaster; his support grants three seconds of protection and stuns nearby enemies or damages an exposed villain. In the maze, Rook stuns its sentinels. Support recharges over 14 seconds of active play. The ally button works on touch screens too. Companions follow visually and provide these commanded abilities; they are not independent escort AI and cannot be lost to enemy fire.

The artifact door leads to a **playable top-down labyrinth**. Find the diamond sigil, then reach the green OUT tile before returning to solve the artifact's maths lock. Arrows move, FIRE or melee stuns nearby sentinels, and B calls support. At IN, JUMP returns to the tower without discarding the sigil. Mazes have walls, branching paths, patrolling sentinels, and distinct deterministic layouts. Continues restore lives at the maze entrance while keeping the sigil; a reload restores the saved maze position. Patrols reset on reload. Tower gadgets are inactive inside the maze; the maze's stun action and ally support are available.

New villain styles add tactical attacks. **Wardens** block hits during windup and attack, then expose themselves during recovery; their shockwaves travel low enough to jump. **Hunters** telegraph a charge, fire a volley and dash across the arena. **Saboteurs** mark three locations before delayed floor blasts, which can be avoided or jumped. At half armor they shorten the delay between attack cycles while keeping the warnings and recovery windows. Their initial objective shield still requires the defense override. Armor ranges from 12 to 16; allies and acquired weapons help with the tougher encounters.

The chapter adds **90 maths gates and 18 generators**: compass-based triangle construction and its length consequences, triangle bounds and side ordering, two-step and multi-step inequalities, absolute-value ranges, dependent/inconsistent systems, square-root and zero-product methods, nonmonic and repeated-root quadratics, the quadratic formula, discriminants and quadratic inequalities. Geometry questions include labeled diagrams. Inequality guides check signs, interval selection and endpoint inclusion; formula guides require calculations before the exact radical expression. Source overlaps and adaptations are documented in the curriculum.

**Jade Current (operations 79–96)** adds 18 missions in six settings: Suzhou's Lantern Canal, Kyoto's fictional Kestrel Castle, Kaohsiung's Meridian Steelworks, Singapore's Stormbreak Harbor, Guilin's Cloud Lantern Observatory and Okinawa's Typhoon Skyport. The final tower has 34 floors. Recover a tidal key, evacuation ledger, coolant canister, rescue cable and Jade Transmitter to stop Director Crosswind from diverting a rescue fleet. Nova, Ibis and Rook return with their existing support abilities.

Each artifact door now leads into a **playable side-view interior**, with platforms, ladders, two additional maths panels, close-combat guards and timed machinery. Press **E/UP** at the door to enter; solve the middle-platform safety panel, then the upper evidence seal. Return through the bottom-left door with E. You can backtrack before finishing. Interior panels, scratch work and checked calculations survive reloads and continues; reloads place you at the safe entrance. The safety panel stops room machinery; securing both panels restores one heart and opens the artifact's tower lock.

New opponents use knives, swords, machetes and kung fu, with different strike ranges, warning times, dashes and recovery windows. Optional caches add a **shock knife**, **stun sword** and **rescue machete**: Q selects them, FIRE swings them. The knife attacks quickly, the sword reaches farther, and the machete hits harder but recovers slowly. All attacks are non-graphic stuns. Aircraft and boats use mounted ranged weapons when the selected tower weapon is a blade.

Solve the first training lock in mission **79** to earn **rising jump**; in **80**, **spinning kick**; in **81**, **aerial strike**. Hold **UP + Space/JUMP** to rise to the floor above. An ordinary jump still clears opponents without changing floors. **C** strikes both sides with an unlocked ground spin or reaches below you during an unlocked aerial attack. Starting a later Jade mission directly awards its prerequisite skills after its first lock. Skills persist on the device and apply in Jade Current; the earlier chapters keep their existing movement.

Steelworks, dockyard and skyport towers have working conveyors and presses. Machinery gives a visible warning before a strike; move away or jump clear. The tower safety override stops its machinery, while each room has its own safety panel. **Boat escapes** add river banks, patrol launches, buoys, wakes and a changing lateral current. Jade airplane and helicopter escapes add crosswinds. Arrows steer against drift, X clears hazards, G shields, and Space boosts. These remain compact arcade escapes; the flight controls extend the existing aircraft stages.

The new chapter adds **18 math generators and 126 required gates**, based on selected material from the 12 latest PDFs: mixed-number supplies, consecutive integers, coins and ticket systems, interest, fraction reconstruction, age models, dilution and blends, combined work, aircraft rendezvous and pursuit, river round trips, Pythagorean routes, trapezoid roofs, reservoir volume and conditional probability. Every worked solution requires checked input at each step.

**Maths on the move:** every car and motorcycle escape has two engineering checkpoints. On a motorcycle, steer toward the numbered exit calculated from dispatch instructions: fractional routes, percentage routes, then intercepting a moving courier. In a car, move a valve to divide fuel between visible amber and blue tanks according to a fraction, percentage or ratio. Use arrows, tap an exit, or drag the valve; **FIRE/X** or the on-screen button commits the choice. Both checkpoints pause traffic, allow harmless retries, and award six seconds of automatic boost plus brief protection when solved. Helicopter, plane and parachute escapes keep their action controls.

“Help me calculate” requires a correct input for each intermediate calculation, then returns control of the route or valve to the learner. Vehicle tasks contribute to the same Practice Record and save their checked steps. Existing escape saves skip checkpoints already passed. Their topic progression uses operations 1–6, 7–16 and 17–96, independently of the tower’s current topic.

There is no countdown. The action freezes during maths. Wrong answers do not cost hearts. “Walk me through it” hides the main answer choices and requires a correct input for each step before revealing the next. Only after all steps are checked does the complete solution appear. Fractions accept equivalent fractions or decimals; symbolic formula steps accept the requested expression with flexible spacing and minus-sign notation. They do not perform general symbolic algebra equivalence checking.

Progress, acquired weapons, villain armor, selected equipment, escape distance, scratch work and checked steps are saved locally. Continue restores lives and preserves recovered items. Storage failure falls back to a playable session. The Advanced game uses its own `spyacademy.advanced.*` keys. Practice Record reports independent and assisted work and retains the last 40 completed problems. All operations can also be selected directly.

## Verification

The game requires no test packages to play. The optional developer checks require Node and Python with Playwright plus Chromium:

```sh
node tests/math_bank.cjs
python tests/browser_game.py
python tests/shadow_atlas.py
python tests/phantom_circuit.py
python tests/eclipse_pact.py
python tests/jade_current.py
python tests/vehicle_maths.py
python tests/mobile_offline.py
```

If needed for a fresh test environment: `python -m pip install playwright` and `python -m playwright install chromium`. The test scripts use `CHROMIUM_PATH`, a system `chromium`, or Playwright's installed Chromium. Each browser test starts and stops its own HTTP server.

The maths suite checks 58,800 seeded variants against independent answer calculations and 275,100 guided inputs. Browser checks cover a full mission through actual controls, maths gating and saved steps, all 294 template/tier forms, weapons and gadgets, all six escape types, all 36 Shadow Atlas/Phantom Circuit operations and 180 objective locks, the 30-floor lift/stair route, the 96-operation finale, Eclipse Pact’s 90 additional gates and all 18 actual maze routes, three companion abilities/gifts and their persistence, new villain telegraphs/defenses/blasts/overdrive, maze firing/damage/pause/continuation, new fractional/system/radical saves and phone guides, Jade Current’s 126 gates and actual interior routes, saved martial-arts unlocks and floor-height jump physics, four melee opponent styles, blade caches, working machinery, boat currents and flight crosswinds, interior scratch/step/continue/reload behavior, villain attack patterns and persistence, weapon caches/piercing/ricochet, trap timing and ice, both vehicle interfaces and six road-problem families, phone input and scrolling, blocked/corrupt storage, and offline rendering of the complete HTML without a network connection. The managed test browser blocks `file://` navigation by policy, so that URL scheme is not covered by the automated checks.

Rendering, sound and game logic are procedural and contained in the HTML. The documentation and tests are development aids; only `index.html` needs to be served.
