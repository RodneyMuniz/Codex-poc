# File: projects/tactics-game/artifacts/project.py

class Project:
    """
    Represents a core unit in the tactics game with health, mana, spell power,
    and casting capabilities.
    """

    def __init__(self, name: str, max_hp: int, current_hp: int, max_mana: int, mana: int, spell_power: int):
        """
        Initialize a new Project unit.

        Args:
            name (str): The name of the unit.
            max_hp (int): Maximum health points (must be positive).
            current_hp (int): Current health points (0 <= current_hp <= max_hp).
            max_mana (int): Maximum mana points (must be non-negative).
            mana (int): Current mana points (0 <= mana <= max_mana).
            spell_power (int): Spell power (must be non-negative).

        Raises:
            ValueError: If provided attribute values are invalid.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")

        if not (isinstance(max_hp, int) and max_hp > 0):
            raise ValueError("max_hp must be a positive integer")

        if not (isinstance(current_hp, int) and 0 <= current_hp <= max_hp):
            raise ValueError("current_hp must be an integer between 0 and max_hp")

        if not (isinstance(max_mana, int) and max_mana >= 0):
            raise ValueError("max_mana must be a non-negative integer")

        if not (isinstance(mana, int) and 0 <= mana <= max_mana):
            raise ValueError("mana must be an integer between 0 and max_mana")

        if not (isinstance(spell_power, int) and spell_power >= 0):
            raise ValueError("spell_power must be a non-negative integer")

        self.name = name
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.max_mana = max_mana
        self.mana = mana
        self.spell_power = spell_power

    def is_alive(self) -> bool:
        """
        Returns True if the unit is alive (current_hp > 0), else False.
        """
        return self.current_hp > 0

    def take_damage(self, amount: int):
        """
        Reduces current_hp by the damage amount, not going below zero.

        Args:
            amount (int): The damage amount (must be non-negative).

        Raises:
            ValueError: If amount is negative.
        """
        if not (isinstance(amount, int) and amount >= 0):
            raise ValueError("Damage amount must be a non-negative integer")

        self.current_hp = max(self.current_hp - amount, 0)

    def heal(self, amount: int):
        """
        Increases current_hp by the heal amount, not exceeding max_hp.

        Args:
            amount (int): The heal amount (must be non-negative).

        Raises:
            ValueError: If amount is negative.
        """
        if not (isinstance(amount, int) and amount >= 0):
            raise ValueError("Heal amount must be a non-negative integer")

        if self.current_hp == 0:
            # Optionally, healing a dead unit could be disallowed or marked as resurrection.
            # Here we allow healing from zero to revive.
            self.current_hp = min(amount, self.max_hp)
        else:
            self.current_hp = min(self.current_hp + amount, self.max_hp)

    def cast_spell(self, mana_cost: int, power: int) -> int:
        """
        Attempts to cast a spell consuming mana_cost and producing damage based on spell_power and power.

        Args:
            mana_cost (int): The mana cost to cast the spell (non-negative).
            power (int): A multiplier or base power of the spell (non-negative).

        Returns:
            int: The damage dealt by the spell.

        Raises:
            ValueError: If mana_cost or power is negative.
            RuntimeError: If not enough mana to cast the spell.
            RuntimeError: If the unit is dead.
        """
        if not (isinstance(mana_cost, int) and mana_cost >= 0):
            raise ValueError("mana_cost must be a non-negative integer")
        if not (isinstance(power, int) and power >= 0):
            raise ValueError("power must be a non-negative integer")
        if not self.is_alive():
            raise RuntimeError(f"Cannot cast spell: {self.name} is dead")
        if self.mana < mana_cost:
            raise RuntimeError(f"Not enough mana to cast spell (needed {mana_cost}, available {self.mana})")

        self.mana -= mana_cost
        damage = self.spell_power * power
        return damage
