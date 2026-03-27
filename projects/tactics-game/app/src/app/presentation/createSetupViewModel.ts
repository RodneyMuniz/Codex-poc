import type { BoardPresetFieldObject, BoardState, CellKey, FieldObjectType, SideId } from "../../engine/model/board";
import type { Facing, UnitDefinition } from "../../engine/model/unit";
import { toCellKey } from "../../engine/model/board";

export interface SetupPlacement {
  placementId: string;
  ownerSide: SideId;
  isLeader: boolean;
  unitDefinitionId: string;
  anchorCell: {
    row: number;
    column: number;
  };
  facing: Facing;
}

export interface SetupFieldObjectPlacement extends BoardPresetFieldObject {
  placementId: string;
  ownerSide: SideId;
}

export interface SetupTileViewModel {
  key: CellKey;
  row: number;
  column: number;
  isPlayable: boolean;
  deploymentZone: SideId | "neutral" | null;
  placementId: string | null;
  unitLabel: string | null;
  isLeader: boolean;
  occupyingSide: SideId | null;
  facing: Facing | null;
  fieldObjectType: FieldObjectType | null;
  fieldObjectOwnerSide: SideId | null;
}

export interface SetupViewModel {
  rowCount: number;
  columnCount: number;
  tiles: SetupTileViewModel[];
}

export function createSetupViewModel(
  boardState: BoardState,
  placements: SetupPlacement[],
  fieldObjectPlacements: SetupFieldObjectPlacement[],
  unitDefinitions: Record<string, UnitDefinition>,
): SetupViewModel {
  const placementsByKey = new Map(placements.map((placement) => [toCellKey(placement.anchorCell), placement]));
  const fieldObjectPlacementsByKey = new Map(fieldObjectPlacements.map((placement) => [toCellKey(placement), placement]));

  const tiles = Object.values(boardState.cellsByKey)
    .sort((left, right) => {
      if (left.row !== right.row) {
        return left.row - right.row;
      }

      return left.column - right.column;
    })
    .map((cell) => {
      const placement = placementsByKey.get(cell.key) ?? null;
      const fieldObjectPlacement = fieldObjectPlacementsByKey.get(cell.key) ?? null;

      return {
        key: cell.key,
        row: cell.row,
        column: cell.column,
        isPlayable: cell.isPlayable,
        deploymentZone: cell.deploymentZone,
        placementId: placement?.placementId ?? null,
        unitLabel: placement ? unitDefinitions[placement.unitDefinitionId].name : null,
        isLeader: placement?.isLeader ?? false,
        occupyingSide: placement?.ownerSide ?? null,
        facing: placement?.facing ?? null,
        fieldObjectType: fieldObjectPlacement?.objectType ?? (cell.tileType === "plain" ? null : cell.tileType),
        fieldObjectOwnerSide: fieldObjectPlacement?.ownerSide ?? null,
      };
    });

  return {
    rowCount: boardState.rowCount,
    columnCount: boardState.columnCount,
    tiles,
  };
}
