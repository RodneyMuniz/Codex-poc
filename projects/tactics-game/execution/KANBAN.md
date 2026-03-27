# Tactics Game Kanban

This file is rendered from `sessions/studio.db`. Do not use it as the source of truth.

## Backlog

### Define progression or base layer concept after the tactical POC proves fun.
- ID: TG-050
- Kind: request
- Status: backlog
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: Define progression or base layer concept after the tactical POC proves fun.

### Define future mission types such as capture flag, rescue VIP, capture chest, and kill target.
- ID: TG-051
- Kind: request
- Status: backlog
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M4 - Content, AI, And Expansion Lanes
- Details: Define future mission types such as capture flag, rescue VIP, capture chest, and kill target.

### Plan future tactical depth expansion such as larger unit footprints, obstacle tiles, and additional classes.
- ID: TG-052
- Kind: request
- Status: backlog
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M4 - Content, AI, And Expansion Lanes
- Details: Plan future tactical depth expansion such as larger unit footprints, obstacle tiles, and additional classes.

### Separate delivery-path evaluation from current range checks
- ID: TG-064
- Kind: request
- Status: backlog
- Owner: Architect / Gameplay Systems Planner
- Assigned Role: Architect / Gameplay Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M2 - Combat Model Expansion Foundations
- Details: Plan the future engine change that splits delivery-path evaluation from the current single-pass targeting or range logic.

Scope In:
dependency planning, engine-boundary planning, future implementation sequencing.

Scope Out:
implementation, live mechanic changes, balance tuning, AI, UI polish.

Acceptance Criteria:
- A future task exists for splitting delivery-path evaluation from current range checks.
- The dependency on metadata and blocker-tag groundwork is recorded.
- The task preserves current mechanics until explicitly implemented later.
- Review Notes: This is the first likely future implementation-sized task once the metadata and blocker vocabulary are ready.

### Introduce damage-family-aware action profiles for physical and magical attacks
- ID: TG-065
- Kind: request
- Status: backlog
- Owner: Architect / Combat Systems Planner
- Assigned Role: Architect / Combat Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M2 - Combat Model Expansion Foundations
- Details: Plan the future action-profile split that lets physical and magical attacks use different blocker and dodge assumptions under the approved `TG-058` baseline.

Scope In:
action-family planning, future migration notes, dependency planning.

Scope Out:
implementation, damage balancing, AI changes, UI polish, resistances, wards, or reflection systems.

Acceptance Criteria:
- A future task exists for physical-vs-magical action-profile separation.
- The approved baseline that magical damage is unblockable and undodgeable is preserved.
- Deeper magic-defense ideas remain outside this task.
- Review Notes: This future task should deliver the approved family split without swallowing later defense-system expansion.

### Add future combat feedback states for visible, blocked, and actionable targets
- ID: TG-066
- Kind: request
- Status: backlog
- Owner: Designer / UI Systems Planner
- Assigned Role: Designer / UI Systems Planner
- Priority: low
- Requires Approval: yes
- Review State: None
- Milestone: M2 - Combat Model Expansion Foundations
- Details: Plan the future UI feedback needed so players can understand visible-but-blocked versus fully actionable targets once the combat model expands.

Scope In:
state naming, tooltip wording, overlay-state planning, future UI sequencing.

Scope Out:
implementation, visual polish, combat-rule changes, AI.

Acceptance Criteria:
- A future task exists for clarifying visible, blocked, and actionable target states.
- The task clearly depends on the underlying combat-model split rather than preceding it.
- No current UI behavior changes are implied by this ticket.
- Review Notes: This should happen after the shared combat-model split is stable enough to expose clear player feedback states.

### Plan deeper magical-defense systems as separate future tasks
- ID: TG-067
- Kind: request
- Status: backlog
- Owner: Designer / Systems Planner
- Assigned Role: Designer / Systems Planner
- Priority: low
- Requires Approval: yes
- Review State: None
- Milestone: M2 - Combat Model Expansion Foundations
- Details: Keep wards, resistances, anti-magic exceptions, reflection, absorption, or similar systems explicitly separated from the approved `TG-058` baseline.

Scope In:
future backlog shaping, naming candidate defense subsystems, documenting separation boundaries.

Scope Out:
implementation, balance tuning, current-release mechanics changes.

Acceptance Criteria:
- A future task exists to shape deeper magical-defense work separately from the approved physical-vs-magical baseline.
- The boundary between approved baseline rules and later defense-system expansion is documented.
- No current combat rules are changed.
- Review Notes: This task exists mainly to prevent future scope creep from reopening `TG-058`.

### Design invincible-status and indestructible-object rules for future releases
- ID: TG-069
- Kind: request
- Status: backlog
- Owner: Designer / Systems Planner
- Assigned Role: Designer / Systems Planner
- Priority: low
- Requires Approval: yes
- Review State: None
- Milestone: M2 - Combat Model Expansion Foundations
- Details: Define how future invincible status and indestructible objects should behave so magical and physical attacks can interact with them cleanly later.

Scope In:
future rule shaping for invincible status, indestructible walls or objects, boundary between damage immunity and targetability, documenting open questions.

Scope Out:
implementation, current-release mechanic changes, balance tuning, AI changes.

Acceptance Criteria:
- A future task exists for defining invincible-status behavior separately from the first magical-damage slice.
- The boundary between targetable-but-immune and untargetable entities is documented for future work.
- The task remains separate from the first Pyromancer implementation slice.
- Review Notes: Created from the user's note that walls may later share an invincible concept with future units or statuses, but that concept should remain open for a near-future design pass rather than being solved inside the first magical-damage implementation slice.

### Design future saved deployment loadouts and formation presets
- ID: TG-084
- Kind: request
- Status: backlog
- Owner: Product Designer / Preparation Systems Planner
- Assigned Role: Product Designer / Preparation Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: define a future system for saved deployment layouts or loadouts so players can keep aggressive, defensive, combo-oriented, or other preferred battlefield presets.

Scope In:
saved layout concept, when layouts should be selectable, relation to future army growth, clear non-goals for Milestone 1.

Scope Out:
implementation, persistence technology, cloud sync, final UX polish.

Acceptance Criteria:
- the future loadout idea is captured durably
- the design explains why this belongs after the current prototype milestone
- the idea is separated clearly from current setup implementation work
- Review Notes: Created from the operator's desire for players to keep several preferred layouts later, such as aggressive, defensive, or combo-focused preparations.

### Define a local-first persistence and storage strategy for progression
- ID: TG-095
- Kind: request
- Status: backlog
- Owner: Solution Architect / Persistence Planner
- Assigned Role: Solution Architect / Persistence Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: define how progression and profile data should be stored as the project grows beyond a pure sandbox while staying local-first for now.

Scope In:
local persistence options, browser storage strategy, growth expectations, swap-friendly storage boundary, future cloud-readiness notes.

Scope Out:
implementation, backend deployment, account systems, cloud sync rollout.

Acceptance Criteria:
- a clear local-first persistence recommendation exists
- the recommendation explains why localStorage, IndexedDB, or later alternatives fit the project at each stage
- the output keeps cloud optional rather than mandatory
- Review Notes: Created because progression, roster growth, and mission results will soon need a real persistence strategy.

### Define the first AI controller architecture for local tactical play
- ID: TG-096
- Kind: request
- Status: backlog
- Owner: Solution Architect / AI Systems Planner
- Assigned Role: Solution Architect / AI Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M4 - Content, AI, And Expansion Lanes
- Details: define how local tactical AI should interact with the engine so scripted and heuristic opponents can be added later without coupling decision-making to UI code.

Scope In:
AI-controller boundary, legal-action interface, local-first feasibility, first heuristic path, mission-loop implications.

Scope Out:
implementing a smart opponent, LLM integration, online matchmaking, training systems.

Acceptance Criteria:
- a durable AI architecture note exists
- the note keeps AI using the same engine action interface as human control
- the first local AI path is clear enough to guide later implementation
- Review Notes: Added when the operator explicitly asked how AI could be implemented locally and what should be considered now.

### Define the first asset-pipeline and design-tooling architecture
- ID: TG-097
- Kind: request
- Status: backlog
- Owner: Art Director / Asset Systems Planner
- Assigned Role: Art Director / Asset Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M4 - Content, AI, And Expansion Lanes
- Details: define the first architecture for handling source art, exported assets, naming, metadata, and tool choices before the game starts accumulating larger visual content.

Scope In:
source versus export discipline, naming conventions, metadata expectations, likely early tools, long-term isometric and card-art implications.

Scope Out:
production art creation, outsourcing, final style lock, asset marketplace selection.

Acceptance Criteria:
- a durable asset-pipeline recommendation exists
- the recommendation separates source files from game-ready exports
- naming and metadata discipline are explicit enough for future asset growth
- Review Notes: Added because visual direction, unit cards, and isometric ambitions will create asset-management pressure long before full production art begins.

### Define the first housing and base-capacity progression packet
- ID: TG-088
- Kind: request
- Status: backlog
- Owner: Product Designer / Base Systems Planner
- Assigned Role: Product Designer / Base Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: turn the housing portion of the progression vision into a small durable packet covering starting house state, upgrade steps, total capacity growth, and the first bounded cap for roster points.

Scope In:
starting house state, number of houses, upgrade steps, per-house capacity values, total cap recommendation, relation to roster-size pacing.

Scope Out:
implementation, UI flow, save system, visual base-building presentation, final balance tuning.

Acceptance Criteria:
- the house-and-capacity progression model is captured clearly
- the starting state and end-state cap are explicit
- the packet is small enough to guide later implementation or balancing tasks
- Review Notes: Split from `TG-083` so the housing and roster-capacity model can later move independently from the broader progression vision.

### Define the first class-unlock and recruitment rules packet
- ID: TG-090
- Kind: request
- Status: backlog
- Owner: Product Designer / Roster Systems Planner
- Assigned Role: Product Designer / Roster Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: define how class-unlock buildings and first recruitment costs should work in the first progression pass.

Scope In:
Barracks, Church, Magic School, unlock-only behavior, first recruitment costs, relation to future rarity and chance-based acquisition.

Scope Out:
implementation, full rarity system, pack-opening mechanics, final class catalog, balancing all future units.

Acceptance Criteria:
- class-unlock buildings and their first recruitment rules are captured clearly
- the current expensive-but-testable unlock philosophy is preserved
- later rarity or chance systems remain explicitly deferred
- Review Notes: Split from `TG-083` so building unlocks and recruitment rules can later become their own implementation or balancing sequence.

### Define the Fountain fallback and anti-softlock economy rule
- ID: TG-091
- Kind: request
- Status: backlog
- Owner: Product Designer / Economy Safety Planner
- Assigned Role: Product Designer / Economy Safety Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: define the zero-gold recovery rule so progression testing never hard-locks the player out of basic play.

Scope In:
Fountain fallback behavior, zero-gold trigger, recovery amount, repeatability assumptions, anti-softlock purpose.

Scope Out:
implementation, final economy abuse prevention, narrative treatment, full admin tooling.

Acceptance Criteria:
- the fallback rule is captured clearly
- the design explains why this exists for testing and loop safety
- the rule is explicit enough for later implementation
- Review Notes: Split from `TG-083` because the fallback rule is a specific economy-safety mechanic rather than only a broad vision idea.

### Plan the first AI-friendly progression mission loop for resource testing
- ID: TG-092
- Kind: request
- Status: backlog
- Owner: Product Designer / Mission Systems Planner
- Assigned Role: Product Designer / Mission Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: define the first mission loop that can support progression testing against AI or otherwise winnable content, so the economy is not blocked on PvP-only outcomes.

Scope In:
repeatable mission-loop concept, relation to AI or safe test opponents, how progression rewards should enter the loop, testing-oriented assumptions.

Scope Out:
full AI implementation, final campaign map, mission scripting engine, final reward balancing.

Acceptance Criteria:
- the progression loop is no longer dependent only on PvP-style matches
- the design captures how players can reliably earn some resources during testing
- the output is clear enough to guide later AI or PvE planning
- Review Notes: Created from the operator's point that a wager-based economy needs missions or AI-facing content where players can realistically secure some wins and keep progression moving.

### Define admin economy multiplier controls for progression testing
- ID: TG-093
- Kind: request
- Status: backlog
- Owner: Product Designer / Testing Tools Planner
- Assigned Role: Product Designer / Testing Tools Planner
- Priority: low
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: define the first test-only multiplier controls so progression pacing can be accelerated during development without rewriting the underlying economy rules.

Scope In:
multiplier options such as `1x`, `2x`, `5x`, `10x`, `50x`, intended use in testing, variable-driven economy requirement, anti-confusion notes.

Scope Out:
implementation, final player-facing admin tools, security, live-service controls.

Acceptance Criteria:
- a clear testing-only multiplier concept exists
- the design keeps the multiplier separate from the real economy model
- the multiplier options are explicit enough for later implementation
- Review Notes: Split from `TG-083` because faster progression testing should be treated as a separate controllability requirement, not buried inside the base economy note.

### Define the first gold economy and wager loop packet
- ID: TG-089
- Kind: request
- Status: backlog
- Owner: Product Designer / Economy Systems Planner
- Assigned Role: Product Designer / Economy Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: turn the first gold-only economy into a durable packet covering wager logic, victory flow, net gain or loss logic, and first-pass building costs.

Scope In:
gold-only economy, wager framing, win/loss examples, first-pass building costs, tuning guardrails, variable-first design.

Scope Out:
implementation, multi-resource economy, final grind balance, live monetization or online economy.

Acceptance Criteria:
- the gold economy and wager loop are captured clearly
- first-pass costs are explicit and easy to tune later
- the packet remains simple enough for early testing rather than pretending to be final balance
- Result: Held behind `TG-083` and `TG-094` so the first gold loop fits the broader progression architecture.
- Review Notes: Moved back to backlog by roadmap decision. Re-open after the long-term roster vision and modular architecture review are accepted.

### Revisit in-battle tile object composition and anchor placement
- ID: TG-118
- Kind: request
- Status: backlog
- Owner: Designer / Battlefield UX Planner
- Assigned Role: Designer / Battlefield UX Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: Capture the follow-up needed for live battle tiles now that the board and badge pass is functional. Objects and markers inside occupied tiles currently read as centered stacks rather than deliberately composed pieces. This future pass should revisit how battlefield pieces anchor within the tile, which signals deserve edge or corner placement, and how mixed tile contents should stay readable without waiting for the full art pipeline.
- Review Notes: Logged from live operator review after the latest battle-mode cleanup pass.

### Revisit battle roster and player-card layout for armies above five units
- ID: TG-119
- Kind: request
- Status: backlog
- Owner: Designer / Battle HUD Planner
- Assigned Role: Designer / Battle HUD Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: Capture the follow-up needed for the in-battle roster/card surface now that setups can exceed five units. The current player-card presentation no longer scales well once armies grow beyond the original smaller roster size. This future pass should redesign the battle roster so larger squads remain scannable, useful, and space-efficient during live play.
- Review Notes: Logged from live operator review after larger-army setup became playable.

### Integrate a Phaser battlefield shell into the React app
- ID: TG-120
- Kind: request
- Status: backlog
- Owner: Gameplay Renderer Implementer
- Assigned Role: Gameplay Renderer Implementer
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M10 - TacticsGame Isometric Vertical Slice
- Expected Artifact: projects/tactics-game/app/src/ui/phaser/BattlefieldScene.ts
- Details: Introduce a Phaser-powered battlefield surface inside the existing React application shell so the renderer transition can begin without replacing the surrounding setup and HUD layers all at once.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement isometric coordinate transform and input mapping
- ID: TG-121
- Kind: request
- Status: backlog
- Owner: Gameplay Renderer Implementer
- Assigned Role: Gameplay Renderer Implementer
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M10 - TacticsGame Isometric Vertical Slice
- Expected Artifact: projects/tactics-game/app/src/ui/phaser/isometric.ts
- Details: Add the first isometric coordinate and input-mapping layer so the game can translate between board-state cells and an isometric battlefield presentation without changing core combat logic.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add authored board import for the first isometric map
- ID: TG-122
- Kind: request
- Status: backlog
- Owner: Technical Artist
- Assigned Role: Technical Artist
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M10 - TacticsGame Isometric Vertical Slice
- Expected Artifact: projects/tactics-game/app/src/engine/data/isometricBoard.json
- Details: Add the first authored board import path for an isometric battlefield so map shape and terrain composition can come from an external map authoring step instead of being implied only by the current DOM grid.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement unit anchor, depth, and facing presentation
- ID: TG-123
- Kind: request
- Status: backlog
- Owner: Technical Artist
- Assigned Role: Gameplay Renderer Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M10 - TacticsGame Isometric Vertical Slice
- Expected Artifact: projects/tactics-game/app/src/ui/phaser/BattlefieldScene.ts
- Details: Define how units sit on isometric tiles, resolve depth ordering, and present facing in a readable way. The first pass should make the battlefield legible before chasing full production-quality animation.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Consume approved visual artifacts in the runtime
- ID: TG-124
- Kind: request
- Status: backlog
- Owner: Gameplay Renderer Implementer
- Assigned Role: Gameplay Renderer Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M10 - TacticsGame Isometric Vertical Slice
- Expected Artifact: projects/tactics-game/app/src/ui/phaser/assetManifest.ts
- Details: Wire the renderer to approved visual artifact manifests instead of relying on ad hoc asset placement. The first pass should prove that reviewed visual outputs can become explicit runtime inputs.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add the first skill VFX and SFX hook
- ID: TG-125
- Kind: request
- Status: backlog
- Owner: Developer
- Assigned Role: Developer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M10 - TacticsGame Isometric Vertical Slice
- Expected Artifact: projects/tactics-game/app/src/ui/phaser/effects.ts
- Details: Add the first integrated visual and sound-effect hook to a skill path so the vertical slice starts to feel like a real game instead of a presentation-only renderer shift.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Prove the isometric vertical slice through QA and operator review
- ID: TG-126
- Kind: request
- Status: backlog
- Owner: QA
- Assigned Role: QA
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M10 - TacticsGame Isometric Vertical Slice
- Expected Artifact: projects/tactics-game/artifacts/isometric_vertical_slice_proof.md
- Details: Record the first vertical-slice proof for the isometric renderer path, including operator review, runtime checks, and evidence that the new presentation feels materially closer to a real game.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Define the deterministic local bot architecture
- ID: TG-127
- Kind: request
- Status: backlog
- Owner: Gameplay AI Designer
- Assigned Role: Gameplay AI Designer
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M11 - Gameplay AI And Encounter Quality
- Expected Artifact: projects/tactics-game/governance/LOCAL_BOT_ARCHITECTURE.md
- Details: Define the first deterministic local bot architecture so enemy turns, heuristics, and evaluation loops can be implemented without relying on live model calls. The first pass should describe how the bot selects legal actions, difficulty modifiers, and debug outputs.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement the local bot framework skeleton
- ID: TG-128
- Kind: request
- Status: backlog
- Owner: Gameplay AI Developer
- Assigned Role: Gameplay AI Developer
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M11 - Gameplay AI And Encounter Quality
- Expected Artifact: projects/tactics-game/app/src/engine/ai/localBot.ts
- Details: Build the first deterministic local bot skeleton that can enumerate legal actions and prepare future heuristic scoring. This should be a real gameplay runtime layer, not a speculative design document.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add bot telemetry and debug review
- ID: TG-129
- Kind: request
- Status: backlog
- Owner: Gameplay AI Developer
- Assigned Role: Gameplay AI Developer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M11 - Gameplay AI And Encounter Quality
- Expected Artifact: projects/tactics-game/app/src/app/presentation/createAiDebugViewModel.ts
- Details: Add operator-usable telemetry and debug review for the deterministic bot so decision quality can be inspected without reading raw engine internals. The first pass should support basic move reasoning, priority visibility, and failure diagnosis.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement difficulty tiers
- ID: TG-130
- Kind: request
- Status: backlog
- Owner: Gameplay AI Developer
- Assigned Role: Gameplay AI Developer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M11 - Gameplay AI And Encounter Quality
- Expected Artifact: projects/tactics-game/app/src/engine/ai/difficultyProfiles.ts
- Details: Add multiple deterministic difficulty tiers so the local bot can behave differently across easy, normal, and hard modes without changing the fundamental runtime model.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Prove AI playtest quality and balancing evidence
- ID: TG-131
- Kind: request
- Status: backlog
- Owner: QA
- Assigned Role: QA
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M11 - Gameplay AI And Encounter Quality
- Expected Artifact: projects/tactics-game/artifacts/ai_playtest_evidence.md
- Details: Record playtest and balancing evidence for the deterministic bot so the studio can judge encounter quality from actual runs instead of intuition. The first pass should capture strengths, failures, and tuning priorities.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

## Ready for Build

### Review the architecture for progression-friendly modular growth
- ID: TG-094
- Kind: request
- Status: ready
- Owner: Solution Architect / Systems Planner
- Assigned Role: Solution Architect / Systems Planner
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: analyze the current code and documentation structure to confirm how progression, persistence, AI, and richer content can be added without creating expensive coupling later.

Scope In:
architecture review, boundary recommendations, module split recommendations, risk identification, durable architecture notes.

Scope Out:
implementation, full refactor, backend deployment, final database selection rollout.

Acceptance Criteria:
- a durable architecture review exists for the current implementation
- the review identifies the most important coupling risks
- the review recommends clean future boundaries for tactical, progression, mission, persistence, AI, and presentation layers
- Result: Promoted as the M3 architecture gate for progression-friendly modular growth.
- Review Notes: Ready for Build after roadmap approval. This task should shape the architecture boundary before heavier progression planning.

### Add future combat action-profile metadata for visibility, targetability, delivery path, and damage family
- ID: TG-062
- Kind: request
- Status: ready
- Owner: Architect / Systems Planner
- Assigned Role: Architect / Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M2 - Combat Model Expansion Foundations
- Details: Define the future action-profile fields needed to support the approved separation between visibility, targetability, delivery path, and damage family.

Scope In:
field naming, ownership boundaries, documentation updates, future schema planning.

Scope Out:
implementation, live-rule changes, balance tuning, AI changes, UI polish.

Acceptance Criteria:
- A future task packet exists for introducing action-profile metadata cleanly.
- The planned metadata matches the approved `TG-058` terminology.
- The task stays documentation/planning-only until explicitly implemented later.
- Review Notes: First follow-through task after `TG-058`; keeps the terminology layer separate from live mechanics.

### Generalize blocker tags for units, walls, and high grass
- ID: TG-063
- Kind: request
- Status: ready
- Owner: Architect / Systems Planner
- Assigned Role: Architect / Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M2 - Combat Model Expansion Foundations
- Details: Plan the future blocker-tag model so delivery and visibility systems can query board blockers without hardcoding special cases.

Scope In:
blocker vocabulary, ownership boundaries between board objects and action profiles, planning notes.

Scope Out:
implementation, live LOS changes, AI changes, UI polish, balance tuning.

Acceptance Criteria:
- A future task exists for converting current blockers into reusable blocker tags.
- Units, walls, and high grass are accounted for in the planned blocker vocabulary.
- The task remains separate from live rules changes.
- Review Notes: Second follow-through task after `TG-058`; prepares the board/object layer for future LOS and delivery work.

## In Progress

### Define the long-term army-growth and roster-acquisition vision
- ID: TG-083
- Kind: request
- Status: in_progress
- Owner: Product Designer / Meta Systems Planner
- Assigned Role: Product Designer / Meta Systems Planner
- Priority: medium
- Requires Approval: no
- Review State: In Review
- Milestone: M3 - Progression And Meta-Loop Foundation
- Details: define the future vision where players begin with a very small roster and gradually earn additional units over time, so the tactical game grows toward an army-building identity instead of assuming an effectively infinite bench.

Scope In:
starting roster concept, future unit acquisition loop, relation between tactical wins and army growth, what stays out of Milestone 1, durable vision notes.

Scope Out:
implementation, economy tuning, save systems, campaign structure, multiplayer.

Acceptance Criteria:
- the small-starting-army vision is captured durably
- future unit acquisition is framed clearly enough for later milestone planning
- the note explains why this is later than Milestone 1
- the output can guide future progression and roster tasks without forcing implementation now
- Review Notes: Drafting is now underway in `ARMY_GROWTH_VISION.md`. Current direction: keep the progression loop theme-agnostic for now, treat the player as the leader of a persistent team, reward victories with later-theme-adjustable resource types, grow the base and roster over time, start with a very small army, keep unit acquisition partly challenge-based and partly luck-based later, and defer permanent death into a separate future high-stakes mode rather than making it mandatory.

## In Review

### Define the first battle visual identity packet for the playable prototype
- ID: TG-098
- Kind: request
- Status: in_review
- Owner: QA
- Assigned Role: Art Director / Visual Identity Planner
- Priority: high
- Requires Approval: no
- Review State: In Review
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Expected Artifact: projects/tactics-game/app/src/styles.css
- Details: define the first cohesive visual direction for the playable prototype so the battle screen starts feeling like a real game instead of only a functional sandbox, while staying inside the current grim / medieval / metal / gore direction.

Scope In:
color direction, board-material feeling, unit marker style direction, panel mood, typography direction, art-reference framing, support for the bottom-strip card surface, and what "some art included" means for the first slice.

Scope Out:
full isometric conversion, production asset set, final art outsourcing, animation system.

Acceptance Criteria:
- a durable visual-identity packet exists for the first playable prototype
- the packet is specific enough to guide a small implementation slice
- the packet distinguishes first-pass presentation goals from long-term final art ambitions
- the packet uses the current visual keywords `grim`, `medieval`, `metal`, and `gore`
- the packet clarifies how much visual emphasis belongs on the board, the right panel, and the first card-style support surface
- Result: Approved Gilded War Table direction is now visible in the live prototype and can be reviewed directly in the running app.
- Review Notes: Live implementation completed and verified locally. Review in the running TacticsGame app.

### Implement heraldic unit tokens and stronger unit-state readability
- ID: TG-103
- Kind: request
- Status: in_review
- Owner: QA
- Assigned Role: UI Implementer / Visual Production
- Priority: high
- Requires Approval: yes
- Review State: In Review
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Expected Artifact: projects/tactics-game/app/src/ui/react/App.tsx
- Details: Upgrade live battlefield unit presentation with heraldic token treatment, clearer class identity, and cleaner status readability.

Scope In:
class markers, side identity, leader and VIP treatment, facing treatment, hp readability, cooldown readability, and battlefield token styling.

Scope Out:
new class design, combat-balance changes, portrait art pipeline.

Acceptance Criteria:
- units are easier to distinguish at a glance
- leader, VIP, facing, hp, and cooldown remain readable
- the new token treatment feels more game-like than the current badge-based look
- Result: Heraldic token styling and stronger unit readability are now visible in the live battlefield and roster surfaces.
- Review Notes: Live implementation completed and verified locally. Review in the running TacticsGame app.

### Rebuild the battle HUD into a command-folio presentation
- ID: TG-104
- Kind: request
- Status: in_review
- Owner: QA
- Assigned Role: UI Implementer / Visual Production
- Priority: high
- Requires Approval: yes
- Review State: In Review
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Expected Artifact: projects/tactics-game/app/src/ui/react/App.tsx
- Details: Turn the current battle panels into a more game-like command folio while preserving clarity.

Scope In:
right-side battle panel hierarchy, selected-unit card treatment, objective panel treatment, turn-state readability, activity-log framing, and reduced text heaviness.

Scope Out:
new systems, progression surfaces, hidden critical information.

Acceptance Criteria:
- the battle HUD feels less text-heavy than the current pass
- the selected-unit and objective surfaces are clearer and more visual
- the activity log and battle controls still remain understandable
- Result: Battle HUD now uses a command-folio presentation with stronger hierarchy and less prototype-heavy framing.
- Review Notes: Live implementation completed and verified locally. Review in the running TacticsGame app.

### Bring setup mode into the same visual world as battle mode
- ID: TG-105
- Kind: request
- Status: in_review
- Owner: QA
- Assigned Role: UI Implementer / Visual Production
- Priority: medium
- Requires Approval: yes
- Review State: In Review
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Expected Artifact: projects/tactics-game/app/src/styles.css
- Details: Restyle setup mode so army placement and objective preparation feel like part of the game rather than a utility form.

Scope In:
setup shell, picker presentation, side summaries, action buttons, and board continuity.

Scope Out:
setup rule changes and new setup systems.

Acceptance Criteria:
- setup mode visually belongs to the same world as battle mode
- pickers and setup summaries feel more intentional and game-like
- tactical clarity remains intact
- Result: Setup mode now shares the same visual world as battle mode and is ready for review in the live app.
- Review Notes: Live implementation completed and verified locally. Review in the running TacticsGame app.

### Add restrained motion and feedback polish to the visual production pass
- ID: TG-106
- Kind: request
- Status: in_review
- Owner: QA
- Assigned Role: UI Implementer / Visual Production
- Priority: medium
- Requires Approval: yes
- Review State: In Review
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Expected Artifact: projects/tactics-game/app/src/styles.css
- Details: Add moderate motion and feedback cues that make the prototype feel more alive without overwhelming tactical readability.

Scope In:
hover lift, active-unit emphasis, selection feedback, action-readiness emphasis, panel transitions, and victory emphasis.

Scope Out:
heavy FX systems, full animation pipeline, distracting spectacle.

Acceptance Criteria:
- motion supports clarity instead of fighting it
- active and selected states feel more alive
- the app feels less static than the current prototype
- Result: Restrained motion and hover/selection polish are now active in the live UI and ready for review.
- Review Notes: Live implementation completed and verified locally. Review in the running TacticsGame app.

## Complete

### Refine the right-side battle panel so objective and rotation support feel less text-heavy and more visual
- ID: TG-101
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: UX Designer / Interface Planner
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Expected Artifact: projects/tactics-game/app/src/ui/react/App.tsx
- Details: reduce the text-heavy feeling of the current right-side battle panel while preserving its usefulness for rotation, objective reminders, and selected-unit support.

Scope In:
visual hierarchy refinement, lower-text presentation, stronger icon or status treatment, objective reminder cleanup, and rotation support presentation.

Scope Out:
full HUD redesign, card-system expansion, AI features, progression systems, battle-rule changes.

Acceptance Criteria:
- the panel feels less text-heavy than the current `TG-099` pass
- objectives and rotation support remain understandable
- the panel uses stronger visual cues instead of relying mostly on paragraphs and labels
- the change stays bounded to presentation, not rules
- Result: Right-side battle panel has been rebuilt into a more visual command folio and is ready for review in the live app.
- Review Notes: Live implementation completed and verified locally. Review in the running TacticsGame app.
Accepted by Studio Lead on 2026-03-27 after live app review.

### Define tactical battle screen flow for the first playable interface
- ID: TG-070
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: UX Designer / Player Experience Planner
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: define the first-pass player flow through the tactical battle screen so the prototype can communicate state, choices, outcomes, and battle closure clearly enough for the Milestone 2 comprehension test.

Scope In:
battle-phase screen flow, setup-to-battle transition only where needed for context, selected-unit flow, move/action/rotate flow, confirmation states, battle-end flow, compressed reward summary flow, objective reminder behavior, and visible-versus-secondary information decisions.

Scope Out:
implementation, visual polish, art direction, animation systems, menu design, progression UX.

Acceptance Criteria:
- A durable flow document exists for the tactical battle screen.
- The flow covers setup, battle start, unit selection, movement, action targeting, confirmation, resolution, and battle end.
- The flow identifies where the player needs explicit feedback or contextual guidance.
- the flow reflects the preferred move -> act -> rotate turn order
- the flow defines the battle-end surface as winner + reason + gold earned first
- Result: Accepted as a reference input to the 2026-03-25 visual production pass.
- Review Notes: No standalone review gate required. Keep as reference input for live implementation work.

### Draft a low-fidelity tactical battle screen wireframe
- ID: TG-071
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: UX Designer / Interface Planner
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: Produce a low-fidelity wireframe for the tactical battle screen that stabilizes information hierarchy before larger UI implementation work.

Scope In:
dominant board placement, right-side action panel, selected-unit area, objective status panel, turn-state panel, bottom-strip current-player card surface, end-of-battle summary surface, and treatment of secondary log visibility.

Scope Out:
implementation, polished visuals, final art style, animation, responsive-production polish.

Acceptance Criteria:
- A durable low-fidelity wireframe exists for the tactical battle screen.
- The wireframe identifies the board as the visual priority.
- The wireframe places contextual controls and supporting information without competing with the board.
- The wireframe is detailed enough for later UI implementation tickets.
- the wireframe reflects the current choice to keep the board as the overwhelming center of the screen
- the wireframe keeps the action panel on the right for now
- Result: Accepted as a reference input to the 2026-03-25 visual production pass.
- Review Notes: No standalone review gate required. Keep as reference input for live implementation work.

### Create the first tactical battle UI component inventory
- ID: TG-072
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: UX Designer / UI Systems Planner
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: Identify the reusable first-pass battle-screen components so the interface can evolve through deliberate components rather than one-off UI patches.

Scope In:
component naming, component purpose, ownership boundaries, reusable battle-screen inventory, durable documentation, and explicit inclusion of the required Milestone 2 component set.

Scope Out:
implementation, design-system expansion, final theming, animation systems.

Acceptance Criteria:
- A durable first-pass component inventory exists for the battle screen.
- The inventory covers the key board, panel, log, control, modal, and feedback components.
- The inventory is clear enough to guide future implementation slicing.
- the inventory explicitly covers: board, action panel, selected unit panel, objective status panel, turn-state panel, unit-card support surface, and end-of-battle summary
- Result: Accepted as a reference input to the 2026-03-25 visual production pass.
- Review Notes: No standalone review gate required. Keep as reference input for live implementation work.

### Define first-pass tactical feedback and interaction states
- ID: TG-073
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: UX Designer / Player Feedback Planner
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: Define the first-pass feedback states the tactical interface must communicate so players understand turn state, legality, risk, and outcome.

Scope In:
selected state, hover state, valid target state, invalid target state, ally-risk warning state, action resolution feedback, turn or phase guidance, durable documentation, and the required Milestone 2 color-only plus hit-resolution signals.

Scope Out:
implementation, final copywriting polish, animation polish, accessibility deep pass.

Acceptance Criteria:
- A durable feedback-state list exists for the tactical battle interface.
- The state list covers turn, selection, legality, risk, and outcome feedback.
- The state list is clear enough to guide later UX and implementation tasks.
- the state list explicitly covers color signals for selectable, reachable, attackable, and objective-related states
- the state list explicitly covers hit or miss, damage number, and death-state feedback after attack resolution
- Result: Accepted as a reference input to the 2026-03-25 visual production pass.
- Review Notes: No standalone review gate required. Keep as reference input for live implementation work.

### Explore the end-state isometric battlefield direction and transition path
- ID: TG-085
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Art Director / Visual Systems Planner
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: define how the project can move from the current prototype presentation toward the intended isometric end state without committing too early to a full visual conversion.

Scope In:
isometric direction goals, feasibility framing, what can be explored safely now, what should remain deferred, relation to current board readability.

Scope Out:
full implementation, engine rewrite, production asset buildout, final camera system.

Acceptance Criteria:
- the intended isometric direction is captured durably
- the document separates safe early exploration from premature implementation
- the output gives a future path instead of only an aspiration
- Result: Accepted as a reference input to the 2026-03-25 visual production pass.
- Review Notes: No standalone review gate required. Keep as reference input for live implementation work.

### Design TCG-inspired live unit cards and a per-turn roster status panel
- ID: TG-086
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: UX Designer / Combat Information Planner
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: define the first battle-side card strip so players can inspect their live roster state each turn, starting with the current player's units only and supporting later deeper character-sheet behavior.

Scope In:
bottom-strip card placement, current-player-only default, right-click enemy inspection direction, mandatory visible fields, status icon treatment, dead-card gray state, relationship to current board readability, and fit with the right action panel.

Scope Out:
implementation, final illustration production, full HUD redesign, animation system.

Acceptance Criteria:
- the unit-card vision is captured durably
- the note identifies the most important statuses to surface, such as HP, carrying VIP, marked leader, and turns left
- the design makes clear that this is future-facing rather than a Milestone 1 implementation commitment
- the packet confirms cards are visible during the current player's turn in the first pass
- the packet clarifies which information stays on the board versus moves into the card surface
- Result: Accepted as a reference input to the 2026-03-25 visual production pass.
- Review Notes: No standalone review gate required. Keep as reference input for live implementation work.

### Define the first digital-asset pipeline and art-direction brief for units, cards, and battlefield visuals
- ID: TG-087
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Art Director / Asset Pipeline Planner
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Details: define how digital assets should be conceived, maintained, and evolved for the future visual direction, including unit art, card art, sprite references, and battlefield presentation, while optimizing first for speed of experimentation and consistency.

Scope In:
art-direction framing, asset categories, source-versus-export workflow, naming conventions, metadata expectations, tool-research boundary, relation to future isometric and card concepts, and what tools are optional versus genuinely needed now.

Scope Out:
final asset creation, vendor selection, production outsourcing, full content pipeline implementation.

Acceptance Criteria:
- the first asset-pipeline questions are captured durably
- the design distinguishes future art direction from immediate implementation
- the output is usable as a starting point for later asset or tooling decisions
- the packet states clearly that early Milestone 2 planning does not require Figma or Photoshop to be installed
- the packet makes the first recommended tooling path explicit if later prep becomes worthwhile
- Result: Accepted as a reference input to the 2026-03-25 visual production pass.
- Review Notes: No standalone review gate required. Keep as reference input for live implementation work.

### Lock tactical sandbox defaults and rewrite the first playable plan around them.
- ID: TG-000
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Lock tactical sandbox defaults and rewrite the first playable plan around them.

### Choose first-slice opposing-side control mode.
- ID: TG-001
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Choose first-slice opposing-side control mode.

### Choose exact starting team size for the tactical sandbox.
- ID: TG-002
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Choose exact starting team size for the tactical sandbox.

### Confirm technology stack for the POC.
- ID: TG-003
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Confirm technology stack for the POC.

### Draft architecture boundaries for the tactical sandbox slice.
- ID: TG-004
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Draft architecture boundaries for the tactical sandbox slice.

### Draft updated data model with locked movement defaults.
- ID: TG-005
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Draft updated data model with locked movement defaults.

### Draft confirmed battle rules summary.
- ID: TG-006
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Draft confirmed battle rules summary.

### Draft tiny execution-prep task sequence.
- ID: TG-007
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Draft tiny execution-prep task sequence.

### Write board preset specification packet.
- ID: TG-010
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Write board preset specification packet.

### Write unit schema and starting roster packet.
- ID: TG-011
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Write unit schema and starting roster packet.

### Write activation and fatigue rules packet.
- ID: TG-012
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Write activation and fatigue rules packet.

### Write movement and attack legality packet.
- ID: TG-013
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Write movement and attack legality packet.

### Choose sandbox opposing-side control setup.
- ID: TG-014
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Choose sandbox opposing-side control setup.

### Assemble tactical sandbox implementation brief.
- ID: TG-015
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Assemble tactical sandbox implementation brief.

### Implement first tactical sandbox slice in code and verify the battle loop locally.
- ID: TG-100
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Implement first tactical sandbox slice in code and verify the battle loop locally.

### Build army setup foundation and expand the sandbox roster with Scout and Cleric.
- ID: TG-110
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Build army setup foundation and expand the sandbox roster with Scout and Cleric.

### Fix deployment layout stability regression in the React setup flow.
- ID: TG-111
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Fix deployment layout stability regression in the React setup flow.

### Restore clear unit HP visibility in the compact board UI.
- ID: TG-112
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Restore clear unit HP visibility in the compact board UI.

### Recover the working build and retry occupied-tile readability in a smaller safer pass.
- ID: TG-114
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Recover the working build and retry occupied-tile readability in a smaller safer pass.

### Establish version control for `TacticsGame` as a workflow safeguard.
- ID: TG-115
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Establish version control for `TacticsGame` as a workflow safeguard.

### Fix follow-up issues from the latest QoL pass.
- ID: TG-116
- Kind: request
- Status: completed
- Owner: Imported Legacy Board
- Assigned Role: Imported Legacy Board
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Fix follow-up issues from the latest QoL pass.

### Fix the pre-commit unit-reselection crash
- ID: TG-117
- Kind: request
- Status: completed
- Owner: Programmer
- Assigned Role: Programmer
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Fix the runtime crash caused by selecting a different eligible unit during the intended pre-commit reselection flow, while preserving the corrected log order and stable layout.

Scope In:
reproduce the blank-screen failure, identify the state/render bug in the reselection path, restore clean pre-commit switching between eligible units.

Scope Out:
new features, battle-rule changes, layout redesign, log redesign, Phaser, save/load, admin tools, progression, multiplayer, AI work.

Acceptance Criteria:
- Selecting a different eligible unit before move/action commitment no longer crashes the app.
- The selection switches cleanly to the second eligible unit.
- The turn is not spent just by inspecting the first unit.
- Activity log ordering remains correct.
- The left-board-right layout remains stable and non-overlapping.
- No validated tactical mechanics change as a side effect.
- Result: Completed in the Dev thread and validated locally by the user; subsequent gameplay/object ideas remain backlog only and have not yet been sent for implementation.
- Review Notes: Completed in the Dev thread and validated locally by the user; subsequent gameplay/object ideas remain backlog only and have not yet been sent for implementation.

### Introduce static blocking objects such as walls into the tactical sandbox
- ID: TG-053
- Kind: request
- Status: completed
- Owner: Programmer
- Assigned Role: Programmer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Add a first-pass wall object that occupies tiles and blocks movement, placement, and ranged line-of-fire without changing the validated core battle loop.

Scope In:
data representation for wall objects, board occupancy treatment, setup placement rules if needed for the slice, movement blocking, ranged targeting or line-of-fire blocking, readable board presentation, local validation.

Scope Out:
destructible terrain, grass behavior, AI adaptation, mission design, map editor expansion, progression, multiplayer, save/load, large environment system redesign.

Acceptance Criteria:
- Walls can exist on the board as static field objects.
- Units cannot move through walls.
- Units cannot end movement on wall tiles.
- Walls block ranged line-of-fire for the intended first-pass rules.
- Existing unit activation rules and damage rules remain unchanged.
- The sandbox remains stable in local testing.
- Result: User reports the wall mechanic itself is working well enough to close this ticket. The unmet original placement expectation has been split into `TG-057`, which will move walls from fixed center-line placement to player-controlled setup placement at a 10-point cost.
- Review Notes: User reports the wall mechanic itself is working well enough to close this ticket. The unmet original placement expectation has been split into `TG-057`, which will move walls from fixed center-line placement to player-controlled setup placement at a 10-point cost.

### Introduce destructible high-grass objects as a future summonable/blocking object concept
- ID: TG-054
- Kind: request
- Status: completed
- Owner: Programmer
- Assigned Role: Programmer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Add a first-pass destructible high-grass field object that blocks tiles until attacked, while preserving current validated unit rules.

Scope In:
high-grass object data, tile blocking behavior, destruction interaction, readable UI state, local validation, future-friendly groundwork for later summonable-object ideas.

Scope Out:
summon skills, wider terrain system, map editor overhaul, AI adaptation, progression, multiplayer, save/load, additional environmental status effects.

Acceptance Criteria:
- High grass can exist on the board as a field object.
- High grass blocks tile occupation according to the first-pass rules.
- High grass can be removed through the intended attack interaction.
- Removing high grass does not alter core activation order or combat resolution rules for units.
- The sandbox remains stable in local testing.
- Result: User reports the high-grass mechanic itself is working well enough to close this ticket. The unmet original placement expectation has been split into `TG-057`, which will move high grass from fixed center-line placement to player-controlled setup placement at a 5-point cost.
- Review Notes: User reports the high-grass mechanic itself is working well enough to close this ticket. The unmet original placement expectation has been split into `TG-057`, which will move high grass from fixed center-line placement to player-controlled setup placement at a 5-point cost.

### Refine the action log toward one-line turn summaries
- ID: TG-055
- Kind: request
- Status: completed
- Owner: Programmer
- Assigned Role: Programmer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Replace separate move/action/rotate activity-log lines with a clearer single-line summary per activation without changing battle rules.

Scope In:
action-log formatting, activation-summary wording, preserving side clarity, preserving action visibility for move-only and move-plus-action turns.

Scope Out:
battle-rule changes, turn-order logic changes, wall objects, high grass objects, AI, layout redesign, Phaser, save/load, progression, multiplayer.

Acceptance Criteria:
- A completed activation is represented as one concise readable line in the activity log.
- Move-only turns remain understandable.
- Move-plus-action turns remain understandable.
- Rotation state remains visible or summarized clearly enough for play review.
- Existing battle mechanics and activation order do not change.
- The UI remains stable in local testing.
- Result: User validated the live behavior and closed the task. Follow-up usability work for log scrolling has been split into `TG-056`.
- Review Notes: User validated the live behavior and closed the task. Follow-up usability work for log scrolling has been split into `TG-056`.

### Add scrolling to the activity log so older entries remain accessible
- ID: TG-056
- Kind: request
- Status: completed
- Owner: Programmer
- Assigned Role: Programmer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Keep the one-line activation summaries from `TG-055` while making older log entries accessible once the log exceeds the visible window.

Scope In:
scrollable activity-log container, visible log window sized for about 7 entries at a time, access to older entries via scrollbar, preserving current one-line summary content, keeping the log on the intended side of the board layout, local UI validation.

Scope Out:
log-content redesign, terrain-system changes, battle-rule changes, layout overhaul, save/load, progression, multiplayer, AI.

Acceptance Criteria:
- The activity log shows about 7 entries at a time in a bounded visible window.
- Older entries remain accessible by scrolling.
- Current one-line log summaries remain intact.
- The scrollable log remains on the intended side of the board layout.
- The visible log area is capped and does not keep growing with the number of entries.
- The board layout and tile spacing remain stable and are not pushed apart by the log container.
- The log area remains readable and stable in local testing.
- Existing gameplay mechanics do not change.
- Result: User validated the final bounded-scroll result and closed the task. The activity log now keeps older one-line summaries accessible without stretching the board footprint or disturbing tile spacing.
- Review Notes: User validated the final bounded-scroll result and closed the task. The activity log now keeps older one-line summaries accessible without stretching the board footprint or disturbing tile spacing.

### Let players place walls and high grass during setup using point costs instead of fixed center-line placement
- ID: TG-057
- Kind: request
- Status: completed
- Owner: Programmer
- Assigned Role: Programmer
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Replace fixed center-line wall and grass placement with player-controlled setup placement so walls cost 10 points and high grass costs 5 points during the setup phase.

Scope In:
setup-flow support for field objects, point-cost handling for walls and high grass, placement rules during setup, enforcing same-side deployment consistency with other playable units, removal of fixed center-line object placement, readable UI support, local validation.

Scope Out:
line-of-sight redesign, physical-vs-magical damage rules, AI adaptation, map editor expansion, save/load, progression, multiplayer.

Acceptance Criteria:
- Players can add walls during setup for 10 points each.
- Players can add high grass during setup for 5 points each.
- Players can only place bought walls and grass on their own side of the board, consistent with unit deployment rules.
- Fixed center-line placement for walls and grass is removed.
- Existing wall and high-grass behavior still works after setup placement changes.
- The setup UI and sandbox remain stable in local testing.
- Result: User validated the setup-side restriction and considers this working well. The task is now closed.
- Review Notes: User validated the setup-side restriction and considers this working well. The task is now closed.

### Design a fuller line-of-sight and damage-type model for future releases
- ID: TG-058
- Kind: request
- Status: completed
- Owner: Designer
- Assigned Role: Designer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Define future line-of-sight and attack-type rules so units, walls, and high grass can interact cleanly with physical and magical attacks.

Scope In:
design and architecture only, rule-model options, terminology, future data-model implications, future UI/readability implications, documenting open questions.

Scope Out:
implementation, balance tuning, AI changes, UI polish, and current-release mechanics changes.

Acceptance Criteria:
- The design thread produces a clear recommendation for how to separate visibility from attack delivery.
- The design thread addresses units, walls, and high grass as future blockers.
- The design thread addresses physical vs magical damage as separate future behaviors.
- The design thread records the Scout-vs-Pikeman inconsistency as a motivating problem.
- The design thread leaves a clean basis for later implementation tasks.
- Result: Approved and completed. `LINE_OF_SIGHT_DAMAGE_MODEL.md` now records the approved baseline that physical and magical attacks use separate blocker logic, and that magical damage is unblockable and undodgeable. Any deeper damage-model expansion such as wards, resistances, reflection, or anti-magic exceptions should be tracked under separate future tasks rather than reopening this ticket.
- Review Notes: Approved and completed. `LINE_OF_SIGHT_DAMAGE_MODEL.md` now records the approved baseline that physical and magical attacks use separate blocker logic, and that magical damage is unblockable and undodgeable. Any deeper damage-model expansion such as wards, resistances, reflection, or anti-magic exceptions should be tracked under separate future tasks rather than reopening this ticket.

### Adjust board-color visibility by phase so side colors appear only during setup
- ID: TG-059
- Kind: request
- Status: completed
- Owner: Programmer / UI Implementer
- Assigned Role: Programmer / UI Implementer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Make board-side colors contextual so setup emphasizes the active player's deployment area, while battle uses a neutral board presentation.

Scope In:
setup-phase board coloring, active-player-side emphasis, neutral coloring for inactive board regions, battle-phase board coloring, preserving black out-of-bounds corner tiles, local UI validation.

Scope Out:
gameplay-rule changes, deployment-rule changes, terrain-system changes, combat mechanics, LOS rules, save/load, progression, multiplayer.

Acceptance Criteria:
- During Player 1 setup, Player 1's side remains blue while the center line and Player 2 side are gray.
- During Player 2 setup, Player 2's side remains orange while the center line and Player 1 side are gray.
- During battle, all in-bounds battlefield tiles are gray.
- Out-of-bounds corner or masked tiles remain black as they are now.
- Existing setup and battle mechanics do not change.
- Result: Implemented in the UI. Setup now highlights only the active side in blue or orange while center and inactive regions stay gray; battle now uses gray for all playable tiles while void corners remain black. The operator has now live-validated this behavior and approved closure.
- Review Notes: Implemented in the UI. Setup now highlights only the active side in blue or orange while center and inactive regions stay gray; battle now uses gray for all playable tiles while void corners remain black. The operator has now live-validated this behavior and approved closure.

### Introduce the first magical-damage implementation slice and add the Pyromancer
- ID: TG-068
- Kind: request
- Status: completed
- Owner: Programmer / Gameplay Implementer
- Assigned Role: Programmer / Gameplay Implementer
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: Add the first live separation between physical and magical damage and introduce a new Pyromancer unit with a plus-shaped magical area attack.

Scope In:
first magical-damage rules slice, Pyromancer unit definition, plus-shaped area targeting, `G` center versus `D` splash logic, magical damage application, friendly-fire confirmation prompt, local validation, documentation updates.

Scope Out:
wards, resistances, anti-magic exceptions, reflection, absorption, broader magic roster expansion, AI work, balance polish.

Acceptance Criteria:
- The first magical-damage slice follows the approved `TG-058` baseline.
- The Pyromancer is added as a playable unit.
- The Pyromancer has 30 HP, 0 armor like Cleric, movement 3, magical damage 15, and range 3 to the selected `G` tile.
- The Pyromancer can target a valid `G` tile up to range 3 and apply magical damage to the `G` tile plus the four orthogonal `D` tiles in the approved plus pattern.
- Only units standing exactly on `G` or `D` tiles take damage; empty `D` tiles do nothing.
- The attack can damage allies as well as enemies.
- If the cast would hit an ally, the UI asks the player to confirm with an `OK / Cancel` style warning before resolving.
- The first magical slice does not damage walls.
- Existing physical units continue to use physical damage rules.
- The sandbox remains stable in local testing.
- Result: Implemented as the first live magical-damage slice. Pyromancer is now playable; valid `G` targeting and separate `D` splash cells are in place; ally hits require UI confirmation; magical bursts do not damage walls; and a follow-up correction pass now also allows `highGrass` as a legal `G` target, adds hover-preview markers for `G` and `D` cells in the board UI, and makes magical bursts clear `highGrass` tiles caught in the affected area while still leaving walls untouched. `npm.cmd test` and `npm.cmd run build` passed. The operator has now live-validated damage on grass, enemies, and allies and approved closure.
- Review Notes: Implemented as the first live magical-damage slice. Pyromancer is now playable; valid `G` targeting and separate `D` splash cells are in place; ally hits require UI confirmation; magical bursts do not damage walls; and a follow-up correction pass now also allows `highGrass` as a legal `G` target, adds hover-preview markers for `G` and `D` cells in the board UI, and makes magical bursts clear `highGrass` tiles caught in the affected area while still leaving walls untouched. `npm.cmd test` and `npm.cmd run build` passed. The operator has now live-validated damage on grass, enemies, and allies and approved closure.

### Define the next `TacticsGame` milestone ladder and closure order for Stage 4
- ID: TG-075
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: turn the current Stage 4 backlog into a small milestone ladder with a clear closure order so the project can show visible progression and avoid opening too many design and systems fronts at once.

Scope In:
current milestone naming, near-term milestone ordering, which tasks belong to the next milestone versus later ones, explicit recommendation on mechanics-first versus low-fidelity UX/design exploration, durable markdown capture.

Scope Out:
implementation, balance tuning, full roadmap rewrite, AI delivery, isometric conversion, asset production pipeline implementation.

Acceptance Criteria:
- a next-milestone ladder exists for the current Stage 4 phase
- the next milestone has a clear closure target
- current backlog themes are grouped into a small number of sensible fronts
- the recommendation clearly states what is safe to explore now versus later
- Result: The next closure order is now defined at a high level: keep `TG-074` as the small UX follow-up inside Milestone 1, start objective expansion with capture-and-extract, split the capture mechanic from the full objective implementation, keep marked leader as a separate independently testable win-condition task, and treat the low-fidelity UX stream as the next milestone rather than one oversized task. The operator has now approved proceeding in that order.
- Review Notes: The next closure order is now defined at a high level: keep `TG-074` as the small UX follow-up inside Milestone 1, start objective expansion with capture-and-extract, split the capture mechanic from the full objective implementation, keep marked leader as a separate independently testable win-condition task, and treat the low-fidelity UX stream as the next milestone rather than one oversized task. The operator has now approved proceeding in that order.

### Define the first capture-or-carry mechanic for objectives
- ID: TG-076
- Kind: request
- Status: completed
- Owner: Product Designer / Systems Planner
- Assigned Role: Product Designer / Systems Planner
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: define the smallest first-pass rule for one unit capturing and carrying a VIP so later objective-based win conditions can share the same base behavior.

Scope In:
per-side VIP custody setup rule, adjacent rescue interaction, VIP carrier rules, inability to attack while carrying, defeat-and-drop behavior, side-owned rescue-area rule, durable rules note.

Scope Out:
full flag objective implementation, AI behavior, animation polish, multiple objective types, balance tuning.

Acceptance Criteria:
- a durable first-pass capture-or-carry rule exists
- the rule is small enough to support later objective implementation without broad system redesign
- the rule is clear enough to guide the first capture-and-extract implementation slice
- Result: Finalized in `OBJECTIVE_MECHANICS.md` as the accepted hostage-exchange VIP-rescue model: each side places one free enemy VIP during setup, rescue is a dedicated adjacent interaction rather than an attack, carriers cannot attack, defeated carriers drop the VIP on their tile, and extraction uses side-owned rescue zones. A later milestone may add skills that deliberately drop the VIP in a chosen location. The operator provided the required rules and this design slice is now closed.
- Review Notes: Finalized in `OBJECTIVE_MECHANICS.md` as the accepted hostage-exchange VIP-rescue model: each side places one free enemy VIP during setup, rescue is a dedicated adjacent interaction rather than an attack, carriers cannot attack, defeated carriers drop the VIP on their tile, and extraction uses side-owned rescue zones. A later milestone may add skills that deliberately drop the VIP in a chosen location. The operator provided the required rules and this design slice is now closed.

### Replace the browser-native ally-hit confirmation popup with a board-native warning layer
- ID: TG-074
- Kind: request
- Status: completed
- Owner: UX Designer / UI Implementer
- Assigned Role: UX Designer / UI Implementer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: replace the browser-native ally-hit confirmation popup with an in-game warning layer that matches the tactical board's own visual language and avoids browser-specific dialog behavior.

Scope In:
board-native warning treatment, same visual language as the board and tactical markers, confirm and cancel actions, better placement layer than browser popup, durable notes for expected player behavior.

Scope Out:
broad modal-system redesign, accessibility deep pass, generalized notification framework, combat-rule changes, Pyromancer damage-rule changes.

Acceptance Criteria:
- Ally-hit confirmation no longer relies on the browser's native popup dialog.
- The warning appears inside the game UI on a layer that feels native to the battle board.
- The warning uses the same tactical visual language as the board where practical, including current marker and color cues.
- The player can clearly confirm or cancel without losing context.
- Existing Pyromancer ally-hit behavior does not change apart from presentation.
- Result: Implemented in the React battle UI as an in-board risk overlay that replaces the browser-native popup. The warning now appears inside the battlefield panel, uses the existing `G` and `D` visual language, and lets the player confirm or cancel without leaving the game surface. The operator has now accepted this change. A follow-up safety tweak also moved `Back To Setup` away from the right action panel so live validation is less error-prone. `npm.cmd run build` passes.
- Review Notes: Implemented in the React battle UI as an in-board risk overlay that replaces the browser-native popup. The warning now appears inside the battlefield panel, uses the existing `G` and `D` visual language, and lets the player confirm or cancel without leaving the game surface. The operator has now accepted this change. A follow-up safety tweak also moved `Back To Setup` away from the right action panel so live validation is less error-prone. `npm.cmd run build` passes.

### Add visible cooldown indicators for units that are still fatigued
- ID: TG-082
- Kind: request
- Status: completed
- Owner: UX Designer / UI Implementer
- Assigned Role: UX Designer / UI Implementer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: make unit fatigue or cooldown state legible in the battle UI so the player can easily see which units are unavailable and how many turns remain before they can act again.

Scope In:
visible marker on fatigued units, simple numeric remaining-cooldown indicator, lightweight presentation that fits the current board readability, durable clarification of how remaining turns should be counted against the current opportunity-based system.

Scope Out:
broader status-effect system, animation polish, final HUD redesign, generalized buff or debuff framework, AI changes.

Acceptance Criteria:
- units with an active cooldown are visibly marked on the board
- the player can see a simple number for how many turns remain until the unit can act again
- the indicator does not make occupied tiles unreadable
- the meaning of the displayed countdown is documented clearly enough for later implementation
- Result: Implemented as a lightweight numbered cooldown badge on fatigued units. The board now shows remaining opportunity-count cooldown directly on the unit tile when a unit is still unavailable, using the current side-opportunity model already used by fatigue logic. The intent is to make Cleric pacing and other skipped-opportunity behavior easier to read without adding a heavier status framework. `npm.cmd test` and `npm.cmd run build` pass. The operator has now accepted the behavior, while noting that a later interface/design pass should make the presentation more beautiful.
- Review Notes: Implemented as a lightweight numbered cooldown badge on fatigued units. The board now shows remaining opportunity-count cooldown directly on the unit tile when a unit is still unavailable, using the current side-opportunity model already used by fatigue logic. The intent is to make Cleric pacing and other skipped-opportunity behavior easier to read without adding a heavier status framework. `npm.cmd test` and `npm.cmd run build` pass. The operator has now accepted the behavior, while noting that a later interface/design pass should make the presentation more beautiful.

### Implement the first capture-and-extract win condition
- ID: TG-077
- Kind: request
- Status: completed
- Owner: Programmer / Gameplay Implementer
- Assigned Role: Programmer / Gameplay Implementer
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: add the first objective-based win condition where each side rescues its own captive VIP and wins by bringing that rescued VIP into its own extraction zone.

Scope In:
per-side VIP board representation, free setup placement when the mode is enabled, adjacent rescue action, per-side rescue zones, carrier marker, drop-on-death behavior, immediate eliminate-all compatibility, local validation, documentation updates.

Scope Out:
additional objective types, AI behavior, mission scripting framework, progression systems, polished presentation.

Acceptance Criteria:
- each side places exactly one free VIP on its own half when the mode is enabled
- each side can rescue only its own VIP and only from an adjacent tile
- rescuing uses a dedicated rescue interaction rather than the normal attack flow
- a carrier is visibly marked, cannot attack, and drops the VIP on death
- each side has its own 6-tile rescue zone and reaching it with the rescued VIP triggers victory correctly
- existing eliminate-all-enemies win logic still works
- the sandbox remains stable in local testing
- Result: Rebuilt after the first live review changed the design. When `Capture and extract VIP` is enabled, each side now places exactly one free VIP during setup on that side's own half of the board, representing the opposing side's captive. Each side then tries to rescue its own VIP first while eliminate-all-enemies still remains a valid immediate victory path. Rescue is now a dedicated adjacent interaction rather than a normal attack. Ranged units must still stand adjacent to rescue. A rescued VIP appears as a carrier marker on the unit, carriers cannot attack, defeated carriers drop the VIP on their death tile, and each side now extracts through its own 6-tile rescue zone (`P1: 0.4/1.4/0.5/1.5/0.6/1.6`, `P2: 9.4/10.4/9.5/10.5/9.6/10.6`). The latest visual pass also changes rescue zones from yellow highlights into player-colored dashed transparent areas and recolors VIP markers toward the side trying to rescue them. `npm.cmd test` and `npm.cmd run build` pass. The operator has now live-validated the mechanic and approved closure.
- Review Notes: Rebuilt after the first live review changed the design. When `Capture and extract VIP` is enabled, each side now places exactly one free VIP during setup on that side's own half of the board, representing the opposing side's captive. Each side then tries to rescue its own VIP first while eliminate-all-enemies still remains a valid immediate victory path. Rescue is now a dedicated adjacent interaction rather than a normal attack. Ranged units must still stand adjacent to rescue. A rescued VIP appears as a carrier marker on the unit, carriers cannot attack, defeated carriers drop the VIP on their death tile, and each side now extracts through its own 6-tile rescue zone (`P1: 0.4/1.4/0.5/1.5/0.6/1.6`, `P2: 9.4/10.4/9.5/10.5/9.6/10.6`). The latest visual pass also changes rescue zones from yellow highlights into player-colored dashed transparent areas and recolors VIP markers toward the side trying to rescue them. `npm.cmd test` and `npm.cmd run build` pass. The operator has now live-validated the mechanic and approved closure.

### Revisit overall roster balance before closing the current gameplay milestone
- ID: TG-081
- Kind: request
- Status: completed
- Owner: Product Designer / Combat Systems Planner
- Assigned Role: Product Designer / Combat Systems Planner
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: step back from isolated unit tweaks and define a broader balance pass for the current live roster so the milestone can close on a more coherent combat feel.

Scope In:
roster-wide balance review, role comparison across Warrior, Pikeman, Scout, Cleric, and Pyromancer, identification of current overperforming or underperforming patterns, lightweight recommendations for the next grouped rebalance slice.

Scope Out:
art direction, UI redesign, meta progression systems, AI implementation.

Acceptance Criteria:
- the current live roster is reviewed as a set rather than only as isolated unit tweaks
- the most important balance pain points are documented clearly
- the output is small enough to guide a later grouped rebalance slice
- Result: Accepted and closed as the broader roster-balance rethink needed to close the first gameplay milestone cleanly without leaving balance as a permanently open excuse to delay milestone transition.
- Review Notes: Accepted and closed as the broader roster-balance rethink needed to close the first gameplay milestone cleanly without leaving balance as a permanently open excuse to delay milestone transition.

### Implement the first playable presentation slice across board, panels, and unit readability
- ID: TG-099
- Kind: request
- Status: completed
- Owner: UI Implementer / Playable Prototype Builder
- Assigned Role: UI Implementer / Playable Prototype Builder
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M0 - Sandbox Foundation And First Combat Slice
- Details: apply the first approved presentation improvements so the prototype feels more like a coherent game loop while preserving the validated tactical rules and producing a milestone jump similar to the confidence gain felt after `TG-081`.

Scope In:
board/panel hierarchy improvements, first visual identity application, stronger unit readability, battle-state clarity, compressed end-of-battle summary, lean right-side selected-unit panel, always-visible current-player card strip, and the first art-informed presentation touches.

Scope Out:
final polish, full HUD redesign, isometric conversion, progression screens, campaign layer, full card system.

Acceptance Criteria:
- the playable battle screen feels meaningfully clearer and more intentional
- first visual-identity decisions are visible in the live prototype
- tactical readability remains strong or improves
- no validated gameplay rules are broken by presentation work
- the board remains the main visual focus
- the first card prototype is visible during the current player's turn
- the end-of-battle summary shows winner, reason for victory, and gold earned
- Result: The first Milestone 2 live slice is now accepted. It keeps the board as the visual anchor while adding a battle-end summary, stronger turn/objective structure in the right panel, a lean selected-unit summary, and the first always-visible current-player unit-card strip. First operator review notes: the new cards and overall flow feel directionally right, the victory summary feels useful, and the overall gameplay loop still feels familiar. The cards are not yet providing full value because equipment, broader skills, and deeper statuses are not live yet. The right panel still feels too text-heavy and not visual enough, so a follow-up refinement has been split into `TG-101`.
- Review Notes: The first Milestone 2 live slice is now accepted. It keeps the board as the visual anchor while adding a battle-end summary, stronger turn/objective structure in the right panel, a lean selected-unit summary, and the first always-visible current-player unit-card strip. First operator review notes: the new cards and overall flow feel directionally right, the victory summary feels useful, and the overall gameplay loop still feels familiar. The cards are not yet providing full value because equipment, broader skills, and deeper statuses are not live yet. The right panel still feels too text-heavy and not visual enough, so a follow-up refinement has been split into `TG-101`.

### Design and implement the Archer class for the tactics game.
- ID: task_9d4e1a2802ce
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Details: Create the Archer class adhering to the current architecture constraints. Provide explicit proof chain including design decisions, code implementation, and testing evidence.
- Result: PM completed all subtasks and QA approved the final deliverables.
- Review Notes: QA approved the parent task.

### Archer Architecture Design
- ID: task_7cfa77d6b59f
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_9d4e1a2802ce
- Expected Artifact: projects/tactics-game/artifacts/archer_design.md
- Details: Document the Archer unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Archer Python Module
- ID: task_cef16194e075
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Parent Task: task_9d4e1a2802ce
- Expected Artifact: projects/tactics-game/artifacts/archer.py
- Details: Write a Python module for Archer suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Archer UI Notes
- ID: task_6b3587074f63
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Design
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_9d4e1a2802ce
- Expected Artifact: projects/tactics-game/artifacts/archer_ui_notes.md
- Details: Describe how the UI should communicate Archer identity, spellcasting feedback, and player readability.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Locate and verify wireframe and reviewable results for TG-071 and other 'for rev
- ID: task_eeca89d2af97
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Orchestrator
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Details: Find the tasks marked as 'for review' in the Tactics game project, confirm the existence and location of wireframes, provide content details and proof of wireframe creation and review results.
- Result: PM completed all subtasks and QA approved the final deliverables.
- Review Notes: QA approved the parent task.

### Project Architecture Design
- ID: task_0d4dd9304289
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_eeca89d2af97
- Expected Artifact: projects/tactics-game/artifacts/project_design.md
- Details: Document the Project unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Project Python Module
- ID: task_505d52afa0ab
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Parent Task: task_eeca89d2af97
- Expected Artifact: projects/tactics-game/artifacts/project.py
- Details: Write a Python module for Project suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Project UI Notes
- ID: task_01649da5391d
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Design
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_eeca89d2af97
- Expected Artifact: projects/tactics-game/artifacts/project_ui_notes.md
- Details: Describe how the UI should communicate Project identity, spellcasting feedback, and player readability.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Locate wireframe and related content for TG-071 and other tasks marked 'for my r
- ID: task_3e0e01726bd1
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Orchestrator
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Details: Retrieve task TG-071 details, verify existence and location of its wireframe, and list other tasks in the same project marked 'for my review' with their content and wireframe availability. Provide explicit proof or evidence for findings.
- Result: PM completed all subtasks and QA approved the final deliverables.
- Review Notes: QA approved the parent task.

### Project Architecture Design
- ID: task_579d694f74e5
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_3e0e01726bd1
- Expected Artifact: projects/tactics-game/artifacts/project_design.md
- Details: Document the Project unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Project Python Module
- ID: task_e491536a805a
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Parent Task: task_3e0e01726bd1
- Expected Artifact: projects/tactics-game/artifacts/project.py
- Details: Write a Python module for Project suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Project UI Notes
- ID: task_34284d9c128d
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Design
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_3e0e01726bd1
- Expected Artifact: projects/tactics-game/artifacts/project_ui_notes.md
- Details: Describe how the UI should communicate Project identity, spellcasting feedback, and player readability.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Locate wireframes and review content for tasks in the Tactics Game project, incl
- ID: task_e014fe66fbc1
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Orchestrator
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Details: Find the task TG-071 content and confirm if a wireframe was created for review. Provide similar information for other tasks in the Tactics Game project that are marked for review. Include explicit proof and evidence of wireframe locations and content.
- Result: PM completed all subtasks and QA approved the final deliverables.
- Review Notes: QA approved the parent task.

### Tg Architecture Design
- ID: task_b1e233ea0166
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_e014fe66fbc1
- Expected Artifact: projects/tactics-game/artifacts/tg_design.md
- Details: Document the Tg unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Tg Python Module
- ID: task_822a0b5dee2f
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Parent Task: task_e014fe66fbc1
- Expected Artifact: projects/tactics-game/artifacts/tg.py
- Details: Write a Python module for Tg suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Tg UI Notes
- ID: task_39fd11bde9be
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Design
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_e014fe66fbc1
- Expected Artifact: projects/tactics-game/artifacts/tg_ui_notes.md
- Details: Describe how the UI should communicate Tg identity, spellcasting feedback, and player readability.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Move task TG-098 for M1 tacticsgame back to 'In Progress'.
- ID: task_7a5487ae0fb7
- Kind: request
- Status: completed
- Owner: Orchestrator
- Assigned Role: Orchestrator
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Details: The user cannot see the outcome of the task from the current build, so the task TG-098 needs to be moved back to 'In Progress' status to continue work.
- Result: Moved TG-098 to in progress.
- Review Notes: Moved TG-098 to in progress.

### Add a test-only support unit called 'Beacon' for tactics-game SDK migration proo
- ID: task_ac500b518bd8
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Orchestrator
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Details: Implement a single bounded slice of functionality for the 'Beacon' unit within the tactics game, focusing on test-only use. Provide explicit proof and evidence of correct implementation as part of the deliverable.
- Result: PM completed all subtasks and QA approved the final deliverables.
- Review Notes: QA approved the parent task.

### Functionality Architecture Design
- ID: task_2c1d3caf961c
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_ac500b518bd8
- Expected Artifact: projects/tactics-game/artifacts/functionality_design.md
- Details: Document the Functionality unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Functionality Python Module
- ID: task_0446fa742027
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Parent Task: task_ac500b518bd8
- Expected Artifact: projects/tactics-game/artifacts/functionality.py
- Details: Write a Python module for Functionality suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Functionality UI Notes
- ID: task_ebc5deeb3a6f
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Design
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_ac500b518bd8
- Expected Artifact: projects/tactics-game/artifacts/functionality_ui_notes.md
- Details: Describe how the UI should communicate Functionality identity, spellcasting feedback, and player readability.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Create a bounded proof slice for Beacon with explicit proof evidence.
- ID: task_3111bbc53123
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Orchestrator
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Details: Generate a proof slice that is bounded in scope specifically for the Beacon component, ensuring explicit proof evidence is included to validate the slice.
- Result: PM completed all subtasks and QA approved the final deliverables.
- Review Notes: QA approved the parent task.

### Evidence Architecture Design
- ID: task_ac93532748a1
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_3111bbc53123
- Expected Artifact: projects/tactics-game/artifacts/evidence_design.md
- Details: Document the Evidence unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Evidence Python Module
- ID: task_c4b77f47d646
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Parent Task: task_3111bbc53123
- Expected Artifact: projects/tactics-game/artifacts/evidence.py
- Details: Write a Python module for Evidence suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Evidence UI Notes
- ID: task_821f7c728c45
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Design
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_3111bbc53123
- Expected Artifact: projects/tactics-game/artifacts/evidence_ui_notes.md
- Details: Describe how the UI should communicate Evidence identity, spellcasting feedback, and player readability.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Create a bounded proof slice for the Beacon component.
- ID: task_a40c6fdb9da9
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Details: Develop a focused and concise proof slice that covers essential functionalities of the Beacon module, ensuring the proof scope is limited and manageable to maintain clarity and efficiency.
- Result: PM completed all subtasks and QA approved the final deliverables.
- Review Notes: QA approved the parent task.

### Component Architecture Design
- ID: task_4c4c94444840
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_a40c6fdb9da9
- Expected Artifact: projects/tactics-game/artifacts/component_design.md
- Details: Document the Component unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Component Python Module
- ID: task_4f71cc7febeb
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Parent Task: task_a40c6fdb9da9
- Expected Artifact: projects/tactics-game/artifacts/component.py
- Details: Write a Python module for Component suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Component UI Notes
- ID: task_81e974c731c2
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Design
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Parent Task: task_a40c6fdb9da9
- Expected Artifact: projects/tactics-game/artifacts/component_ui_notes.md
- Details: Describe how the UI should communicate Component identity, spellcasting feedback, and player readability.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.

### Implement the Gilded War Table battlefield shell and board treatment
- ID: TG-102
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: UI Implementer / Visual Production
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Playable Prototype Surface And Visual Cohesion
- Expected Artifact: projects/tactics-game/app/src/styles.css
- Details: Apply the approved Gilded War Table direction to the live battlefield shell and board so the prototype feels like a game surface instead of a flat prototype grid.

Scope In:
board materials and atmosphere, battlefield framing, legend and heading hierarchy, rescue-zone presentation, and setup-to-battle visual continuity where needed.

Scope Out:
rule changes, isometric conversion, custom painted assets, progression systems.

Acceptance Criteria:
- the live battlefield has a materially stronger visual identity
- the board remains tactically readable
- the pass uses local-first CSS and layout work rather than depending on external art assets
- Result: Battlefield shell and board treatment now present a stronger war-table identity in the live app.
- Review Notes: Live implementation completed and verified locally. Review in the running TacticsGame app.
Accepted by Studio Lead on 2026-03-27 after live app review.

## Blocked

### Multiplayer planning.
- ID: TG-060
- Status: deferred
- Secondary State: deferred
- Owner: Imported Legacy Board
- Details: Multiplayer planning.

### Base management implementation.
- ID: TG-061
- Status: deferred
- Secondary State: deferred
- Owner: Imported Legacy Board
- Details: Base management implementation.

### Create a bounded proof slice for Beacon with explicit proof evidence.
- ID: task_fea00642ce7a
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Develop a proof slice that is limited in scope (bounded) for the Beacon component and ensure all proof evidence is detailed explicitly.

### Evidence Architecture Design
- ID: task_2b5b43258c95
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Document the Evidence unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.

### Evidence Python Module
- ID: task_d3aee01ec831
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Write a Python module for Evidence suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.

### Evidence UI Notes
- ID: task_4089b01b801f
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Describe how the UI should communicate Evidence identity, spellcasting feedback, and player readability.

### Create a bounded proof slice for Beacon with explicit proof evidence.
- ID: task_331e1f80c2bd
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Generate a proof slice specifically scoped to the Beacon component and document the explicit evidence supporting the proof.

### Evidence Architecture Design
- ID: task_ae04b28b827e
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Document the Evidence unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.

### Evidence Python Module
- ID: task_782ed00cb402
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Write a Python module for Evidence suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.

### Evidence UI Notes
- ID: task_a82204961824
- Status: deferred
- Secondary State: deferred
- Owner: Orchestrator
- Details: Describe how the UI should communicate Evidence identity, spellcasting feedback, and player readability.
