```markdown
# Tg Design

## Overview
The Tg unit is a core gameplay entity in the tactics-game. It represents a single combatant on the isometric turn-based battlefield. Tg units are designed to embody tactical depth through positioning, facing, and modular ability sets that will support future gameplay expansions. Each Tg operates on alternating activation turns, allowing players to strategically maneuver and engage on a grid-based map.

## Attributes
- **ID**: Unique identifier for the Tg unit instance.
- **Name**: Display name of the Tg unit.
- **Faction**: Team or side the unit belongs to.
- **Position**: Current coordinates on the isometric grid.
- **Facing**: Direction the unit is facing, influencing attack and defense.
- **Health**: Numeric value representing the unit’s current vitality.
- **Max Health**: Maximum vitality capacity.
- **Action Points (AP)**: Points available for performing actions per activation.
- **Max Action Points**: Maximum AP a unit can have per activation.
- **Movement Range**: Maximum number of tiles the unit can move during its turn.
- **Armor**: Damage mitigation value.
- **Speed**: Determines turn order and initiative.
- **Status Effects**: Temporary modifiers affecting unit performance.
- **Inventory**: Equipment or items currently held.
- **Abilities List**: Collection of actionable skills and powers available to the Tg unit.

## Abilities
- **Basic Attack**: A default ranged or melee attack that consumes AP and depends on facing and position.
- **Defensive Stance**: An ability that temporarily boosts armor or evasion.
- **Move**: Ability to navigate on the board consuming AP within Movement Range limits.
- **Special Ability Slots**: Configurable slots for future unique skills, e.g., area control, buffs, debuffs.
- **Interact**: Enables environmental interactions such as opening doors or triggering mechanisms.

## Acceptance Criteria
- The Tg unit must instantiate with all defined attributes initialized and validated.
- Position and Facing must update correctly based on player input and game mechanics.
- The unit must consume Action Points properly when executing abilities.
- Movement must be restricted by Movement Range and blocked by obstacles or terrain.
- Basic Attack must correctly calculate damage considering facing, armor, and status effects.
- Status Effects should stack and expire accurately according to game rules.
- Units must accurately display current health and status information on the UI.
- Ability execution must trigger appropriate animations or visual feedback.
- The unit must integrate seamlessly with the turn-based activation system, alternating with opposing units.
- Future ability slots must support modular addition without modification to core Tg logic.
```