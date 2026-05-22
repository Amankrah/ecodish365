# Decomposer-agreement analysis

- Benchmark JSON: `matcher_benchmark_e416d7d_20260522T192528Z.json`
- Git rev: `e416d7d`
- Sample size: 184
- Tier γ attempts: 60
- Matcher-agreement confidence floor (Hypothesis B): 0.75

## Classification

| Cat | Count | Description |
|:---:|:---:|:---|
| A | 15 | resolved, n_ing≥2, agreement (decomposer confirmed matcher's primary choice) |
| B | 32 | resolved, n_ing≥2, no agreement (decomposer disagreed with matcher) |
| C | 0 | resolved, n_ing=1, agreement (impossible under current gate) |
| D | 2 | REJECTED min_ingredients, AGREEMENT — FALSE REJECTIONS (Hypothesis B would convert) |
| E | 0 | REJECTED min_ingredients, no agreement (genuinely lazy 1-ingredient decomp) |
| F | 11 | REJECTED mass_too_large (genuine no-clean-decomposition) |
| G | 0 | REJECTED other (low_confidence / hallucinated / etc.) |

### Category A — resolved, n_ing≥2, agreement (decomposer confirmed matcher's primary choice)

**Count: 15**

Per CNF FoodGroup:
- Baked Products: 4
- Sausages and Luncheon meats: 3
- Fast Foods: 2
- Snacks: 2
- Babyfoods: 2
- Soups, Sauces and Gravies: 1
- Sweets: 1

Examples:
- `food_id=501536` [Fast Foods] matcher conf=0.8 → `[25502] Chicken burger , fast foods restaurant` ; decomp n=2 first=`[25502]` resolved=True fallback=-
    - CNF: Fast foods, sandwiches and burgers, crispy chicken fillet sandwich, with lettuce tomato and mayonnaise
- `food_id=5615` [Snacks] matcher conf=0.8 → `[38105] Corn chips or tortilla chips` ; decomp n=2 first=`[38105]` resolved=True fallback=-
    - CNF: Snacks, tortilla chips, light (baked with less oil)
- `food_id=5363` [Soups, Sauces and Gravies] matcher conf=0.8 → `[25947] Broth, stock or bouillon, poultry, recon` ; decomp n=2 first=`[25947]` resolved=True fallback=-
    - CNF: Soup, broth, chicken, ready-to-serve, no salt added
- `food_id=3792` [Baked Products] matcher conf=0.8 → `[23594] Soft cake, plain, sponge cake type` ; decomp n=3 first=`[23594]` resolved=True fallback=-
    - CNF: Cake, white, homemade, without icing (frosting)
- `food_id=4335` [Sweets] matcher conf=0.8 → `[31003] Candies, all types` ; decomp n=4 first=`[31003]` resolved=True fallback=-
    - CNF: Candies, Skittles

### Category B — resolved, n_ing≥2, no agreement (decomposer disagreed with matcher)

**Count: 32**

Per CNF FoodGroup:
- Snacks: 6
- Sweets: 5
- Mixed Dishes: 5
- Soups, Sauces and Gravies: 4
- Babyfoods: 4
- Sausages and Luncheon meats: 3
- Baked Products: 3
- Fast Foods: 2

Examples:
- `food_id=4280` [Sweets] matcher conf=0.4 → `[31040] Dulce de leche or confiture de lait` ; decomp n=2 first=`[39247]` resolved=True fallback=-
    - CNF: Dessert, flan, caramel custard, dry mix, prepared with whole milk
- `food_id=502495` [Mixed Dishes] matcher conf=0.6 → `[25568] Pastilla, filled with chicken (pie)` ; decomp n=3 first=`[7813]` resolved=True fallback=-
    - CNF: Taquito, chicken and cheese, frozen, heated in oven
- `food_id=4086` [Snacks] matcher conf=0.4 → `[30300] Dry sausage` ; decomp n=3 first=`[30300]` resolved=True fallback=-
    - CNF: Snacks, beef jerky, chopped and formed
- `food_id=5501` [Snacks] matcher conf=0.8 → `[9231] Pop-corn or air-popped maize, unsalted` ; decomp n=2 first=`[9230]` resolved=True fallback=-
    - CNF: Snacks, popcorn, oil-popped, unsalted
- `food_id=4389` [Snacks] matcher conf=0.6 → `[7330] Rusk, multigrain` ; decomp n=2 first=`[7330]` resolved=True fallback=-
    - CNF: Snacks, rice cakes, brown rice, multigrain, unsalted

### Category D — REJECTED min_ingredients, AGREEMENT — FALSE REJECTIONS (Hypothesis B would convert)

**Count: 2**

Per CNF FoodGroup:
- Fast Foods: 1
- Sausages and Luncheon meats: 1

Examples:
- `food_id=4652` [Fast Foods] matcher conf=0.8 → `[25431] Sandwich made with French bread, tuna, r` ; decomp n=1 first=`[25431]` resolved=False fallback=too_few_ingredients:1<2
    - CNF: Fast foods, sandwiches and burgers, submarine sandwich on white bread, with tuna salad, lettuce and tomatoes
- `food_id=5691` [Sausages and Luncheon meats] matcher conf=0.8 → `[28963] Chicken cooked ham, in slices` ; decomp n=1 first=`[28963]` resolved=False fallback=too_few_ingredients:1<2
    - CNF: Deli-meat, chicken breast, oven-roasted, fat free, sliced

### Category F — REJECTED mass_too_large (genuine no-clean-decomposition)

**Count: 11**

Per CNF FoodGroup:
- Sweets: 2
- Fast Foods: 2
- Babyfoods: 2
- Soups, Sauces and Gravies: 2
- Mixed Dishes: 2
- Baked Products: 1

Examples:
- `food_id=4259` [Sweets] matcher conf=0.4 → `[31044] Sugar, vanilla flavoured` ; decomp n=3 first=`[19021]` resolved=False fallback=unresolved_mass_too_large:47.0g (> 10% of 100.0)
    - CNF: Dessert, pudding, vanilla, dry mix, regular, unprepared
- `food_id=501641` [Fast Foods] matcher conf=0.6 → `[25542] Toasted ham sandwich topped with grated ` ; decomp n=4 first=`[22502]` resolved=False fallback=unresolved_mass_too_large:20.0g (> 10% of 100.0)
    - CNF: Fast foods, egg, cheese and sausage griddlecake sandwich
- `food_id=503337` [Babyfoods] matcher conf=0.8 → `[13162] Dairy cereal-based beverage with fruits ` ; decomp n=2 first=`[13162]` resolved=False fallback=unresolved_mass_too_large:20.0g (> 10% of 100.0)
    - CNF: Babyfood, cereal, mixed grain, with milk powder and fruit, prepared with water
- `food_id=4286` [Sweets] matcher conf=0.4 → `[31016] Sugar, white` ; decomp n=4 first=`[31016]` resolved=False fallback=unresolved_mass_too_large:19.0g (> 10% of 100.0)
    - CNF: Icing (frosting), white, fluffy, dry mix, prepared with water
- `food_id=502852` [Babyfoods] matcher conf=0.8 → `[42606] Vegetable dish for baby, w meat/fish and` ; decomp n=5 first=`[6230]` resolved=False fallback=unresolved_mass_too_large:20.0g (> 10% of 100.0)
    - CNF: Babyfood, dinner, jarred or frozen, beef with vegetables, all stages

## Decision rule (Hypothesis B)

**Verdict**: PROCEED — Hypothesis B is clearly correct.

- Category D (false rejections that Hypothesis B would convert): **2**
- Category E (genuine 1-ingredient rejections; B would correctly leave alone): 0
- Category F (genuine mass-balance rejections; B does not affect): 11
- Category G (other rejections): 0

**Expected resolve-rate climb after shipping Hypothesis B**:
- Before: 47/60 = 78%
- After:  49/60 = 82%
