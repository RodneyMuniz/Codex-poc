# projects/tactics-game/artifacts/healer.py

class Healer:
    def __init__(
        self,
        name: str,
        max_hp: int,
        max_mana: int,
        spell_power: int,
    ):
        if not name or max_hp <= 0 or max_mana < 0 or spell_power < 0:
            raise ValueError("Invalid initialization parameters for Healer.")
        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.max_mana = max_mana
        self.mana = max_mana
        self.spell_power = spell_power
        self.group_heal_cooldown = 0

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def take_damage(self, amount: int):
        if amount < 0:
            raise ValueError("Damage amount cannot be negative.")
        self.current_hp = max(self.current_hp - amount, 0)

    def heal(self, target, amount: int):
        if not self.is_alive():
            raise RuntimeError(f"{self.name} is not alive and cannot cast heal.")
        if amount <= 0:
            raise ValueError("Heal amount must be positive.")
        if not target.is_alive():
            raise ValueError("Cannot heal a dead unit.")
        if self.mana < amount:
            raise RuntimeError("Not enough mana to cast heal.")
        # Heal amount might be boosted by spell_power:
        heal_amount = amount + self.spell_power
        target.receive_healing(heal_amount)
        self.mana -= amount

    def cast_spell(self, spell_name: str, target=None, allies=None):
        """
        Cast a spell by name.

        Spells:
        - 'heal': single target heal, costs 10 mana, heals 20 HP + spell_power
        - 'group_heal': group heal, costs 25 mana, heals 10 HP + spell_power to all allies, cooldown 3 turns
        - 'cleanse': remove one negative status effect from target, costs 15 mana
        
        Args:
          spell_name (str): spell to cast
          target (optional): target unit for spells that require it
          allies (optional): list of ally units for group_heal
        
        Raises:
          RuntimeError on invalid spell use or insufficient mana or cooldowns.
        """
        if not self.is_alive():
            raise RuntimeError(f"{self.name} is not alive and cannot cast spells.")

        spell_name = spell_name.lower()

        if spell_name == "heal":
            mana_cost = 10
            heal_base = 20
            if target is None:
                raise ValueError("Heal requires a target.")
            if self.mana < mana_cost:
                raise RuntimeError("Not enough mana to cast Heal.")
            if not target.is_alive():
                raise RuntimeError("Cannot heal a dead target.")
            target.receive_healing(heal_base + self.spell_power)
            self.mana -= mana_cost

        elif spell_name == "group_heal":
            mana_cost = 25
            heal_base = 10
            if self.group_heal_cooldown > 0:
                raise RuntimeError(f"Group Heal is on cooldown for {self.group_heal_cooldown} more turn(s).")
            if allies is None or not isinstance(allies, list):
                raise ValueError("Group Heal requires a list of allies.")
            if self.mana < mana_cost:
                raise RuntimeError("Not enough mana to cast Group Heal.")
            any_healed = False
            for ally in allies:
                if ally.is_alive():
                    ally.receive_healing(heal_base + self.spell_power)
                    any_healed = True
            if not any_healed:
                raise RuntimeError("No alive allies to heal in Group Heal.")
            self.mana -= mana_cost
            self.group_heal_cooldown = 3

        elif spell_name == "cleanse":
            mana_cost = 15
            if target is None:
                raise ValueError("Cleanse requires a target.")
            if self.mana < mana_cost:
                raise RuntimeError("Not enough mana to cast Cleanse.")
            if not target.is_alive():
                raise RuntimeError("Cannot cleanse a dead target.")
            if not hasattr(target, "remove_one_negative_status"):
                raise RuntimeError("Target does not support cleansing.")
            removed = target.remove_one_negative_status()
            if not removed:
                # No negative status removed but mana still spent according to typical game logic?
                # Here we choose to raise error and not spend mana if no effect.
                raise RuntimeError("Target has no negative status to cleanse.")
            self.mana -= mana_cost

        else:
            raise ValueError(f"Spell '{spell_name}' is not recognized or cannot be cast by Healer.")

    def cooldown_tick(self):
        """Reduce cooldown counters by 1, call this once per turn."""
        if self.group_heal_cooldown > 0:
            self.group_heal_cooldown -= 1

# Example supportive interface for healed units must implement:
# - is_alive()
# - receive_healing(amount)
# - remove_one_negative_status() => returns bool if a negative status was removed
