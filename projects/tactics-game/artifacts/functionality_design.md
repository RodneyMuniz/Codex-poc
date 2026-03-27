```markdown
# Functionality Design

## Overview
The Functionality unit encapsulates the core gameplay mechanics and interactive capabilities of units within the tactics-game. It defines how units operate, respond to player commands, and interact with other game entities. This design aims to establish a modular and extensible architecture enabling future expansion of unit capabilities aligned with the game’s turn-based tactical framework, focusing on alternating unit activations, positioning, and facing.

## Attributes
- **Activation State**: Tracks whether the unit is active, inactive, or exhausted for the current turn.
- **Position**: Represents the unit’s current location on the isometric grid.
- **Facing Direction**: Represents which way the unit is currently oriented, influencing movement and combat interactions.
- **Movement Range**: Maximum distance a unit can move when activated.
- **Action Points**: Resource pool defining how many actions or abilities a unit can perform per activation.
- **Health Points (HP)**: Current and maximum hit points reflecting unit survivability.
- **Status Effects**: List of temporary or persistent conditions affecting unit performance (e.g., stunned, poisoned).
- **Unit Type**: Classification to enable ability and attribute differentiation (e.g., infantry, archer).

## Abilities
- **Move**: Allows the unit to relocate on the board within its Movement Range, respecting obstructions and terrain.
- **Rotate/Facing Change**: Enables changing the unit’s facing direction without moving position, critical for tactical positioning.
- **Attack**: Executes a combat action against an enemy unit within range and facing parameters; consumes action points.
- **Use Ability**: Executes special abilities or skills unique to the unit type, consuming appropriate action points.
- **Wait/End Turn**: Ends the unit’s activation early, preserving remaining action points for future turns according to progression rules.
- **Status Application and Clearance**: Handles adding and removing status effects dynamically as gameplay events occur.

## Acceptance Criteria
- The Functionality design clearly defines all relevant attributes to represent unit state and capabilities.
- All abilities are explicitly described with their purpose, resource costs, and constraints.
- The architecture supports modular addition of new abilities and attributes without requiring refactoring.
- Unit activation toggles correctly between states, reflecting available action points and turn progression.
- Positioning and facing changes are accurately represented and reflected in gameplay effects.
- Status effects can be applied and cleared, impacting unit capabilities as intended.
- The design document aligns with the overarching tactics-game roadmap and milestone objectives, particularly milestone M1 and foundational M2 packets.
- The artifact is stored at `projects/tactics-game/artifacts/functionality_design.md` and formatted for easy reference by developers and designers.
```