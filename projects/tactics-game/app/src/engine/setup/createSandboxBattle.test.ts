import { describe, expect, it } from "vitest";
import { sandboxDefaultBoardPreset } from "../data/boardPresets";
import { createBoardState } from "./createBoardState";
import { createSandboxBattle } from "./createSandboxBattle";

describe("createBoardState", () => {
  it("loads the tapered playable mask and deployment zones", () => {
    const boardState = createBoardState(sandboxDefaultBoardPreset);

    expect(boardState.playableCellKeys).toHaveLength(109);
    expect(boardState.deploymentZoneCellKeys.player1).toHaveLength(49);
    expect(boardState.deploymentZoneCellKeys.player2).toHaveLength(49);
    expect(boardState.cellsByKey.r5c0.deploymentZone).toBe("neutral");
    expect(boardState.cellsByKey.r0c0.isPlayable).toBe(false);
    expect(boardState.cellsByKey.r0c2.isPlayable).toBe(true);
    expect(boardState.cellsByKey.r5c3.tileType).toBe("plain");
    expect(boardState.cellsByKey.r5c5.tileType).toBe("plain");
  });
});

describe("createSandboxBattle", () => {
  it("creates a two-unit default battle and opens the first side opportunity", () => {
    const battleState = createSandboxBattle({ randomValue: () => 0.1 });

    expect(battleState.turnState.startingSideId).toBe("player1");
    expect(battleState.turnState.currentSideId).toBe("player1");
    expect(battleState.turnState.sideOpportunityIndexBySide.player1).toBe(1);
    expect(battleState.sides.player1.unitInstanceIds).toHaveLength(2);
    expect(battleState.sides.player2.unitInstanceIds).toHaveLength(2);
    expect(battleState.occupancyByCellKey.r5c5).toBeUndefined();
    expect(battleState.boardState.cellsByKey.r5c5.tileType).toBe("plain");
  });

  it("accepts a custom player roster up to the setup budget", () => {
    const battleState = createSandboxBattle({
      randomValue: () => 0.1,
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 0, column: 2 }, facing: "south" },
          { unitDefinitionId: "pikeman", anchorCell: { row: 0, column: 3 }, facing: "south" },
          { unitDefinitionId: "scout", anchorCell: { row: 0, column: 4 }, facing: "south" },
          { unitDefinitionId: "cleric", anchorCell: { row: 0, column: 5 }, facing: "south" },
          { unitDefinitionId: "warrior", anchorCell: { row: 0, column: 6 }, facing: "south" },
        ],
      },
    });

    expect(battleState.sides.player1.unitInstanceIds).toHaveLength(5);
    expect(battleState.unitsById["player1-unit-0-2"].unitDefinitionId).toBe("scout");
    expect(battleState.unitsById["player1-unit-0-3"].unitDefinitionId).toBe("cleric");
  });

  it("accepts larger custom rosters when a higher points budget is provided and unit cap is disabled", () => {
    const battleState = createSandboxBattle({
      randomValue: () => 0.1,
      pointsBudget: 1000,
      maxUnitsPerSide: null,
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 0, column: 2 }, facing: "south" },
          { unitDefinitionId: "pikeman", anchorCell: { row: 0, column: 3 }, facing: "south" },
          { unitDefinitionId: "scout", anchorCell: { row: 0, column: 4 }, facing: "south" },
          { unitDefinitionId: "cleric", anchorCell: { row: 0, column: 5 }, facing: "south" },
          { unitDefinitionId: "pyromancer", anchorCell: { row: 0, column: 6 }, facing: "south" },
          { unitDefinitionId: "warrior", anchorCell: { row: 1, column: 1 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 10, column: 2 }, facing: "north" },
          { unitDefinitionId: "pikeman", anchorCell: { row: 10, column: 3 }, facing: "north" },
          { unitDefinitionId: "scout", anchorCell: { row: 10, column: 4 }, facing: "north" },
          { unitDefinitionId: "cleric", anchorCell: { row: 10, column: 5 }, facing: "north" },
          { unitDefinitionId: "pyromancer", anchorCell: { row: 10, column: 6 }, facing: "north" },
          { unitDefinitionId: "warrior", anchorCell: { row: 9, column: 1 }, facing: "north" },
        ],
      },
    });

    expect(battleState.sides.player1.unitInstanceIds).toHaveLength(6);
    expect(battleState.sides.player2.unitInstanceIds).toHaveLength(6);
  });

  it("accepts field objects supplied by setup instead of preset seeding", () => {
    const battleState = createSandboxBattle({
      randomValue: () => 0.1,
      fieldObjects: [
        { row: 5, column: 3, objectType: "wall" },
        { row: 5, column: 5, objectType: "highGrass" },
      ],
    });

    expect(battleState.boardState.cellsByKey.r5c3.tileType).toBe("wall");
    expect(battleState.boardState.cellsByKey.r5c3.blocksLineOfFire).toBe(true);
    expect(battleState.boardState.cellsByKey.r5c5.tileType).toBe("highGrass");
    expect(battleState.boardState.cellsByKey.r5c5.blocksOccupation).toBe(true);
  });

  it("requires exactly one leader per side when marked leader is enabled", () => {
    expect(() =>
      createSandboxBattle({
        randomValue: () => 0.1,
        winConditions: { markedLeader: true },
      }),
    ).toThrow("player1 must designate exactly 1 leader when marked leader is enabled.");
  });

  it("accepts custom marked leaders when the win condition is enabled", () => {
    const battleState = createSandboxBattle({
      randomValue: () => 0.1,
      winConditions: { markedLeader: true },
      playerSideLayout: {
        sideId: "player1",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 0, column: 2 }, facing: "south", isLeader: true },
          { unitDefinitionId: "cleric", anchorCell: { row: 0, column: 3 }, facing: "south" },
        ],
      },
      enemySideLayout: {
        sideId: "player2",
        units: [
          { unitDefinitionId: "warrior", anchorCell: { row: 10, column: 8 }, facing: "north", isLeader: true },
          { unitDefinitionId: "cleric", anchorCell: { row: 10, column: 7 }, facing: "north" },
        ],
      },
    });

    expect(battleState.winConditions.markedLeader).toBe(true);
    expect(battleState.unitsById["player1-unit-0-0"].isLeader).toBe(true);
    expect(battleState.unitsById["player2-unit-1-0"].isLeader).toBe(true);
  });

  it("rejects setup-bought field objects placed outside the owning side's setup half", () => {
    expect(() =>
      createSandboxBattle({
        randomValue: () => 0.1,
        fieldObjects: [{ row: 6, column: 5, objectType: "wall", ownerSide: "player1" }],
      }),
    ).toThrow("Field object cell r6c5 is not legal for player1.");
  });

  it("creates one VIP objective per side with side-owned rescue zones when capture-and-extract is enabled", () => {
    const battleState = createSandboxBattle({
      randomValue: () => 0.1,
      winConditions: { captureAndExtract: true },
      fieldObjects: [
        { row: 0, column: 4, objectType: "vip", ownerSide: "player1" },
        { row: 10, column: 6, objectType: "vip", ownerSide: "player2" },
      ],
    });

    expect(battleState.winConditions.captureAndExtract).toBe(true);
    expect(battleState.objectives.player1?.kind).toBe("vip");
    expect(battleState.objectives.player1?.state).toBe("idle");
    expect(battleState.objectives.player1?.carrierUnitId).toBeNull();
    expect(battleState.objectives.player1?.cellKey).toBe("r10c6");
    expect(battleState.objectives.player1?.rescueCellKeys).toEqual(["r0c4", "r1c4", "r0c5", "r1c5", "r0c6", "r1c6"]);
    expect(battleState.objectives.player2?.cellKey).toBe("r0c4");
    expect(battleState.objectives.player2?.rescueCellKeys).toEqual(["r9c4", "r10c4", "r9c5", "r10c5", "r9c6", "r10c6"]);
  });
});
