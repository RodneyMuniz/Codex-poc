import type { FieldObjectType } from "../../engine/model/board";
import type { CellKey } from "../../engine/model/board";
import type { BattleState } from "../../engine/model/battle";
import type { Facing } from "../../engine/model/unit";

export interface BattleTileViewModel {
  key: CellKey;
  row: number;
  column: number;
  isPlayable: boolean;
  deploymentZone: "player1" | "player2" | "neutral" | null;
  occupyingUnitId: string | null;
  occupyingSide: "player1" | "player2" | null;
  unitLabel: string | null;
  isLeader: boolean;
  carriedVipSideId: "player1" | "player2" | null;
  remainingCooldown: number;
  currentHp: number | null;
  maxHp: number | null;
  facing: Facing | null;
  fieldObjectType: FieldObjectType | null;
  vipOwnerSide: "player1" | "player2" | null;
  vipLabel: string | null;
  rescueZoneForSide: "player1" | "player2" | null;
}

export interface BattleViewModel {
  rowCount: number;
  columnCount: number;
  tiles: BattleTileViewModel[];
}

export function createBattleViewModel(battleState: BattleState): BattleViewModel {
  const vipByCellKey = new Map<string, "player1" | "player2">();
  const rescueZoneByCellKey = new Map<string, "player1" | "player2">();

  (["player1", "player2"] as const).forEach((sideId) => {
    const objective = battleState.objectives[sideId];
    if (objective?.cellKey) {
      vipByCellKey.set(objective.cellKey, sideId);
    }
    objective?.rescueCellKeys.forEach((cellKey) => rescueZoneByCellKey.set(cellKey, sideId));
  });

  const tiles = Object.values(battleState.boardState.cellsByKey)
    .sort((left, right) => {
      if (left.row !== right.row) {
        return left.row - right.row;
      }

      return left.column - right.column;
    })
    .map((cell) => {
      const occupyingUnitId = battleState.occupancyByCellKey[cell.key] ?? null;
      const occupyingUnit = occupyingUnitId ? battleState.unitsById[occupyingUnitId] : null;
      const definition = occupyingUnit ? battleState.unitDefinitions[occupyingUnit.unitDefinitionId] : null;
      const currentOpportunity = occupyingUnit
        ? battleState.turnState.sideOpportunityIndexBySide[occupyingUnit.ownerSide]
        : 0;

      return {
        key: cell.key,
        row: cell.row,
        column: cell.column,
        isPlayable: cell.isPlayable,
        deploymentZone: cell.deploymentZone,
        occupyingUnitId,
        occupyingSide: occupyingUnit?.ownerSide ?? null,
        unitLabel: definition?.name ?? null,
        isLeader: occupyingUnit?.isLeader ?? false,
        carriedVipSideId: occupyingUnit?.carriedVipSideId ?? null,
        remainingCooldown: occupyingUnit
          ? Math.max(0, occupyingUnit.eligibleOnOrAfterSideOpportunity - currentOpportunity)
          : 0,
        currentHp: occupyingUnit?.currentHp ?? null,
        maxHp: definition?.maxHp ?? null,
        facing: occupyingUnit?.facing ?? null,
        fieldObjectType: cell.tileType === "plain" ? null : cell.tileType,
        vipOwnerSide: vipByCellKey.get(cell.key) ?? null,
        vipLabel: vipByCellKey.has(cell.key) ? "VIP" : null,
        rescueZoneForSide: rescueZoneByCellKey.get(cell.key) ?? null,
      };
    });

  return {
    rowCount: battleState.boardState.rowCount,
    columnCount: battleState.boardState.columnCount,
    tiles,
  };
}
