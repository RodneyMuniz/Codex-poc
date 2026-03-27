import { useEffect, useState } from "react";
import { createBattleViewModel } from "../../app/presentation/createBattleViewModel";
import {
  createSetupViewModel,
  type SetupFieldObjectPlacement,
  type SetupPlacement,
} from "../../app/presentation/createSetupViewModel";
import {
  continueAfterForcedPass,
  moveActiveUnit,
  performActionWithActiveUnit,
  rotateActiveUnit,
  selectActiveUnit,
  skipAttack,
} from "../../engine/actions/battleActions";
import { sandboxDefaultBoardPreset } from "../../engine/data/boardPresets";
import { MAX_UNITS_PER_SIDE, PLAYER_ARMY_BUDGET } from "../../engine/data/setupRules";
import { unitDefinitions } from "../../engine/data/unitDefinitions";
import type { BoardPresetFieldObject, CellKey, FieldObjectType, SideId } from "../../engine/model/board";
import type { BattleState, SandboxSideLayout, WinConditions } from "../../engine/model/battle";
import type { Facing } from "../../engine/model/unit";
import { getActionRangeCellKeys } from "../../engine/queries/getActionRangeCellKeys";
import { getEligibleUnitIds } from "../../engine/queries/getEligibleUnitIds";
import { getLegalTargets } from "../../engine/queries/getLegalTargets";
import { getReachableCellKeys } from "../../engine/queries/getReachableCellKeys";
import { createBoardState } from "../../engine/setup/createBoardState";
import { createSandboxBattle } from "../../engine/setup/createSandboxBattle";

const rotateFacings: Facing[] = ["west", "north", "south", "east"];
const MIN_ARMY_BUDGET = 100;
const MAX_ARMY_BUDGET = 1000;
const setupBoardState = createBoardState(sandboxDefaultBoardPreset);
const unitOrder = ["warrior", "pikeman", "scout", "cleric", "pyromancer"] as const;
const baseSetupFieldObjectOrder: FieldObjectType[] = ["wall", "highGrass"];
const fieldObjectCosts: Record<FieldObjectType, number> = {
  wall: 10,
  highGrass: 5,
  vip: 0,
};

type AppMode = "setupConfig" | "setupDeploy" | "battle";
type SetupPlacementsBySide = Record<SideId, SetupPlacement[]>;
type SetupFieldObjectPlacementsBySide = Record<SideId, SetupFieldObjectPlacement[]>;
type SetupSelection = { kind: "unit"; unitDefinitionId: string } | { kind: "fieldObject"; fieldObjectType: FieldObjectType };
type SetupInteractionMode = "place" | "markLeader";
type ActivityLogEntry = {
  key: string;
  order: number;
  summary: string;
};
type PendingRiskConfirmation = {
  targetCellKey: CellKey;
  allyCount: number;
};

function sideLabel(sideId: SideId): string {
  return sideId === "player1" ? "Player 1" : "Player 2";
}

function zoneClassName(zone: string | null): string {
  if (zone === "player1") {
    return "tile--player1";
  }

  if (zone === "player2") {
    return "tile--player2";
  }

  if (zone === "neutral") {
    return "tile--neutral";
  }

  return "tile--void";
}

function setupZoneClassName(zone: string | null, activeSetupSide: SideId): string {
  if (zone === activeSetupSide) {
    return zoneClassName(zone);
  }

  if (zone === "player1" || zone === "player2" || zone === "neutral") {
    return "tile--neutral";
  }

  return "tile--void";
}

function battleZoneClassName(isPlayable: boolean): string {
  return isPlayable ? "tile--neutral" : "tile--void";
}

function facingGlyph(facing: Facing): string {
  if (facing === "north") {
    return "^";
  }

  if (facing === "east") {
    return ">";
  }

  if (facing === "south") {
    return "v";
  }

  return "<";
}

function facingShortLabel(facing: Facing): string {
  if (facing === "north") {
    return "N";
  }

  if (facing === "east") {
    return "E";
  }

  if (facing === "south") {
    return "S";
  }

  return "W";
}

function facingLabel(facing: Facing): string {
  if (facing === "north") {
    return "North";
  }

  if (facing === "east") {
    return "East";
  }

  if (facing === "south") {
    return "South";
  }

  return "West";
}

function setupDefaultFacing(sideId: SideId): Facing {
  return sideId === "player1" ? "south" : "north";
}

function unitShortLabel(unitLabel: string | null): string {
  if (unitLabel === "Warrior") {
    return "WAR";
  }

  if (unitLabel === "Pikeman") {
    return "PIK";
  }

  if (unitLabel === "Scout") {
    return "SCT";
  }

  if (unitLabel === "Cleric") {
    return "CLR";
  }

  if (unitLabel === "Pyromancer") {
    return "PYR";
  }

  return "UNK";
}

function unitThemeKey(unitLabel: string | null): string {
  if (unitLabel === "Warrior") {
    return "warrior";
  }

  if (unitLabel === "Pikeman") {
    return "pikeman";
  }

  if (unitLabel === "Scout") {
    return "scout";
  }

  if (unitLabel === "Cleric") {
    return "cleric";
  }

  if (unitLabel === "Pyromancer") {
    return "pyromancer";
  }

  return "unknown";
}

function UnitGlyph({ unitLabel }: { unitLabel: string | null }) {
  if (unitLabel === "Warrior") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3 18 6v5c0 4-2.5 7.5-6 10-3.5-2.5-6-6-6-10V6z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
        <path d="M12 7v8" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  }

  if (unitLabel === "Pikeman") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 18 16 8" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
        <path d="m15 5 5 4-6 2z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        <path d="M5 19h4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  }

  if (unitLabel === "Scout") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 12c2.2-3.6 5.5-5.4 9-5.4s6.8 1.8 9 5.4c-2.2 3.6-5.5 5.4-9 5.4S5.2 15.6 3 12Z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="2.2" fill="none" stroke="currentColor" strokeWidth="1.7" />
      </svg>
    );
  }

  if (unitLabel === "Cleric") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="7" fill="none" stroke="currentColor" strokeWidth="1.7" />
        <path d="M12 8v8M8 12h8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }

  if (unitLabel === "Pyromancer") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 4c2.2 2 3.4 3.8 3.4 5.6 1.6.7 2.6 2.3 2.6 4.4A6 6 0 0 1 12 20a6 6 0 0 1-6-6c0-2.5 1.4-4.2 3.6-5.3.2 1.1.8 2 1.8 2.7.1-2.6.9-4.6 2.6-7.4Z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="7" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <path d="M12 9v4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="12" cy="16.5" r="1" fill="currentColor" />
    </svg>
  );
}

function fieldObjectLabel(fieldObjectType: FieldObjectType | null): string | null {
  if (fieldObjectType === "wall") {
    return "Wall";
  }

  if (fieldObjectType === "highGrass") {
    return "Grass";
  }

  if (fieldObjectType === "vip") {
    return "VIP";
  }

  return null;
}

function fieldObjectTrait(fieldObjectType: FieldObjectType | null): string {
  if (fieldObjectType === "wall") {
    return "Blocks movement";
  }

  if (fieldObjectType === "highGrass") {
    return "Conceals approach";
  }

  if (fieldObjectType === "vip") {
    return "Rescue objective";
  }

  return "Unknown";
}

function FieldObjectGlyph({ fieldObjectType }: { fieldObjectType: FieldObjectType | null }) {
  if (fieldObjectType === "wall") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 8h16v10H4zM9 8v10M15 8v10M4 13h5M9 18h6M15 13h5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    );
  }

  if (fieldObjectType === "highGrass") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 19c0-4 1.1-7.4 3.3-10.4M12 19c0-5.2.7-9 2.1-12M17 19c0-4.4-1-7.8-3-10.4" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
      </svg>
    );
  }

  if (fieldObjectType === "vip") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 4 14 9l5 .7-3.7 3.6.9 5-4.2-2.3-4.2 2.3.9-5L5 9.7 10 9z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.7" />
    </svg>
  );
}

function createSideLayout(sideId: SideId, placements: SetupPlacement[]): SandboxSideLayout {
  return {
    sideId,
    units: placements.map((placement) => ({
      unitDefinitionId: placement.unitDefinitionId,
      isLeader: placement.isLeader,
      anchorCell: placement.anchorCell,
      facing: placement.facing,
    })),
  };
}

function createFieldObjectEntries(placementsBySide: SetupFieldObjectPlacementsBySide): BoardPresetFieldObject[] {
  return [...placementsBySide.player1, ...placementsBySide.player2].map((placement) => ({
    row: placement.row,
    column: placement.column,
    objectType: placement.objectType,
    ownerSide: placement.ownerSide,
  }));
}

function getStageInstruction(battleState: BattleState | null): string {
  if (battleState === null) {
    return "Complete setup for both players to begin the battle.";
  }

  if (battleState.status === "victory") {
    return "The battle is complete. You can return to setup to redeploy both sides.";
  }

  if (battleState.turnState.activationStage === "selectUnit") {
    return "Select one eligible unit for the current side from the battlefield.";
  }

  if (battleState.turnState.activationStage === "move") {
    return "Move the active unit to a highlighted tile, or click another eligible unit to switch your selection before any move is committed.";
  }

  if (battleState.turnState.activationStage === "attackOrSkip") {
    const activeUnitId = battleState.turnState.activeUnitId;
    const activeUnit = activeUnitId ? battleState.unitsById[activeUnitId] : null;
    const activeDefinition = activeUnit ? battleState.unitDefinitions[activeUnit.unitDefinitionId] : null;

    if (activeDefinition?.actionType === "castPyromancerBurst") {
      return "Choose a valid G tile for the Pyromancer's burst. Units on G and the four orthogonal D tiles will be scorched.";
    }

    if (activeUnit?.carriedVipSideId) {
      return "This unit is carrying the VIP and cannot attack. Move toward the rescue zone or skip the action step.";
    }

    return "Choose a highlighted action target, rescue an adjacent VIP if available, or skip the action step.";
  }

  if (battleState.turnState.activationStage === "rotate") {
    return "Choose the unit's final facing with the arrow controls in this panel.";
  }

  return "No units are eligible on this side opportunity, so the turn auto-passes.";
}

function createActionLogKey(battleState: BattleState): string | null {
  const action = battleState.lastResolvedAction;

  if (action === null) {
    return null;
  }

  if (!["battleStart", "forcedPass", "rotate"].includes(action.actionType)) {
    return null;
  }

  return [
    battleState.turnState.globalOpportunityIndex,
    action.actionType,
    action.actingUnitId ?? "none",
    action.targetUnitId ?? "none",
    action.summary,
  ].join("|");
}

function activationStageLabel(stage: BattleState["turnState"]["activationStage"]): string {
  const labels: Record<BattleState["turnState"]["activationStage"], string> = {
    selectUnit: "Select Unit",
    move: "Move",
    attackOrSkip: "Action",
    rotate: "Rotate",
    forcedPass: "Forced Pass",
  };

  return labels[stage];
}

function getObjectiveSummary(objective: BattleState["objectives"][SideId]): string {
  if (!objective) {
    return "Inactive";
  }

  if (objective.state === "carried") {
    return `Carried by ${objective.carrierUnitId}`;
  }

  if (objective.state === "extracted") {
    return "Extracted";
  }

  if (objective.cellKey) {
    return `At ${objective.cellKey}`;
  }

  return "On board";
}

function getVictoryReason(battleState: BattleState, winnerSideId: SideId): string {
  const losingSideId = winnerSideId === "player1" ? "player2" : "player1";
  const losingSideUnits = battleState.sides[losingSideId].unitInstanceIds.map((unitId) => battleState.unitsById[unitId]);

  if (battleState.winConditions.eliminateAllEnemies && losingSideUnits.every((unit) => !unit.isAlive)) {
    return "Eliminated all enemy units";
  }

  if (battleState.winConditions.markedLeader && losingSideUnits.some((unit) => unit.isLeader && !unit.isAlive)) {
    return "Defeated the marked leader";
  }

  if (battleState.winConditions.captureAndExtract) {
    const objective = battleState.objectives[winnerSideId];
    if (objective?.carrierUnitId) {
      const carrier = battleState.unitsById[objective.carrierUnitId];
      const carrierCellKey = `${carrier.anchorCell.row},${carrier.anchorCell.column}` as CellKey;
      if (carrier.isAlive && objective.rescueCellKeys.includes(carrierCellKey)) {
        return "Rescued and extracted the captive VIP";
      }
    }
  }

  return battleState.lastResolvedAction?.summary ?? "Victory secured";
}

function getBattleGoldPreview(battleState: BattleState, winnerSideId: SideId): number {
  const losingSideId = winnerSideId === "player1" ? "player2" : "player1";
  const enemyValue = battleState.sides[losingSideId].unitInstanceIds.reduce((total, unitId) => {
    const unit = battleState.unitsById[unitId];
    const definition = battleState.unitDefinitions[unit.unitDefinitionId];
    return total + definition.cost;
  }, 0);
  const ownLossValue = battleState.sides[winnerSideId].unitInstanceIds.reduce((total, unitId) => {
    const unit = battleState.unitsById[unitId];
    if (unit.isAlive) {
      return total;
    }

    const definition = battleState.unitDefinitions[unit.unitDefinitionId];
    return total + definition.cost;
  }, 0);

  return Math.max(0, enemyValue - ownLossValue);
}

function clampNumber(value: number, minimum: number, maximum: number): number {
  if (Number.isNaN(value)) {
    return minimum;
  }

  return Math.min(maximum, Math.max(minimum, value));
}

export function App() {
  const [mode, setMode] = useState<AppMode>("setupConfig");
  const [battleState, setBattleState] = useState<BattleState | null>(null);
  const [selectedSetupSelection, setSelectedSetupSelection] = useState<SetupSelection>({
    kind: "unit",
    unitDefinitionId: "warrior",
  });
  const [setupInteractionMode, setSetupInteractionMode] = useState<SetupInteractionMode>("place");
  const [setupArmyBudget, setSetupArmyBudget] = useState(PLAYER_ARMY_BUDGET);
  const [setupStartAttempted, setSetupStartAttempted] = useState(false);
  const [setupStartError, setSetupStartError] = useState<string | null>(null);
  const [setupWinConditions, setSetupWinConditions] = useState<WinConditions>({
    eliminateAllEnemies: true,
    markedLeader: true,
    captureAndExtract: false,
  });
  const [activeSetupSide, setActiveSetupSide] = useState<SideId>("player1");
  const [setupPlacementsBySide, setSetupPlacementsBySide] = useState<SetupPlacementsBySide>({
    player1: [],
    player2: [],
  });
  const [setupFieldObjectPlacementsBySide, setSetupFieldObjectPlacementsBySide] = useState<SetupFieldObjectPlacementsBySide>({
    player1: [],
    player2: [],
  });
  const [nextPlacementId, setNextPlacementId] = useState(1);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [hoveredActionCellKey, setHoveredActionCellKey] = useState<CellKey | null>(null);
  const [pendingRiskConfirmation, setPendingRiskConfirmation] = useState<PendingRiskConfirmation | null>(null);

  useEffect(() => {
    if (mode !== "battle" || battleState === null || battleState.status === "victory") {
      return undefined;
    }

    if (battleState.turnState.activationStage !== "forcedPass") {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setBattleState((current) => {
        if (current === null || current.status === "victory" || current.turnState.activationStage !== "forcedPass") {
          return current;
        }

        return continueAfterForcedPass(current);
      });
    }, 700);

    return () => window.clearTimeout(timeoutId);
  }, [mode, battleState]);

  useEffect(() => {
    if (mode !== "battle" || battleState === null) {
      return;
    }

    const key = createActionLogKey(battleState);
    const summary = battleState.lastResolvedAction?.summary;

    if (key === null || summary === undefined) {
      return;
    }

    setActivityLog((current) => {
      if (current.some((entry) => entry.key === key)) {
        return current;
      }

      const nextOrder = current.length > 0 ? current[current.length - 1].order + 1 : 1;
      return [...current, { key, order: nextOrder, summary }];
    });
  }, [mode, battleState]);

  useEffect(() => {
    if (setupStartError !== null) {
      setSetupStartError(null);
    }
  }, [
    activeSetupSide,
    setupArmyBudget,
    setupFieldObjectPlacementsBySide,
    setupPlacementsBySide,
    setupWinConditions,
  ]);

  const selectedUnitDefinition =
    selectedSetupSelection.kind === "unit" ? unitDefinitions[selectedSetupSelection.unitDefinitionId] : null;
  const allSetupPlacements = [...setupPlacementsBySide.player1, ...setupPlacementsBySide.player2];
  const allSetupFieldObjectPlacements = [
    ...setupFieldObjectPlacementsBySide.player1,
    ...setupFieldObjectPlacementsBySide.player2,
  ];
  const setupViewModel = createSetupViewModel(
    setupBoardState,
    allSetupPlacements,
    allSetupFieldObjectPlacements,
    unitDefinitions,
  );
  const activeSetupPlacements = setupPlacementsBySide[activeSetupSide];
  const activeSetupFieldObjectPlacements = setupFieldObjectPlacementsBySide[activeSetupSide];
  const setupSquadSize = MAX_UNITS_PER_SIDE;
  const activeSideVipPlacement = activeSetupFieldObjectPlacements.find((placement) => placement.objectType === "vip") ?? null;
  const spentPointsBySide = {
    player1:
      setupPlacementsBySide.player1.reduce(
        (total, placement) => total + unitDefinitions[placement.unitDefinitionId].weight,
        0,
      ) + setupFieldObjectPlacementsBySide.player1.reduce(
        (total, placement) => total + fieldObjectCosts[placement.objectType],
        0,
      ),
    player2:
      setupPlacementsBySide.player2.reduce(
        (total, placement) => total + unitDefinitions[placement.unitDefinitionId].weight,
        0,
      ) + setupFieldObjectPlacementsBySide.player2.reduce(
        (total, placement) => total + fieldObjectCosts[placement.objectType],
        0,
      ),
  };
  const remainingPointsBySide = {
    player1: setupArmyBudget - spentPointsBySide.player1,
    player2: setupArmyBudget - spentPointsBySide.player2,
  };
  const remainingPoints = remainingPointsBySide[activeSetupSide];
  const player1Leader = setupPlacementsBySide.player1.find((placement) => placement.isLeader) ?? null;
  const player2Leader = setupPlacementsBySide.player2.find((placement) => placement.isLeader) ?? null;
  const leadersReady = !setupWinConditions.markedLeader || (player1Leader !== null && player2Leader !== null);
  const vipReady =
    !setupWinConditions.captureAndExtract ||
    (
      setupFieldObjectPlacementsBySide.player1.some((placement) => placement.objectType === "vip")
      && setupFieldObjectPlacementsBySide.player2.some((placement) => placement.objectType === "vip")
    );
  const squadCapEnabled = false;
  const squadCountsValid =
    !squadCapEnabled ||
    (
      setupPlacementsBySide.player1.length <= setupSquadSize &&
      setupPlacementsBySide.player2.length <= setupSquadSize
    );
  const budgetValid = remainingPointsBySide.player1 >= 0 && remainingPointsBySide.player2 >= 0;
  const setupReadiness = [
    { label: "Player 1 Ready", ready: setupPlacementsBySide.player1.length > 0 },
    { label: "Player 2 Ready", ready: setupPlacementsBySide.player2.length > 0 },
    { label: "Leaders Set", ready: leadersReady, required: setupWinConditions.markedLeader },
    { label: "VIPs Placed", ready: vipReady, required: setupWinConditions.captureAndExtract },
    { label: "Budget Valid", ready: budgetValid },
    { label: "Squad Cap OK", ready: squadCountsValid, required: squadCapEnabled },
  ].filter((item) => item.required !== false);
  const missingSetupReadiness = setupReadiness.filter((item) => !item.ready);
  const canStartBattle = missingSetupReadiness.length === 0;
  const startBattleLabel = canStartBattle
    ? "Start Battle"
    : missingSetupReadiness.length === 1
      ? `Need ${missingSetupReadiness[0].label}`
      : `Need ${missingSetupReadiness.length} Setup Items`;
  const setupFieldObjectOrder: FieldObjectType[] = setupWinConditions.captureAndExtract
    ? [...baseSetupFieldObjectOrder, "vip"]
    : baseSetupFieldObjectOrder;

  const activeBattleState = battleState;
  const battleViewModel = activeBattleState ? createBattleViewModel(activeBattleState) : null;
  const canReselectBeforeCommit =
    activeBattleState?.turnState.activationStage === "move" &&
    activeBattleState.lastResolvedAction?.actionType === "selectUnit";
  const canSelectDuringBattle =
    activeBattleState?.turnState.activationStage === "selectUnit" || canReselectBeforeCommit;
  const eligibleUnitIds = canSelectDuringBattle && activeBattleState ? getEligibleUnitIds(activeBattleState) : [];
  const reachableCellKeys =
    activeBattleState &&
    activeBattleState.turnState.activationStage === "move" &&
    activeBattleState.turnState.activeUnitId
      ? getReachableCellKeys(activeBattleState, activeBattleState.turnState.activeUnitId)
      : [];
  const legalTargets =
    activeBattleState &&
    activeBattleState.turnState.activationStage === "attackOrSkip" &&
    activeBattleState.turnState.activeUnitId
      ? getLegalTargets(activeBattleState, activeBattleState.turnState.activeUnitId)
      : [];
  const legalTargetsByCellKey = new Map(legalTargets.map((target) => [target.cellKey, target]));
  const actionRangeCellKeys =
    activeBattleState &&
    activeBattleState.turnState.activationStage === "attackOrSkip" &&
    activeBattleState.turnState.activeUnitId
      ? getActionRangeCellKeys(activeBattleState, activeBattleState.turnState.activeUnitId)
      : [];
  const forcedPassSummary =
    activeBattleState?.lastResolvedAction?.actionType === "forcedPass"
      ? activeBattleState.lastResolvedAction.summary
      : null;
  const activeUnitId = activeBattleState?.turnState.activeUnitId ?? null;
  const activeUnit = activeUnitId && activeBattleState ? activeBattleState.unitsById[activeUnitId] : null;
  const activeDefinition = activeUnit && activeBattleState
    ? activeBattleState.unitDefinitions[activeUnit.unitDefinitionId]
    : null;
  const supportAffectedUnitIds =
    activeBattleState && activeDefinition?.actionType === "healAllAllies"
      ? activeBattleState.sides[activeBattleState.turnState.currentSideId].unitInstanceIds.filter(
          (unitId) => activeBattleState.unitsById[unitId].isAlive,
        )
      : [];
  const hoveredBurstTarget =
    activeDefinition?.actionType === "castPyromancerBurst" && hoveredActionCellKey
      ? legalTargetsByCellKey.get(hoveredActionCellKey) ?? null
      : null;
  const activeObjectives = activeBattleState?.objectives ?? {};
  const currentBattleSideId = activeBattleState?.turnState.currentSideId ?? null;
  const rosterSideId =
    activeBattleState?.status === "victory"
      ? activeBattleState.winnerSideId ?? currentBattleSideId
      : currentBattleSideId;
  const rosterUnits =
    rosterSideId && activeBattleState
      ? activeBattleState.sides[rosterSideId].unitInstanceIds
          .map((unitId) => {
            const unit = activeBattleState.unitsById[unitId];
            const definition = activeBattleState.unitDefinitions[unit.unitDefinitionId];
            const sideOpportunity = activeBattleState.turnState.sideOpportunityIndexBySide[unit.ownerSide];

            return {
              unit,
              definition,
              cooldown: Math.max(0, unit.eligibleOnOrAfterSideOpportunity - sideOpportunity),
            };
          })
          .sort((left, right) => {
            if (left.unit.isAlive !== right.unit.isAlive) {
              return left.unit.isAlive ? -1 : 1;
            }

            if (left.unit.unitInstanceId === activeUnitId) {
              return -1;
            }

            if (right.unit.unitInstanceId === activeUnitId) {
              return 1;
            }

            return left.unit.unitInstanceId.localeCompare(right.unit.unitInstanceId);
          })
      : [];
  const activeWinConditionLabels = [
    activeBattleState?.winConditions.eliminateAllEnemies ? "Eliminate All" : null,
    activeBattleState?.winConditions.markedLeader ? "Marked Leader" : null,
    activeBattleState?.winConditions.captureAndExtract ? "Capture & Extract" : null,
  ].filter(Boolean);
  const battleVictoryReason =
    activeBattleState?.winnerSideId ? getVictoryReason(activeBattleState, activeBattleState.winnerSideId) : null;
  const battleVictoryGold =
    activeBattleState?.winnerSideId ? getBattleGoldPreview(activeBattleState, activeBattleState.winnerSideId) : null;
  const actionAvailable = activeBattleState?.turnState.activationStage === "attackOrSkip";

  const commitBattleAction = (tileKey: CellKey) => {
    setPendingRiskConfirmation(null);
    setBattleState((current) => (current ? performActionWithActiveUnit(current, tileKey) : current));
  };

  const handleSetupTileClick = (tileKey: CellKey) => {
    const tile = setupBoardState.cellsByKey[tileKey];
    const existingPlacement = allSetupPlacements.find(
      (placement) => placement.anchorCell.row === tile.row && placement.anchorCell.column === tile.column,
    );
    const existingFieldObjectPlacement = allSetupFieldObjectPlacements.find(
      (placement) => placement.row === tile.row && placement.column === tile.column,
    );

    if (existingPlacement) {
      if (existingPlacement.ownerSide !== activeSetupSide) {
        return;
      }

      if (setupInteractionMode === "markLeader") {
        setSetupPlacementsBySide((current) => ({
          ...current,
          [activeSetupSide]: current[activeSetupSide].map((placement) => ({
            ...placement,
            isLeader:
              placement.placementId === existingPlacement.placementId ? !placement.isLeader : false,
          })),
        }));
        return;
      }

      setSetupPlacementsBySide((current) => ({
        ...current,
        [activeSetupSide]: current[activeSetupSide].filter(
          (placement) => placement.placementId !== existingPlacement.placementId,
        ),
      }));
      return;
    }

    if (existingFieldObjectPlacement) {
      if (existingFieldObjectPlacement.ownerSide !== activeSetupSide) {
        return;
      }

      setSetupFieldObjectPlacementsBySide((current) => ({
        ...current,
        [activeSetupSide]: current[activeSetupSide].filter(
          (placement) => placement.placementId !== existingFieldObjectPlacement.placementId,
        ),
      }));
      return;
    }

    if (!tile.isPlayable) {
      return;
    }

    if (tile.blocksOccupation) {
      return;
    }

    if (setupInteractionMode === "markLeader") {
      return;
    }

    const placementId = `setup-${nextPlacementId}`;
    setNextPlacementId((current) => current + 1);

    if (selectedSetupSelection.kind === "unit") {
      if (tile.deploymentZone !== activeSetupSide) {
        return;
      }

      if (squadCapEnabled && activeSetupPlacements.length >= setupSquadSize) {
        return;
      }

      if (selectedUnitDefinition === null || remainingPoints < selectedUnitDefinition.weight) {
        return;
      }

      setSetupPlacementsBySide((current) => ({
        ...current,
        [activeSetupSide]: [
          ...current[activeSetupSide],
          {
            placementId,
            ownerSide: activeSetupSide,
            isLeader: false,
            unitDefinitionId: selectedSetupSelection.unitDefinitionId,
            anchorCell: { row: tile.row, column: tile.column },
            facing: setupDefaultFacing(activeSetupSide),
          },
        ],
      }));
      return;
    }

    if (tile.deploymentZone !== activeSetupSide) {
      return;
    }

    if (selectedSetupSelection.fieldObjectType === "vip" && activeSideVipPlacement) {
      return;
    }

    if (remainingPoints < fieldObjectCosts[selectedSetupSelection.fieldObjectType]) {
      return;
    }

    setSetupFieldObjectPlacementsBySide((current) => ({
      ...current,
      [activeSetupSide]: [
        ...current[activeSetupSide],
        {
          placementId,
          ownerSide: activeSetupSide,
          row: tile.row,
          column: tile.column,
          objectType: selectedSetupSelection.fieldObjectType,
        },
      ],
    }));
  };

  const startBattle = () => {
    if (!canStartBattle) {
      setSetupStartAttempted(true);
      return;
    }

    try {
      setSetupStartAttempted(false);
      setSetupStartError(null);
      setActivityLog([]);
      setPendingRiskConfirmation(null);
      setBattleState(
        createSandboxBattle({
          playerSideLayout: createSideLayout("player1", setupPlacementsBySide.player1),
          enemySideLayout: createSideLayout("player2", setupPlacementsBySide.player2),
          fieldObjects: createFieldObjectEntries(setupFieldObjectPlacementsBySide),
          winConditions: setupWinConditions,
          pointsBudget: setupArmyBudget,
          maxUnitsPerSide: squadCapEnabled ? setupSquadSize : null,
        }),
      );
      setMode("battle");
    } catch (error) {
      setSetupStartAttempted(true);
      setSetupStartError(error instanceof Error ? error.message : "Battle start failed.");
    }
  };

  const handleBattleTileClick = (tileKey: CellKey, occupyingUnitId: string | null) => {
    if (activeBattleState === null || activeBattleState.status === "victory") {
      return;
    }

    if (occupyingUnitId && eligibleUnitIds.includes(occupyingUnitId)) {
      if (activeBattleState.turnState.activationStage === "selectUnit") {
        setBattleState((current) => (current ? selectActiveUnit(current, occupyingUnitId) : current));
        return;
      }

      if (canReselectBeforeCommit && occupyingUnitId !== activeUnitId) {
        setBattleState((current) => {
          if (current === null) {
            return current;
          }

          return selectActiveUnit(
            {
              ...current,
              turnState: {
                ...current.turnState,
                activeUnitId: null,
                activationStage: "selectUnit",
                activationSummary: null,
              },
            },
            occupyingUnitId,
          );
        });
        return;
      }
    }

    if (activeBattleState.turnState.activationStage === "move" && activeBattleState.turnState.activeUnitId) {
      if (!reachableCellKeys.includes(tileKey)) {
        return;
      }

      setBattleState((current) => (current ? moveActiveUnit(current, tileKey) : current));
      return;
    }

    if (activeBattleState.turnState.activationStage === "attackOrSkip") {
      const legalTarget = legalTargetsByCellKey.get(tileKey);
      if (!legalTarget) {
        return;
      }

      if (legalTarget.targetKind === "areaCell" && legalTarget.alliedAffectedUnitIds.length > 0) {
        setPendingRiskConfirmation({
          targetCellKey: tileKey,
          allyCount: legalTarget.alliedAffectedUnitIds.length,
        });
        return;
      }

      commitBattleAction(tileKey);
    }
  };

  return (
    <main className="app-shell">
      <section className="hero hero--wide">
        <p className="eyebrow">Prototype Build</p>
        <h1>TacticsGame</h1>
        <p className="lede">
          The current pass is focused on getting the prototype closer to a real game: cleaner setup
          flow, clearer tactical readability, and a stronger board-first play surface.
        </p>
        <div className="hero-chips">
          <span className="hero-chip">Board First</span>
          <span className="hero-chip">Clear Tactical State</span>
          <span className="hero-chip">Config Before Deployment</span>
        </div>
      </section>

      {mode === "setupConfig" ? (
        <section className="setup-config-layout">
          <section className="panel setup-config-card">
            <div className="setup-config-card__header">
              <p className="section-eyebrow">Pre-Battle Configuration</p>
              <h2>Match Setup</h2>
              <div className="legend-note">
                Lock the rules, squad cap, and point budget before moving into deployment.
              </div>
            </div>

            <div className="setup-config-grid">
              <div className="setup-config-section">
                <h3>Battle Rules</h3>
                <label className="toggle-row">
                  <input
                    type="checkbox"
                    checked={setupWinConditions.eliminateAllEnemies}
                    onChange={(event) =>
                      setSetupWinConditions((current) => ({
                        ...current,
                        eliminateAllEnemies: event.target.checked,
                      }))}
                  />
                  <span>Eliminate all enemy units</span>
                </label>
                <label className="toggle-row">
                  <input
                    type="checkbox"
                    checked={setupWinConditions.markedLeader}
                    onChange={(event) => {
                      const checked = event.target.checked;
                      setSetupWinConditions((current) => ({
                        ...current,
                        markedLeader: checked,
                      }));
                      if (!checked) {
                        setSetupInteractionMode("place");
                      }
                    }}
                  />
                  <span>Marked leader</span>
                </label>
                <label className="toggle-row">
                  <input
                    type="checkbox"
                    checked={setupWinConditions.captureAndExtract}
                    onChange={(event) =>
                      setSetupWinConditions((current) => ({
                        ...current,
                        captureAndExtract: event.target.checked,
                      }))}
                  />
                  <span>Capture and extract VIP</span>
                </label>
              </div>

              <div className="setup-config-section">
                <h3>Player Limits</h3>
                <label className="setup-control">
                  <span>Points per player</span>
                  <div className="setup-control__row">
                    <input
                      type="range"
                      min={MIN_ARMY_BUDGET}
                      max={MAX_ARMY_BUDGET}
                      step={50}
                      value={setupArmyBudget}
                      onChange={(event) => setSetupArmyBudget(clampNumber(Number(event.target.value), MIN_ARMY_BUDGET, MAX_ARMY_BUDGET))}
                    />
                    <input
                      type="number"
                      min={MIN_ARMY_BUDGET}
                      max={MAX_ARMY_BUDGET}
                      step={50}
                      value={setupArmyBudget}
                      onChange={(event) => setSetupArmyBudget(clampNumber(Number(event.target.value), MIN_ARMY_BUDGET, MAX_ARMY_BUDGET))}
                    />
                  </div>
                </label>
                <div className="setup-overview-grid">
                  <div className="setup-overview-card">
                    <span>Point budget</span>
                    <strong>{setupArmyBudget}</strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="setup-config-actions">
              <button type="button" onClick={() => {
                setSetupStartAttempted(false);
                setMode("setupDeploy");
              }}>
                Continue To Deployment
              </button>
            </div>
          </section>
        </section>
      ) : null}

      {mode === "setupDeploy" ? (
        <section className="board-sidebar-layout">
          <section className="panel board-panel board-panel--centered board-panel--war-table">
            <div className="board-title-row board-title-row--war-table">
              <p className="section-eyebrow">Deployment Stage</p>
              <h2>War Table Deployment</h2>
              <div className="legend-note">Both sides now deploy through the same setup flow on their own half of the board.</div>
            </div>
            <div className="board-grid board-grid--war-table board-grid--deployment" style={{ gridTemplateColumns: `repeat(${setupViewModel.columnCount}, 1fr)` }}>
              {setupViewModel.tiles.map((tile) => {
                const isActiveZone = tile.deploymentZone === activeSetupSide;
                const isSetupLegal =
                  tile.fieldObjectType === null &&
                  tile.placementId === null &&
                  (
                    selectedSetupSelection.kind === "fieldObject"
                      ? isActiveZone && remainingPoints >= fieldObjectCosts[selectedSetupSelection.fieldObjectType]
                      : isActiveZone &&
                        activeSetupPlacements.length < setupSquadSize &&
                        selectedUnitDefinition !== null &&
                        remainingPoints >= selectedUnitDefinition.weight
                  );

                return (
                  <button
                    key={tile.key}
                    type="button"
                    className={[
                      "tile",
                      "tile--war-table",
                      setupZoneClassName(tile.deploymentZone, activeSetupSide),
                      tile.fieldObjectType ? `tile--field-${tile.fieldObjectType}` : "",
                      isActiveZone ? "tile--setup-zone-active" : "",
                      isSetupLegal ? "tile--setup-legal" : "",
                      tile.placementId ? `tile--setup-${tile.occupyingSide}` : "",
                    ].join(" ").trim()}
                    disabled={!tile.isPlayable}
                    onClick={() => handleSetupTileClick(tile.key)}
                    title={`${tile.key} ${tile.unitLabel ?? "empty"}`}
                  >
                    <span className="tile__coords">{tile.row},{tile.column}</span>
                    {tile.placementId ? (
                      <span className={`unit-badge unit-badge--token unit-badge--setup unit-badge--${tile.occupyingSide} unit-badge--${unitThemeKey(tile.unitLabel)}`}>
                        {tile.isLeader ? <span className="unit-badge__leader">LD</span> : null}
                        <span className="unit-badge__crest">
                          <UnitGlyph unitLabel={tile.unitLabel} />
                        </span>
                        <span className="unit-badge__content">
                          <span className="unit-badge__name">{tile.unitLabel}</span>
                          <span className="unit-badge__subline">{unitShortLabel(tile.unitLabel)} | {facingLabel(tile.facing!)}</span>
                        </span>
                      </span>
                    ) : tile.fieldObjectType ? (
                      <span className={`field-object-badge field-object-badge--${tile.fieldObjectType}`}>
                        <span className="field-object-badge__crest">
                          <FieldObjectGlyph fieldObjectType={tile.fieldObjectType} />
                        </span>
                        <span className="field-object-badge__content">
                          <span className="field-object-badge__name">{fieldObjectLabel(tile.fieldObjectType)}</span>
                          <span className="field-object-badge__trait">{fieldObjectTrait(tile.fieldObjectType)}</span>
                        </span>
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </section>

          <aside className="panel side-panel side-panel--folio setup-layout__panel">
            <div className="side-panel__section side-panel__section--folio">
              <p className="section-eyebrow">Preparation Folio</p>
              <h2>Setup Panel</h2>
              <div className="side-toggle-row">
                {(["player1", "player2"] as SideId[]).map((sideId) => (
                  <button
                    key={sideId}
                    type="button"
                    className={activeSetupSide === sideId ? "side-toggle side-toggle--active" : "side-toggle"}
                    onClick={() => setActiveSetupSide(sideId)}
                  >
                    {sideLabel(sideId)}
                  </button>
                ))}
              </div>
              <div className="setup-overview-grid">
                <div className="setup-overview-card">
                  <span>Editing</span>
                  <strong>{sideLabel(activeSetupSide)}</strong>
                </div>
                <div className="setup-overview-card">
                  <span>Points</span>
                  <strong>{remainingPoints} / {setupArmyBudget}</strong>
                </div>
                <div className="setup-overview-card">
                  <span>Units</span>
                  <strong>{activeSetupPlacements.length} / {setupSquadSize}</strong>
                </div>
                <div className="setup-overview-card">
                  <span>Objects</span>
                  <strong>{activeSetupFieldObjectPlacements.length}</strong>
                </div>
              </div>
              <div className="setup-panel-actions">
                <button type="button" className="setup-panel-actions__secondary" onClick={() => setMode("setupConfig")}>
                  Back To Match Setup
                </button>
                <button
                  type="button"
                  className={setupInteractionMode === "markLeader" ? "picker-button picker-button--selected" : "picker-button"}
                  disabled={!setupWinConditions.markedLeader}
                  onClick={() =>
                    setSetupInteractionMode((current) => (current === "markLeader" ? "place" : "markLeader"))
                  }
                >
                  <strong>{setupInteractionMode === "markLeader" ? "Leader Mode Active" : "Mark Leader"}</strong>
                  <span>Toggle the marked leader on one deployed unit for the active side.</span>
                </button>
              </div>
            </div>

            <div className="side-panel__section side-panel__section--folio unit-picker">
              <p className="section-eyebrow">Roster Draft</p>
              <div className="unit-picker__group">
                <h3>Units</h3>
                <div className="unit-picker__grid">
                  {unitOrder.map((unitId) => {
                    const definition = unitDefinitions[unitId];
                    const isSelected = selectedSetupSelection.kind === "unit" && selectedSetupSelection.unitDefinitionId === unitId;

                    return (
                      <button
                        key={unitId}
                        type="button"
                        className={isSelected ? `picker-button picker-button--unit picker-button--${unitId} picker-button--selected` : `picker-button picker-button--unit picker-button--${unitId}`}
                        onClick={() => {
                          setSetupInteractionMode("place");
                          setSelectedSetupSelection({ kind: "unit", unitDefinitionId: unitId });
                        }}
                      >
                        <span className="picker-button__header">
                          <span className="picker-button__crest">
                            <UnitGlyph unitLabel={definition.name} />
                          </span>
                          <span className="picker-button__title">
                            <strong>{definition.name}</strong>
                            <span>Weight {definition.weight}</span>
                          </span>
                        </span>
                        <span className="picker-button__line">HP {definition.maxHp} | Move {definition.movement} | Range {definition.attackRange}</span>
                        <span className="picker-button__line">
                          {definition.actionType === "healAllAllies"
                            ? `Heal ${definition.healAmount}`
                            : definition.actionType === "castPyromancerBurst"
                              ? `Burst ${definition.attack} | Def ${definition.defence}`
                              : `Atk ${definition.attack} | Def ${definition.defence}`}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="unit-picker__group">
                <h3>Field Tools</h3>
                <div className="unit-picker__grid unit-picker__grid--objects">
                  {setupFieldObjectOrder.map((fieldObjectType) => {
                    const isSelected = selectedSetupSelection.kind === "fieldObject" && selectedSetupSelection.fieldObjectType === fieldObjectType;

                    return (
                      <button
                        key={fieldObjectType}
                        type="button"
                        className={isSelected ? `picker-button picker-button--object picker-button--field-${fieldObjectType} picker-button--selected` : `picker-button picker-button--object picker-button--field-${fieldObjectType}`}
                        onClick={() => {
                          setSetupInteractionMode("place");
                          setSelectedSetupSelection({ kind: "fieldObject", fieldObjectType });
                        }}
                      >
                        <span className="picker-button__header">
                          <span className="picker-button__crest">
                            <FieldObjectGlyph fieldObjectType={fieldObjectType} />
                          </span>
                          <span className="picker-button__title">
                            <strong>{fieldObjectLabel(fieldObjectType)}</strong>
                            <span>Cost {fieldObjectCosts[fieldObjectType]}</span>
                          </span>
                        </span>
                        <span className="picker-button__line picker-button__line--compact">
                          {fieldObjectType === "wall"
                            ? "Blocks movement and line of fire."
                            : fieldObjectType === "highGrass"
                              ? "Occupies a tile until cleared."
                              : "Free rescue objective marker."}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="side-panel__section side-panel__section--folio">
              <details className="setup-readiness" open={setupStartAttempted}>
                <summary>Show setup checks</summary>
                <div className="status-pills status-pills--wrap">
                  {setupReadiness.map((item) => (
                    <span key={item.label} className={item.ready ? "status-pill status-pill--active" : "status-pill status-pill--muted"}>
                      {item.label}
                    </span>
                  ))}
                </div>
              </details>
              {setupStartAttempted && missingSetupReadiness.length > 0 ? (
                <div className="legend-note">
                  Missing: {missingSetupReadiness.map((item) => item.label).join(", ")}.
                </div>
              ) : null}
              {setupStartError ? (
                <div className="setup-error">
                  {setupStartError}
                </div>
              ) : null}
              <div className="setup-actions">
                <button
                  type="button"
                  onClick={() => {
                    setSetupStartAttempted(false);
                    setSetupPlacementsBySide((current) => ({ ...current, [activeSetupSide]: [] }));
                    setSetupFieldObjectPlacementsBySide((current) => ({ ...current, [activeSetupSide]: [] }));
                  }}
                >
                  Clear Side
                </button>
                <button type="button" onClick={startBattle}>
                  {startBattleLabel}
                </button>
              </div>
            </div>
          </aside>
        </section>
      ) : null}

      {mode === "battle" && activeBattleState && battleViewModel ? (
        <>
          {forcedPassSummary ? (
            <section className="event-banner event-banner--pass hero--wide">
              <strong>Forced pass:</strong> {forcedPassSummary}
              {activeBattleState.turnState.activationStage === "forcedPass" ? " Auto-skipping..." : null}
            </section>
          ) : null}

          {activeBattleState.status === "victory" && activeBattleState.winnerSideId ? (
            <section className="panel battle-summary hero--wide">
              <div className="battle-summary__eyebrow">Battle Complete</div>
              <div className="battle-summary__grid">
                <div>
                  <h2>{sideLabel(activeBattleState.winnerSideId)} Wins</h2>
                  <p>{battleVictoryReason}</p>
                </div>
                <div className="battle-summary__metrics">
                  <div>
                    <span className="battle-summary__label">Reason</span>
                    <strong>{battleVictoryReason}</strong>
                  </div>
                  <div>
                    <span className="battle-summary__label">Gold Preview</span>
                    <strong>{battleVictoryGold}g</strong>
                  </div>
                </div>
              </div>
            </section>
          ) : null}

          <section className="battle-layout">
            <aside className="panel side-panel side-panel--log side-panel--folio battle-layout__log">
              <div className="side-panel__section side-panel__section--folio">
                <p className="section-eyebrow">Battle Overview</p>
                <h2>Field Snapshot</h2>
                <div className="legend-note">The battle log is still captured under the hood, but the live screen now uses this space for the information you need while playing.</div>
                <button
                  type="button"
                  className="battle-nav-button"
                  onClick={() => {
                    setPendingRiskConfirmation(null);
                    setMode("setupDeploy");
                  }}
                >
                  Back To Deployment
                </button>
              </div>
              <div className="side-panel__section side-panel__section--folio side-panel__section--summary">
                <h3>Objectives</h3>
                <div className="status-pills status-pills--wrap">
                  {activeWinConditionLabels.length > 0 ? activeWinConditionLabels.map((label) => (
                    <span key={label} className="status-pill status-pill--objective">{label}</span>
                  )) : <span className="status-pill status-pill--muted">No active objectives</span>}
                </div>
                {activeObjectives.player1 ? (
                  <div><strong>P1 VIP:</strong> {getObjectiveSummary(activeObjectives.player1)}</div>
                ) : null}
                {activeObjectives.player2 ? (
                  <div><strong>P2 VIP:</strong> {getObjectiveSummary(activeObjectives.player2)}</div>
                ) : null}
                <div><strong>P1 opportunities:</strong> {activeBattleState.turnState.sideOpportunityIndexBySide.player1}</div>
                <div><strong>P2 opportunities:</strong> {activeBattleState.turnState.sideOpportunityIndexBySide.player2}</div>
                <div><strong>Recorded events:</strong> {activityLog.length}</div>
                <div><strong>Last event:</strong> {activeBattleState.lastResolvedAction?.summary ?? "None"}</div>
              </div>
              <div className="side-panel__section side-panel__section--folio side-panel__section--summary">
                <h3>{rosterSideId ? `${sideLabel(rosterSideId)} Roster` : "Roster"}</h3>
                <div className="battle-roster__list">
                  {rosterUnits.length > 0 ? rosterUnits.map(({ unit, definition, cooldown }) => (
                    <article
                      key={unit.unitInstanceId}
                      className={[
                        "battle-roster__item",
                        `battle-roster__item--${unit.ownerSide}`,
                        unit.unitInstanceId === activeUnitId ? "battle-roster__item--active" : "",
                        !unit.isAlive ? "battle-roster__item--dead" : "",
                      ].join(" ").trim()}
                    >
                      <span className="battle-roster__crest">
                        <UnitGlyph unitLabel={definition.name} />
                      </span>
                      <div className="battle-roster__body">
                        <strong>{unit.unitInstanceId}</strong>
                        <span>{definition.name} | HP {unit.currentHp}/{definition.maxHp} | Facing {facingShortLabel(unit.facing)}</span>
                      </div>
                      <div className="battle-roster__tags">
                        {unit.isLeader ? <span className="battle-roster__tag">LD</span> : null}
                        {unit.carriedVipSideId ? <span className="battle-roster__tag">VIP</span> : null}
                        {cooldown > 0 ? <span className="battle-roster__tag">CD {cooldown}</span> : null}
                      </div>
                    </article>
                  )) : (
                    <div className="legend-note">Battle units will appear here once combat begins.</div>
                  )}
                </div>
              </div>
            </aside>

            <section className="panel board-panel board-panel--centered board-panel--war-table battle-layout__board">
              <div className="board-title-row board-title-row--war-table">
                <p className="section-eyebrow">Battlefield</p>
                <h2>Live War Table</h2>
                <div className="legend-note">The board stays dominant. Movement, targets, support states, and rescue lanes stay on the surface while the folios carry context and command.</div>
              </div>
              {pendingRiskConfirmation ? (
                <div className="risk-overlay" role="alertdialog" aria-modal="false">
                  <div className="risk-overlay__eyebrow">Ally Risk</div>
                  <h3>Pyromancer burst warning</h3>
                  <p>
                    This cast will hit {pendingRiskConfirmation.allyCount} allied unit{pendingRiskConfirmation.allyCount === 1 ? "" : "s"}.
                  </p>
                  <div className="risk-overlay__markers">
                    <span className="tile__burst-marker tile__burst-marker--center risk-overlay__marker">G</span>
                    <span className="tile__burst-marker tile__burst-marker--splash risk-overlay__marker">D</span>
                  </div>
                  <div className="risk-overlay__actions">
                    <button type="button" onClick={() => commitBattleAction(pendingRiskConfirmation.targetCellKey)}>
                      Continue
                    </button>
                    <button type="button" onClick={() => setPendingRiskConfirmation(null)}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : null}
              <div className="board-grid board-grid--war-table board-grid--battlefield" style={{ gridTemplateColumns: `repeat(${battleViewModel.columnCount}, 1fr)` }}>
                {battleViewModel.tiles.map((tile) => {
                  const isEligible = tile.occupyingUnitId ? eligibleUnitIds.includes(tile.occupyingUnitId) : false;
                  const isReachable = reachableCellKeys.includes(tile.key);
                  const isInActionRange = actionRangeCellKeys.includes(tile.key);
                  const targetKind = legalTargetsByCellKey.get(tile.key)?.targetKind ?? null;
                  const isEnemyTarget = targetKind === "enemy";
                  const isObjectTarget = targetKind === "fieldObject";
                  const isAreaTarget = targetKind === "areaCell";
                  const isObjectiveTarget = targetKind === "objective";
                  const isSupportTarget = targetKind === "self";
                  const isSupportAffected = tile.occupyingUnitId ? supportAffectedUnitIds.includes(tile.occupyingUnitId) : false;
                  const isActive = tile.occupyingUnitId === activeUnitId;
                  const isBurstCenter = hoveredBurstTarget?.centerCellKey === tile.key;
                  const isBurstSplash = hoveredBurstTarget?.splashCellKeys.includes(tile.key) ?? false;
                  const hpLabel =
                    tile.currentHp !== null && tile.maxHp !== null
                      ? `${tile.currentHp}/${tile.maxHp}`
                      : "--";
                  const hpPercent =
                    tile.currentHp !== null && tile.maxHp !== null && tile.maxHp > 0
                      ? Math.max(8, Math.round((tile.currentHp / tile.maxHp) * 100))
                      : 0;

                  return (
                    <button
                      key={tile.key}
                      type="button"
                      className={[
                        "tile",
                        "tile--war-table",
                        battleZoneClassName(tile.isPlayable),
                        tile.fieldObjectType ? `tile--field-${tile.fieldObjectType}` : "",
                        tile.vipOwnerSide ? "tile--field-vip" : "",
                        tile.vipOwnerSide ? `tile--field-vip-${tile.vipOwnerSide}` : "",
                        tile.rescueZoneForSide ? "tile--rescue-zone" : "",
                        tile.rescueZoneForSide ? `tile--rescue-zone-${tile.rescueZoneForSide}` : "",
                        isEligible ? "tile--eligible" : "",
                        isReachable ? "tile--reachable" : "",
                        isInActionRange ? "tile--action-range" : "",
                        isEnemyTarget ? "tile--target" : "",
                        isObjectTarget ? "tile--target" : "",
                        isAreaTarget ? "tile--target" : "",
                        isObjectiveTarget ? "tile--target" : "",
                        isBurstCenter ? "tile--burst-center" : "",
                        isBurstSplash ? "tile--burst-splash" : "",
                        isSupportAffected ? "tile--support-affected" : "",
                        isSupportTarget ? "tile--support-target" : "",
                        isActive ? "tile--active" : "",
                      ].join(" ").trim()}
                      disabled={!tile.isPlayable}
                      onClick={() => handleBattleTileClick(tile.key, tile.occupyingUnitId)}
                      onMouseEnter={() => {
                        if (activeDefinition?.actionType === "castPyromancerBurst") {
                          setHoveredActionCellKey(tile.key);
                        }
                      }}
                      onMouseLeave={() => {
                        setHoveredActionCellKey(null);
                      }}
                      onFocus={() => {
                        if (activeDefinition?.actionType === "castPyromancerBurst") {
                          setHoveredActionCellKey(tile.key);
                        }
                      }}
                      onBlur={() => {
                        setHoveredActionCellKey(null);
                      }}
                      title={`${tile.key} ${tile.occupyingUnitId ?? "empty"}`}
                    >
                      {tile.rescueZoneForSide ? (
                        <span className={`tile__zone-marker tile__zone-marker--${tile.rescueZoneForSide}`}>
                          {tile.rescueZoneForSide === "player1" ? "P1" : "P2"}
                        </span>
                      ) : null}
                      {isBurstCenter ? <span className="tile__burst-marker tile__burst-marker--center">G</span> : null}
                      {!isBurstCenter && isBurstSplash ? <span className="tile__burst-marker tile__burst-marker--splash">D</span> : null}
                      {tile.occupyingUnitId ? (
                        <span className="tile__unit tile__unit--board">
                          <span className={`unit-badge unit-badge--token unit-badge--board unit-badge--${tile.occupyingSide} unit-badge--${unitThemeKey(tile.unitLabel)}`} title={tile.unitLabel ?? undefined}>
                            <span className="unit-badge__crest">
                              <UnitGlyph unitLabel={tile.unitLabel} />
                            </span>
                          </span>
                          <span className="tile__hp tile__hp--corner">
                            <span className="tile__hp-track">
                              <span
                                className="tile__hp-fill"
                                style={{ width: `${hpPercent}%` }}
                              />
                            </span>
                            <span className="tile__hp-label">{hpLabel}</span>
                          </span>
                          <span className="tile__unit-meta tile__unit-meta--top-left">
                            {tile.isLeader ? <span className="tile__status-chip tile__status-chip--leader">LD</span> : null}
                          </span>
                          <span className="tile__unit-meta tile__unit-meta--bottom-left">
                            {tile.carriedVipSideId ? <span className="tile__status-chip tile__status-chip--objective">VIP</span> : null}
                          </span>
                          <span className="tile__unit-meta tile__unit-meta--bottom-right">
                            {tile.remainingCooldown > 0 ? <span className="tile__status-chip tile__status-chip--cooldown">CD {tile.remainingCooldown}</span> : null}
                            <span className="tile__facing-badge" title={`Facing ${facingLabel(tile.facing!)}`}>
                              {facingShortLabel(tile.facing!)}
                            </span>
                          </span>
                        </span>
                      ) : tile.vipOwnerSide ? (
                        <span className={`field-object-badge field-object-badge--vip field-object-badge--vip-${tile.vipOwnerSide} field-object-badge--battle`}>
                          <span className="field-object-badge__crest">
                            <FieldObjectGlyph fieldObjectType="vip" />
                          </span>
                          <span className="field-object-badge__content">
                            <span className="field-object-badge__name">{tile.vipOwnerSide === "player1" ? "P1 VIP" : "P2 VIP"}</span>
                            <span className="field-object-badge__trait">Rescue objective</span>
                          </span>
                        </span>
                      ) : tile.fieldObjectType ? (
                        <span className={`field-object-badge field-object-badge--${tile.fieldObjectType} field-object-badge--battle`}>
                          <span className="field-object-badge__crest">
                            <FieldObjectGlyph fieldObjectType={tile.fieldObjectType} />
                          </span>
                          <span className="field-object-badge__content">
                            <span className="field-object-badge__name">{fieldObjectLabel(tile.fieldObjectType)}</span>
                            <span className="field-object-badge__trait">{fieldObjectTrait(tile.fieldObjectType)}</span>
                          </span>
                        </span>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            </section>

            <aside className="panel side-panel side-panel--folio battle-layout__actions">
              <div className="side-panel__section side-panel__section--folio side-panel__section--command">
                <p className="section-eyebrow">Command Folio</p>
                <h2>Turn State</h2>
                <div className="status-pills">
                  <span className={`status-pill status-pill--side status-pill--${activeBattleState.turnState.currentSideId}`}>{sideLabel(activeBattleState.turnState.currentSideId)}</span>
                  <span className="status-pill">{activationStageLabel(activeBattleState.turnState.activationStage)}</span>
                  <span className={actionAvailable ? "status-pill status-pill--active" : "status-pill"}>
                    {actionAvailable ? "Action Ready" : "Action Spent"}
                  </span>
                </div>
                <div><strong>Active unit:</strong> {activeUnit?.unitInstanceId ?? "None"}</div>
                <div><strong>Facing:</strong> {activeUnit ? `${facingLabel(activeUnit.facing)} (${facingShortLabel(activeUnit.facing)})` : "-"}</div>
                <div className="instruction-box">{getStageInstruction(activeBattleState)}</div>
              </div>

              <div className="side-panel__section side-panel__section--folio side-panel__section--summary">
                <h3>Selected Unit</h3>
                {activeUnit && activeDefinition ? (
                  <div className={`unit-summary-card unit-summary-card--${activeUnit.ownerSide} unit-summary-card--${activeDefinition.unitDefinitionId}`}>
                    <div className="unit-summary-card__banner">
                      <span className="unit-summary-card__crest">
                        <UnitGlyph unitLabel={activeDefinition.name} />
                      </span>
                      <div className="unit-summary-card__identity">
                        <strong>{activeUnit.unitInstanceId}</strong>
                        <span>{activeDefinition.name}</span>
                      </div>
                    </div>
                    <div className="unit-summary-card__title">
                      <span>{activeDefinition.damageFamily}</span>
                      <span>Move {activeDefinition.movement} · Range {activeDefinition.attackRange}</span>
                    </div>
                    <div className="unit-summary-card__stats">
                      <span>HP {activeUnit.currentHp} / {activeDefinition.maxHp}</span>
                      <span>Atk {activeDefinition.attack} · Def {activeDefinition.defence}</span>
                      <span>Facing {facingLabel(activeUnit.facing)} ({facingShortLabel(activeUnit.facing)})</span>
                    </div>
                    <div className="status-pills status-pills--compact">
                      <span className={activeUnit.isLeader ? "status-pill status-pill--active" : "status-pill status-pill--muted"}>Leader</span>
                      <span className={activeUnit.carriedVipSideId ? "status-pill status-pill--active" : "status-pill status-pill--muted"}>VIP</span>
                      <span className={Math.max(0, activeUnit.eligibleOnOrAfterSideOpportunity - activeBattleState.turnState.sideOpportunityIndexBySide[activeUnit.ownerSide]) > 0 ? "status-pill status-pill--active" : "status-pill status-pill--muted"}>
                        CD {Math.max(0, activeUnit.eligibleOnOrAfterSideOpportunity - activeBattleState.turnState.sideOpportunityIndexBySide[activeUnit.ownerSide])}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="legend-note">Select a unit to inspect its live battle state.</div>
                )}
              </div>

              {activeBattleState.turnState.activationStage === "attackOrSkip" ? (
                <div className="side-panel__section side-panel__section--folio">
                  <button type="button" onClick={() => setBattleState((current) => (current ? skipAttack(current) : current))}>
                    Skip Action
                  </button>
                  <div><strong>Legal targets:</strong> {legalTargets.length}</div>
                  <div className="legend-note">
                    {activeDefinition?.actionType === "healAllAllies"
                      ? "The caster is the green target. All living allies glow green because they will receive the heal if the action is used."
                      : activeDefinition?.actionType === "castPyromancerBurst"
                        ? "Highlighted tiles are valid G targets, including high grass. Hover a G tile to preview the four orthogonal D tiles the burst will scorch, and ally hits still require confirmation."
                      : activeUnit?.carriedVipSideId
                        ? "This unit is carrying the VIP and cannot attack. Move toward the rescue zone or skip the action step."
                        : "Light red tiles show the full action range. Stronger red highlights show enemy units, adjacent rescue-eligible VIPs, or high grass that are legal targets right now."}
                  </div>
                </div>
              ) : null}

              {activeBattleState.turnState.activationStage === "rotate" ? (
                <div className="side-panel__section side-panel__section--folio">
                  <div><strong>Choose final facing:</strong></div>
                  <div className="rotate-controls rotate-controls--arrows">
                    {rotateFacings.map((facing) => (
                      <button
                        key={facing}
                        type="button"
                        className={activeUnit?.facing === facing ? "facing-button facing-button--active" : "facing-button"}
                        onClick={() => setBattleState((current) => (current ? rotateActiveUnit(current, facing) : current))}
                        title={`Face ${facing}`}
                      >
                        {facingGlyph(facing)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </aside>
          </section>
        </>
      ) : null}
    </main>
  );
}

