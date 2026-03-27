import type {
  BoardCell,
  BoardPreset,
  BoardPresetFieldObject,
  BoardPresetRow,
  BoardState,
  CellKey,
  DeploymentZone,
  SideId,
} from "../model/board";
import { toCellKey } from "../model/board";

function isPlayableColumn(row: BoardPresetRow, column: number): boolean {
  const endExclusive = row.playableColumnStart + row.playableColumnCount;
  return column >= row.playableColumnStart && column < endExclusive;
}

function buildCell(
  row: number,
  column: number,
  deploymentZone: DeploymentZone | null,
  isPlayable: boolean,
  fieldObject: BoardPresetFieldObject | null,
): BoardCell {
  const tileType = fieldObject?.objectType ?? "plain";

  return {
    key: toCellKey({ row, column }),
    row,
    column,
    isPlayable,
    tileType,
    blocksMovement: tileType === "wall" || tileType === "highGrass" || tileType === "vip",
    blocksOccupation: tileType === "wall" || tileType === "highGrass" || tileType === "vip",
    blocksLineOfFire: tileType === "wall",
    deploymentZone,
  };
}

function createEmptyDeploymentIndex(): Record<SideId, CellKey[]> {
  return {
    player1: [],
    player2: [],
  };
}

export function createBoardState(
  boardPreset: BoardPreset,
  fieldObjectOverrides: BoardPresetFieldObject[] = boardPreset.fieldObjects ?? [],
): BoardState {
  const rowsByIndex = new Map<number, BoardPresetRow>(
    boardPreset.rows.map((row) => [row.rowIndex, row]),
  );
  const fieldObjectsByKey = new Map<CellKey, BoardPresetFieldObject>(
    fieldObjectOverrides.map((fieldObject) => [toCellKey(fieldObject), fieldObject]),
  );
  const cellsByKey = {} as Record<CellKey, BoardCell>;
  const playableCellKeys: CellKey[] = [];
  const deploymentZoneCellKeys = createEmptyDeploymentIndex();

  for (let row = 0; row < boardPreset.rowCount; row += 1) {
    const presetRow = rowsByIndex.get(row);

    for (let column = 0; column < boardPreset.columnCount; column += 1) {
      const playable = presetRow ? isPlayableColumn(presetRow, column) : false;
      const deploymentZone = playable && presetRow ? presetRow.deploymentZone : null;
      const cellKey = toCellKey({ row, column });
      const cell = buildCell(row, column, deploymentZone, playable, fieldObjectsByKey.get(cellKey) ?? null);

      cellsByKey[cell.key] = cell;

      if (!playable) {
        continue;
      }

      playableCellKeys.push(cell.key);

      if (deploymentZone === "player1" || deploymentZone === "player2") {
        deploymentZoneCellKeys[deploymentZone].push(cell.key);
      }
    }
  }

  return {
    boardPresetId: boardPreset.boardPresetId,
    rowCount: boardPreset.rowCount,
    columnCount: boardPreset.columnCount,
    cellsByKey,
    playableCellKeys,
    deploymentZoneCellKeys,
  };
}
