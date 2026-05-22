# Matcher benchmark — flagged-for-review rows

- Benchmark JSON: `matcher_benchmark_e416d7d_20260522T194544Z.json`
- Git rev: `e416d7d`
- Sample size: 184; flagged: 76 (41.3%)

Reviewer: for each row below, add `reviewer_verdict: "good" | "stretched" | "fallback"` and `reviewer_notes: "..."` to the per_food row in the JSON.

### food_id=3310 — Peanut flour, defatted, salted

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15001`  → "Peanut"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Peanut flour defatted salted best matches raw peanut; no exact defatted salted flour in candidates, but same commodity family."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.418  cnf_default=0.054  ratio=7.74x

### food_id=4259 — Dessert, pudding, vanilla, dry mix, regular, unprepared

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31044`  → "Sugar, vanilla flavoured"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Vanilla-flavored sugar is closest proxy for dry vanilla pudding mix; others are chocolate or fruit-based sweets, less relevant."
- Quality checks: group=False  magnitude=False  token=False

### food_id=3077 — Fish, tilefish, raw

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `26009`  → "Atlantic halibut, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Atlantic halibut is a large white fish, closest in type and raw state to tilefish among candidates."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.46900000000000003  cnf_default=1.08  ratio=0.43x

### food_id=5290 — Tea, instant, unsweetened, powder, decaffeinated

- CNF group: `Beverages`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `18072`  → "Decaffeinated instant coffee, without sugar, ready-to-drink"
- Matched Agribalyse group: `boissons`
- Justification: "No instant tea LCI; decaf instant coffee closest in processing and form despite different raw material."
- Quality checks: group=False  magnitude=False  token=False

### food_id=3094 — Crustaceans, crab, alaska king, boiled or steamed

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `10025`  → "Crab, boiled/cooked in water"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Same commodity family (crab), similar cooking method (boiled), though not specified as Alaska king crab in Agribalyse."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=3.3  cnf_default=1.08  ratio=3.06x

### food_id=4280 — Dessert, flan, caramel custard, dry mix, prepared with whole milk

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31040`  → "Dulce de leche or confiture de lait"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Dulce de leche is a milk-based sweet similar in dairy content and caramel flavor, though processing differs from flan dry mix."
- Quality checks: group=False  magnitude=False  token=False

### food_id=5644 — Emu, full rump, cooked, broiled

- CNF group: `Poultry Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `36203`  → "Duck, leg, meat and skin, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Duck leg meat is closest poultry match to emu rump; both are dark poultry meat, though emu is red meat, no exact broiled cooked match available."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.46799999999999997  cnf_default=1.254  ratio=0.37x

### food_id=4086 — Snacks, beef jerky, chopped and formed

- CNF group: `Snacks`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `30300`  → "Dry sausage"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Dry sausage is the closest processed meat snack, though jerky is dried and formed beef, not sausage; no exact beef jerky match available."
- Quality checks: group=False  magnitude=False  token=False

### food_id=6081 — Beef, rib, rib roast with bone, lean and fat, 3mm (1/8") trim, cooked, roasted

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `6001`  → "Beef, rib, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Same beef rib cut, raw form; closest to cooked roasted CNF entry despite raw state difference."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=2.91  cnf_default=10.0  ratio=0.29x

### food_id=502426 — Cereal, ready-to-eat, Krave, Kellogg's

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `32115`  → "Breakfast cereals, chocolate puffed/popped wheat grain, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Chocolate puffed/popped wheat grain cereal closely matches Krave's chocolate-flavored, puffed cereal profile and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4286 — Icing (frosting), white, fluffy, dry mix, prepared with water

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31016`  → "Sugar, white"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Icing dry mix mainly consists of sugar; closest proxy is white sugar despite missing other ingredients and processing."
- Quality checks: group=False  magnitude=False  token=False

### food_id=5694 — Deli-meat, Bologna (baloney), reduced fat

- CNF group: `Sausages and Luncheon meats`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `30791`  → "Pork and beef mortadella"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Mortadella is a cooked, emulsified pork and beef sausage similar to bologna; reduced fat variant not specified but closest match in type and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5546 — Vegetarian meat loaf or patty, meatless

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `25591`  → "Plant-based patty or steak from lentil, soybean and vegetables"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Closest match: plant-based patty from lentil, soybean, and vegetables aligns well with vegetarian meat loaf, legume-based, minor processing differences."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.16799999999999998  cnf_default=0.054  ratio=3.11x

### food_id=3648 — Game meat, whale, raw

- CNF group: `Lamb, Veal and Game`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `8245`  → "Game pâté"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Game pâté is the closest available game meat proxy, though processed; no raw whale or similar game meat present in candidates."
- Quality checks: group=False  magnitude=False  token=False

### food_id=502852 — Babyfood, dinner, jarred or frozen, beef with vegetables, all stages

- CNF group: `Babyfoods`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `42606`  → "Vegetable dish for baby, w meat/fish and starch, from 18 months"
- Matched Agribalyse group: `aliments infantiles`
- Justification: "Matches baby food with meat/fish and starch, closest to beef with vegetables; age range 18 months is a minor difference."
- Quality checks: group=True  magnitude=True  token=False

### food_id=1711 — Fig, raw

- CNF group: `Fruits and fruit juices`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `13012`  → "Fig, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Exact match: raw fig in both CNF and Agribalyse, same commodity and form."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0611  cnf_default=0.08  ratio=0.76x

### food_id=2539 — Nuts, almonds, toasted, unblanched

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `15041`  → "Almond, peeled, unpeeled or blanched"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is almond, unpeeled; toasted unblanched almonds differ slightly but same commodity and similar processing."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.263  cnf_default=0.06  ratio=4.38x

### food_id=4142 — Dessert, frozen, pudding pop, vanilla

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31014`  → "Fruit jelly"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Closest available proxy is fruit jelly; no exact frozen vanilla pudding pop match in list."
- Quality checks: group=False  magnitude=False  token=False

### food_id=627 — Chicken, broiler, wing, meat and skin, batter dipped, fried

- CNF group: `Poultry Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `36027`  → "Chicken, nugget, breaded croquette"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Chicken nugget, breaded croquette is closest to batter dipped, fried wings in processing and coating, despite different cut; better match than roasted or raw wings."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.387  cnf_default=1.254  ratio=0.31x

### food_id=5609 — Beans, baked, canned, no salt added

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `20524`  → "Red kidney bean, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Red kidney bean canned is the closest canned legume match; similar processing and form, though not explicitly no salt added."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.145  cnf_default=0.054  ratio=2.69x

### food_id=502204 — Yogourt, plain, fresh cheese-type (quark), fat free,  no salt added

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `19594`  → "Yogurt, fermented milk or dairy specialty, plain, fat free"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Plain, fat free yogurt matches fat free fresh cheese-type quark closely in composition and processing, both are fermented dairy products without added fat or salt."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.189  cnf_default=1.0782265372168285  ratio=0.18x

### food_id=502164 — Yogourt, fruit flavoured, low fat (0.5-1.9% M.F.)

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `19559`  → "Yogurt, fermented milk or dairy specialty, flavoured, with sweetener, fat free"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Flavoured yogurt with sweetener, fat free closest to low fat fruit flavoured yogurt; minor fat content difference."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.188  cnf_default=1.0782265372168285  ratio=0.17x

### food_id=501810 — Yambean (jimaca), tuber, boiled, drained, with salt

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `53503`  → "Yam or Indian potato, peeled, boiled/cooked in water"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Yambean is a tuber similar to yam; boiled yam is closest match in processing and form despite botanical differences."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0806  cnf_default=0.1  ratio=0.81x

### food_id=2221 — Squash, summer, crookneck, frozen, unprepared

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `20230`  → "Courgette or zucchini, pulp and peel, frozen, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Frozen courgette/zucchini is closest frozen squash type; crookneck is summer squash like zucchini; frozen state matches; minor variety difference."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0702  cnf_default=0.1  ratio=0.70x

### food_id=6285 — Beef, composite cuts, stewing beef, 0mm (0") trim, raw

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `6231`  → "Beef, stewing meat, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Beef stewing meat, raw matches composite cuts for stewing; both raw, similar use and cut type, minor differences in trimming likely."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=2.8899999999999997  cnf_default=10.0  ratio=0.29x

### food_id=2696 — Beef, ground, medium, patty, pan-fried

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `6260`  → "Burger, beef based, 15% fat, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Beef burger patty, 15% fat, raw is closest to medium fat ground beef patty before pan-frying; cooking method differs but composition matches well."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=1.75  cnf_default=10.0  ratio=0.17x

### food_id=5647 — Emu, outside drum, raw

- CNF group: `Poultry Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `36022`  → "Chicken, drumstick, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Chicken drumstick raw is the closest poultry match to emu outside drum raw; same broad group but different species and likely different environmental impacts."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.5780000000000001  cnf_default=1.254  ratio=0.46x

### food_id=5894 — Fish, pike, northern, native, liver

- CNF group: `Finfish and Shellfish Products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `26237`  → "Atlantic herring, lean, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both are raw oily fish from northern waters; no exact pike liver match, Atlantic herring is closest proxy in composition and processing."
- Quality checks: group=False  magnitude=False  token=False

### food_id=502059 — Cereal, ready to eat, Hemp Plus Granola, Nature's Path

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `32123`  → "Breakfast cereals, wheat flakes with walnuts, hazelnuts or almonds, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Closest match is wheat flakes with nuts, similar granola style; lacks hemp but same breakfast cereal family and nut inclusion."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2561 — Nuts, coconut meat, desiccated, sweetened, flaked, canned

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15007`  → "Coconut, kernel, dried"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is dried coconut kernel; desiccated sweetened canned coconut is processed but no exact sweetened canned option available."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.242  cnf_default=0.06  ratio=4.03x

### food_id=3251 — Beans, baked, canned, with pork and sweet sauce

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `25098`  → "White bean stew, with pork, canned"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "White bean stew with pork, canned closely matches baked canned beans with pork and sweet sauce in composition and processing."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.213  cnf_default=0.054  ratio=3.94x

### food_id=5515 — Salad dressing, caesar dressing, regular

- CNF group: `Fats and Oils`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `16614`  → "Vegetable fat (like margarine), 80% fat, salted"
- Matched Agribalyse group: `matières grasses`
- Justification: "Caesar dressing is a complex mix; closest proxy is high-fat vegetable fat, though composition and processing differ significantly."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2579 — Nuts, mixed nuts, oil roasted without peanuts

- CNF group: `Nuts and Seeds`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `15004`  → "Hazelnut"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest single nut match; oil roasted mixed nuts not available, so hazelnut alone is a stretched proxy for nuts group."
- Quality checks: group=False  magnitude=False  token=False

### food_id=501535 — Grains, teff, cooked

- CNF group: `Cereals, Grains and Pasta`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `9330`  → "Millet, whole"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Millet, whole, raw is the closest cereal grain to teff; both are small grains, though teff is cooked and not millet, this is the best available proxy."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0674  cnf_default=0.18  ratio=0.37x

### food_id=502338 — Yogourt, goat, plain

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `19556`  → "Yogurt, goat's milk, plain, around 5% fat"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Exact match: plain goat's milk yogurt with similar fat content, same product type and processing."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.20400000000000001  cnf_default=1.0782265372168285  ratio=0.19x

### food_id=5544 — Meatless, sandwich spread

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `1027`  → "Plant-based spread-cheese type, with soybean, prepacked"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Closest match is plant-based spread with soybean, similar legume base and spread form, though not exactly sandwich spread."
- Quality checks: group=False  magnitude=False  token=True
- GW per 100g: matched=0.187  cnf_default=0.054  ratio=3.46x

### food_id=4758 — Beef, hip, rump roast, lean and fat, 3mm (1/8") trim, broiled

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `6206`  → "Beef, rump steak, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Beef rump steak raw is closest cut to rump roast; both are whole muscle beef, though raw vs broiled and steak vs roast differ slightly."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=2.8899999999999997  cnf_default=10.0  ratio=0.29x

### food_id=502262 — Chickpeas (garbanzo beans, bengal gram), canned, drained, rinsed

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `20532`  → "Chick pea, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Exact match: chickpeas, canned, drained, same processing and form as CNF entry."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.22000000000000003  cnf_default=0.054  ratio=4.07x

### food_id=4588 — Fast foods, mexican, burrito with beans and cheese

- CNF group: `Fast Foods`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `25459`  → "Burritos"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Exact match on burrito; minor differences possible in bean and cheese types or preparation, but same commodity family and form."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4467 — Grains, hominy, canned, yellow

- CNF group: `Cereals, Grains and Pasta`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `20066`  → "Sweet corn, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Canned sweet corn closely matches canned hominy in processing and form, both are canned maize products, though hominy is nixtamalized, a minor difference."
- Quality checks: group=False  magnitude=True  token=False
- GW per 100g: matched=0.13899999999999998  cnf_default=0.18  ratio=0.77x

### food_id=4058 — Pie, pumpkin, commercial

- CNF group: `Baked Products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `20043`  → "Pumpkin, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is canned pumpkin, reflecting cooked and processed form in pie; raw pumpkin less representative of commercial pie ingredients."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2519 — Seeds, safflower seed meal, partially defatted

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15011`  → "Sunflower seed"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Sunflower seed is the closest seed meal proxy; safflower seed meal unavailable, similar oilseed family but different species and partial defatting not matched."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.29100000000000004  cnf_default=0.06  ratio=4.85x

### food_id=1577 — Groundcherry, raw

- CNF group: `Fruits and fruit juices`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `13008`  → "Cherry, pitted, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Groundcherry is a small fruit like cherry; closest available raw fruit match despite botanical differences."
- Quality checks: group=False  magnitude=False  token=False

### food_id=3790 — Cake, white, regular, dry mix, unprepared

- CNF group: `Baked Products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `23032`  → "Brownie (chocolate cake)"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Closest cake-type match; no dry mix option available; brownie is a processed cake product, though different from dry mix unprepared cake."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2577 — Nuts, mixed nuts, dry roasted with peanuts

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `15002`  → "Peanut, grilled, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Peanut, grilled, salted closely matches dry roasted peanuts; mixed nuts not available, so single nut with similar processing chosen."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.418  cnf_default=0.06  ratio=6.97x

### food_id=2201 — Sauerkraut, canned, solids and liquid

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `25003`  → "Sauerkraut, with garnish"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Sauerkraut with garnish closely matches canned sauerkraut; minor difference in garnish presence, same vegetable and processing."
- Quality checks: group=False  magnitude=True  token=True
- GW per 100g: matched=0.22400000000000003  cnf_default=0.1  ratio=2.24x

### food_id=4291 — Dessert, frozen, ice pop

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.20
- Matched ciqual: `31059`  → "Hard candy and lollipop"
- Matched Agribalyse group: `produits sucrés`
- Justification: "No ice pop or frozen dessert candidate; hard candy is a poor proxy within sweets category."
- Quality checks: group=False  magnitude=False  token=False

### food_id=1003 — Gravy, chicken, canned

- CNF group: `Soups, Sauces and Gravies`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `25174`  → "Chicken with curry and coconut milk sauce"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Closest match is chicken with sauce, but curry and coconut milk differ from plain chicken gravy; canned form not specified."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2022 — Beet greens, boiled, drained

- CNF group: `Vegetables and Vegetable Products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `20003`  → "Beetroot, cooked"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest in commodity (beet family) and cooked state, but matches beetroot not beet greens; no exact beet greens entry available."
- Quality checks: group=False  magnitude=False  token=False

### food_id=3627 — Veal, pancreas, raw

- CNF group: `Lamb, Veal and Game`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `6583`  → "Veal, knuckle or shank, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Closest veal raw cut available; pancreas is organ meat, but no organ-specific raw pancreas entry exists."
- Quality checks: group=False  magnitude=False  token=False

### food_id=172 — Spices, bay leaf

- CNF group: `Spices and Herbs`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `11053`  → "Bay, leaves"
- Matched Agribalyse group: `aides culinaires et ingrédients divers`
- Justification: "Exact match for bay leaf, same spice, form, and commodity; highest similarity and perfect alignment with CNF entry."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3269 — Beans, pinto, raw

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `20126`  → "Lima bean, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Lima bean is a close legume family member, raw form matches; pinto bean not listed, so best proxy within raw legumes."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0817  cnf_default=0.054  ratio=1.51x

### food_id=1847 — Pork, lungs, braised

- CNF group: `Pork Products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `40004`  → "Brain, pork, braised"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Both are pork offal, braised; lungs and brain differ but no closer braised pork offal match available."
- Quality checks: group=False  magnitude=False  token=False

### food_id=5139 — Cereal, ready to eat, Selects, Cranberry Almond Crunch, Post

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `32123`  → "Breakfast cereals, wheat flakes with walnuts, hazelnuts or almonds, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Closest match: breakfast cereal with nuts, similar to cranberry almond crunch; minor differences in fruit type and fortification."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2552 — Nuts, Chinese chestnuts, roasted

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15024`  → "Chestnut, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is raw chestnut; roasting differs but same commodity, making it a reasonable proxy for LCA purposes."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.194  cnf_default=0.06  ratio=3.23x

### food_id=6212 — Pork, cured, ham, shank, bone-in, separable lean and fat, heated, roasted

- CNF group: `Pork Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `28913`  → "Cooked ham, choice, rind less and fatless"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Cooked ham, choice, rind less and fatless is closest to cured, roasted ham shank; minor differences in rind and fat presence."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.765  cnf_default=1.52  ratio=0.50x

### food_id=544 — Shortening, industrial, for baking (cake), soybean

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `17420`  → "Soy oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Soy oil is the closest match to industrial soybean shortening, sharing the same commodity family despite differences in processing and form."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3203 — Fish, sardine, Atlantic, canned in oil, drained solids with bone

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `26034`  → "European pilchard or sardine, in oil, canned, drained (packaging fixed)"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Same species (European pilchard), canned in oil, drained; closest to Atlantic sardine canned in oil with bone, minor difference in fish origin and bone presence."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.268  cnf_default=1.08  ratio=0.25x

### food_id=502439 — Nuts, walnuts, glazed

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `15005`  → "Walnut, dried, husked"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Walnut, dried, husked is the closest match to glazed walnuts, same nut type with minor processing differences."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.41100000000000003  cnf_default=0.06  ratio=6.85x

### food_id=2636 — Nuts, pecans, oil roasted, salted

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `15046`  → "Pecan nut, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Same nut (pecan), salted; oil roasted not specified but closest match in processing and form."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.366  cnf_default=0.06  ratio=6.10x

### food_id=501754 — Salad dressing, mayonnaise, imitation, soybean

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `17420`  → "Soy oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Soy oil is the closest single ingredient proxy for imitation soybean mayonnaise fat content and source."
- Quality checks: group=True  magnitude=True  token=False

### food_id=502287 — Corn dog, wiener/sausage with cornflour coating, frozen, prepared

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `25403`  → "Hot-dog"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Hot-dog is the closest match to corn dog with sausage and coating, though lacks cornflour batter and frozen prepared state."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5453 — Dessert, frozen, ice cream, vanilla, fat free

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.20
- Matched ciqual: `31044`  → "Sugar, vanilla flavoured"
- Matched Agribalyse group: `produits sucrés`
- Justification: "No exact ice cream or frozen dessert match; sugar vanilla flavor closest but lacks dairy and frozen fat-free characteristics."
- Quality checks: group=False  magnitude=False  token=False

### food_id=3233 — Fish, goldeye, raw

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `26210`  → "Golden redfish, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Golden redfish is the closest species match to goldeye; both are raw finfish, though not identical species."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=1.2  cnf_default=1.08  ratio=1.11x

### food_id=1267 — Cereal, ready to eat, Special K, Kellogg's

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `32121`  → "Breakfast cereals, corn flakes, sugar iced, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Closest match is corn flakes, sugar iced, fortified, similar processing and fortification as Special K, a fortified wheat-based cereal with sugar coating."
- Quality checks: group=True  magnitude=True  token=False

### food_id=501992 — Meatballs, sweet and sour

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `25211`  → "Meat balls, beef, with tomato sauce"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Meat balls with tomato sauce is the closest match to sweet and sour meatballs, sharing main ingredient and form despite different sauce."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4126 — Snacks, rice cakes, brown rice, sesame seed

- CNF group: `Snacks`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `38402`  → "Salty snacks, crackers, plain"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Closest match is plain salty crackers, a processed snack like rice cakes; no exact rice cake or sesame seed snack available."
- Quality checks: group=False  magnitude=False  token=False

### food_id=501509 — Seasoning mix, taco, dry mix

- CNF group: `Spices and Herbs`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `11056`  → "Mix of 4 spices"
- Matched Agribalyse group: `aides culinaires et ingrédients divers`
- Justification: "Mix of 4 spices best matches dry taco seasoning mix as a spice blend; others are sauces or single spices, less appropriate."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4400 — Candied foods, ginger root, crystallized

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31003`  → "Candies, all types"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Closest generic candy category; no specific crystallized ginger entry; composition and processing differ but usable as proxy for candied sweets."
- Quality checks: group=False  magnitude=False  token=False

### food_id=5607 — Roll, pumpernickel

- CNF group: `Baked Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `7262`  → "Rolls for hamburger/hotdog (buns), wholemeal, prepacked"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Wholemeal rolls closest to pumpernickel roll; similar grain base and form, though pumpernickel is denser and darker, so not exact but best available match."
- Quality checks: group=True  magnitude=True  token=False

### food_id=501803 — Turkey pot pie, frozen

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `25009`  → "Shepherd's pie or cottage pie with meat"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Shepherd's pie with meat is a similar savory meat and potato pie, close in processing and form to turkey pot pie, though different meat type."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5458 — Salad dressing, creamy, made with sour cream and/or buttermilk and oil, calorie-reduced

- CNF group: `Fats and Oils`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `16746`  → "Blended fat (vegetable and animal origins), spreadable, 30-40% fat, lightly salted"
- Matched Agribalyse group: `matières grasses`
- Justification: "Closest match is blended fat of vegetable and animal origin, reflecting creamy dressing fat mix; no exact sour cream or reduced-calorie dressing available."
- Quality checks: group=False  magnitude=False  token=False

### food_id=501926 — Cereal, ready to eat, Life, Toasted Cinnamon, Quaker

- CNF group: `Breakfast cereals`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `32000`  → "Breakfast cereals, popped or puffed wheat grain, with honey or caramel, fortified with vitamins and chemical elements"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Puffed wheat cereal with sweetener closest to toasted cinnamon flavor; matches processing and cereal type broadly, though flavor specifics differ."
- Quality checks: group=True  magnitude=True  token=False

### food_id=502145 — Papaya, canned, heavy syrup pack, drained

- CNF group: `Fruits and fruit juices`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `13718`  → "Pineapple, in light syrup, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest canned fruit in syrup, similar processing; different fruit (pineapple vs papaya) reduces confidence."
- Quality checks: group=False  magnitude=False  token=False

### food_id=502191 — Yogourt, Greek style, plain, rich (8-12% M.F.)

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.90
- Matched ciqual: `19860`  → "Yogurt, Greek-style, plain"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Exact match for Greek-style plain yogurt; likely similar fat content range, best available proxy for rich (8-12% M.F.) variant."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.189  cnf_default=1.0782265372168285  ratio=0.18x

### food_id=532 — Salad dressing, italian, commercial, regular

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `17270`  → "Olive oil, extra virgin"
- Matched Agribalyse group: `matières grasses`
- Justification: "Italian salad dressing typically contains olive oil; extra virgin olive oil is the closest Agribalyse fat source despite missing other ingredients."
- Quality checks: group=True  magnitude=True  token=False

