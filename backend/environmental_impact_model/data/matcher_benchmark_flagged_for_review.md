# Matcher benchmark — flagged-for-review rows

- Benchmark JSON: `matcher_benchmark_16a5ca7_20260522T161706Z.json`
- Git rev: `16a5ca7`
- Sample size: 184; flagged: 68 (37.0%)

Reviewer: for each row below, add `reviewer_verdict: "good" | "stretched" | "fallback"` and `reviewer_notes: "..."` to the per_food row in the JSON.

### food_id=3310 — Peanut flour, defatted, salted

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `15202`  → "Peanut butter or peanut paste"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Peanut butter shares similar processing and composition with defatted salted peanut flour, both derived from peanuts."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.40599999999999997  cnf_default=0.054  ratio=7.52x

### food_id=3077 — Fish, tilefish, raw

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `26018`  → "Anglerfish, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Anglerfish and tilefish are both finfish, sharing similar raw processing and marine provenance."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=1.2  cnf_default=1.08  ratio=1.11x

### food_id=5290 — Tea, instant, unsweetened, powder, decaffeinated

- CNF group: `Beverages`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `18020`  → "Tea, brewed, without sugar"
- Matched Agribalyse group: `boissons`
- Justification: "Brewed tea is closely related to instant tea; both are derived from tea leaves, differing mainly in processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3094 — Crustaceans, crab, alaska king, boiled or steamed

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `10025`  → "Crab, boiled/cooked in water"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both entries are boiled crab, closely matching in processing and species."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=3.3  cnf_default=1.08  ratio=3.06x

### food_id=4280 — Dessert, flan, caramel custard, dry mix, prepared with whole milk

- CNF group: `Sweets`
- Matched: `True`  confidence: 0.70
- Matched ciqual: `31040`  → "Dulce de leche or confiture de lait"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Flan and dulce de leche share similar creamy, sweet profiles and milk-based ingredients, making them closely related desserts."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5644 — Emu, full rump, cooked, broiled

- CNF group: `Poultry Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `36203`  → "Duck, leg, meat and skin, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Duck leg shares similar processing and meat characteristics with cooked emu, both being poultry products."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.46799999999999997  cnf_default=1.254  ratio=0.37x

### food_id=4086 — Snacks, beef jerky, chopped and formed

- CNF group: `Snacks`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `30300`  → "Dry sausage"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Beef jerky is closely related to dry sausage, sharing similar processing and meat composition."
- Quality checks: group=True  magnitude=True  token=False

### food_id=502426 — Cereal, ready-to-eat, Krave, Kellogg's

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `32009`  → "Breakfast cereals, chocolate wheat grain flakes, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Both are chocolate-flavored breakfast cereals, with similar processing and fortification characteristics."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4286 — Icing (frosting), white, fluffy, dry mix, prepared with water

- CNF group: `Sweets`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `31044`  → "Sugar, vanilla flavoured"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Vanilla-flavored sugar aligns closely with the sweet, dry mix composition of icing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5694 — Deli-meat, Bologna (baloney), reduced fat

- CNF group: `Sausages and Luncheon meats`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `30789`  → "Mortadella"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Mortadella is similar in composition and processing to reduced fat bologna, both being processed meats with similar fat content."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5546 — Vegetarian meat loaf or patty, meatless

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `25591`  → "Plant-based patty or steak from lentil, soybean and vegetables"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Both are plant-based patties, with the CNF entry likely containing legumes, aligning closely with lentils and vegetables in candidate."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.16799999999999998  cnf_default=0.054  ratio=3.11x

### food_id=502852 — Babyfood, dinner, jarred or frozen, beef with vegetables, all stages

- CNF group: `Babyfoods`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `42606`  → "Vegetable dish for baby, w meat/fish and starch, from 18 months"
- Matched Agribalyse group: `aliments infantiles`
- Justification: "Both entries are baby foods with meat and vegetables, suitable for similar age stages, aligning in composition and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=1711 — Fig, raw

- CNF group: `Fruits and fruit juices`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `13012`  → "Fig, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Fig, raw is the exact match in both composition and state, ensuring high confidence."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0611  cnf_default=0.08  ratio=0.76x

### food_id=2539 — Nuts, almonds, toasted, unblanched

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `15000`  → "Almond, (with peel)"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Toasted unblanched almonds closely match the unpeeled almond entry, considering processing and composition."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.263  cnf_default=0.06  ratio=4.38x

### food_id=627 — Chicken, broiler, wing, meat and skin, batter dipped, fried

- CNF group: `Poultry Products`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `36027`  → "Chicken, nugget, breaded croquette"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both are fried chicken products; the nugget shares similar processing and composition with batter-dipped wings."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.387  cnf_default=1.254  ratio=0.31x

### food_id=1822 — Pork, shoulder, picnic (arm), lean, roasted

- CNF group: `Pork Products`
- Matched: `False`  confidence: 0.00
- Matched ciqual: `None`  → ""
- Matched Agribalyse group: ``
- Justification: "LLM proposed '28910' not in candidate set"
- Quality checks: group=False  magnitude=False  token=False

### food_id=5609 — Beans, baked, canned, no salt added

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `20063`  → "Butter bean or yellow bean, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Butter beans are similar in processing and form to baked canned beans, making this the closest match."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.141  cnf_default=0.054  ratio=2.61x

### food_id=502204 — Yogourt, plain, fresh cheese-type (quark), fat free,  no salt added

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `19594`  → "Yogurt, fermented milk or dairy specialty, plain, fat free"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Both are fat-free plain yogurts, closely matching in composition and processing as fermented dairy products."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.189  cnf_default=1.0782265372168285  ratio=0.18x

### food_id=502164 — Yogourt, fruit flavoured, low fat (0.5-1.9% M.F.)

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `19581`  → "Yogurt, fermented milk or dairy specialty, with fruits, with sweetener, fat free"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Closest match with similar fruit flavoring and low fat content, aligning with the CNF entry."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.189  cnf_default=1.0782265372168285  ratio=0.18x

### food_id=501810 — Yambean (jimaca), tuber, boiled, drained, with salt

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `53503`  → "Yam or Indian potato, peeled, boiled/cooked in water"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Both are tubers, boiled, and share similar processing; yambean and yam have comparable textures and culinary uses."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0806  cnf_default=0.1  ratio=0.81x

### food_id=6285 — Beef, composite cuts, stewing beef, 0mm (0") trim, raw

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `6231`  → "Beef, stewing meat, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Closest match as it specifically refers to stewing meat, aligning with the CNF entry for stewing beef."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=2.8899999999999997  cnf_default=10.0  ratio=0.29x

### food_id=5647 — Emu, outside drum, raw

- CNF group: `Poultry Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `36022`  → "Chicken, drumstick, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both are poultry products; chicken drumsticks are similar in composition and processing to raw emu meat."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.5780000000000001  cnf_default=1.254  ratio=0.46x

### food_id=5894 — Fish, pike, northern, native, liver

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `26237`  → "Atlantic herring, lean, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both are fish products; pike liver is fatty like herring, and both are raw, aligning in processing and nutritional profile."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.268  cnf_default=1.08  ratio=0.25x

### food_id=502059 — Cereal, ready to eat, Hemp Plus Granola, Nature's Path

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `32123`  → "Breakfast cereals, wheat flakes with walnuts, hazelnuts or almonds, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Hemp Plus Granola contains nuts and is fortified, similar to wheat flakes with nuts, aligning in composition and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2561 — Nuts, coconut meat, desiccated, sweetened, flaked, canned

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `15007`  → "Coconut, kernel, dried"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Desiccated coconut meat aligns closely with dried coconut kernel; both are processed coconut products."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.242  cnf_default=0.06  ratio=4.03x

### food_id=3251 — Beans, baked, canned, with pork and sweet sauce

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `25098`  → "White bean stew, with pork, canned"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Both entries contain beans and pork in a canned format, closely matching composition and processing."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.213  cnf_default=0.054  ratio=3.94x

### food_id=5515 — Salad dressing, caesar dressing, regular

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `16614`  → "Vegetable fat (like margarine), 80% fat, salted"
- Matched Agribalyse group: `matières grasses`
- Justification: "Caesar dressing typically contains vegetable fats, similar to margarine, making this a close match in composition."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2579 — Nuts, mixed nuts, oil roasted without peanuts

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `15049`  → "Mix of unsalted grains/nuts and raisins"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Mixed nuts align with the unsalted grain/nut mix, reflecting similar processing and composition without peanuts."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.262  cnf_default=0.06  ratio=4.37x

### food_id=5698 — Deli-meat, macaroni and cheese loaf, chicken/pork/beef

- CNF group: `Sausages and Luncheon meats`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `30130`  → "Poultry sausage, delicatessen style"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Poultry sausage aligns closely with deli-meat composition and processing, fitting the luncheon meat category."
- Quality checks: group=True  magnitude=True  token=False

### food_id=501535 — Grains, teff, cooked

- CNF group: `Cereals, Grains and Pasta`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `9320`  → "Barley, whole, raw"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Barley is a grain like teff, both are cooked cereals, making it a closer match than other candidates."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.0586  cnf_default=0.18  ratio=0.33x

### food_id=502338 — Yogourt, goat, plain

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `19556`  → "Yogurt, goat's milk, plain, around 5% fat"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Closest match in terms of milk source (goat) and plain yogurt type."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.20400000000000001  cnf_default=1.0782265372168285  ratio=0.19x

### food_id=5544 — Meatless, sandwich spread

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `1027`  → "Plant-based spread-cheese type, with soybean, prepacked"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Both are plant-based spreads; the soybean content aligns well with the meatless sandwich spread."
- Quality checks: group=False  magnitude=False  token=True
- GW per 100g: matched=0.187  cnf_default=0.054  ratio=3.46x

### food_id=4758 — Beef, hip, rump roast, lean and fat, 3mm (1/8") trim, broiled

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `6206`  → "Beef, rump steak, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Beef rump steak is closely related in cut and cooking method, matching the broiled preparation of the CNF entry."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=2.8899999999999997  cnf_default=10.0  ratio=0.29x

### food_id=502262 — Chickpeas (garbanzo beans, bengal gram), canned, drained, rinsed

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.90
- Matched ciqual: `20532`  → "Chick pea, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Canned chickpeas match composition and processing closely, making it the best candidate."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.22000000000000003  cnf_default=0.054  ratio=4.07x

### food_id=4588 — Fast foods, mexican, burrito with beans and cheese

- CNF group: `Fast Foods`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `25459`  → "Burritos"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Burritos closely match the composition of beans and cheese, aligning with the CNF entry for fast food."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4467 — Grains, hominy, canned, yellow

- CNF group: `Cereals, Grains and Pasta`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `20066`  → "Sweet corn, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Canned hominy is closely related to canned sweet corn, both being processed corn products."
- Quality checks: group=False  magnitude=True  token=False
- GW per 100g: matched=0.13899999999999998  cnf_default=0.18  ratio=0.77x

### food_id=4058 — Pie, pumpkin, commercial

- CNF group: `Baked Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `20043`  → "Pumpkin, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Canned pumpkin is a common ingredient in commercial pumpkin pie, closely matching the composition and processing of the CNF entry."
- Quality checks: group=False  magnitude=True  token=True

### food_id=2519 — Seeds, safflower seed meal, partially defatted

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15011`  → "Sunflower seed"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Safflower seed meal and sunflower seed share similar processing routes and nutritional profiles as oilseed meals."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.29100000000000004  cnf_default=0.06  ratio=4.85x

### food_id=1577 — Groundcherry, raw

- CNF group: `Fruits and fruit juices`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `20172`  → "Tomato, cherry, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Groundcherries and cherry tomatoes share similar fruit characteristics and processing routes, making tomato, cherry, raw the closest match."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0626  cnf_default=0.08  ratio=0.78x

### food_id=3790 — Cake, white, regular, dry mix, unprepared

- CNF group: `Baked Products`
- Matched: `True`  confidence: 0.70
- Matched ciqual: `9440`  → "Wheat flour, type 55 (for pastry)"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Wheat flour is a primary ingredient in dry cake mixes, making it the closest match in terms of composition."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2577 — Nuts, mixed nuts, dry roasted with peanuts

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `15002`  → "Peanut, grilled, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Grilled and salted peanuts align closely with dry roasted mixed nuts, sharing similar processing and ingredient characteristics."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.418  cnf_default=0.06  ratio=6.97x

### food_id=2201 — Sauerkraut, canned, solids and liquid

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `25220`  → "Sauerkraut, without garnish, drained, cooked"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Canned sauerkraut without garnish closely matches the composition and processing of canned sauerkraut, aligning with the CNF entry."
- Quality checks: group=False  magnitude=True  token=True
- GW per 100g: matched=0.141  cnf_default=0.1  ratio=1.41x

### food_id=4291 — Dessert, frozen, ice pop

- CNF group: `Sweets`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `31060`  → "Jelly candy"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Jelly candy shares similar texture and processing as frozen ice pops, both being sweet, chewy, and often fruit-flavored."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2022 — Beet greens, boiled, drained

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.70
- Matched ciqual: `20005`  → "Swiss chard, cooked"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Swiss chard is closely related to beet greens and shares similar cooking methods and nutrient profiles."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.145  cnf_default=0.1  ratio=1.45x

### food_id=172 — Spices, bay leaf

- CNF group: `Spices and Herbs`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `11053`  → "Bay, leaves"
- Matched Agribalyse group: `aides culinaires et ingrédients divers`
- Justification: "Bay leaves are the same as the CNF entry, matching in composition and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3269 — Beans, pinto, raw

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `20525`  → "Red kidney bean, dried"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Dried red kidney beans are similar in composition and processing to raw pinto beans, both being legumes."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0858  cnf_default=0.054  ratio=1.59x

### food_id=1847 — Pork, lungs, braised

- CNF group: `Pork Products`
- Matched: `True`  confidence: 0.70
- Matched ciqual: `40004`  → "Brain, pork, braised"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both entries involve braised pork organ meats, aligning closely in processing and type."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.391  cnf_default=1.52  ratio=0.26x

### food_id=5139 — Cereal, ready to eat, Selects, Cranberry Almond Crunch, Post

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `32123`  → "Breakfast cereals, wheat flakes with walnuts, hazelnuts or almonds, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Cranberry Almond Crunch is a fortified breakfast cereal with similar ingredients and processing to wheat flakes with almonds."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2552 — Nuts, Chinese chestnuts, roasted

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `15021`  → "Chestnut, grilled"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Roasted Chinese chestnuts closely match grilled chestnuts in processing and composition."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.19  cnf_default=0.06  ratio=3.17x

### food_id=6212 — Pork, cured, ham, shank, bone-in, separable lean and fat, heated, roasted

- CNF group: `Pork Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `28913`  → "Cooked ham, choice, rind less and fatless"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Cooked ham, choice, rind less and fatless closely matches the processed nature and composition of roasted ham shank."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.765  cnf_default=1.52  ratio=0.50x

### food_id=544 — Shortening, industrial, for baking (cake), soybean

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `17420`  → "Soy oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Soy oil closely matches the composition and processing of industrial soybean shortening used in baking."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3203 — Fish, sardine, Atlantic, canned in oil, drained solids with bone

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `26034`  → "European pilchard or sardine, in oil, canned, drained (packaging fixed)"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both entries are canned sardines in oil, closely matching processing and composition, with similar provenance."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.268  cnf_default=1.08  ratio=0.25x

### food_id=502439 — Nuts, walnuts, glazed

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `15005`  → "Walnut, dried, husked"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Walnuts are the primary ingredient; dried and husked form closely matches glazed walnuts in processing."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.41100000000000003  cnf_default=0.06  ratio=6.85x

### food_id=2636 — Nuts, pecans, oil roasted, salted

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.90
- Matched ciqual: `15046`  → "Pecan nut, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Pecan nut, salted directly matches the CNF entry for oil roasted, salted pecans in composition and processing."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.366  cnf_default=0.06  ratio=6.10x

### food_id=501754 — Salad dressing, mayonnaise, imitation, soybean

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `17420`  → "Soy oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Imitation mayonnaise primarily uses soybean oil, aligning closely with the soybean oil entry."
- Quality checks: group=True  magnitude=True  token=False

### food_id=502287 — Corn dog, wiener/sausage with cornflour coating, frozen, prepared

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `25403`  → "Hot-dog"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Corn dog contains a sausage and a batter, similar to hot-dogs, making it the closest match in composition and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3233 — Fish, goldeye, raw

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `26210`  → "Golden redfish, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Golden redfish is a finfish, similar in habitat and processing to goldeye, making it the closest match."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=1.2  cnf_default=1.08  ratio=1.11x

### food_id=1267 — Cereal, ready to eat, Special K, Kellogg's

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `32121`  → "Breakfast cereals, corn flakes, sugar iced, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Special K is a fortified corn flake cereal, closely matching the composition and processing of sugar iced corn flakes."
- Quality checks: group=True  magnitude=True  token=False

### food_id=501992 — Meatballs, sweet and sour

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.70
- Matched ciqual: `25211`  → "Meat balls, beef, with tomato sauce"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Beef meatballs with tomato sauce closely resemble sweet and sour meatballs in composition and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=501509 — Seasoning mix, taco, dry mix

- CNF group: `Spices and Herbs`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `11056`  → "Mix of 4 spices"
- Matched Agribalyse group: `aides culinaires et ingrédients divers`
- Justification: "Mix of 4 spices closely resembles a taco seasoning mix in composition and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=502789 — Plant-based beverage, cashew, enriched, sweetened

- CNF group: `Beverages`
- Matched: `True`  confidence: 0.70
- Matched ciqual: `18902`  → "Soy drink, flavoured, with sugar"
- Matched Agribalyse group: `boissons`
- Justification: "Both are plant-based beverages with added sugar; cashew and soy drinks share similar processing and nutritional profiles."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4400 — Candied foods, ginger root, crystallized

- CNF group: `Sweets`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `31003`  → "Candies, all types"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Candies, all types encompasses various sweetened products, aligning with crystallized ginger's sugary nature and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5607 — Roll, pumpernickel

- CNF group: `Baked Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `7262`  → "Rolls for hamburger/hotdog (buns), wholemeal, prepacked"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Wholemeal rolls share similar ingredients and processing methods with pumpernickel, making them the closest match."
- Quality checks: group=True  magnitude=True  token=False

### food_id=501803 — Turkey pot pie, frozen

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `25009`  → "Shepherd's pie or cottage pie with meat"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Shepherd's pie shares similar composition and processing as turkey pot pie, both being meat-based mixed dishes."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5458 — Salad dressing, creamy, made with sour cream and/or buttermilk and oil, calorie-reduced

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `16746`  → "Blended fat (vegetable and animal origins), spreadable, 30-40% fat, lightly salted"
- Matched Agribalyse group: `matières grasses`
- Justification: "Creamy salad dressing aligns with blended fats, combining dairy and oil, similar to the spreadable nature of this entry."
- Quality checks: group=True  magnitude=True  token=False

### food_id=501926 — Cereal, ready to eat, Life, Toasted Cinnamon, Quaker

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `32134`  → "Breakfast cereals, puffed/popped cereals, wholemeal, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Toasted Cinnamon cereal is a fortified breakfast cereal, closely matching the composition and processing of puffed wholemeal cereals."
- Quality checks: group=True  magnitude=True  token=False

### food_id=502191 — Yogourt, Greek style, plain, rich (8-12% M.F.)

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.90
- Matched ciqual: `19860`  → "Yogurt, Greek-style, plain"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Greek-style yogurt, plain, matches closely in fat content and processing, aligning with the CNF entry."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.189  cnf_default=1.0782265372168285  ratio=0.18x

### food_id=532 — Salad dressing, italian, commercial, regular

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.70
- Matched ciqual: `16734`  → "Vegetable fat (margarine type), spreadable, 30-40% fat, light, lightly salted"
- Matched Agribalyse group: `matières grasses`
- Justification: "Italian salad dressing typically contains vegetable fats, making the spreadable margarine type a close match."
- Quality checks: group=True  magnitude=True  token=False

