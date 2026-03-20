# File: projects/tactics-game/artifacts/mage.py

class Mage:
    def __init__(self, name: str, max_hp: int, max_mana: int, spell_power: int):
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
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

    def take_damage(self, damage: int):
        if damage < 0:
            raise ValueError("Damage must be non-negative.")
        self.current_hp -= damage
        if self.current_hp < 0:
            self.current_hp = 0

    def heal(self, amount: int):
        if amount < 0:
            raise ValueError("Heal amount must be non-negative.")
        if not self.is_alive():
            return  # Cannot heal dead mage
        self.current_hp += amount
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp

    def cast_spell(self, mana_cost: int):
        if mana_cost <= 0:
            raise ValueError("Mana cost must be positive.")
        if mana_cost > self.mana:
            raise ValueError(f"Not enough mana to cast spell. Current mana: {self.mana}, required: {mana_cost}")
        self.mana -= mana_cost
        # The actual spell effect could be implemented separately,
        # returning spell power to be used for damage calculation or healing
        return self.spell_power

    def is_alive(self) -> bool:
        return self.current_hp > 0
