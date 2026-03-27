# Evidence Unit Design Document

## Overview
The Evidence unit represents a specialized tactical asset within the game, designed to influence battlefield intelligence and strategic decision-making. It functions primarily as a support unit capable of gathering, revealing, or manipulating information about enemy units and terrain. Evidence units are critical for enabling informed tactical maneuvers and can alter the flow of combat by providing actionable insights.

## Attributes
- **Health:** Low to moderate, reflecting its support role and vulnerability.
- **Movement Range:** Moderate, allowing repositioning to optimal vantage points.
- **Detection Radius:** Defines the area around the unit where it can gather intelligence.
- **Stealth Resistance:** Moderate, enabling it to detect hidden or cloaked enemy units.
- **Durability:** Lower than frontline combat units, emphasizing protection through positioning.

## Abilities
- **Scan Area:** Reveals enemy units and traps within the detection radius for a limited number of turns.
- **Mark Target:** Applies a debuff to an enemy unit, increasing damage taken from allied units for a set duration.
- **Deploy Sensor:** Places a stationary device on the battlefield that extends detection capabilities in a fixed radius.
- **Intercept Communication:** Temporarily disrupts enemy unit coordination, reducing their movement or action efficiency.

## Acceptance Criteria
- The Evidence unit must be selectable and deployable within the game interface.
- Its detection radius and abilities must function correctly, revealing enemy units and traps as designed.
- Abilities must have clear visual and audio feedback when activated.
- Mark Target debuff must correctly increase damage received by the marked enemy.
- Deploy Sensor devices must persist on the battlefield and provide extended detection.
- Intercept Communication must apply the intended debuff effects on enemy units within range.
- The unit's health and movement attributes must align with the documented values.
- The unit must be vulnerable to frontline attacks, encouraging strategic positioning.
- All abilities must have cooldowns and usage limits consistent with game balance.
- The unit's presence and abilities must integrate seamlessly with existing game mechanics and UI elements.

---

*Document path: projects/tactics-game/artifacts/evidence_design.md*