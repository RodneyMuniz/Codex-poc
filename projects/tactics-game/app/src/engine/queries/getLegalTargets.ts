import type { CellKey } from "../model/board";
import type { BattleState, RelativeFacingBucket } from "../model/battle";
import type { Facing } from "../model/unit";
import { toCellKey } from "../model/board";
import { getBurstAreaCellKeys } from "./getBurstAreaCellKeys";

export interface LegalTarget {
  cellKey: CellKey;
  targetUnitId: string | null;
  targetKind: "enemy" | "self" | "fieldObject" | "areaCell" | "objective";
  objectiveOwnerSide: "player1" | "player2" | null;
  relativeFacing: RelativeFacingBucket | null;
  distance: number;
  fieldObjectType: "wall" | "highGrass" | null;
  centerCellKey: CellKey;
  splashCellKeys: CellKey[];
  affectedUnitIds: string[];
  alliedAffectedUnitIds: string[];
  enemyAffectedUnitIds: string[];
}

function manhattanDistance(
  left: { row: number; column: number },
  right: { row: number; column: number },
): number {
  return Math.abs(left.row - right.row) + Math.abs(left.column - right.column);
}

function getOppositeFacing(facing: Facing): Facing {
  if (facing === "north") {
    return "south";
  }

  if (facing === "south") {
    return "north";
  }

  if (facing === "east") {
    return "west";
  }

  return "east";
}

export function getRelativeFacingBucket(
  attackerCell: { row: number; column: number },
  defenderCell: { row: number; column: number },
  defenderFacing: Facing,
): RelativeFacingBucket {
  const deltaRow = attackerCell.row - defenderCell.row;
  const deltaColumn = attackerCell.column - defenderCell.column;

  if (deltaRow !== 0 && deltaColumn !== 0 && Math.abs(deltaRow) === Math.abs(deltaColumn)) {
    return "side";
  }

  const approachDirection: Facing =
    Math.abs(deltaRow) > Math.abs(deltaColumn)
      ? deltaRow < 0
        ? "north"
        : "south"
      : deltaColumn < 0
        ? "west"
        : "east";

  if (approachDirection === defenderFacing) {
    return "front";
  }

  if (approachDirection === getOppositeFacing(defenderFacing)) {
    return "back";
  }

  return "side";
}

function manhattanLineOfFireIsClear(
  battleState: BattleState,
  from: { row: number; column: number },
  to: { row: number; column: number },
): boolean {
  if (from.row !== to.row && from.column !== to.column) {
    return true;
  }

  if (from.row === to.row) {
    const start = Math.min(from.column, to.column) + 1;
    const end = Math.max(from.column, to.column);

    for (let column = start; column < end; column += 1) {
      if (battleState.boardState.cellsByKey[toCellKey({ row: from.row, column })]?.blocksLineOfFire) {
        return false;
      }
    }

    return true;
  }

  const start = Math.min(from.row, to.row) + 1;
  const end = Math.max(from.row, to.row);

  for (let row = start; row < end; row += 1) {
    if (battleState.boardState.cellsByKey[toCellKey({ row, column: from.column })]?.blocksLineOfFire) {
      return false;
    }
  }

  return true;
}

export function getLegalTargets(battleState: BattleState, unitId: string): LegalTarget[] {
  const actor = battleState.unitsById[unitId];
  const definition = battleState.unitDefinitions[actor.unitDefinitionId];

  if (actor.carriedVipSideId) {
    return [];
  }

  if (definition.actionType === "healAllAllies") {
    return [
      {
        cellKey: toCellKey(actor.anchorCell),
        targetUnitId: actor.unitInstanceId,
        targetKind: "self",
        objectiveOwnerSide: null,
        relativeFacing: null,
        distance: 0,
        fieldObjectType: null,
        centerCellKey: toCellKey(actor.anchorCell),
        splashCellKeys: [],
        affectedUnitIds: [actor.unitInstanceId],
        alliedAffectedUnitIds: [actor.unitInstanceId],
        enemyAffectedUnitIds: [],
      },
    ];
  }

  if (definition.actionType === "castPyromancerBurst") {
    return Object.values(battleState.boardState.cellsByKey)
      .filter((cell) => cell.isPlayable && cell.tileType !== "wall")
      .map((cell) => {
        const burstArea = getBurstAreaCellKeys(battleState.boardState, { row: cell.row, column: cell.column });
        const affectedUnitIds = [burstArea.centerCellKey, ...burstArea.splashCellKeys]
          .map((cellKey) => battleState.occupancyByCellKey[cellKey] ?? null)
          .filter((unitId): unitId is string => unitId !== null);
        const alliedAffectedUnitIds = affectedUnitIds.filter(
          (unitId) => battleState.unitsById[unitId].ownerSide === actor.ownerSide,
        );
        const enemyAffectedUnitIds = affectedUnitIds.filter(
          (unitId) => battleState.unitsById[unitId].ownerSide !== actor.ownerSide,
        );

        return {
          cellKey: cell.key,
          targetUnitId: battleState.occupancyByCellKey[cell.key] ?? null,
          targetKind: "areaCell" as const,
          objectiveOwnerSide: null,
          relativeFacing: null,
          distance: manhattanDistance(actor.anchorCell, { row: cell.row, column: cell.column }),
          fieldObjectType: null,
          centerCellKey: burstArea.centerCellKey,
          splashCellKeys: burstArea.splashCellKeys,
          affectedUnitIds,
          alliedAffectedUnitIds,
          enemyAffectedUnitIds,
        };
      })
      .filter((target) => target.distance <= definition.attackRange)
      .sort((left, right) => left.distance - right.distance || left.cellKey.localeCompare(right.cellKey));
  }

  const unitTargets = Object.values(battleState.unitsById)
    .filter((candidate) => candidate.isAlive && candidate.ownerSide !== actor.ownerSide)
    .map((target) => {
      const cellKey = toCellKey(target.anchorCell);

      return {
        cellKey,
        targetUnitId: target.unitInstanceId,
        targetKind: "enemy" as const,
        objectiveOwnerSide: null,
        relativeFacing: getRelativeFacingBucket(actor.anchorCell, target.anchorCell, target.facing),
        distance: manhattanDistance(actor.anchorCell, target.anchorCell),
        fieldObjectType: null,
        centerCellKey: cellKey,
        splashCellKeys: [],
        affectedUnitIds: [target.unitInstanceId],
        alliedAffectedUnitIds: [],
        enemyAffectedUnitIds: [target.unitInstanceId],
      };
    })
    .filter((target) => target.distance <= definition.attackRange)
    .filter((target) => manhattanLineOfFireIsClear(battleState, actor.anchorCell, battleState.unitsById[target.targetUnitId].anchorCell));

  const fieldObjectTargets = Object.values(battleState.boardState.cellsByKey)
    .filter((cell) => cell.tileType === "highGrass")
    .map((cell) => ({
      cellKey: cell.key,
      targetUnitId: cell.key,
      targetKind: "fieldObject" as const,
      objectiveOwnerSide: null,
      relativeFacing: null,
      distance: manhattanDistance(actor.anchorCell, { row: cell.row, column: cell.column }),
      fieldObjectType: "highGrass" as const,
      centerCellKey: cell.key,
      splashCellKeys: [],
      affectedUnitIds: [],
      alliedAffectedUnitIds: [],
      enemyAffectedUnitIds: [],
    }))
    .filter((target) => target.distance <= definition.attackRange);

  const objectiveTargets = (["player1", "player2"] as const).flatMap((sideId) => {
    const objective = battleState.objectives[sideId];
    if (!objective || objective.ownerSide !== actor.ownerSide || objective.state === "carried" || !objective.cellKey) {
      return [];
    }

    const objectiveCell = battleState.boardState.cellsByKey[objective.cellKey];
    const distance = manhattanDistance(actor.anchorCell, objectiveCell);
    if (distance !== 1) {
      return [];
    }

    return [
      {
        cellKey: objective.cellKey,
        targetUnitId: objective.cellKey,
        targetKind: "objective" as const,
        objectiveOwnerSide: objective.ownerSide,
        relativeFacing: null,
        distance,
        fieldObjectType: null,
        centerCellKey: objective.cellKey,
        splashCellKeys: [],
        affectedUnitIds: [],
        alliedAffectedUnitIds: [],
        enemyAffectedUnitIds: [],
      },
    ];
  });

  return [...unitTargets, ...fieldObjectTargets, ...objectiveTargets]
    .sort((left, right) => left.distance - right.distance || left.cellKey.localeCompare(right.cellKey));
}
