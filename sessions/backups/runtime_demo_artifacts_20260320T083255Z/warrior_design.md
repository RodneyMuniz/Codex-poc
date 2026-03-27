# Warrior Design Document

## Purpose

The Warrior slice represents a fundamental unit in the tactics game. It models a ground melee combatant with attributes critical for combat interactions. The design serves as a basis for implementing the character's lifecycle, actions, and health management in battle scenarios.

## Core Fields

- **name** (string): Identifier for the warrior instance.
- **max_hp** (integer): Maximum hit points the warrior can have.
- **attack_power** (integer): The damage inflicted when the warrior attacks.
- **current_hp** (integer): Current hit points, constrained between 0 and max_hp.

## Behaviors

- **take_damage(amount: int)**: Reduces `current_hp` by `amount` after applying any game-specific damage modifiers. `current_hp` should not fall below zero.
- **heal(amount: int)**: Increases `current_hp` by `amount` without surpassing `max_hp`.
- **attack(target: Warrior)**: Initiates an attack on another Warrior instance, causing the target to `take_damage` equal to the attacker's `attack_power`.
- **is_alive() -> bool**: Returns `True` if `current_hp` is greater than zero, otherwise `False`.

## Validation Rules

- `max_hp` must be a positive integer greater than zero.
- `attack_power` must be a non-negative integer (zero allowed).
- `current_hp` must be between 0 and `max_hp` inclusive.
- `name` must be a non-empty string.
- The `take_damage` and `heal` inputs must be non-negative integers.

## Acceptance Criteria

- Creating a Warrior with valid fields succeeds.
- `take_damage` deducts hit points correctly and clamps at zero.
- `heal` increases hit points up to `max_hp` without exceeding it.
- `attack` on another Warrior reduces the target's `current_hp` by `attack_power`.
- `is_alive` reflects the state of `current_hp` correctly.
- Validation rules are enforced on state-changing and initialization operations.
- Behavior methods handle edge cases gracefully (e.g., healing a dead warrior does not exceed max_hp).
- All behavior and validation functions are covered by unit tests.
