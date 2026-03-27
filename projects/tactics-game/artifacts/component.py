class Component:
    def __init__(self, id_, name, max_health, max_mana, spell_power):
        if max_health <= 0:
            raise ValueError("max_health must be positive")
        if max_mana < 0:
            raise ValueError("max_mana cannot be negative")
        if spell_power < 0:
            raise ValueError("spell_power cannot be negative")

        self.id = id_
        self.name = name
        self.max_health = max_health
        self.health = max_health
        self.max_mana = max_mana
        self.mana = max_mana
        self.spell_power = spell_power

    def take_damage(self, amount):
        if amount < 0:
            raise ValueError("Damage amount cannot be negative")
        self.health = max(self.health - amount, 0)

    def heal(self, amount):
        if amount < 0:
            raise ValueError("Heal amount cannot be negative")
        self.health = min(self.health + amount, self.max_health)

    def cast_spell(self, mana_cost):
        if mana_cost < 0:
            raise ValueError("Mana cost cannot be negative")
        if mana_cost > self.mana:
            raise ValueError(f"Insufficient mana to cast spell: required {mana_cost}, available {self.mana}")
        self.mana -= mana_cost
        # Spell effect calculation could be expanded here
        return self.spell_power

    def is_alive(self):
        return self.health > 0
