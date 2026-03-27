import { MAX_UNITS_PER_SIDE, PLAYER_ARMY_BUDGET } from "../data/setupRules";
import type { SandboxSideLayout } from "../model/battle";
import type { UnitDefinition } from "../model/unit";

function assert(condition: boolean, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

export function validateArmySelection(
  sideLayout: SandboxSideLayout,
  definitions: Record<string, UnitDefinition>,
  pointsBudget: number = PLAYER_ARMY_BUDGET,
  maxUnitsPerSide: number | null = MAX_UNITS_PER_SIDE,
): void {
  assert(sideLayout.units.length > 0, `${sideLayout.sideId} must field at least 1 unit.`);
  if (maxUnitsPerSide !== null) {
    assert(
      sideLayout.units.length <= maxUnitsPerSide,
      `${sideLayout.sideId} cannot field more than ${maxUnitsPerSide} units.`,
    );
  }

  const totalWeight = sideLayout.units.reduce((sum, unit) => {
    const definition = definitions[unit.unitDefinitionId];
    assert(definition !== undefined, `Missing unit definition: ${unit.unitDefinitionId}`);
    return sum + definition.weight;
  }, 0);

  assert(totalWeight <= pointsBudget, `${sideLayout.sideId} exceeds the ${pointsBudget}-point budget.`);
}
