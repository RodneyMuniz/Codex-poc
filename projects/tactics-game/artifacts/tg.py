# projects/tactics-game/artifacts/tg.py

class Tg:
    """
    Tg unit class representing a combatant in the tactics-game.
    Encapsulates health, mana, spell power, and casting behavior.

    Attributes:
        name (str): Display name of the unit.
        max_hp (int): Maximum health points.
        current_hp (int): Current health points.
        max_mana (int): Maximum mana points.
        mana (int): Current mana points.
        spell_power (int): Spell power value affecting spell effects.
    """

    def __init__(self, name: str, max_hp: int, max_mana: int, spell_power: int):
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
        if not isinstance(max_hp, int) or max_hp <= 0:
            raise ValueError("max_hp must be a positive integer.")
        if not isinstance(max_mana, int) or max_mana < 0:
            raise ValueError("max_mana must be a non-negative integer.")
        if not isinstance(spell_power, int) or spell_power < 0:
            raise ValueError("spell_power must be a non-negative integer.")

        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.max_mana = max_mana
        self.mana = max_mana
        self.spell_power = spell_power

    def is_alive(self) -> bool:
        """
        Check if the unit is alive.

        Returns:
            bool: True if current_hp > 0, False otherwise.
        """
        return self.current_hp > 0

    def take_damage(self, amount: int) -> None:
        """
        Apply damage to the unit, reducing current_hp.

        Args:
            amount (int): Amount of damage to apply; must be non-negative.

        Raises:
            ValueError: If amount is negative.
        """
        if not isinstance(amount, int) or amount < 0:
            raise ValueError("Damage amount must be a non-negative integer.")
        self.current_hp = max(self.current_hp - amount, 0)

    def heal(self, amount: int) -> None:
        """
        Heal the unit, increasing current_hp up to max_hp.

        Args:
            amount (int): Amount of healing to apply; must be non-negative.

        Raises:
            ValueError: If amount is negative.
        """
        if not isinstance(amount, int) or amount < 0:
            raise ValueError("Heal amount must be a non-negative integer.")
        if self.is_alive():
            self.current_hp = min(self.current_hp + amount, self.max_hp)

    def cast_spell(self, mana_cost: int) -> bool:
        """
        Attempt to cast a spell consuming mana.

        Args:
            mana_cost (int): Mana cost of the spell; must be non-negative.

        Returns:
            bool: True if spell cast successfully, False otherwise.

        Raises:
            ValueError: If mana_cost is negative.
        """
        if not isinstance(mana_cost, int) or mana_cost < 0:
            raise ValueError("Mana cost must be a non-negative integer.")
        if mana_cost > self.mana:
            return False  # Not enough mana to cast
        self.mana -= mana_cost
        return True
