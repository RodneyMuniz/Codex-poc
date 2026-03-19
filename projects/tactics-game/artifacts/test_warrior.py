import pytest
from warrior import Warrior

@pytest.fixture
def healthy_warrior():
    return Warrior(name="Conan", max_hp=100, attack_power=15, current_hp=100)

@pytest.fixture
def wounded_warrior():
    return Warrior(name="Aragorn", max_hp=100, attack_power=10, current_hp=50)

@pytest.fixture
def defeated_warrior():
    w = Warrior(name="Fallen", max_hp=100, attack_power=10, current_hp=1)
    w.take_damage(1)  # Proper defeated state simulation
    return w

def test_initialization_valid():
    w = Warrior("TestWarrior", 120, 20)
    assert w.name == "TestWarrior"
    assert w.max_hp == 120
    assert w.attack_power == 20
    assert w.current_hp == w.max_hp

def test_initialization_invalid_params():
    with pytest.raises(ValueError):
        Warrior("Invalid", -10, 10)
    with pytest.raises(ValueError):
        Warrior("Invalid", 100, -5)


def test_attack_damage(healthy_warrior, wounded_warrior):
    assert wounded_warrior.current_hp == 50
    wounded_warrior.take_damage(20)
    assert wounded_warrior.current_hp == 30


def test_attack_defeated_warrior_cannot_attack(defeated_warrior, healthy_warrior):
    assert not defeated_warrior.is_alive
    with pytest.raises(Exception):
        defeated_warrior.attack(healthy_warrior)


def test_healing_cap(wounded_warrior):
    wounded_warrior.heal(1000)
    assert wounded_warrior.current_hp == wounded_warrior.max_hp


def test_healing_normal(wounded_warrior):
    wounded_warrior.heal(20)
    assert wounded_warrior.current_hp > 50


def test_defeated_behavior():
    w = Warrior("Temp", 100, 10)
    assert w.is_alive
    w.take_damage(w.max_hp)
    assert not w.is_alive
    with pytest.raises(Exception):
        w.attack(w)
    with pytest.raises(ValueError):
        w.heal(10)
    assert w.current_hp == 0  # Healing defeated warrior leaves health at zero
