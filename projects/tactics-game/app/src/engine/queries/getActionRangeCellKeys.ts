import type { CellKey } from "../model/board";
import type { BattleState } from "../model/battle";
import { toCellKey } from "../model/board";
import { getLegalTargets } from "./getLegalTargets";

function manhattanDistance(
  left: { row: number; column: number },
  right: { row: number; column: number },
): number {
  return Math.abs(left.row - right.row) + Math.abs(left.column - right.column);
}

export function getActionRangeCellKeys(battleState: BattleState, unitId: string): CellKey[] {
  const unit = battleState.unitsById[unitId];
  const definition = battleState.unitDefinitions[unit.unitDefinitionId];

  if (definition.actionType === "castPyromancerBurst") {
    return getLegalTargets(battleState, unitId).map((target) => target.cellKey);
  }

  if (definition.actionType !== "attackEnemy") {
    return [];
  }

  return Object.values(battleState.boardState.cellsByKey)
    .filter((cell) => cell.isPlayable)
    .filter((cell) => manhattanDistance(unit.anchorCell, { row: cell.row, column: cell.column }) <= definition.attackRange)
    .map((cell) => toCellKey({ row: cell.row, column: cell.column }));
}
