class Evidence:
    def __init__(self, health, mana, spell_power):
        if not (isinstance(health, int) and health > 0):
            raise ValueError('Health must be a positive integer')
        if not (isinstance(mana, int) and mana >= 0):
            raise ValueError('Mana must be a non-negative integer')
        if not (isinstance(spell_power, (int, float)) and spell_power >= 0):
            raise ValueError('Spell power must be a non-negative number')

        self.max_health = health
        self.health = health
        self.mana = mana
        self.spell_power = spell_power

        # Define available spells with their mana cost and effect descriptions
        self.spells = {
            'scan_area': {'mana_cost': 10, 'description': 'Reveals enemy units and traps within detection radius.'},
            'mark_target': {'mana_cost': 15, 'description': 'Applies a debuff increasing damage taken by target.'},
            'deploy_sensor': {'mana_cost': 20, 'description': 'Places a sensor device extending detection.'},
            'intercept_communication': {'mana_cost': 25, 'description': 'Disrupts enemy coordination reducing their efficiency.'}
        }

    def take_damage(self, amount):
        if amount < 0:
            raise ValueError('Damage amount must be non-negative')
        self.health = max(self.health - amount, 0)

    def heal(self, amount):
        if amount < 0:
            raise ValueError('Heal amount must be non-negative')
        self.health = min(self.health + amount, self.max_health)

    def cast_spell(self, spell_name):
        if spell_name not in self.spells:
            raise ValueError(f"Invalid spell: {spell_name}")
        spell = self.spells[spell_name]
        if self.mana < spell['mana_cost']:
            raise ValueError(f"Not enough mana to cast {spell_name}")
        self.mana -= spell['mana_cost']
        # Here would be the logic to apply the spell effect in the game
        return f"Cast {spell_name}: {spell['description']}"

    def is_alive(self):
        return self.health > 0

# Example usage (commented out):
# evidence_unit = Evidence(health=100, mana=50, spell_power=30)
# evidence_unit.take_damage(20)
# evidence_unit.heal(10)
# print(evidence_unit.cast_spell('scan_area'))
# print(evidence_unit.is_alive())
