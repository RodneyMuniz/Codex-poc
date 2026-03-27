import type { CombatSnapshot, RelativeFacingBucket } from "../model/battle";
import type { UnitDefinition, UnitInstance } from "../model/unit";

const missChanceByFacing: Record<RelativeFacingBucket, number> = {
  front: 0.3,
  side: 0.15,
  back: 0,
};

export function resolveCombat(
  attacker: UnitInstance,
  attackerDefinition: UnitDefinition,
  defender: UnitInstance,
  defenderDefinition: UnitDefinition,
  relativeFacing: RelativeFacingBucket,
  randomValue: number,
): CombatSnapshot {
  const missChance = missChanceByFacing[relativeFacing];
  const didHit = randomValue >= missChance;
  const damageDealt = didHit ? Math.max(1, attackerDefinition.attack - defenderDefinition.defence) : 0;
  const defenderRemainingHp = didHit ? defender.currentHp - damageDealt : defender.currentHp;

  return {
    attackerId: attacker.unitInstanceId,
    defenderId: defender.unitInstanceId,
    relativeFacing,
    didHit,
    damageDealt,
    defenderRemainingHp,
    defenderDefeated: defenderRemainingHp <= 0,
  };
}