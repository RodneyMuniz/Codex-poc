import type { CellKey, GridCoordinate } from "../model/board";
import type { BattleState } from "../model/battle";
import { toCellKey } from "../model/board";

const directions = [
  { row: -1, column: 0 },
  { row: 1, column: 0 },
  { row: 0, column: -1 },
  { row: 0, column: 1 },
];

export function getReachableCellKeys(battleState: BattleState, unitId: string): CellKey[] {
  const unit = battleState.unitsById[unitId];
  const unitDefinition = battleState.unitDefinitions[unit.unitDefinitionId];
  const startKey = toCellKey(unit.anchorCell);
  const visited = new Set<CellKey>([startKey]);
  const reachable = new Set<CellKey>([startKey]);
  const queue: Array<{ coordinate: GridCoordinate; distance: number }> = [
    { coordinate: unit.anchorCell, distance: 0 },
  ];

  while (queue.length > 0) {
    const current = queue.shift();

    if (!current) {
      continue;
    }

    if (current.distance >= unitDefinition.movement) {
      continue;
    }

    for (const direction of directions) {
      const nextCoordinate = {
        row: current.coordinate.row + direction.row,
        column: current.coordinate.column + direction.column,
      };
      const nextKey = toCellKey(nextCoordinate);
      const nextCell = battleState.boardState.cellsByKey[nextKey];

      if (!nextCell || !nextCell.isPlayable || visited.has(nextKey)) {
        continue;
      }

      if (nextCell.blocksMovement || nextCell.blocksOccupation) {
        visited.add(nextKey);
        continue;
      }

      const occupyingUnitId = battleState.occupancyByCellKey[nextKey];
      const isBlocked = Boolean(occupyingUnitId && occupyingUnitId !== unitId);

      visited.add(nextKey);

      if (isBlocked) {
        continue;
      }

      reachable.add(nextKey);
      queue.push({ coordinate: nextCoordinate, distance: current.distance + 1 });
    }
  }

  return Array.from(reachable.values());
}

export function isLegalMoveDestination(
  battleState: BattleState,
  unitId: string,
  destinationKey: CellKey,
): boolean {
  return getReachableCellKeys(battleState, unitId).includes(destinationKey);
}
