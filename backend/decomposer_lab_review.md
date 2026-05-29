# Decomposer compound-meal lab — review

- Lab JSON: `decomposer_lab_f16d78d_20260529T104312Z.json`
- Scenarios: 20  |  pass: 14  review: 4  flagged: 2
- compound-gate correct: 20/20  |  must_keep all survived: 18/20  |  collapsed-onto-single: 0

## FLAGGED (2)

### beef puddy with a glass of orange juice  — `flagged`
- reasons: ['must_keep_dropped:beef patty/pie', 'unmatched:too_few_ingredients:1<2', 'energy_density_out_of_band:11.2_not_in_[80, 230]', 'behavior:failed_expected_decompose']
- behavior=`failed` (expected `decompose`) matched=`False` fallback=`too_few_ingredients:1<2` conf=0.75
- energy=11.2 kcal/100g (band [80, 230]) in_band=False
- kept=['orange juice'] dropped=['beef patty/pie'] dish_as_ingredient=0
- ingredients: Orange juice, raw(100.0g,single)
- note: The headline regression case: catalog preference must NOT collapse this onto one food and drop the juice.

### fish and chips  — `flagged`
- reasons: ['must_keep_dropped:chips/fries', 'behavior:catalog_override_expected_decompose']
- behavior=`catalog_override` (expected `decompose`) matched=`True` fallback=`catalog_override:kcal_err=0.439` conf=0.8
- energy=197.0 kcal/100g (band [170, 330]) in_band=True
- kept=['fish'] dropped=['chips/fries'] dish_as_ingredient=0
- ingredients: Fish, battered and fried(300.0g,mixed)
- note: Single dish using 'and' as a recipe descriptor — not compound.

## REVIEW (4)

### chicken caesar salad  — `review`
- reasons: ['behavior:catalog_override_expected_decompose']
- behavior=`catalog_override` (expected `decompose`) matched=`True` fallback=`catalog_override:kcal_err=0.257` conf=0.85
- energy=151.0 kcal/100g (band [110, 260]) in_band=True
- kept=['chicken', 'lettuce'] dropped=[] dish_as_ingredient=0
- ingredients: Salad, Caesar with chicken, homemade(250.0g,mixed)

### beef stew  — `review`
- reasons: ['behavior:catalog_override_expected_decompose']
- behavior=`catalog_override` (expected `decompose`) matched=`True` fallback=`catalog_override:kcal_err=1.197` conf=0.85
- energy=64.0 kcal/100g (band [60, 170]) in_band=True
- kept=['beef', 'vegetable'] dropped=[] dish_as_ingredient=0
- ingredients: Beef stew with potatoes and vegetables(300.0g,mixed)
- note: Key new-gate case: must NOT be collapsed onto a SINGLE ingredient (e.g. 'Beef, ground'). Should decompose, or at worst override onto a measured beef-STEW (mixed) food.

### vegetable stir fry with rice  — `review`
- reasons: ['behavior:catalog_override_expected_decompose']
- behavior=`catalog_override` (expected `decompose`) matched=`True` fallback=`catalog_override:kcal_err=0.047` conf=0.75
- energy=117.9 kcal/100g (band [90, 200]) in_band=True
- kept=['vegetable', 'rice'] dropped=[] dish_as_ingredient=0
- ingredients: Frozen entree, Asian dish, vegetables fried rice, heated(350.0g,mixed)

### pepperoni pizza  — `review`
- reasons: ['behavior:catalog_override_expected_catalog_short_circuit']
- behavior=`catalog_override` (expected `catalog_short_circuit`) matched=`True` fallback=`catalog_override:decomp_failed:unresolved_mass_too_large:105.0 (> 10% of 200.0)` conf=0.85
- energy=259.0 kcal/100g (band [220, 330]) in_band=True
- kept=['pizza'] dropped=[] dish_as_ingredient=0
- ingredients: Pizza, cheese and pepperoni, thick crust, whole grain, frozen, cooked(200.0g,mixed)
- note: A measured mixed dish in CNF — expect a confident catalog name match (short-circuit) or override onto the measured pizza.

