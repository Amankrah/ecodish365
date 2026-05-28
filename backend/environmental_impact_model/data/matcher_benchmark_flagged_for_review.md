# Matcher benchmark — flagged-for-review rows

- Benchmark JSON: `matcher_benchmark_6e2a999_20260528T165427Z.json`
- Git rev: `6e2a999`
- Sample size: 200; flagged: 77 (38.5%)

Reviewer: for each row below, add `reviewer_verdict: "good" | "stretched" | "fallback"` and `reviewer_notes: "..."` to the per_food row in the JSON.

### food_id=7243 — Refried beans, canned, reduced sodium

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `20524`  → "Red kidney bean, canned, drained"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Canned red kidney beans are the closest canned legume match; refried beans are processed but kidney beans best represent canned legume base."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.145  cnf_default=0.054  ratio=2.69x

### food_id=2637 — Nuts, pistachio nuts, dry roasted, salt added

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `15009`  → "Pistachio nut, grilled, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Exact nut type, dry roasted (grilled) and salted matches CNF's dry roasted, salt added pistachios closely."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.722  cnf_default=0.06  ratio=12.03x

### food_id=700733 — Mopane worm, canned

- CNF group: `WAFCT — Meat, poultry and their products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `10014`  → "Mussel, common, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Mopane worm is an edible insect (animal protein); closest available animal protein is raw mussel, both aquatic protein sources, but different species and processing."
- Quality checks: group=False  magnitude=False  token=False

### food_id=700922 — Groundnut oil, fortified with vitamin A, 1100–2400 mcg/100g (Benin, Burkina Faso, Côte d’Ivoire, Guinea, Guinea-Bissau, Liberia, Mali, Niger, Senegal, Togo)

- CNF group: `WAFCT — Fats and oils`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `17040`  → "Peanut oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Peanut oil matches groundnut oil closely; vitamin A fortification is a minor difference; same commodity and processing type."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700565 — Cashew apple, fruit, raw

- CNF group: `WAFCT — Fruits and their products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `13620`  → "Apple, var. Golden, pulp and skin, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Cashew apple is a fruit; closest available is raw apple variety, though different species and composition."
- Quality checks: group=False  magnitude=False  token=False

### food_id=6045 — Beef, hip, outside (bottom) round steak, boneless, lean and fat, 0mm (0) trim, raw

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `6206`  → "Beef, rump steak, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Beef rump steak raw is the closest whole muscle cut to bottom round steak, both are lean beef cuts; minced steak candidates differ in form and fat content."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=2.8899999999999997  cnf_default=10.0  ratio=0.29x

### food_id=5605 — Yeast extract spread

- CNF group: `Vegetables and Vegetable Products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `16734`  → "Vegetable fat (margarine type), spreadable, 30-40% fat, light, lightly salted"
- Matched Agribalyse group: `matières grasses`
- Justification: "Vegetable fat spread is closest proxy for yeast extract spread, both are spreadable vegetable-based products, though composition and processing differ significantly."
- Quality checks: group=False  magnitude=False  token=False

### food_id=6714 — Egg, chicken, Western omelet, with peppers, onion and ham

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `22507`  → "Omelette, with lardoons"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Omelette with lardoons (bacon) is closest to Western omelet with ham and vegetables; similar protein and fat sources, though peppers and onion differ."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.371  cnf_default=1.0782265372168285  ratio=0.34x

### food_id=3094 — Crustaceans, crab, alaska king, boiled or steamed

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `10025`  → "Crab, boiled/cooked in water"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Same commodity family (crab), boiled/cooked in water matches processing; Alaska king crab specificity not distinguished but closest match available."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=3.3  cnf_default=1.08  ratio=3.06x

### food_id=3391 — Chili with beans, canned

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `25111`  → "Chili con carne"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Chili con carne is closest canned chili variant; includes beans and similar processing, though meat presence differs from bean-only chili."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=1.9600000000000002  cnf_default=0.054  ratio=36.30x

### food_id=701018 — Siikam zéédo (Burkina Faso)*: groundnut sauce with vegetables, fish and fermented African locust beans

- CNF group: `WAFCT — Soups and sauces`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `15002`  → "Peanut, grilled, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Peanut is the main ingredient in groundnut sauce; closest match despite missing fish, vegetables, and fermentation."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2623 — Seeds, sunflower seed butter, salt added

- CNF group: `Nuts and Seeds`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `15045`  → "Sunflower seed, grilled, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is salted sunflower seeds, but butter form differs; no exact sunflower seed butter available in candidates."
- Quality checks: group=False  magnitude=False  token=False

### food_id=25 — Cheese, cottage, creamed (4.5% M.F.)

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `19649`  → "Fresh cream cheese, plain, creamy, around 8% fat"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Closest fat content and fresh cream cheese form; creamed cottage cheese is similar to fresh cream cheese with moderate fat."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.23399999999999999  cnf_default=1.0782265372168285  ratio=0.22x

### food_id=7702 — Salisbury steak with gravy, frozen

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `25009`  → "Shepherd's pie or cottage pie with meat"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Shepherd's pie with meat is a mixed meat dish with gravy-like sauce, closest to Salisbury steak with gravy among stews and plant-based patties."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700384 — Pigeon pea, cream, dry, raw

- CNF group: `WAFCT — Legumes and their products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `20516`  → "Chick pea, dried"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Pigeon pea is a legume like chickpea; both are dried pulses, making chickpea dried the closest available match despite species difference."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700772 — Egg, quail, raw

- CNF group: `WAFCT — Eggs and their products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `22000`  → "Egg, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Raw egg matches raw egg; species differs (chicken vs quail) but same form and minimal processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=2201 — Sauerkraut, canned, solids and liquid

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `25003`  → "Sauerkraut, with garnish"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Sauerkraut with garnish closely matches canned sauerkraut; minor difference in garnish presence, same vegetable product and processing."
- Quality checks: group=False  magnitude=True  token=True
- GW per 100g: matched=0.22400000000000003  cnf_default=0.1  ratio=2.24x

### food_id=628 — Chicken, broiler, wing, meat and skin, flour coated, fried

- CNF group: `Poultry Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `36027`  → "Chicken, nugget, breaded croquette"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Chicken nugget, breaded croquette closely matches flour coated, fried chicken wing in processing and coating, despite different cut."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.387  cnf_default=1.254  ratio=0.31x

### food_id=700970 — Anis seed

- CNF group: `WAFCT — Miscellaneous`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `11066`  → "Fennel, seed"
- Matched Agribalyse group: `aides culinaires et ingrédients divers`
- Justification: "Fennel seed is the closest spice seed to anise seed in composition and use, though not identical; other candidates are less similar botanically or culinarily."
- Quality checks: group=False  magnitude=False  token=False

### food_id=700111 — Porridge, soft, from sifted white maize meal fortified with vitamin A (Nigeria)* (without salt)

- CNF group: `WAFCT — Cereals and their products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `32014`  → "Breakfast cereals, corn flakes, plain (not fortified with vitamins and chemical elements)"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Closest match is plain corn flakes; porridge from maize meal differs in processing and form, but both are maize-based breakfast cereals."
- Quality checks: group=False  magnitude=False  token=False

### food_id=5739 — Dessert, pudding, vanilla, dry mix, instant, prepared with whole milk

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31044`  → "Sugar, vanilla flavoured"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Closest match is vanilla-flavored sugar, but no direct pudding dry mix; composition and processing differ significantly."
- Quality checks: group=False  magnitude=False  token=False

### food_id=5392 — Candied, maraschino cherries, jar, drained

- CNF group: `Sweets`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `31038`  → "Jam, cherry"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Candied maraschino cherries are preserved fruit like cherry jam, but differ in processing and sugar content; closest available match is cherry jam."
- Quality checks: group=True  magnitude=True  token=False

### food_id=63 — Milk, fluid, partly skimmed, 1% M.F.

- CNF group: `Dairy and Egg Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `19041`  → "Milk, semi-skimmed, UHT"
- Matched Agribalyse group: `lait et produits laitiers`
- Justification: "Semi-skimmed UHT milk closely matches partly skimmed 1% M.F. fluid milk in fat content and processing."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.127  cnf_default=1.0782265372168285  ratio=0.12x

### food_id=6313 — Salad dressing, honey mustard, calorie-reduced

- CNF group: `Fats and Oils`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `16654`  → "Vegetable fat (margarine type), 60% fat, unsalted, sunflowerseed"
- Matched Agribalyse group: `matières grasses`
- Justification: "Closest match is vegetable fat margarine type; honey mustard dressing is complex, but no direct match exists, so proxy with vegetable fat margarine is used."
- Quality checks: group=False  magnitude=False  token=False

### food_id=4655 — Fast foods, side dish, hush puppies

- CNF group: `Fast Foods`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `25551`  → "Meat, poultry or fish fritters, home-made"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Meat, poultry or fish fritters are closest in processing and form to hush puppies, both being fried batter-based side dishes with protein content."
- Quality checks: group=True  magnitude=True  token=False

### food_id=7182 — Alcohol, energy drink (7% alcohol by volume)

- CNF group: `Beverages`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `18352`  → "Energy drink, with sugar"
- Matched Agribalyse group: `boissons`
- Justification: "Closest match is energy drink with sugar; no exact alcoholic energy drink available, so this is a stretched proxy."
- Quality checks: group=False  magnitude=False  token=False

### food_id=700923 — Groundnut oil, fortified with vitamin A, 600–1000 mcg/100g (Ghana, Nigeria, Sierra Leone)

- CNF group: `WAFCT — Fats and oils`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `17040`  → "Peanut oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Peanut oil matches groundnut oil closely; fortification with vitamin A is a minor difference; same commodity family and oil form."
- Quality checks: group=True  magnitude=True  token=False

### food_id=1601 — Loquat, raw

- CNF group: `Fruits and fruit juices`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `13023`  → "Lychee, pulp, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Loquat is a tropical stone fruit; lychee pulp is the closest available tropical fruit pulp, though different species and textures."
- Quality checks: group=False  magnitude=False  token=False

### food_id=701009 — Katre nagouri vând maasse zéindo (Burkina Faso)*: fresh sicklepod leaf sauce with vegetables, shea butter, groundnut paste and fermented African locust beans

- CNF group: `WAFCT — Soups and sauces`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `58103`  → "Okra, cooked, without salt"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Okra cooked is a vegetable-based cooked dish, closest proxy for fresh sicklepod leaf sauce with vegetables; other candidates are nuts or meats, less relevant."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2578 — Nuts, mixed nuts, oil roasted with peanuts

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `15002`  → "Peanut, grilled, salted"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Peanut, grilled, salted matches peanuts in mixed nuts, oil roasted; closest processing and nut type despite missing other nuts and oil roasting."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.418  cnf_default=0.06  ratio=6.97x

### food_id=700763 — Egg, chicken, local breed, raw

- CNF group: `WAFCT — Eggs and their products`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `22000`  → "Egg, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Exact match: raw egg, same state and commodity, despite breed difference; best available Agribalyse entry for chicken egg raw."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700305 — Bambara groundnut, white, dry, raw

- CNF group: `WAFCT — Legumes and their products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `20501`  → "Haricot bean, dry"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Haricot bean dry is a legume similar in use and form to Bambara groundnut, both dry seeds; closest available legume match despite species difference."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700622 — Groundnut, red, shelled, dried, raw (Benin)

- CNF group: `WAFCT — Nuts, seeds and their products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `15001`  → "Peanut"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Raw peanut matches groundnut, red, shelled, dried, raw; same commodity family, no processing differences."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700787 — Atlantic cod (Northeast Atlantic), fillet, boiled* (as part of a recipe)

- CNF group: `WAFCT — Fish and its products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `26008`  → "Haddock, steamed"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Haddock steamed is a white Atlantic fish, closer in processing and type to boiled Atlantic cod than other oily or smoked fish."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3251 — Beans, baked, canned, with pork and sweet sauce

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `25098`  → "White bean stew, with pork, canned"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "White bean stew with pork, canned closely matches baked canned beans with pork and sweet sauce in composition and processing."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.213  cnf_default=0.054  ratio=3.94x

### food_id=700402 — Soya bean, Salintuya-1 variety, dry, raw (Ghana), n=1

- CNF group: `WAFCT — Legumes and their products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `20901`  → "Soybean, whole grain"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Soybean whole grain matches dry raw soya bean closely; same commodity, minor variety difference, no processing mismatch."
- Quality checks: group=True  magnitude=True  token=False

### food_id=7045 — Salad dressing, honey mustard, regular

- CNF group: `Fats and Oils`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `16734`  → "Vegetable fat (margarine type), spreadable, 30-40% fat, light, lightly salted"
- Matched Agribalyse group: `matières grasses`
- Justification: "No direct match for honey mustard dressing; margarine-type vegetable fat is closest in fat-based processed product category."
- Quality checks: group=False  magnitude=False  token=False

### food_id=701006 — Groundnut sauce with fish and vegetables (Burkina Faso)*

- CNF group: `WAFCT — Soups and sauces`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15202`  → "Peanut butter or peanut paste"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Peanut butter/paste best matches groundnut sauce base; fish and vegetables not separately modeled, so ingredient-equivalent but not exact."
- Quality checks: group=True  magnitude=True  token=False

### food_id=1598 — Loganberry, frozen

- CNF group: `Fruits and fruit juices`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `13136`  → "Raspberry, frozen, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Frozen raspberry is the closest in fruit family and frozen state to frozen loganberry, both are aggregate berries with similar processing."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.182  cnf_default=0.08  ratio=2.27x

### food_id=700936 — Soya oil, fortified with vitamin A, 600–1000 mcg/100g (Ghana, Nigeria, Sierra Leone)

- CNF group: `WAFCT — Fats and oils`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `17420`  → "Soy oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Soy oil matches the commodity and processing; fortification with vitamin A is a minor difference, typical for edible oils."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3648 — Game meat, whale, raw

- CNF group: `Lamb, Veal and Game`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `8245`  → "Game pâté"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Game pâté is the closest game meat proxy, though processed; no raw whale or similar game meat available in candidates."
- Quality checks: group=False  magnitude=False  token=False

### food_id=1671 — Prune, dehydrated (low moisture), cooked

- CNF group: `Fruits and fruit juices`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `13042`  → "Prune"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Prune dried matches prune dehydrated; minor difference is 'cooked' state not specified in Agribalyse."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.311  cnf_default=0.08  ratio=3.89x

### food_id=2221 — Squash, summer, crookneck, frozen, unprepared

- CNF group: `Vegetables and Vegetable Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `20230`  → "Courgette or zucchini, pulp and peel, frozen, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Frozen courgette/zucchini pulp and peel raw closely matches frozen crookneck summer squash unprepared in form and processing."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.0702  cnf_default=0.1  ratio=0.70x

### food_id=700015 — Fonio, black, whole grains, boiled* (without salt), drained

- CNF group: `WAFCT — Cereals and their products`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `9691`  → "Wheat bulgur, cooked, unsalted"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Wheat bulgur, cooked, unsalted is a cooked cereal grain similar to boiled fonio; both are whole grains, though different species."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3328 — Soy protein isolate (prepared with sodium)

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `20591`  → "Soy protein, textured, dehydrated, from soy flour"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Soy protein isolate closest to textured soy protein from soy flour; both are concentrated soy protein products, though isolate is purer and prepared with sodium."
- Quality checks: group=False  magnitude=True  token=True
- GW per 100g: matched=0.131  cnf_default=0.054  ratio=2.43x

### food_id=700934 — Soya oil, unfortified

- CNF group: `WAFCT — Fats and oils`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `17420`  → "Soy oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Soy oil matches soya oil unfortified closely; both are oils from soybeans with minimal processing differences."
- Quality checks: group=True  magnitude=True  token=False

### food_id=6022 — Beef, flank, flank steak, boneless, lean, raw

- CNF group: `Beef Products`
- Matched: `True`  confidence: 0.85
- Matched ciqual: `6212`  → "Beef, flank steak, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Exact cut (flank steak), raw, matches CNF entry closely; minor differences possible in fat content or trimming."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=2.8899999999999997  cnf_default=10.0  ratio=0.29x

### food_id=4252 — Dessert, pudding, tapioca, dry mix, prepared with whole milk

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31040`  → "Dulce de leche or confiture de lait"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Dulce de leche is a dairy-based sweet spread, closer to pudding than chocolate bars; tapioca pudding mix with milk is a dairy dessert, but no exact match exists."
- Quality checks: group=False  magnitude=False  token=False

### food_id=700435 — Cassava, leaves, fresh, boiled* (without salt), drained

- CNF group: `WAFCT — Vegetables and their products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `54034`  → "Cassava or manioc, roots, cooked"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is cassava root, but leaves differ significantly in composition and processing; no exact leaf match available."
- Quality checks: group=False  magnitude=False  token=False

### food_id=700019 — Fonio, decorticated grains (bran removed), washed (mid wet), raw

- CNF group: `WAFCT — Cereals and their products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `9330`  → "Millet, whole"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Fonio is a cereal grain similar to millet; closest available whole grain cereal match in Agribalyse."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3862 — Cracker, matzo, plain

- CNF group: `Baked Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `38402`  → "Salty snacks, crackers, plain"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Plain salty crackers are closest to plain matzo crackers in processing and composition, though matzo is unleavened and simpler."
- Quality checks: group=True  magnitude=True  token=False

### food_id=6678 — Snacks, Sunchips, Harvest Cheddar flavour

- CNF group: `Snacks`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `38105`  → "Corn chips or tortilla chips"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Corn chips closest to Sunchips (corn-based, flavored snacks), though exact flavor and processing differ."
- Quality checks: group=True  magnitude=True  token=False

### food_id=5859 — Dessert, frozen, ice cream, chocolate, low fat

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.20
- Matched ciqual: `31012`  → "Chocolate confectionery or bar, with dairy filling"
- Matched Agribalyse group: `produits sucrés`
- Justification: "No ice cream or frozen dessert candidate; closest is chocolate confectionery with dairy, but form and processing differ significantly."
- Quality checks: group=False  magnitude=False  token=False

### food_id=3364 — Peanuts, Valencia, oil-roasted

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15037`  → "Peanut, grilled"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Peanut, grilled is closest to oil-roasted peanuts; both involve dry heat and nuts, though roasting method differs (oil vs dry). Valencia variety not specified."
- Quality checks: group=True  magnitude=False  token=False
- GW per 100g: matched=0.418  cnf_default=0.054  ratio=7.74x

### food_id=700343 — Cowpea, white, soaked, boiled in different water* (without salt), with cooking liquid

- CNF group: `WAFCT — Legumes and their products`
- Matched: `True`  confidence: 0.65
- Matched ciqual: `20502`  → "Haricot bean, cooked"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Haricot bean cooked is a legume similar to cowpea; closest in processing and food group despite species difference."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700499 — Pumpkin, leaves, dried

- CNF group: `WAFCT — Vegetables and their products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `20128`  → "Pumpkin (cucurbita moschata), pulp, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is raw pumpkin pulp; no dried leaves available, so this is a stretched proxy within the same plant species."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2581 — Nuts, simulated product, wheat-based, unflavoured, with salt

- CNF group: `Nuts and Seeds`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `15018`  → "Mix of salted grains/nuts and raisins"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match with salted grains/nuts mix; includes salt and nuts, though with raisins, approximating wheat-based salted nut product."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.262  cnf_default=0.06  ratio=4.37x

### food_id=6708 — Cretons

- CNF group: `Sausages and Luncheon meats`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `8214`  → "Breton pâté"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Breton pâté is a processed meat product similar to Cretons, both being pork-based spreads or sausages, though regional recipes differ."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3627 — Veal, pancreas, raw

- CNF group: `Lamb, Veal and Game`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `40408`  → "Kidney, veal, sautéed/pan-fried"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Closest organ meat match (kidney) though pancreas is not listed; same raw state and veal category, but different organ type."
- Quality checks: group=False  magnitude=False  token=False

### food_id=700963 — Sap, palm, fresh (0.3% v/v alcohol)

- CNF group: `WAFCT — Beverages`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `5005`  → "Shandy, prepacked (<1° alcohol)"
- Matched Agribalyse group: `boissons`
- Justification: "Sap, palm, fresh is a low-alcohol beverage; shandy (<1° alcohol) is the closest beverage proxy despite different base ingredients."
- Quality checks: group=False  magnitude=False  token=False

### food_id=4419 — Grains, cornstarch

- CNF group: `Cereals, Grains and Pasta`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `9510`  → "Maize/corn starch"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Exact match: maize/corn starch corresponds directly to cornstarch in CNF, same commodity and processing."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.155  cnf_default=0.18  ratio=0.86x

### food_id=700969 — Allspice, ground

- CNF group: `WAFCT — Miscellaneous`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `11056`  → "Mix of 4 spices"
- Matched Agribalyse group: `aides culinaires et ingrédients divers`
- Justification: "No exact allspice match; mix of 4 spices is closest proxy for ground spice blend."
- Quality checks: group=False  magnitude=False  token=False

### food_id=2341 — Pickles, cucumber, sour, low sodium

- CNF group: `Vegetables and Vegetable Products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `20210`  → "Cucumber, pulp, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is raw cucumber pulp; pickling and sour, low sodium processing not represented, but same vegetable base."
- Quality checks: group=False  magnitude=False  token=False

### food_id=700263 — Yam, tuber, pale, raw

- CNF group: `WAFCT — Starchy roots, tubers and their products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `53502`  → "Yam or Indian potato, peeled, raw"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Yam, peeled, raw matches pale yam tuber raw closely; same commodity family, minor peeling difference."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700383 — Pigeon pea, brown, soaked, boiled in different water* (without salt), with cooking liquid

- CNF group: `WAFCT — Legumes and their products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `20506`  → "Split pea, cooked"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Split pea cooked is the closest legume match to pigeon pea, similar processing (soaked, boiled), though different species; reasonable proxy for LCA purposes."
- Quality checks: group=True  magnitude=True  token=False

### food_id=552 — Shortening, household, unspecified vegetable oil

- CNF group: `Fats and Oils`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `16128`  → "Frying oil"
- Matched Agribalyse group: `matières grasses`
- Justification: "Frying oil is closest to household shortening from vegetable oil, both used as cooking fats though exact fat content and form may differ."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700394 — Porridge of cowpeas, yam and potash (Burkina Faso)*

- CNF group: `WAFCT — Legumes and their products`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `53503`  → "Yam or Indian potato, peeled, boiled/cooked in water"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Closest match is cooked yam, but lacks cowpeas and potash; partial proxy for porridge base ingredient only."
- Quality checks: group=False  magnitude=False  token=False

### food_id=701015 — Maân mâass zéindo (Burkina Faso)*: fresh okra sauce with fish, vegetables, red palm oil and fermented African locust beans

- CNF group: `WAFCT — Soups and sauces`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `58103`  → "Okra, cooked, without salt"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Okra cooked is the main vegetable in the sauce; fish, palm oil, and locust beans missing, but no closer composite match available."
- Quality checks: group=False  magnitude=False  token=False

### food_id=7507 — Babyfood, dinner, jarred or frozen, chicken with vegetables, all stages

- CNF group: `Babyfoods`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `42606`  → "Vegetable dish for baby, w meat/fish and starch, from 18 months"
- Matched Agribalyse group: `aliments infantiles`
- Justification: "Matches baby food with meat/fish and starch, closest to chicken with vegetables; age range difference minor, suitable proxy for composition and processing."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3312 — Peas, pigeon (red gram), mature seeds, dry

- CNF group: `Legumes and Legume Products`
- Matched: `True`  confidence: 0.75
- Matched ciqual: `20516`  → "Chick pea, dried"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Chick pea dried is the closest legume seed to pigeon pea; both are mature dry pulses with similar use, though different species."
- Quality checks: group=True  magnitude=True  token=False
- GW per 100g: matched=0.08990000000000001  cnf_default=0.054  ratio=1.66x

### food_id=700291 — Bambara groundnut, dry, raw

- CNF group: `WAFCT — Legumes and their products`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `20518`  → "Broad bean, dried"
- Matched Agribalyse group: `fruits, légumes, légumineuses et oléagineux`
- Justification: "Bambara groundnut is a legume similar to broad beans; both are dry, raw legumes though different species, making broad bean the closest available match."
- Quality checks: group=True  magnitude=True  token=False

### food_id=700765 — Egg, chicken, raw

- CNF group: `WAFCT — Eggs and their products`
- Matched: `True`  confidence: 0.95
- Matched ciqual: `22000`  → "Egg, raw"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Exact match: raw chicken egg, same state and commodity, near-identical for LCA purposes."
- Quality checks: group=True  magnitude=True  token=False

### food_id=7278 — Chinese dish, lo mein, vegetable, without meat, restaurant prepared

- CNF group: `Mixed Dishes`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `20273`  → "Vegetables pan-fried or stir-fried, Asian-style, frozen, raw"
- Matched Agribalyse group: `entrées et plats composés`
- Justification: "Vegetables pan-fried or stir-fried, Asian-style matches vegetable lo mein's main cooking method and ingredients closely."
- Quality checks: group=True  magnitude=True  token=False

### food_id=3203 — Fish, sardine, Atlantic, canned in oil, drained solids with bone

- CNF group: `Finfish and Shellfish Products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `26034`  → "European pilchard or sardine, in oil, canned, drained (packaging fixed)"
- Matched Agribalyse group: `viandes, œufs, poissons`
- Justification: "Same species and canned in oil, drained; slight uncertainty on oil type and presence of bones versus fillets."
- Quality checks: group=True  magnitude=False  token=True
- GW per 100g: matched=0.268  cnf_default=1.08  ratio=0.25x

### food_id=700024 — Fonio, white, whole grains, boiled* (without salt), drained

- CNF group: `WAFCT — Cereals and their products`
- Matched: `True`  confidence: 0.80
- Matched ciqual: `9331`  → "Millet, cooked, unsalted"
- Matched Agribalyse group: `produits céréaliers`
- Justification: "Millet, cooked, unsalted is the closest cereal grain match to boiled fonio, sharing similar processing and whole grain form."
- Quality checks: group=True  magnitude=True  token=False

### food_id=4273 — Dessert, rennin, chocolate, dry mix, unprepared

- CNF group: `Sweets`
- Matched: `False`  confidence: 0.40
- Matched ciqual: `31085`  → "Dark chocolate bar, more than 40% cocoa, for cooking"
- Matched Agribalyse group: `produits sucrés`
- Justification: "Closest match is dark chocolate for cooking, but dessert rennin chocolate dry mix differs in form and preparation."
- Quality checks: group=False  magnitude=False  token=False

### food_id=6312 — Seasoning mix, taco, dry mix

- CNF group: `Spices and Herbs`
- Matched: `True`  confidence: 0.60
- Matched ciqual: `11056`  → "Mix of 4 spices"
- Matched Agribalyse group: `aides culinaires et ingrédients divers`
- Justification: "Mix of 4 spices best matches dry seasoning mix; not taco-specific but closest in form and category among candidates."
- Quality checks: group=True  magnitude=True  token=False

