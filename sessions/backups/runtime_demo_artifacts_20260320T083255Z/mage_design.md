```markdown
# Mage Design

## Overview
The Mage is a ranged spellcaster unit specializing in magical damage and crowd control. Positioned as a high-impact glass cannon, the Mage excels at dealing area-of-effect damage and debilitating enemies from a distance but has low defense and health.

## Attributes
- **HP:** Low (e.g., 40)
- **Movement Range:** Medium (e.g., 3 tiles per turn)
- **Attack Range:** Long (e.g., 2-4 tiles)
- **Defense:** Low (e.g., 5)
- **Magic Power:** High (e.g., 15)
- **Speed:** Medium (affects turn order)

## Abilities
- **Fireball**
  - Type: Ranged attack
  - Effect: Deals moderate area-of-effect fire damage to all enemies within a 2-tile radius.
  - Cooldown: 3 turns
- **Frost Nova**
  - Type: Crowd control spell
  - Effect: Deals minor ice damage and slows enemy movement by 50% for 2 turns in a 1-tile radius.
  - Cooldown: 4 turns
- **Arcane Shield**
  - Type: Defensive buff
  - Effect: Grants temporary increased defense (+10) to the Mage for 2 turns.
  - Cooldown: 5 turns

## Acceptance Criteria
- The Mage unit can be instantiated with defined attributes.
- All abilities execute according to their defined effects, cooldowns, and ranges.
- The Mage’s low defense and health make positioning critical in gameplay mechanics.
- The abilities must visually and mechanically differentiate the Mage as a ranged magic user.
- Cooldowns and area effects are correctly applied and visually indicated in the UI.
- Abilities affect appropriate targets (enemies) within specified ranges.
- The Mage is balanced according to MVP lean design principles and plays a distinct tactical role.
```