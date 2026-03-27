import type { BoardState, DeploymentZone } from "../../engine/model/board";

export interface BoardTileViewModel {
  key: string;
  row: number;
  column: number;
  isPlayable: boolean;
  deploymentZone: DeploymentZone | null;
}

export interface BoardViewModel {
  rowCount: number;
  columnCount: number;
  tiles: BoardTileViewModel[];
}

export function createBoardViewModel(boardState: BoardState): BoardViewModel {
  const tiles = Object.values(boardState.cellsByKey)
    .sort((left, right) => {
      if (left.row !== right.row) {
        return left.row - right.row;
      }

      return left.column - right.column;
    })
    .map((cell) => ({
      key: cell.key,
      row: cell.row,
      column: cell.column,
      isPlayable: cell.isPlayable,
      deploymentZone: cell.deploymentZone,
    }));

  return {
    rowCount: boardState.rowCount,
    columnCount: boardState.columnCount,
    tiles,
  };
}