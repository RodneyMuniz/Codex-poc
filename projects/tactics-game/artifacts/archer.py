# File: projects/tactics-game/artifacts/archer.py

class Archer:
    """
    Archer unit class for tactics game.

    Attributes:
        name (str): Unit's name.
        max_hp (int): Maximum health points.
        current_hp (int): Current health points.
        max_mana (int): Maximum mana points.
        mana (int): Current mana points.
        spell_power (int): Power of cast spells.
    """

    def __init__(self, name: str, max_hp: int, max_mana: int, spell_power: int):
        if not name or not isinstance(name, str):
            raise ValueError("Invalid name for Archer.")
        if max_hp <= 0:
            raise ValueError("max_hp must be positive.")
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
        Reduce current HP by amount of damage taken.

        Args:
            amount (int): Damage to take; must be non-negative.

        Raises:
            ValueError: If amount is negative.
        """
        if amount < 0:
            raise ValueError("Damage amount cannot be negative.")
        self.current_hp = max(self.current_hp - amount, 0)

    def heal(self, amount: int):
        """
        Heal the Archer by a specified amount, not exceeding max HP.

        Args:
            amount (int): Healing amount; must be non-negative.

        Raises:
            ValueError: If amount is negative.
        """
        if amount < 0:
            raise ValueError("Heal amount cannot be negative.")
        self.current_hp = min(self.current_hp + amount, self.max_hp)

    def cast_spell(self, mana_cost: int):
        """
        Cast a spell consuming mana. Checks that there is enough mana.

        Args:
            mana_cost (int): Mana cost of the spell; must be positive.

        Raises:
            ValueError: If mana_cost is not positive.
            RuntimeError: If not enough mana to cast the spell.
        """
        if mana_cost <= 0:
            raise ValueError("mana_cost must be positive to cast a spell.")
        if self.mana < mana_cost:
            raise RuntimeError(f"{self.name} does not have enough mana to cast the spell.")
        # Spend mana
        self.mana -= mana_cost
        # Implement spell effect influenced by spell_power elsewhere in game logic

    def is_alive(self) -> bool:
        """
        Check if the Archer is alive (current_hp > 0).

        Returns:
            bool: True if alive, False if dead.
        """
        return self.current_hp > 0
