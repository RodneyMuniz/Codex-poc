```markdown
# Healer Design

## Overview

The Healer is a support unit in the tactics game designed to sustain allied units during combat. Positioned typically behind front-line units, the Healer excels at restoring health and removing negative status effects. The unit emphasizes strategic positioning and timing to maximize team survivability without direct offensive capabilities.

## Attributes

- **Health:** Moderate (e.g., 75 HP)
- **Movement Range:** Medium (e.g., 4 tiles per turn)
- **Attack Range:** None (Healer is non-offensive)
- **Defense:** Low to Moderate (e.g., 10 Defense)
- **Speed:** Average (e.g., initiative determines turn order)

## Abilities

- **Heal:** Restore a moderate amount of HP (e.g., 20 HP) to a single ally within 3 tiles.
- **Group Heal (Cooldown: 3 turns):** Restore a lesser amount of HP (e.g., 10 HP) to all allies within 2 tiles.
- **Cleanse:** Remove one negative status effect from an ally within 3 tiles.
- **Protective Aura (Passive):** Allies within 1 tile gain +2 Defense while Healer is alive and adjacent.

## Acceptance Criteria

- The Healer can move up to its movement range each turn.
- The Heal ability restores the defined HP amount to a valid ally within range.
- Group Heal affects all valid allies within range and respects cooldown restrictions.
- Cleanse successfully removes one negative status from a targeted ally if present.
- Protective Aura passive automatically applies defense boost to adjacent allies.
- Healer cannot perform direct attacks on enemy units.
- UI elements clearly indicate Healer abilities, ranges, cooldowns, and status effects.
- Gameplay tests demonstrate the Healer's ability to sustain the team without unbalancing offensive power.
```