import { defaultEnemySideLayout, defaultPlayerSideLayout } from "../data/sandboxSideLayouts";
import { unitDefinitions } from "../data/unitDefinitions";
import { sandboxDefaultBoardPreset } from "../data/boardPresets";
import { MAX_UNITS_PER_SIDE } from "../data/setupRules";
import type { CellKey, SideId } from "../model/board";
import type {
  ActionResultSnapshot,
  BattleState,
  ObjectivesBySide,
  SandboxBattleOptions,
  SandboxSideLayout,
  SideState,
  WinConditions,
} from "../model/battle";
import type { Facing, UnitInstance } from "../model/unit";
import { toCellKey } from "../model/board";
import { createBoardState } from "./createBoardState";
import { validateArmySelection } from "./validateArmySelection";
import { validateDeployment } from "./validateDeployment";

function buildSideState(sideId: SideId): SideState {
  return {
    sideId,
    label: sideId === "player1" ? "Player 1" : "Player 2",
    controllerType: "human",
    unitInstanceIds: [],
  };
}

function createUnitInstance(
  sideId: SideId,
  layoutIndex: number,
  unitIndex: number,
  unitLayout: SandboxSideLayout["units"][number],
): UnitInstance {
  const definition = unitDefinitions[unitLayout.unitDefinitionId];
  const defaultFacing: Facing = sideId === "player1" ? "south" : "north";

  if (!definition) {
    throw new Error(`Missing unit definition: ${unitLayout.unitDefinitionId}`);
  }

  return {
    unitInstanceId: `${sideId}-unit-${layoutIndex}-${unitIndex}`,
    unitDefinitionId: definition.unitDefinitionId,
    ownerSide: sideId,
    isLeader: unitLayout.isLeader ?? false,
    carriedVipSideId: null,
    anchorCell: unitLayout.anchorCell,
    facing: unitLayout.facing ?? defaultFacing,
    currentHp: definition.maxHp,
    isAlive: true,
    eligibleOnOrAfterSideOpportunity: 1,
    assetVariantId: `${definition.unitDefinitionId}_placeholder`,
  };
}

function pickStartingSide(randomValue: () => number): SideId {
  return randomValue() < 0.5 ? "player1" : "player2";
}

function nextSide(sideId: SideId): SideId {
  return sideId === "player1" ? "player2" : "player1";
}

function buildBattleStartSummary(startingSideId: SideId): ActionResultSnapshot {
  return {
    actionType: "battleStart",
    actingUnitId: null,
    targetUnitId: null,
    hitResult: null,
    supportResult: null,
    defeatedUnitIds: [],
    positionChanges: [],
    nextTurnSideId: startingSideId,
    summary: `${startingSideId === "player1" ? "Player 1" : "Player 2"} starts the battle.`,
  };
}

function validateSetupFieldObjects(
  boardState: BattleState["boardState"],
  fieldObjects: SandboxBattleOptions["fieldObjects"] = [],
): void {
  const occupiedCellKeys = new Set<CellKey>();

  fieldObjects.forEach((fieldObject) => {
    const cellKey = toCellKey(fieldObject);
    const cell = boardState.cellsByKey[cellKey];

    if (cell === undefined) {
      throw new Error(`Field object cell ${cellKey} is outside the board.`);
    }

    if (!cell.isPlayable) {
      throw new Error(`Field object cell ${cellKey} is not playable.`);
    }

    if (fieldObject.ownerSide !== undefined && cell.deploymentZone !== fieldObject.ownerSide) {
      throw new Error(`Field object cell ${cellKey} is not legal for ${fieldObject.ownerSide}.`);
    }

    if (occupiedCellKeys.has(cellKey)) {
      throw new Error(`Field object cell ${cellKey} already contains another field object.`);
    }

    occupiedCellKeys.add(cellKey);
  });
}

function resolveWinConditions(winConditions?: Partial<WinConditions>): WinConditions {
  return {
    eliminateAllEnemies: winConditions?.eliminateAllEnemies ?? true,
    markedLeader: winConditions?.markedLeader ?? false,
    captureAndExtract: winConditions?.captureAndExtract ?? false,
  };
}

function getRescueCellKeys(sideId: SideId): CellKey[] {
  return sideId === "player1"
    ? [
        toCellKey({ row: 0, column: 4 }),
        toCellKey({ row: 1, column: 4 }),
        toCellKey({ row: 0, column: 5 }),
        toCellKey({ row: 1, column: 5 }),
        toCellKey({ row: 0, column: 6 }),
        toCellKey({ row: 1, column: 6 }),
      ]
    : [
        toCellKey({ row: 9, column: 4 }),
        toCellKey({ row: 10, column: 4 }),
        toCellKey({ row: 9, column: 5 }),
        toCellKey({ row: 10, column: 5 }),
        toCellKey({ row: 9, column: 6 }),
        toCellKey({ row: 10, column: 6 }),
      ];
}

function createObjectivesState(
  fieldObjects: SandboxBattleOptions["fieldObjects"] = [],
  winConditions: WinConditions,
): ObjectivesBySide {
  if (!winConditions.captureAndExtract) {
    return {};
  }

  const vipFieldObjects = fieldObjects.filter((fieldObject) => fieldObject.objectType === "vip");
  const vipByCaptorSide = new Map<SideId, (typeof vipFieldObjects)[number]>();

  vipFieldObjects.forEach((fieldObject) => {
    if (fieldObject.ownerSide) {
      vipByCaptorSide.set(fieldObject.ownerSide, fieldObject);
    }
  });

  return {
    player1: vipByCaptorSide.has("player2")
      ? {
          kind: "vip",
          ownerSide: "player1",
          state: "idle",
          cellKey: toCellKey(vipByCaptorSide.get("player2")!),
          carrierUnitId: null,
          rescueCellKeys: getRescueCellKeys("player1"),
        }
      : undefined,
    player2: vipByCaptorSide.has("player1")
      ? {
          kind: "vip",
          ownerSide: "player2",
          state: "idle",
          cellKey: toCellKey(vipByCaptorSide.get("player1")!),
          carrierUnitId: null,
          rescueCellKeys: getRescueCellKeys("player2"),
        }
      : undefined,
  };
}

function validateVipPlacement(fieldObjects: SandboxBattleOptions["fieldObjects"] = [], winConditions: WinConditions): void {
  if (!winConditions.captureAndExtract) {
    return;
  }

  const vipFieldObjects = fieldObjects.filter((fieldObject) => fieldObject.objectType === "vip");
  const player1Vip = vipFieldObjects.filter((fieldObject) => fieldObject.ownerSide === "player1");
  const player2Vip = vipFieldObjects.filter((fieldObject) => fieldObject.ownerSide === "player2");

  if (player1Vip.length !== 1 || player2Vip.length !== 1) {
    throw new Error("Each side must place exactly 1 VIP when capture-and-extract is enabled.");
  }
}

function validateLeaderSelection(sideLayouts: SandboxSideLayout[], winConditions: WinConditions): void {
  if (!winConditions.markedLeader) {
    return;
  }

  sideLayouts.forEach((sideLayout) => {
    const leaderCount = sideLayout.units.filter((unit) => unit.isLeader).length;

    if (leaderCount !== 1) {
      throw new Error(`${sideLayout.sideId} must designate exactly 1 leader when marked leader is enabled.`);
    }
  });
}

export function createSandboxBattle(options: SandboxBattleOptions = {}): BattleState {
  const boardState = createBoardState(sandboxDefaultBoardPreset, options.fieldObjects);
  const playerSideLayout = options.playerSideLayout ?? defaultPlayerSideLayout;
  const enemySideLayout = options.enemySideLayout ?? defaultEnemySideLayout;
  const sideLayouts = [playerSideLayout, enemySideLayout];
  const winConditions = resolveWinConditions(options.winConditions);

  const maxUnitsPerSide = options.maxUnitsPerSide === undefined ? MAX_UNITS_PER_SIDE : options.maxUnitsPerSide;
  validateArmySelection(playerSideLayout, unitDefinitions, options.pointsBudget, maxUnitsPerSide);
  validateArmySelection(enemySideLayout, unitDefinitions, options.pointsBudget, maxUnitsPerSide);
  validateSetupFieldObjects(boardState, options.fieldObjects);
  validateDeployment(boardState, sideLayouts, maxUnitsPerSide);
  validateLeaderSelection(sideLayouts, winConditions);
  validateVipPlacement(options.fieldObjects, winConditions);

  const randomValue = options.randomValue ?? Math.random;
  const startingSideId = pickStartingSide(randomValue);
  const sides: Record<SideId, SideState> = {
    player1: buildSideState("player1"),
    player2: buildSideState("player2"),
  };
  const unitsById: Record<string, UnitInstance> = {};
  const occupancyByCellKey: Partial<Record<CellKey, string>> = {};

  sideLayouts.forEach((sideLayout, layoutIndex) => {
    sideLayout.units.forEach((unitLayout, unitIndex) => {
      const unit = createUnitInstance(sideLayout.sideId, layoutIndex, unitIndex, unitLayout);
      const cellKey = toCellKey(unit.anchorCell);

      unitsById[unit.unitInstanceId] = unit;
      occupancyByCellKey[cellKey] = unit.unitInstanceId;
      sides[sideLayout.sideId].unitInstanceIds.push(unit.unitInstanceId);
    });
  });

  const battleState: BattleState = {
    battleId: options.battleId ?? "sandbox-battle-01",
    status: "active",
    winConditions,
    objectives: createObjectivesState(options.fieldObjects, winConditions),
    boardState,
    sides,
    unitDefinitions,
    unitsById,
    occupancyByCellKey,
    turnState: {
      startingSideId,
      currentSideId: startingSideId,
      globalOpportunityIndex: 0,
      sideOpportunityIndexBySide: {
        player1: 0,
        player2: 0,
      },
      activeUnitId: null,
      activationStage: "selectUnit",
      activationSummary: null,
    },
    lastResolvedAction: buildBattleStartSummary(startingSideId),
    winnerSideId: null,
  };

  return openOpportunity(battleState, startingSideId);
}

export function openOpportunity(battleState: BattleState, sideId: SideId): BattleState {
  const sideOpportunityIndexBySide = {
    ...battleState.turnState.sideOpportunityIndexBySide,
    [sideId]: battleState.turnState.sideOpportunityIndexBySide[sideId] + 1,
  };
  const activeUnitIds = battleState.sides[sideId].unitInstanceIds.filter((unitId) => {
    const unit = battleState.unitsById[unitId];
    return unit.isAlive && unit.eligibleOnOrAfterSideOpportunity <= sideOpportunityIndexBySide[sideId];
  });

  return {
    ...battleState,
    turnState: {
      ...battleState.turnState,
      currentSideId: sideId,
      globalOpportunityIndex: battleState.turnState.globalOpportunityIndex + 1,
      sideOpportunityIndexBySide,
      activeUnitId: null,
      activationStage: activeUnitIds.length === 0 ? "forcedPass" : "selectUnit",
      activationSummary: null,
    },
    lastResolvedAction:
      activeUnitIds.length === 0
        ? {
            actionType: "forcedPass",
            actingUnitId: null,
            targetUnitId: null,
            hitResult: null,
            supportResult: null,
            defeatedUnitIds: [],
            positionChanges: [],
            nextTurnSideId: nextSide(sideId),
            summary: `${sideId === "player1" ? "Player 1" : "Player 2"} has no eligible units and must pass.`,
          }
        : battleState.lastResolvedAction,
  };
}

export function getOpposingSide(sideId: SideId): SideId {
  return nextSide(sideId);
}
