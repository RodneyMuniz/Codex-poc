import type { SandboxSideLayout } from "../model/battle";

export const defaultPlayerSideLayout: SandboxSideLayout = {
  sideId: "player1",
  units: [
    {
      unitDefinitionId: "warrior",
      anchorCell: { row: 3, column: 4 },
      facing: "south",
    },
    {
      unitDefinitionId: "pikeman",
      anchorCell: { row: 4, column: 6 },
      facing: "south",
    },
  ],
};

export const defaultEnemySideLayout: SandboxSideLayout = {
  sideId: "player2",
  units: [
    {
      unitDefinitionId: "warrior",
      anchorCell: { row: 7, column: 6 },
      facing: "north",
    },
    {
      unitDefinitionId: "pikeman",
      anchorCell: { row: 6, column: 4 },
      facing: "north",
    },
  ],
};

export const sandboxSideLayouts: SandboxSideLayout[] = [defaultPlayerSideLayout, defaultEnemySideLayout];