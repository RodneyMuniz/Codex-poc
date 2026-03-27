import type { GridCoordinate, SideId } from "./board";

export type Facing = "north" | "east" | "south" | "west";
export type UnitActionType = "attackEnemy" | "healAllAllies" | "castPyromancerBurst";
export type DamageFamily = "physical" | "magical" | "support";

export interface Footprint {
  anchor: "topLeft";
  width: number;
  height: number;
}

export interface UnitDefinition {
  unitDefinitionId: string;
  name: string;
  maxHp: number;
  attack: number;
  defence: number;
  movement: number;
  attackRange: number;
  cost: number;
  weight: number;
  actionType: UnitActionType;
  damageFamily: DamageFamily;
  healAmount: number | null;
  defaultFacing: Facing;
  footprint: Footprint;
}

export interface UnitInstance {
  unitInstanceId: string;
  unitDefinitionId: string;
  ownerSide: SideId;
  isLeader: boolean;
  carriedVipSideId: SideId | null;
  anchorCell: GridCoordinate;
  facing: Facing;
  currentHp: number;
  isAlive: boolean;
  eligibleOnOrAfterSideOpportunity: number;
  assetVariantId: string;
}
