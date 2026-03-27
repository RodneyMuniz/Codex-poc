import type { BattleState } from "../model/battle";
import { toCellKey } from "../model/board";
import { getOpposingSide } from "../setup/createSandboxBattle";

export function getWinnerSideId(battleState: BattleState): "player1" | "player2" | null {
  const player1Alive = battleState.sides.player1.unitInstanceIds.some((unitId) => battleState.unitsById[unitId].isAlive);
  const player2Alive = battleState.sides.player2.unitInstanceIds.some((unitId) => battleState.unitsById[unitId].isAlive);

  if (battleState.winConditions.eliminateAllEnemies) {
    if (!player2Alive && player1Alive) {
      return "player1";
    }

    if (!player1Alive && player2Alive) {
      return "player2";
    }

    if (!player1Alive && !player2Alive) {
      return getOpposingSide(battleState.turnState.currentSideId);
    }
  }

  if (battleState.winConditions.markedLeader) {
    const player1LeaderAlive = battleState.sides.player1.unitInstanceIds
      .map((unitId) => battleState.unitsById[unitId])
      .some((unit) => unit.isLeader && unit.isAlive);
    const player2LeaderAlive = battleState.sides.player2.unitInstanceIds
      .map((unitId) => battleState.unitsById[unitId])
      .some((unit) => unit.isLeader && unit.isAlive);

    if (player1LeaderAlive && !player2LeaderAlive) {
      return "player1";
    }

    if (player2LeaderAlive && !player1LeaderAlive) {
      return "player2";
    }
  }

  if (battleState.winConditions.captureAndExtract) {
    for (const sideId of ["player1", "player2"] as const) {
      const objective = battleState.objectives[sideId];
      if (!objective?.carrierUnitId) {
        continue;
      }

      const carrier = battleState.unitsById[objective.carrierUnitId];
      if (!carrier?.isAlive) {
        continue;
      }

      const carrierCellKey = toCellKey(carrier.anchorCell);
      if (objective.rescueCellKeys.includes(carrierCellKey)) {
        return sideId;
      }
    }
  }

  return null;
}
