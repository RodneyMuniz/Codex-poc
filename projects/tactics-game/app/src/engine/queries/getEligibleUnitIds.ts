import type { BattleState } from "../model/battle";

export function getEligibleUnitIds(battleState: BattleState): string[] {
  const currentSideId = battleState.turnState.currentSideId;
  const currentOpportunity = battleState.turnState.sideOpportunityIndexBySide[currentSideId];

  return battleState.sides[currentSideId].unitInstanceIds.filter((unitId) => {
    const unit = battleState.unitsById[unitId];
    return unit.isAlive && unit.eligibleOnOrAfterSideOpportunity <= currentOpportunity;
  });
}