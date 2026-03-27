import { MAX_UNITS_PER_SIDE } from "../data/setupRules";
import type { BoardState, CellKey, SideId } from "../model/board";
import type { SandboxSideLayout } from "../model/battle";
import { toCellKey } from "../model/board";

function assert(condition: boolean, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

export function validateDeployment(
  boardState: BoardState,
  sideLayouts: SandboxSideLayout[],
  maxUnitsPerSide: number | null = MAX_UNITS_PER_SIDE,
): void {
  const occupied = new Set<CellKey>();

  for (const sideLayout of sideLayouts) {
    assert(sideLayout.units.length > 0, `${sideLayout.sideId} must deploy at least 1 unit.`);
    if (maxUnitsPerSide !== null) {
      assert(
        sideLayout.units.length <= maxUnitsPerSide,
        `${sideLayout.sideId} cannot deploy more than ${maxUnitsPerSide} units.`,
      );
    }

    for (const unit of sideLayout.units) {
      const cellKey = toCellKey(unit.anchorCell);
      const cell = boardState.cellsByKey[cellKey];
      const requiredZone: SideId = sideLayout.sideId;

      assert(cell !== undefined, `Deployment cell ${cellKey} is outside the board.`);
      assert(cell.isPlayable, `Deployment cell ${cellKey} is not playable.`);
      assert(cell.deploymentZone === requiredZone, `Deployment cell ${cellKey} is not legal for ${requiredZone}.`);
      assert(unit.anchorCell.row !== 5, `Deployment cell ${cellKey} cannot use the neutral middle row.`);
      assert(!cell.blocksOccupation, `Deployment cell ${cellKey} is blocked by a field object.`);
      assert(!occupied.has(cellKey), `Deployment cell ${cellKey} is already occupied.`);

      occupied.add(cellKey);
    }
  }
}
