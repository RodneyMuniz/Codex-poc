# File: projects/tactics-game/artifacts/functionality.py

class Functionality:
    """
    Functionality class encapsulates health, mana, spell power, and casting behavior
    for a unit in the tactics game domain. It provides methods to manage HP/mana,
    perform spell casting, and verify unit status.
    """

    def __init__(self, name: str, max_hp: int, max_mana: int, spell_power: int):
        if not name or not isinstance(name, str):
            raise ValueError("Invalid name: Must be a non-empty string.")
        if max_hp <= 0:
            raise ValueError("max_hp must be a positive integer.")
        if max_mana < 0:
            raise ValueError("max_mana cannot be negative.")
        if spell_power < 0:
            raise ValueError("spell_power cannot be negative.")

        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.max_mana = max_mana
        self.mana = max_mana
        self.spell_power = spell_power

    def take_damage(self, amount: int):
        """
        Reduces current HP by damage amount, not dropping below zero.
        """
        if amount < 0:
            raise ValueError("Damage amount cannot be negative.")
        self.current_hp = max(self.current_hp - amount, 0)

    def heal(self, amount: int):
        """
        Increases current HP by heal amount, not exceeding max HP.
        """
        if amount < 0:
            raise ValueError("Heal amount cannot be negative.")
        if self.current_hp == 0:
            # Cannot heal a dead unit.
            return
        self.current_hp = min(self.current_hp + amount, self.max_hp)

    def cast_spell(self, mana_cost: int):
        """
        Attempts to cast a spell consuming mana_cost.
        Raises exception if not enough mana or invalid mana_cost.
        """
        if mana_cost <= 0:
            raise ValueError("Mana cost must be a positive integer.")
        if self.mana < mana_cost:
            raise RuntimeError(f"Not enough mana to cast spell (needed {mana_cost}, have {self.mana}).")
        self.mana -= mana_cost
        return self.spell_power

    def is_alive(self) -> bool:
        """
        Returns True if current HP is greater than 0, False otherwise.
        """
        return self.current_hp > 0
