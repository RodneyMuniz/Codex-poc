# Component Design Document

## Overview
The Component unit represents a fundamental entity within the tactics-game, embodying a modular and extensible game piece used in turn-based tactical combat. Each Component is designed to interact with the game environment and other units through positioning, facing, and activation mechanics. The design supports future expansion by allowing flexible attribute and ability configurations.

## Attributes
- **ID**: Unique identifier for the Component.
- **Name**: Descriptive name of the Component.
- **Health**: Current and maximum health points.
- **Position**: Coordinates on the isometric grid.
- **Facing**: Direction the Component is oriented towards.
- **Movement Range**: Number of tiles the Component can move per activation.
- **Action Points**: Points available for performing actions each turn.
- **Armor**: Damage mitigation value.
- **Status Effects**: List of current status modifiers affecting the Component.
- **Team/Faction**: Identifier for the Component's allegiance.

## Abilities
- **Move**: Relocate the Component within its movement range.
- **Attack**: Perform an offensive action against an enemy within range.
- **Defend**: Enter a defensive stance to reduce incoming damage.
- **Special Ability**: Unique skill or power specific to the Component type.
- **Wait**: Skip the current activation without performing actions.

## Acceptance Criteria
- The Component must be instantiable with all defined attributes.
- Movement must respect the movement range and board boundaries.
- Facing must update correctly after movement or actions.
- Abilities must consume appropriate action points and trigger expected effects.
- Status effects must apply and expire according to game rules.
- Components must correctly register team affiliation for targeting and interaction.
- The design must allow easy addition of new attributes and abilities without breaking existing functionality.

---

*Document path: projects/tactics-game/artifacts/component_design.md*