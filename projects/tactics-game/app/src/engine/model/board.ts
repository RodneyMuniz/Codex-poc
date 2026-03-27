export type SideId = "player1" | "player2";

export type DeploymentZone = SideId | "neutral";

export type CellKey = `r${number}c${number}`;
export type FieldObjectType = "wall" | "highGrass" | "vip";

export interface GridCoordinate {
  row: number;
  column: number;
}

export interface BoardPresetRow {
  rowIndex: number;
  playableColumnStart: number;
  playableColumnCount: number;
  deploymentZone: DeploymentZone;
}

export interface BoardPreset {
  boardPresetId: string;
  rowCount: number;
  columnCount: number;
  rows: BoardPresetRow[];
  fieldObjects?: BoardPresetFieldObject[];
}

export interface BoardPresetFieldObject extends GridCoordinate {
  objectType: FieldObjectType;
  ownerSide?: SideId;
}

export interface BoardCell extends GridCoordinate {
  key: CellKey;
  isPlayable: boolean;
  tileType: "plain" | FieldObjectType;
  blocksMovement: boolean;
  blocksOccupation: boolean;
  blocksLineOfFire: boolean;
  deploymentZone: DeploymentZone | null;
}

export interface BoardState {
  boardPresetId: string;
  rowCount: number;
  columnCount: number;
  cellsByKey: Record<CellKey, BoardCell>;
  playableCellKeys: CellKey[];
  deploymentZoneCellKeys: Record<SideId, CellKey[]>;
}

export function toCellKey({ row, column }: GridCoordinate): CellKey {
  return `r${row}c${column}`;
}
