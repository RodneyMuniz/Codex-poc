import type { BoardState, CellKey } from "../model/board";
import { toCellKey } from "../model/board";

export interface BurstAreaCellKeys {
  centerCellKey: CellKey;
  splashCellKeys: CellKey[];
}

export function getBurstAreaCellKeys(
  boardState: BoardState,
  center: { row: number; column: number },
): BurstAreaCellKeys {
  const orthogonalOffsets = [
    { rowOffset: -1, columnOffset: 0 },
    { rowOffset: 1, columnOffset: 0 },
    { rowOffset: 0, columnOffset: -1 },
    { rowOffset: 0, columnOffset: 1 },
  ];

  const splashCellKeys = orthogonalOffsets
    .map(({ rowOffset, columnOffset }) =>
      boardState.cellsByKey[toCellKey({ row: center.row + rowOffset, column: center.column + columnOffset })] ?? null,
    )
    .filter((cell): cell is NonNullable<typeof cell> => cell !== null && cell.isPlayable)
    .map((cell) => cell.key);

  return {
    centerCellKey: toCellKey(center),
    splashCellKeys,
  };
}
