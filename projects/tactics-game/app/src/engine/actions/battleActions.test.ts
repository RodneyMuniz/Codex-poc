import { describe, expect, it } from "vitest";
import {
  moveActiveUnit,
  performActionWithActiveUnit,
  rotateActiveUnit,
  selectActiveUnit,
  skipAttack,
} from "./battleActions";
import { getLegalTargets } from "../queries/getLegalTargets";
import { getReachableCellKeys } from "../queries/getReachableCellKeys";
import { createSandboxBattle } from "../setup/createSandboxBattle";

describe("battleActions", () => {
  it("applies move, attack, fatigue, and turn advance", () => {
    let battleState = createSandboxBattle({ randomValue: () => 0.1 });

    battleState = selectActiveUnit(battleState, "player1-unit-0-1");
    battleState = moveActiveUnit(battleState, "r5c6");
    battleState = performActionWithActiveUnit(battleState, "r7c6", () => 0.99);

    expect(battleState.unitsById["player1-unit-0-1"].eligibleOnOrAfterSideOpportunity).toBe(3);
    expect(battleState.unitsById["player2-unit-1-0"].currentHp).toBe(45);

    battleState = rotateActiveUnit(battleState, "south");

    expect(battleState.lastResolvedAction?.summary).toBe(
      "Player 1: player1-unit-0-1 moved r4c6 -> r5c6, hit player2-unit-1-0 for 15, facing south.",
    );
    expect(battleState.turnState.currentSideId).toBe("player2");
    expect(battleState.turnState.sideOpportunityIndexBySide.player2).toBe(1);
  });

  it("allows skipping an action before rotating", () => {
    let battleState = createSandboxBattle({ randomValue: () => 0.1 });

    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r3c4");
    battleState = skipAttack(battleState);

    expect(battleState.turnState.activationSummary?.actionSummary).toBe("took no action");

    expect(battleState.turnState.activationStage).toBe("rotate");
    expect(battleState.unitsById["player1-unit-0-0"].eligibleOnOrAfterSideOpportunity).toBe(1);

    battleState = rotateActiveUnit(battleState, "east");

    expect(battleState.lastResolvedAction?.summary).toBe(
      "Player 1: player1-unit-0-0 held at r3c4, took no action, facing east.",
    );
  });

  it("lets the cleric heal allied units during the action step", () => {
    let battleState = createSandboxBattle({
      randomValue: () => 0.1,
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "cleric", anchorCell: { row: 3, column: 4 }, facing: "south" },
          { unitDefinitionId: "warrior", anchorCell: { row: 4, column: 4 }, facing: "south" },
        ],
      },
    });

    battleState.unitsById["player1-unit-0-1"].currentHp = 30;
    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r3c4");
    battleState = performActionWithActiveUnit(battleState, "r3c4");

    expect(battleState.lastResolvedAction?.actionType).toBe("rotate");
    expect(battleState.unitsById["player1-unit-0-1"].currentHp).toBe(50);
    expect(battleState.unitsById["player1-unit-0-0"].eligibleOnOrAfterSideOpportunity).toBe(4);
    expect(battleState.turnState.currentSideId).toBe("player2");

    expect(battleState.lastResolvedAction?.summary).toBe(
      "Player 1: player1-unit-0-0 held at r3c4, healed 1 allies, facing south.",
    );
  });

  it("prevents movement through walls and blocks straight ranged line of fire", () => {
    const battleState = createSandboxBattle({
      randomValue: () => 0.1,
      fieldObjects: [
        { row: 5, column: 3, objectType: "wall" },
      ],
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "scout", anchorCell: { row: 4, column: 3 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 6, column: 3 }, facing: "north" },
        ],
      },
    });

    expect(getReachableCellKeys(battleState, "player1-unit-0-0")).not.toContain("r5c3");
    expect(getLegalTargets(battleState, "player1-unit-0-0").some((target) => target.targetUnitId === "player2-unit-1-0")).toBe(false);
  });

  it("lets attacks clear high grass and spend the unit action normally", () => {
    let battleState = createSandboxBattle({
      randomValue: () => 0.1,
      fieldObjects: [
        { row: 5, column: 5, objectType: "highGrass" },
      ],
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 4, column: 5 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 7, column: 6 }, facing: "north" },
        ],
      },
    });

    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r4c5");

    expect(getLegalTargets(battleState, "player1-unit-0-0").some((target) => target.cellKey === "r5c5")).toBe(true);

    battleState = performActionWithActiveUnit(battleState, "r5c5");

    expect(battleState.boardState.cellsByKey.r5c5.tileType).toBe("plain");
    expect(battleState.unitsById["player1-unit-0-0"].eligibleOnOrAfterSideOpportunity).toBe(3);
    expect(battleState.turnState.activationSummary?.actionSummary).toBe("cleared high grass at r5c5");
  });

  it("lets the pyromancer hit units on G and D tiles without wall blocking or dodge", () => {
    let battleState = createSandboxBattle({
      randomValue: () => 0.1,
      fieldObjects: [{ row: 4, column: 4, objectType: "wall" }],
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "pyromancer", anchorCell: { row: 3, column: 4 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 6, column: 4 }, facing: "north" },
          { unitDefinitionId: "cleric", anchorCell: { row: 7, column: 5 }, facing: "north" },
        ],
      },
    });

    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r5c5");

    const legalTargets = getLegalTargets(battleState, "player1-unit-0-0");
    const centerTarget = legalTargets.find((target) => target.cellKey === "r6c5");

    expect(centerTarget?.targetKind).toBe("areaCell");
    expect(centerTarget?.alliedAffectedUnitIds).toEqual(["player1-unit-0-0"]);
    expect(centerTarget?.enemyAffectedUnitIds).toEqual(["player2-unit-1-1", "player2-unit-1-0"]);
    expect(legalTargets.some((target) => target.cellKey === "r4c4")).toBe(false);

    battleState = performActionWithActiveUnit(battleState, "r6c5");

    expect(battleState.unitsById["player1-unit-0-0"].currentHp).toBe(15);
    expect(battleState.unitsById["player2-unit-1-0"].currentHp).toBe(45);
    expect(battleState.unitsById["player2-unit-1-1"].currentHp).toBe(15);
    expect(battleState.turnState.activationSummary?.actionSummary).toBe("scorched 3 units and cleared 0 grass tiles from r6c5");
    expect(battleState.unitsById["player1-unit-0-0"].eligibleOnOrAfterSideOpportunity).toBe(3);
    expect(battleState.boardState.cellsByKey.r4c4.tileType).toBe("wall");
  });

  it("lets the pyromancer choose a high-grass cell as G and still scorch units on D cells", () => {
    let battleState = createSandboxBattle({
      randomValue: () => 0.1,
      fieldObjects: [{ row: 6, column: 5, objectType: "highGrass" }],
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "pyromancer", anchorCell: { row: 3, column: 5 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 7, column: 5 }, facing: "north" },
        ],
      },
    });

    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r5c5");

    const legalTargets = getLegalTargets(battleState, "player1-unit-0-0");
    const grassCenterTarget = legalTargets.find((target) => target.cellKey === "r6c5");

    expect(grassCenterTarget?.targetKind).toBe("areaCell");
    expect(grassCenterTarget?.centerCellKey).toBe("r6c5");
    expect(grassCenterTarget?.splashCellKeys).toContain("r7c5");

    battleState = performActionWithActiveUnit(battleState, "r6c5");

    expect(battleState.unitsById["player1-unit-0-0"].currentHp).toBe(15);
    expect(battleState.unitsById["player2-unit-1-0"].currentHp).toBe(45);
    expect(battleState.turnState.activationSummary?.actionSummary).toBe("scorched 2 units and cleared 1 grass tiles from r6c5");
    expect(battleState.boardState.cellsByKey.r6c5.tileType).toBe("plain");
  });

  it("awards victory when a marked leader is defeated and that win condition is enabled", () => {
    let battleState = createSandboxBattle({
      randomValue: () => 0.1,
      winConditions: {
        eliminateAllEnemies: false,
        markedLeader: true,
      },
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "scout", anchorCell: { row: 4, column: 5 }, facing: "south", isLeader: true },
          { unitDefinitionId: "cleric", anchorCell: { row: 3, column: 4 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 6, column: 5 }, facing: "south", isLeader: true },
          { unitDefinitionId: "cleric", anchorCell: { row: 8, column: 8 }, facing: "north" },
        ],
      },
    });

    battleState.unitsById["player2-unit-1-0"].currentHp = 10;

    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r4c5");
    battleState = performActionWithActiveUnit(battleState, "r6c5", () => 0.99);
    battleState = rotateActiveUnit(battleState, "south");

    expect(battleState.status).toBe("victory");
    expect(battleState.winnerSideId).toBe("player1");
    expect(battleState.lastResolvedAction?.summary).toContain("Player 1 wins.");
  });

  it("lets a unit rescue its own VIP from adjacent range, disables further attacks while carrying, and wins on extraction", () => {
    let battleState = createSandboxBattle({
      randomValue: () => 0.1,
      winConditions: {
        eliminateAllEnemies: false,
        captureAndExtract: true,
      },
      fieldObjects: [
        { row: 0, column: 4, objectType: "vip", ownerSide: "player1" },
        { row: 10, column: 6, objectType: "vip", ownerSide: "player2" },
      ],
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 1, column: 5 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "cleric", anchorCell: { row: 10, column: 8 }, facing: "north" },
        ],
      },
    });

    battleState.objectives.player1 = {
      ...battleState.objectives.player1!,
      state: "idle",
      cellKey: "r2c5",
      carrierUnitId: null,
    };
    battleState.boardState.cellsByKey.r2c5 = {
      ...battleState.boardState.cellsByKey.r2c5,
      tileType: "vip",
      blocksMovement: true,
      blocksOccupation: true,
      blocksLineOfFire: false,
    };

    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r1c5");

    expect(getLegalTargets(battleState, "player1-unit-0-0").some((target) => target.targetKind === "objective" && target.cellKey === "r2c5")).toBe(true);

    battleState = performActionWithActiveUnit(battleState, "r2c5");

    expect(battleState.unitsById["player1-unit-0-0"].carriedVipSideId).toBe("player1");
    expect(battleState.objectives.player1?.state).toBe("carried");
    expect(getLegalTargets(battleState, "player1-unit-0-0")).toEqual([]);
    expect(battleState.boardState.cellsByKey.r2c5.tileType).toBe("plain");

    battleState = rotateActiveUnit(battleState, "south");
    battleState = {
      ...battleState,
      unitsById: {
        ...battleState.unitsById,
        "player1-unit-0-0": {
          ...battleState.unitsById["player1-unit-0-0"],
          eligibleOnOrAfterSideOpportunity: 3,
        },
      },
      turnState: {
        ...battleState.turnState,
        currentSideId: "player1",
        sideOpportunityIndexBySide: {
          ...battleState.turnState.sideOpportunityIndexBySide,
          player1: 3,
        },
        activeUnitId: null,
        activationStage: "selectUnit",
      },
    };
    battleState = selectActiveUnit(battleState, "player1-unit-0-0");
    battleState = moveActiveUnit(battleState, "r1c5");
    battleState = skipAttack(battleState);
    battleState = rotateActiveUnit(battleState, "south");

    expect(battleState.status).toBe("victory");
    expect(battleState.winnerSideId).toBe("player1");
    expect(battleState.lastResolvedAction?.summary).toContain("Player 1 wins.");
  });
});
