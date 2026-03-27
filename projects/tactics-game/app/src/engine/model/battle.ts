import type { BoardPresetFieldObject, BoardState, CellKey, SideId } from "./board";
import type { Facing, UnitDefinition, UnitInstance } from "./unit";

export type BattleStatus = "active" | "victory";

export type ActivationStage =
  | "selectUnit"
  | "move"
  | "attackOrSkip"
  | "rotate"
  | "forcedPass";

export type RelativeFacingBucket = "front" | "side" | "back";

export interface SideState {
  sideId: SideId;
  label: string;
  controllerType: "human";
  unitInstanceIds: string[];
}

export interface WinConditions {
  eliminateAllEnemies: boolean;
  markedLeader: boolean;
  captureAndExtract: boolean;
}

export interface ObjectiveState {
  kind: "vip";
  ownerSide: SideId;
  state: "idle" | "carried" | "dropped" | "extracted";
  cellKey: CellKey | null;
  carrierUnitId: string | null;
  rescueCellKeys: CellKey[];
}

export type ObjectivesBySide = Partial<Record<SideId, ObjectiveState>>;

export interface TurnState {
  startingSideId: SideId;
  currentSideId: SideId;
  globalOpportunityIndex: number;
  sideOpportunityIndexBySide: Record<SideId, number>;
  activeUnitId: string | null;
  activationStage: ActivationStage;
  activationSummary: ActivationSummary | null;
}

export interface ActivationSummary {
  actingUnitId: string;
  actingSideId: SideId;
  startCellKey: CellKey;
  endCellKey: CellKey;
  actionSummary: string;
}

export interface PositionChange {
  unitInstanceId: string;
  from: CellKey;
  to: CellKey;
}

export interface CombatSnapshot {
  attackerId: string;
  defenderId: string;
  relativeFacing: RelativeFacingBucket;
  didHit: boolean;
  damageDealt: number;
  defenderRemainingHp: number;
  defenderDefeated: boolean;
}

export interface HealingChange {
  unitId: string;
  healedAmount: number;
  resultingHp: number;
}

export interface SupportSnapshot {
  sourceUnitId: string;
  targetUnitId: string;
  healingChanges: HealingChange[];
}

export interface ActionResultSnapshot {
  actionType: "battleStart" | "selectUnit" | "move" | "attack" | "support" | "skipAttack" | "rotate" | "forcedPass";
  actingUnitId: string | null;
  targetUnitId: string | null;
  hitResult: CombatSnapshot | null;
  supportResult: SupportSnapshot | null;
  defeatedUnitIds: string[];
  positionChanges: PositionChange[];
  nextTurnSideId: SideId | null;
  summary: string;
}

export interface BattleState {
  battleId: string;
  status: BattleStatus;
  winConditions: WinConditions;
  objectives: ObjectivesBySide;
  boardState: BoardState;
  sides: Record<SideId, SideState>;
  unitDefinitions: Record<string, UnitDefinition>;
  unitsById: Record<string, UnitInstance>;
  occupancyByCellKey: Partial<Record<CellKey, string>>;
  turnState: TurnState;
  lastResolvedAction: ActionResultSnapshot | null;
  winnerSideId: SideId | null;
}

export interface SandboxUnitLayout {
  unitDefinitionId: string;
  isLeader?: boolean;
  anchorCell: {
    row: number;
    column: number;
  };
  facing?: Facing;
}

export interface SandboxSideLayout {
  sideId: SideId;
  units: SandboxUnitLayout[];
}

export interface SandboxBattleOptions {
  battleId?: string;
  boardPresetId?: string;
  randomValue?: () => number;
  pointsBudget?: number;
  maxUnitsPerSide?: number | null;
  winConditions?: Partial<WinConditions>;
  playerSideLayout?: SandboxSideLayout;
  enemySideLayout?: SandboxSideLayout;
  fieldObjects?: Array<BoardPresetFieldObject & { ownerSide?: SideId }>;
}
