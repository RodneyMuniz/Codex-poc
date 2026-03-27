import type { CellKey, SideId } from "../model/board";
import type { ActionResultSnapshot, BattleState } from "../model/battle";
import type { Facing, UnitInstance } from "../model/unit";
import { toCellKey } from "../model/board";
import { getEligibleUnitIds } from "../queries/getEligibleUnitIds";
import { getLegalTargets } from "../queries/getLegalTargets";
import { isLegalMoveDestination } from "../queries/getReachableCellKeys";
import { openOpportunity } from "../setup/createSandboxBattle";
import { getWinnerSideId } from "../systems/getWinnerSideId";
import { resolveCombat } from "../systems/resolveCombat";
import { resolveSupportAction } from "../systems/resolveSupportAction";

function assert(condition: boolean, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

function nextSide(sideId: SideId): SideId {
  return sideId === "player1" ? "player2" : "player1";
}

function sideLabel(sideId: SideId): string {
  return sideId === "player1" ? "Player 1" : "Player 2";
}

function cloneUnits(unitsById: BattleState["unitsById"]): BattleState["unitsById"] {
  return Object.fromEntries(
    Object.entries(unitsById).map(([unitId, unit]) => [unitId, { ...unit, anchorCell: { ...unit.anchorCell } }]),
  );
}

function cloneBoardState(boardState: BattleState["boardState"]): BattleState["boardState"] {
  return {
    ...boardState,
    cellsByKey: Object.fromEntries(
      Object.entries(boardState.cellsByKey).map(([cellKey, cell]) => [cellKey, { ...cell }]),
    ) as BattleState["boardState"]["cellsByKey"],
  };
}

function cloneObjectives(objectives: BattleState["objectives"]): BattleState["objectives"] {
  return Object.fromEntries(
    Object.entries(objectives).map(([sideId, objective]) => [
      sideId,
      objective ? { ...objective, rescueCellKeys: [...objective.rescueCellKeys] } : objective,
    ]),
  ) as BattleState["objectives"];
}

function withLastResolvedAction(battleState: BattleState, action: ActionResultSnapshot): BattleState {
  return {
    ...battleState,
    lastResolvedAction: action,
  };
}

function advanceToNextSide(battleState: BattleState): BattleState {
  const nextSideId = nextSide(battleState.turnState.currentSideId);
  return openOpportunity(battleState, nextSideId);
}

function getActiveUnit(battleState: BattleState): UnitInstance {
  const activeUnitId = battleState.turnState.activeUnitId;
  assert(activeUnitId !== null, "There is no active unit.");
  return battleState.unitsById[activeUnitId];
}

function applyFatigueToActiveUnit(
  battleState: BattleState,
  activeUnitId: string,
  cooldownTurns: number = 2,
): BattleState["unitsById"] {
  const unitsById = cloneUnits(battleState.unitsById);
  const currentSideId = battleState.turnState.currentSideId;
  const currentOpportunity = battleState.turnState.sideOpportunityIndexBySide[currentSideId];

  unitsById[activeUnitId] = {
    ...unitsById[activeUnitId],
    eligibleOnOrAfterSideOpportunity: currentOpportunity + cooldownTurns,
  };

  return unitsById;
}

function createActivationLogSummary(battleState: BattleState, activeUnit: UnitInstance, facing: Facing): string {
  const activationSummary = battleState.turnState.activationSummary;
  assert(activationSummary !== null, "Activation summary is missing.");

  const movementSummary =
    activationSummary.startCellKey === activationSummary.endCellKey
      ? `held at ${activationSummary.endCellKey}`
      : `moved ${activationSummary.startCellKey} -> ${activationSummary.endCellKey}`;

  return `${sideLabel(activationSummary.actingSideId)}: ${activeUnit.unitInstanceId} ${movementSummary}, ${activationSummary.actionSummary}, facing ${facing}.`;
}

function completeActivation(battleState: BattleState, activeUnit: UnitInstance, facing: Facing): BattleState {
  const finalizedState = withLastResolvedAction(
    {
      ...battleState,
      turnState: {
        ...battleState.turnState,
        activeUnitId: null,
        activationSummary: null,
      },
    },
    {
      actionType: "rotate",
      actingUnitId: activeUnit.unitInstanceId,
      targetUnitId: null,
      hitResult: null,
      supportResult: null,
      defeatedUnitIds: [],
      positionChanges: [],
      nextTurnSideId: nextSide(battleState.turnState.currentSideId),
      summary: createActivationLogSummary(battleState, activeUnit, facing),
    },
  );
  const winnerSideId = getWinnerSideId(finalizedState);

  if (winnerSideId) {
    return {
      ...finalizedState,
      status: "victory",
      winnerSideId,
      turnState: {
        ...finalizedState.turnState,
        activationStage: "selectUnit",
      },
      lastResolvedAction: {
        ...finalizedState.lastResolvedAction!,
        nextTurnSideId: null,
        summary: `${finalizedState.lastResolvedAction!.summary} ${winnerSideId === "player1" ? "Player 1" : "Player 2"} wins.`,
      },
    };
  }

  return advanceToNextSide(finalizedState);
}

export function continueAfterForcedPass(battleState: BattleState): BattleState {
  assert(battleState.turnState.activationStage === "forcedPass", "Battle is not waiting on a forced pass.");
  return advanceToNextSide(battleState);
}

export function selectActiveUnit(battleState: BattleState, unitId: string): BattleState {
  assert(battleState.turnState.activationStage === "selectUnit", "A unit cannot be selected right now.");
  assert(getEligibleUnitIds(battleState).includes(unitId), "Unit is not eligible for activation.");
  const activeUnit = battleState.unitsById[unitId];

  return withLastResolvedAction(
    {
      ...battleState,
      turnState: {
        ...battleState.turnState,
        activeUnitId: unitId,
        activationStage: "move",
        activationSummary: {
          actingUnitId: unitId,
          actingSideId: activeUnit.ownerSide,
          startCellKey: toCellKey(activeUnit.anchorCell),
          endCellKey: toCellKey(activeUnit.anchorCell),
          actionSummary: "took no action",
        },
      },
    },
    {
      actionType: "selectUnit",
      actingUnitId: unitId,
      targetUnitId: null,
      hitResult: null,
      supportResult: null,
      defeatedUnitIds: [],
      positionChanges: [],
      nextTurnSideId: null,
      summary: `${activeUnit.unitInstanceId} is now active.`,
    },
  );
}

export function moveActiveUnit(battleState: BattleState, destinationKey: CellKey): BattleState {
  assert(battleState.turnState.activationStage === "move", "Move step is not active.");

  const activeUnit = getActiveUnit(battleState);
  const fromKey = toCellKey(activeUnit.anchorCell);
  assert(isLegalMoveDestination(battleState, activeUnit.unitInstanceId, destinationKey), "Destination is not reachable.");

  const destinationCell = battleState.boardState.cellsByKey[destinationKey];
  const unitsById = cloneUnits(battleState.unitsById);
  const occupancyByCellKey = { ...battleState.occupancyByCellKey };

  unitsById[activeUnit.unitInstanceId] = {
    ...unitsById[activeUnit.unitInstanceId],
    anchorCell: {
      row: destinationCell.row,
      column: destinationCell.column,
    },
  };

  delete occupancyByCellKey[fromKey];
  occupancyByCellKey[destinationKey] = activeUnit.unitInstanceId;

  return withLastResolvedAction(
    {
      ...battleState,
      unitsById,
      occupancyByCellKey,
      turnState: {
        ...battleState.turnState,
        activationStage: "attackOrSkip",
        activationSummary: battleState.turnState.activationSummary
          ? {
              ...battleState.turnState.activationSummary,
              endCellKey: destinationKey,
            }
          : null,
      },
    },
    {
      actionType: "move",
      actingUnitId: activeUnit.unitInstanceId,
      targetUnitId: null,
      hitResult: null,
      supportResult: null,
      defeatedUnitIds: [],
      positionChanges: [{ unitInstanceId: activeUnit.unitInstanceId, from: fromKey, to: destinationKey }],
      nextTurnSideId: null,
      summary:
        fromKey === destinationKey
          ? `${activeUnit.unitInstanceId} holds position.`
          : `${activeUnit.unitInstanceId} moves to ${destinationKey}.`,
    },
  );
}

export function skipAttack(battleState: BattleState): BattleState {
  assert(battleState.turnState.activationStage === "attackOrSkip", "Attack step is not active.");
  assert(battleState.turnState.activeUnitId !== null, "There is no active unit to skip attack.");

  return withLastResolvedAction(
    {
      ...battleState,
      turnState: {
        ...battleState.turnState,
        activationStage: "rotate",
        activationSummary: battleState.turnState.activationSummary
          ? {
              ...battleState.turnState.activationSummary,
              actionSummary: "took no action",
            }
          : null,
      },
    },
    {
      actionType: "skipAttack",
      actingUnitId: battleState.turnState.activeUnitId,
      targetUnitId: null,
      hitResult: null,
      supportResult: null,
      defeatedUnitIds: [],
      positionChanges: [],
      nextTurnSideId: null,
      summary: `${battleState.turnState.activeUnitId} skips its action.`,
    },
  );
}

export function performActionWithActiveUnit(
  battleState: BattleState,
  targetCellKey: CellKey,
  randomValue: () => number = Math.random,
): BattleState {
  assert(battleState.turnState.activationStage === "attackOrSkip", "Action step is not active.");

  const activeUnit = getActiveUnit(battleState);
  const activeDefinition = battleState.unitDefinitions[activeUnit.unitDefinitionId];
  const legalTarget = getLegalTargets(battleState, activeUnit.unitInstanceId).find(
    (target) => target.cellKey === targetCellKey,
  );
  assert(legalTarget !== undefined, "Target is not legal.");

  if (activeDefinition.actionType === "healAllAllies") {
    const supportResult = resolveSupportAction(
      activeUnit,
      activeDefinition,
      Object.values(battleState.unitsById).filter((unit) => unit.ownerSide === activeUnit.ownerSide),
      battleState.unitDefinitions,
    );
    const unitsById = applyFatigueToActiveUnit(battleState, activeUnit.unitInstanceId, 3);

    supportResult.healingChanges.forEach((change) => {
      unitsById[change.unitId] = {
        ...unitsById[change.unitId],
        currentHp: change.resultingHp,
      };
    });

    const actionState = withLastResolvedAction(
      {
        ...battleState,
        unitsById,
        turnState: {
          ...battleState.turnState,
          activationStage: "rotate",
          activationSummary: battleState.turnState.activationSummary
            ? {
                ...battleState.turnState.activationSummary,
                actionSummary:
                  supportResult.healingChanges.length > 0
                    ? `healed ${supportResult.healingChanges.length} allies`
                    : "used support with no healing",
              }
            : null,
        },
      },
      {
        actionType: "support",
        actingUnitId: activeUnit.unitInstanceId,
        targetUnitId: targetCellKey,
        hitResult: null,
        supportResult,
        defeatedUnitIds: [],
        positionChanges: [],
        nextTurnSideId: null,
        summary:
          supportResult.healingChanges.length > 0
            ? `${activeUnit.unitInstanceId} heals ${supportResult.healingChanges.length} allied units.`
            : `${activeUnit.unitInstanceId} uses a support action, but no allies needed healing.`,
      },
    );

    return completeActivation(actionState, unitsById[activeUnit.unitInstanceId], unitsById[activeUnit.unitInstanceId].facing);
  }

  if (activeDefinition.actionType === "castPyromancerBurst") {
    const unitsById = cloneUnits(battleState.unitsById);
    const occupancyByCellKey = { ...battleState.occupancyByCellKey };
    const boardState = cloneBoardState(battleState.boardState);
    const objectives = cloneObjectives(battleState.objectives);
    const defeatedUnitIds: string[] = [];
    const affectedCellKeys = [legalTarget.centerCellKey, ...legalTarget.splashCellKeys];
    let clearedGrassCount = 0;

    legalTarget.affectedUnitIds.forEach((unitId) => {
      const targetUnit = unitsById[unitId];
      const nextHp = Math.max(0, targetUnit.currentHp - activeDefinition.attack);
      const isAlive = nextHp > 0;

      unitsById[unitId] = {
        ...targetUnit,
        currentHp: nextHp,
        isAlive,
      };

      if (!isAlive) {
        defeatedUnitIds.push(unitId);
        delete occupancyByCellKey[toCellKey(targetUnit.anchorCell)];

        const carriedVipSideId = unitsById[unitId].carriedVipSideId;
        if (carriedVipSideId && objectives[carriedVipSideId]) {
          objectives[carriedVipSideId] = {
            ...objectives[carriedVipSideId]!,
            state: "dropped",
            cellKey: toCellKey(targetUnit.anchorCell),
            carrierUnitId: null,
          };
          boardState.cellsByKey[toCellKey(targetUnit.anchorCell)] = {
            ...boardState.cellsByKey[toCellKey(targetUnit.anchorCell)],
            tileType: "vip",
            blocksMovement: true,
            blocksOccupation: true,
            blocksLineOfFire: false,
          };
          unitsById[unitId] = {
            ...unitsById[unitId],
            carriedVipSideId: null,
          };
        }
      }
    });

    affectedCellKeys.forEach((cellKey) => {
      const targetCell = boardState.cellsByKey[cellKey];
      if (targetCell?.tileType === "highGrass") {
        boardState.cellsByKey[cellKey] = {
          ...targetCell,
          tileType: "plain",
          blocksMovement: false,
          blocksOccupation: false,
          blocksLineOfFire: false,
        };
        clearedGrassCount += 1;
      }
    });

    unitsById[activeUnit.unitInstanceId] = {
      ...unitsById[activeUnit.unitInstanceId],
      eligibleOnOrAfterSideOpportunity:
        battleState.turnState.sideOpportunityIndexBySide[battleState.turnState.currentSideId] + 2,
    };

    const hitCount = legalTarget.affectedUnitIds.length;
    const actionSummary =
      hitCount > 0 || clearedGrassCount > 0
        ? `scorched ${hitCount} units and cleared ${clearedGrassCount} grass tiles from ${legalTarget.centerCellKey}`
        : `cast flames at ${legalTarget.centerCellKey} with no effect`;
    const actionState = withLastResolvedAction(
      {
        ...battleState,
        unitsById,
        occupancyByCellKey,
        boardState,
        objectives,
        turnState: {
          ...battleState.turnState,
          activationStage: "rotate",
          activationSummary: battleState.turnState.activationSummary
            ? {
                ...battleState.turnState.activationSummary,
                actionSummary,
              }
            : null,
        },
      },
      {
        actionType: "attack",
        actingUnitId: activeUnit.unitInstanceId,
        targetUnitId: legalTarget.centerCellKey,
        hitResult: null,
        supportResult: null,
        defeatedUnitIds,
        positionChanges: [],
        nextTurnSideId: null,
        summary:
          hitCount > 0 || clearedGrassCount > 0
            ? `${activeUnit.unitInstanceId} scorches ${hitCount} units and clears ${clearedGrassCount} grass tiles from ${legalTarget.centerCellKey}.`
            : `${activeUnit.unitInstanceId} casts flames at ${legalTarget.centerCellKey}, but nothing is affected.`,
      },
    );

    const actorAfterAction = actionState.unitsById[activeUnit.unitInstanceId];
    if (!actorAfterAction.isAlive) {
      return completeActivation(actionState, actorAfterAction, actorAfterAction.facing);
    }

    return actionState;
  }

  if (legalTarget.targetKind === "fieldObject") {
    const boardState = cloneBoardState(battleState.boardState);
    const targetCell = boardState.cellsByKey[targetCellKey];
    const unitsById = applyFatigueToActiveUnit(battleState, activeUnit.unitInstanceId);

    boardState.cellsByKey[targetCellKey] = {
      ...targetCell,
      tileType: "plain",
      blocksMovement: false,
      blocksOccupation: false,
      blocksLineOfFire: false,
    };

    return withLastResolvedAction(
      {
        ...battleState,
        boardState,
        unitsById,
        turnState: {
          ...battleState.turnState,
          activationStage: "rotate",
          activationSummary: battleState.turnState.activationSummary
            ? {
                ...battleState.turnState.activationSummary,
                actionSummary: `cleared high grass at ${targetCellKey}`,
              }
            : null,
        },
      },
      {
        actionType: "attack",
        actingUnitId: activeUnit.unitInstanceId,
        targetUnitId: targetCellKey,
        hitResult: null,
        supportResult: null,
        defeatedUnitIds: [],
        positionChanges: [],
        nextTurnSideId: null,
        summary: `${activeUnit.unitInstanceId} clears high grass at ${targetCellKey}.`,
      },
    );
  }

  if (legalTarget.targetKind === "objective") {
    const unitsById = applyFatigueToActiveUnit(battleState, activeUnit.unitInstanceId);
    const objectives = cloneObjectives(battleState.objectives);
    const boardState = cloneBoardState(battleState.boardState);
    const objectiveOwnerSide = legalTarget.objectiveOwnerSide;

    assert(objectiveOwnerSide !== null, "Objective owner side is missing.");
    assert(objectives[objectiveOwnerSide] !== undefined, "Objective is missing.");

    unitsById[activeUnit.unitInstanceId] = {
      ...unitsById[activeUnit.unitInstanceId],
      carriedVipSideId: objectiveOwnerSide,
    };

    objectives[objectiveOwnerSide] = {
      ...objectives[objectiveOwnerSide]!,
      state: "carried",
      cellKey: null,
      carrierUnitId: activeUnit.unitInstanceId,
    };
    boardState.cellsByKey[targetCellKey] = {
      ...boardState.cellsByKey[targetCellKey],
      tileType: "plain",
      blocksMovement: false,
      blocksOccupation: false,
      blocksLineOfFire: false,
    };

    return withLastResolvedAction(
      {
        ...battleState,
        unitsById,
        boardState,
        objectives,
        turnState: {
          ...battleState.turnState,
          activationStage: "rotate",
          activationSummary: battleState.turnState.activationSummary
            ? {
              ...battleState.turnState.activationSummary,
              actionSummary: `rescued the ${objectiveOwnerSide === "player1" ? "Player 1" : "Player 2"} VIP`,
            }
            : null,
        },
      },
      {
        actionType: "support",
        actingUnitId: activeUnit.unitInstanceId,
        targetUnitId: legalTarget.cellKey,
        hitResult: null,
        supportResult: null,
        defeatedUnitIds: [],
        positionChanges: [],
        nextTurnSideId: null,
        summary: `${activeUnit.unitInstanceId} rescues the ${objectiveOwnerSide === "player1" ? "Player 1" : "Player 2"} VIP.`,
      },
    );
  }

  assert(legalTarget.targetUnitId !== null, "Enemy target is missing.");
  const targetUnitId = legalTarget.targetUnitId;
  const defender = battleState.unitsById[targetUnitId];
  const defenderDefinition = battleState.unitDefinitions[defender.unitDefinitionId];
  const combatSnapshot = resolveCombat(
    activeUnit,
    activeDefinition,
    defender,
    defenderDefinition,
    legalTarget.relativeFacing!,
    randomValue(),
  );
  const unitsById = applyFatigueToActiveUnit(battleState, activeUnit.unitInstanceId);
  const occupancyByCellKey = { ...battleState.occupancyByCellKey };
  const objectives = cloneObjectives(battleState.objectives);
  const boardState = cloneBoardState(battleState.boardState);
  const defeatedUnitIds: string[] = [];

  unitsById[targetUnitId] = {
    ...unitsById[targetUnitId],
    currentHp: Math.max(0, combatSnapshot.defenderRemainingHp),
    isAlive: !combatSnapshot.defenderDefeated,
  };

  if (combatSnapshot.defenderDefeated) {
    defeatedUnitIds.push(targetUnitId);
    delete occupancyByCellKey[toCellKey(defender.anchorCell)];

    const carriedVipSideId = unitsById[targetUnitId].carriedVipSideId;
    if (carriedVipSideId && objectives[carriedVipSideId]) {
      objectives[carriedVipSideId] = {
        ...objectives[carriedVipSideId]!,
        state: "dropped",
        cellKey: toCellKey(defender.anchorCell),
        carrierUnitId: null,
      };
      boardState.cellsByKey[toCellKey(defender.anchorCell)] = {
        ...boardState.cellsByKey[toCellKey(defender.anchorCell)],
        tileType: "vip",
        blocksMovement: true,
        blocksOccupation: true,
        blocksLineOfFire: false,
      };
      unitsById[targetUnitId] = {
        ...unitsById[targetUnitId],
        carriedVipSideId: null,
      };
    }
  }

  return withLastResolvedAction(
    {
      ...battleState,
      unitsById,
      occupancyByCellKey,
      boardState,
      objectives,
      turnState: {
        ...battleState.turnState,
        activationStage: "rotate",
        activationSummary: battleState.turnState.activationSummary
          ? {
              ...battleState.turnState.activationSummary,
              actionSummary: combatSnapshot.didHit
                ? `hit ${targetUnitId} for ${combatSnapshot.damageDealt}`
                : `missed ${targetUnitId}`,
            }
          : null,
      },
    },
    {
      actionType: "attack",
      actingUnitId: activeUnit.unitInstanceId,
      targetUnitId,
      hitResult: combatSnapshot,
      supportResult: null,
      defeatedUnitIds,
      positionChanges: [],
      nextTurnSideId: null,
      summary: combatSnapshot.didHit
        ? `${activeUnit.unitInstanceId} hits ${targetUnitId} for ${combatSnapshot.damageDealt}.`
        : `${activeUnit.unitInstanceId} misses ${targetUnitId}.`,
    },
  );
}

export function rotateActiveUnit(battleState: BattleState, facing: Facing): BattleState {
  assert(battleState.turnState.activationStage === "rotate", "Rotate step is not active.");

  const activeUnit = getActiveUnit(battleState);
  const unitsById = cloneUnits(battleState.unitsById);

  unitsById[activeUnit.unitInstanceId] = {
    ...unitsById[activeUnit.unitInstanceId],
    facing,
  };

  return completeActivation(
    {
      ...battleState,
      unitsById,
    },
    unitsById[activeUnit.unitInstanceId],
    facing,
  );
}

