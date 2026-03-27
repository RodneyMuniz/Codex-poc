import type { SupportSnapshot } from "../model/battle";
import type { UnitDefinition, UnitInstance } from "../model/unit";

export function resolveSupportAction(
  sourceUnit: UnitInstance,
  sourceDefinition: UnitDefinition,
  allies: UnitInstance[],
  unitDefinitions: Record<string, UnitDefinition>,
): SupportSnapshot {
  const healAmount = sourceDefinition.healAmount ?? 0;
  const healingChanges = allies
    .filter((ally) => ally.isAlive)
    .map((ally) => {
      const allyDefinition = unitDefinitions[ally.unitDefinitionId];
      const healedAmount = Math.max(0, Math.min(healAmount, allyDefinition.maxHp - ally.currentHp));

      return {
        unitId: ally.unitInstanceId,
        healedAmount,
        resultingHp: ally.currentHp + healedAmount,
      };
    })
    .filter((change) => change.healedAmount > 0);

  return {
    sourceUnitId: sourceUnit.unitInstanceId,
    targetUnitId: sourceUnit.unitInstanceId,
    healingChanges,
  };
}