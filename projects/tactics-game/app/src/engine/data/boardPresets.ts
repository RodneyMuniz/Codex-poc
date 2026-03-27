import type { BoardPreset } from "../model/board";

export const sandboxDefaultBoardPreset: BoardPreset = {
  boardPresetId: "sandbox_default_tapered_01",
  rowCount: 11,
  columnCount: 11,
  rows: [
    { rowIndex: 0, playableColumnStart: 2, playableColumnCount: 7, deploymentZone: "player1" },
    { rowIndex: 1, playableColumnStart: 1, playableColumnCount: 9, deploymentZone: "player1" },
    { rowIndex: 2, playableColumnStart: 0, playableColumnCount: 11, deploymentZone: "player1" },
    { rowIndex: 3, playableColumnStart: 0, playableColumnCount: 11, deploymentZone: "player1" },
    { rowIndex: 4, playableColumnStart: 0, playableColumnCount: 11, deploymentZone: "player1" },
    { rowIndex: 5, playableColumnStart: 0, playableColumnCount: 11, deploymentZone: "neutral" },
    { rowIndex: 6, playableColumnStart: 0, playableColumnCount: 11, deploymentZone: "player2" },
    { rowIndex: 7, playableColumnStart: 0, playableColumnCount: 11, deploymentZone: "player2" },
    { rowIndex: 8, playableColumnStart: 0, playableColumnCount: 11, deploymentZone: "player2" },
    { rowIndex: 9, playableColumnStart: 1, playableColumnCount: 9, deploymentZone: "player2" },
    { rowIndex: 10, playableColumnStart: 2, playableColumnCount: 7, deploymentZone: "player2" }
  ]
};
