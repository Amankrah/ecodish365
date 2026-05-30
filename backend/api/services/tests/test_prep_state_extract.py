"""Unit tests for prep_state_extract (Phase 1.5 / 1.6 regex tagger)."""
from __future__ import annotations

import pytest

from api.services.prep_state_extract import (
    extract_prep_state,
    preservation_states_equivalent,
    thermal_states_equivalent,
)


@pytest.mark.parametrize(
    ('description', 'thermal', 'preservation'),
    [
        # Phase 1.5 baselines
        ('Pork, loin, whole, lean and fat, braised', 'braised', 'fresh'),
        ('Grains, wheat germ, toasted, plain', 'toasted', 'fresh'),
        ('Beans, mung, mature seeds, sprouted, stir-fried, no fat added', 'stir_fried', 'fresh'),
        ('Chicken, broiler, breast, skinless, boneless, meat, raw', 'raw', 'fresh'),
        ('Cassava, fermented, paste', 'unknown', 'fermented'),
        # Phase 1.6 — French plural participles
        ('Porc, longe, entiere, sauti', 'sauteed', 'fresh'),
        ('Amarante, feuilles, bouillies, egouttees', 'boiled', 'fresh'),
        ('Porc, poumons, braisés', 'braised', 'fresh'),
        ('Poulet à griller, viande brune et peau, rôties', 'roasted', 'fresh'),
        ('Crustaces, a vapeur ou bouillies', 'steamed', 'fresh'),
        # Phase 1.6 — preservation / product form
        ('Cereal, ready to eat, granola, homemade', 'unknown', 'ready_to_eat'),
        ('Céréale, prête-à-manger, granola', 'unknown', 'ready_to_eat'),
        ('Milk, dry, skim, powder, instant', 'unknown', 'dried'),
        ('Lait, poudre, ecreme', 'unknown', 'dried'),
        ('Milk, canned, evaporated, with added vitamin A', 'unknown', 'condensed'),
        ('Yogurt, plain, whole milk', 'unknown', 'fermented'),
        ('Yogourt, nature, lait entier', 'unknown', 'fermented'),
        ('Biscuit, plain/buttermilk, refrigerated dough, lower fat', 'unknown', 'fresh'),
        # Phase 1.6 — frozen produce defaults to raw
        ('Blueberry, frozen, unsweetened', 'raw', 'frozen'),
        ('Frozen entree, beef pot roast with potatoes and vegetables, heated', 'heated', 'frozen'),
        # False-positive guards
        ('Cereal, ready-to-eat, Cinnamon Toast Crunch, General Mills', 'unknown', 'ready_to_eat'),
        ('Cheese, cottage, uncreamed, dry curd (0.4% M.F.)', 'unknown', 'unknown'),
        ('Riz, farine, blanche', 'unknown', 'unknown'),
    ],
)
def test_extract_prep_state_cases(description, thermal, preservation):
    ps = extract_prep_state(description)
    assert ps.thermal_state == thermal, description
    assert ps.preservation_state == preservation, description


def test_broiled_not_broiler():
    ps = extract_prep_state('Pork, loin, whole, lean and fat, broiled')
    assert ps.thermal_state == 'broiled'


def test_cooked_class_equivalence_includes_braised():
    assert thermal_states_equivalent('braised', 'cooked')
    assert thermal_states_equivalent('toasted', 'roasted')


def test_preservation_exact_match_only():
    assert preservation_states_equivalent('dried', 'dried')
    assert preservation_states_equivalent('ready_to_eat', 'dried') is False
    assert preservation_states_equivalent('ready_to_eat', 'unknown')
