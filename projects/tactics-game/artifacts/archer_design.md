```markdown
# Archer Design

## Overview
The Archer is a ranged combat unit specializing in striking enemies from a distance with precision and mobility. This unit excels at positioning, utilizing line-of-sight, and maintaining distance to minimize enemy retaliation. Archers play a tactical role in controlling the battlefield by softening enemy forces before direct engagement, supporting frontline units, and exploiting enemy vulnerabilities from afar.

## Attributes
- **Health:** Moderate (e.g., 75 HP)
- **Movement Range:** Medium (e.g., 4 tiles per turn)
- **Attack Range:** Long (e.g., minimum 2 tiles, maximum 5 tiles)
- **Attack Damage:** Moderate, with potential critical strike bonuses
- **Defense:** Low (emphasizing evasion and distance rather than durability)
- **Facing Requirement:** Attacks must be targeted in the direction the Archer is facing; turning costs action points.
- **Action Points:** Standard allotment allowing movement, attack, and aiming actions per turn.

## Abilities
- **Basic Shot:** A ranged attack consuming action points to deal moderate damage to a single enemy within range and line-of-sight.
- **Aimed Shot:** A higher accuracy attack that consumes additional action points for increased damage and critical chance.
- **Rapid Fire:** Allows the Archer to perform two low-damage shots in one turn, with reduced accuracy.
- **Camouflage:** Temporarily increases evasion or makes the Archer harder to detect when stationary and unobstructed.
- **Multi-Tile Movement:** The ability to reposition before or after attacking to maintain optimal distance and line-of-sight.

## Acceptance Criteria
- The Archer unit can move up to its movement range each turn without errors.
- The Archer can perform ranged attacks only within its specified minimum and maximum range.
- Attacks verify and respect line-of-sight constraints.
- Facing direction influences which enemies can be targeted; attacks cannot be made outside the facing arc without turning first.
- Action point costs and spending are correctly tracked for movement, turning, aiming, and attacking actions.
- Abilities function according to their descriptions with appropriate effects, animations, and cooldowns if applicable.
- The Archer's health, defense, and damage values correspond to balance parameters established in design.
- The unit integrates seamlessly with the existing turn-based activation and state management systems.
```