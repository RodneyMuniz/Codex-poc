"""
Module defining the Warrior class for the tactics game.
Provides Warrior character with encapsulated health and combat mechanics.
"""


class Warrior:
    """A warrior character with health points and attack capabilities."""

    def __init__(self, name: str, max_hp: int, attack_power: int, current_hp: int = None):
        """
        Initialize a Warrior instance.

        Args:
            name (str): The warrior's name; must be non-empty.
            max_hp (int): Maximum hit points; must be positive integer.
            attack_power (int): Attack power; must be positive integer.
            current_hp (int, optional): Current hit points; defaults to max_hp. Must be positive and <= max_hp if provided.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Name must be a non-empty string.")
        if not isinstance(max_hp, int) or max_hp <= 0:
            raise ValueError("max_hp must be a positive integer.")
        if not isinstance(attack_power, int) or attack_power <= 0:
            raise ValueError("attack_power must be a positive integer.")
        if current_hp is None:
            current_hp = max_hp
        else:
            if not isinstance(current_hp, int) or not (0 < current_hp <= max_hp):
                raise ValueError("current_hp must be a positive integer no greater than max_hp.")

        self._name = name
        self._max_hp = max_hp
        self._attack_power = attack_power
        self._current_hp = current_hp

    @property
    def name(self) -> str:
        """The warrior's name (read-only)."""
        return self._name

    @property
    def max_hp(self) -> int:
        """Maximum hit points (read-only)."""
        return self._max_hp

    @property
    def attack_power(self) -> int:
        """Attack power value (read-only)."""
        return self._attack_power

    @property
    def current_hp(self) -> int:
        """Current hit points (read-only)."""
        return self._current_hp

    @property
    def is_alive(self) -> bool:
        """Whether the warrior is alive (current_hp > 0)."""
        return self._current_hp > 0

    def take_damage(self, amount: int) -> None:
        """
        Apply damage to the warrior, reducing current_hp.

        Args:
            amount (int): Damage amount, must be positive integer.

        Raises:
            ValueError: If amount is invalid or warrior is already dead.
        """
        if not self.is_alive:
            raise ValueError("Cannot damage a dead warrior.")
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("Damage amount must be a positive integer.")

        self._current_hp = max(self._current_hp - amount, 0)

    def heal(self, amount: int) -> None:
        """
        Heal the warrior by the specified amount, not exceeding max_hp.

        Args:
            amount (int): Healing amount, must be positive integer.

        Raises:
            ValueError: If amount is invalid or warrior is dead.
        """
        if not self.is_alive:
            raise ValueError("Cannot heal a dead warrior.")
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("Heal amount must be a positive integer.")

        self._current_hp = min(self._current_hp + amount, self._max_hp)

    def attack(self, target: "Warrior") -> None:
        """
        Attack another warrior, causing them to take damage equal to this warrior's attack power.

        Args:
            target (Warrior): Another warrior instance to attack.

        Raises:
            ValueError: If self is dead, target is invalid, or target is dead.
        """
        if not self.is_alive:
            raise ValueError("Dead warriors cannot attack.")
        if not isinstance(target, Warrior):
            raise ValueError("Target must be a Warrior instance.")
        if not target.is_alive:
            raise ValueError("Cannot attack a dead warrior.")

        target.take_damage(self._attack_power)

