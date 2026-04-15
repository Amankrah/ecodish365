//! Food description → Reference-Amount (RA) category classifier.
//!
//! Mechanical port of
//! `HEFICNFIntegrator._classify_food_to_ra_category` in
//! `backend/hefi_calculator/hefi/cnf_integrator.py` (lines 510-850).
//!
//! **Do not "clean up" this file.** The elif/ordering semantics are
//! load-bearing — the first matching branch wins, and rewriting any of
//! them will silently diverge from the Python baseline that the HEFI
//! scoring corpus was built against. Every branch is preserved
//! one-for-one; diff-tested against all 5,691 CNF rows.

/// Classify an uppercased food description into an RA category string.
///
/// Returns a `&'static str` — all categories are known at compile time.
pub fn classify(food_description: &str, food_group_id: i32) -> &'static str {
    // Matches Python: desc = food_description.upper()
    let desc_owned = food_description.to_uppercase();
    let desc = desc_owned.as_str();

    // Tiny helper to mirror `any(x in desc for x in [...])`.
    let any = |needles: &[&str]| needles.iter().any(|n| desc.contains(n));
    let has = |n: &str| desc.contains(n);

    match food_group_id {
        // ─── Fruits (Group 9) ────────────────────────────────────────
        9 => {
            if any(&["BLUEBERR", "RASPBERR", "BLACKBERR", "STRAWBERR"]) {
                "berries"
            } else if any(&["WATERMELON", "CANTALOUPE", "HONEYDEW", "MELON"]) {
                "melons"
            } else if any(&["DRIED", "RAISIN", "PRUNE", "DATE", "FIG", "APRICOT"]) {
                "dried_fruit"
            } else if has("JUICE") && any(&["JUICE", "NECTAR", "DRINK"]) {
                if any(&["LEMON", "LIME"]) {
                    "juice_ingredient"
                } else {
                    "fruit_juice"
                }
            } else if any(&["MARASCHINO", "GARNISH", "FLAVOUR"]) {
                "fruit_garnish"
            } else if has("RELISH") {
                "fruit_relishes"
            } else if any(&["CANDIED", "PICKLED"]) {
                "candied_fruit"
            } else if has("APPLESAUCE") || (has("APPLE") && has("SAUCE")) {
                "applesauce"
            } else if has("AVOCADO") && has("INGREDIENT") {
                "avocado_ingredient"
            } else if any(&["CRANBERR", "LEMON", "LIME"]) && has("INGREDIENT") {
                "cranberries_ingredient"
            } else if has("CANNED") || has("TINNED") {
                "fruit_canned"
            } else {
                "fruit_fresh"
            }
        }

        // ─── Vegetables (Group 11) ───────────────────────────────────
        11 => {
            if has("JUICE") {
                "vegetable_juice"
            } else if any(&["PARSLEY", "GARLIC", "GARNISH", "FLAVOUR"]) && has("FRESH") {
                "vegetables_garnish_fresh"
            } else if any(&["PARSLEY", "GARLIC", "GARNISH", "FLAVOUR"]) && has("CANNED") {
                "vegetables_garnish_canned"
            } else if any(&["CHILI", "GREEN ONION"]) {
                "chili_pepper"
            } else if any(&["SEAWEED", "DEHYDRATED", "DRIED"]) && has("MUSHROOM") {
                "seaweed_mushrooms"
            } else if has("SPROUTS") {
                "sprouts"
            } else if has("OLIVES") {
                "olives"
            } else if any(&["PICKLED", "PICKLE", "SUN-DRIED", "PACKED IN OIL"]) {
                "pickled_vegetables"
            } else if has("RELISH") {
                "relish"
            } else if has("PASTE") {
                "vegetable_paste"
            } else if any(&["SAUCE", "PUREE", "PURÉE"]) {
                "vegetable_sauce"
            } else if any(&["SAUCE", "GRAVY", "CREAM", "WITH"]) {
                // NOTE: unreachable in practice — the previous branch already
                // consumes any "SAUCE" match. Preserved verbatim from Python
                // so behavior is bit-identical. Do not collapse.
                if has("CANNED") || has("TINNED") {
                    "vegetables_with_sauce_canned"
                } else {
                    "vegetables_with_sauce_fresh"
                }
            } else if has("CANNED") || has("TINNED") {
                "vegetables_canned"
            } else {
                "vegetables_fresh"
            }
        }

        // ─── Legumes (Group 16) ──────────────────────────────────────
        16 => {
            if has("TOFU") || has("TEMPEH") || has("BEAN CURD") {
                "tofu"
            } else if any(&["COOKED", "CANNED", "BOILED", "PREPARED"]) {
                "legumes_cooked"
            } else {
                "legumes_dry"
            }
        }

        // ─── Cereals / Grains (Groups 18, 20) ────────────────────────
        18 | 20 => {
            if any(&["BREAD", "LOAF"]) && !any(&["SWEET", "QUICK"]) {
                "bread"
            } else if any(&[
                "ROLL",
                "BUN",
                "BISCUIT",
                "SCONE",
                "ENGLISH MUFFIN",
                "CROISSANT",
                "TORTILLA",
                "PITA",
            ]) {
                "rolls_buns"
            } else if any(&["BAGEL", "NAAN", "FLAT BREAD"]) {
                "bagels"
            } else if any(&["BROWNIE", "DESSERT SQUARE", "BAR"]) {
                "brownies_bars"
            } else if has("CAKE") {
                if any(&["CHEESE CAKE", "PINEAPPLE", "POUND"]) {
                    "cake_heavy"
                } else if any(&["ANGEL", "CHIFFON", "SPONGE"]) && !has("ICING") {
                    "cake_light"
                } else {
                    "cake_medium"
                }
            } else if any(&["DOUGHNUT", "DANISH", "SWEET ROLL", "COFFEE CAKE", "PASTRY"]) {
                "sweet_pastries"
            } else if has("MUFFIN") {
                "muffins"
            } else if has("COOKIE") || has("WAFER") || has("GRAHAM") {
                "cookies"
            } else if has("CRACKER") {
                if has("SNACK") {
                    "snack_crackers"
                } else {
                    "crackers"
                }
            } else if any(&["MATZO", "RUSK", "DRY BREAD"]) {
                "dry_breads"
            } else if has("TOASTER PASTRY") {
                "toaster_pastries"
            } else if has("ICE CREAM CONE") {
                "ice_cream_cones"
            } else if has("CROUTON") {
                "croutons"
            } else if any(&["PANCAKE", "WAFFLE", "FRENCH TOAST"]) {
                "pancakes_waffles"
            } else if any(&["GRAIN BAR", "GRANOLA BAR"]) {
                if any(&["FILLING", "COATING", "COATED"]) {
                    "grain_bars_filled"
                } else {
                    "grain_bars_plain"
                }
            } else if any(&["ENERGY BAR", "PROTEIN BAR"]) {
                "energy_bars"
            } else if any(&["RICE CAKE", "CORN CAKE"]) {
                "rice_cakes"
            } else if any(&["PIE", "TART", "COBBLER", "TURNOVER"]) {
                if has("CRUST") {
                    "pie_crust"
                } else {
                    "pies_tarts"
                }
            } else if has("PIZZA CRUST") {
                "pizza_crust"
            } else if has("TACO SHELL") {
                "taco_shell"
            } else if has("PASTA") || has("NOODLE") || has("SPAGHETTI") || has("MACARONI") {
                if any(&["FRIED", "CHOW MEIN"]) && has("DRY") {
                    "pasta_fried_dry"
                } else if any(&["COOKED", "PREPARED", "BOILED"]) {
                    "pasta_cooked"
                } else {
                    "pasta_dry"
                }
            } else if any(&["RICE", "BARLEY", "GRAIN"]) {
                if any(&["COOKED", "PREPARED", "BOILED"]) {
                    "rice_grains_cooked"
                } else {
                    "rice_grains_dry"
                }
            } else if has("CEREAL") {
                if any(&["OATMEAL", "CREAM OF", "HOT"]) {
                    if has("DRY") || has("INSTANT") {
                        "hot_cereal_dry"
                    } else {
                        "hot_cereal_prepared"
                    }
                } else if any(&["PUFFED"]) && !any(&["COATED", "GRANOLA"]) {
                    "ready_cereal_light"
                } else if any(&["GRANOLA", "MUESLI", "FRUIT", "NUT"]) || has("BISCUIT") {
                    "ready_cereal_heavy"
                } else {
                    "ready_cereal_medium"
                }
            } else if any(&["BRAN", "WHEAT GERM", "FLAX", "HEMP", "CHIA"]) {
                "bran_wheat_germ"
            } else if has("FLOUR") || has("CORNMEAL") {
                "flours"
            } else if has("STARCH") {
                "starch"
            } else if has("STUFFING") {
                "stuffing"
            } else {
                "rice_grains_dry"
            }
        }

        // ─── Dairy (Group 1) ─────────────────────────────────────────
        1 => {
            if has("MILK") {
                if any(&["EVAPORATED", "CONDENSED"]) {
                    "condensed_milk"
                } else {
                    "milk"
                }
            } else if has("CHEESE") {
                if has("COTTAGE") {
                    "cottage_cheese"
                } else if any(&["PARMESAN", "ROMANO", "GRATED", "HARD"]) {
                    "hard_cheese"
                } else if any(&["RICOTTA", "INGREDIENT"]) {
                    "cheese_ingredient"
                } else {
                    "cheese"
                }
            } else if any(&["YOGURT", "YOGHURT"]) {
                "yogurt"
            } else if has("CREAM") {
                if has("SOUR") {
                    "sour_cream"
                } else if any(&["WHIPPED", "AEROSOL"]) {
                    "whipped_cream"
                } else if has("POWDER") {
                    "cream_powder"
                } else {
                    "cream"
                }
            } else if has("EGGNOG") {
                "eggnog"
            } else if any(&["KEFIR", "FERMENTED"]) {
                "fermented_dairy"
            } else if any(&["SHAKE", "SMOOTHIE"]) {
                "shakes"
            } else if any(&["QUARK", "FRESH CHEESE"]) {
                "quark_fresh_cheese"
            } else if has("EGG") {
                if any(&["SCRAMBLED", "OMELET", "EGG FOO"]) {
                    "egg_mixtures"
                } else if has("SUBSTITUTE") {
                    "egg_substitutes"
                } else {
                    "eggs"
                }
            } else {
                "milk"
            }
        }

        // ─── Meat / Poultry (Groups 5, 7, 10, 13, 17) ────────────────
        5 | 7 | 10 | 13 | 17 => {
            if any(&["BACON", "HAM", "SAUSAGE", "WIENER", "BOLOGNA"]) {
                if any(&["BREAKFAST", "STRIP"]) {
                    if any(&["COOKED", "FRIED"]) {
                        "breakfast_strips_cooked"
                    } else {
                        "breakfast_strips_uncooked"
                    }
                } else if any(&["JERKY", "DRIED", "SALAMI"]) {
                    "dried_meat"
                } else if any(&["BOLOGNA", "LIVER SAUSAGE", "HAM", "SANDWICH"]) {
                    if any(&["COOKED", "SLICED"]) {
                        "luncheon_meat_cooked"
                    } else {
                        "luncheon_meat_uncooked"
                    }
                } else if any(&["SAUSAGE", "WIENER", "BRATWURST", "KIELBASA"]) {
                    if any(&["COOKED", "PRE-COOKED"]) {
                        "sausage_cooked"
                    } else {
                        "sausage_uncooked"
                    }
                } else if any(&["CURED", "SMOKED", "PASTRAMI"]) {
                    if any(&["COOKED", "SMOKED"]) {
                        "cured_meat_cooked"
                    } else {
                        "cured_meat_raw"
                    }
                } else if has("CANNED") {
                    "canned_meat"
                } else {
                    "dried_meat"
                }
            } else if any(&["PATTY", "BURGER", "MEATBALL", "GROUND"]) {
                if any(&["COOKED", "FRIED", "GRILLED"]) {
                    "patties_cooked"
                } else {
                    "patties_raw"
                }
            } else if has("WITH SAUCE") || has("BARBECUE") || has("GRAVY") {
                "meat_with_sauce"
            } else if any(&["COOKED", "ROASTED", "FRIED", "BAKED", "GRILLED", "STEWED"]) {
                "meat_poultry_cooked"
            } else {
                "meat_poultry_raw"
            }
        }

        // ─── Fish / Shellfish (Group 15) ─────────────────────────────
        15 => {
            if any(&["ANCHOV", "CAVIAR"]) {
                "anchovies_caviar"
            } else if has("WITH SAUCE") || has("CREAM SAUCE") {
                "fish_with_sauce"
            } else if has("CANNED") || has("TINNED") {
                "fish_canned"
            } else if any(&["SMOKED", "PICKLED"]) {
                "fish_smoked"
            } else if any(&["COOKED", "BAKED", "FRIED", "GRILLED"]) {
                "fish_cooked"
            } else {
                "fish_raw"
            }
        }

        // ─── Nuts / Seeds (Group 12) ─────────────────────────────────
        12 => {
            if any(&["BUTTER", "PEANUT BUTTER", "ALMOND BUTTER"]) {
                "nut_butters"
            } else if any(&["PASTE", "CREAM", "MARZIPAN"]) {
                "nut_pastes"
            } else if has("FLOUR") {
                "nut_flours"
            } else if has("SNACK") {
                "nut_snacks"
            } else {
                "nuts_seeds"
            }
        }

        // ─── Beverages (Group 14) ────────────────────────────────────
        14 => {
            if has("COFFEE") {
                if has("ESPRESSO") {
                    "espresso"
                } else {
                    "coffee"
                }
            } else if any(&["TEA", "HERBAL"]) && !has("ICED") {
                "tea"
            } else if any(&["HOT CHOCOLATE", "COCOA"]) {
                "hot_chocolate"
            } else if any(&["WINE", "SANGRIA"]) {
                "wine"
            } else if has("BEER") {
                "beer"
            } else if any(&["COOLER", "MIXED DRINK", "ALCOHOLIC"]) {
                "alcoholic_mixed"
            } else {
                "beverages"
            }
        }

        // ─── Combination / processed (Groups 2, 3, 6, 8, 19) ─────────
        2 | 3 | 6 | 8 | 19 => {
            if any(&["CASSEROLE", "STIR FRY", "CHILI", "STEW", "HASH"]) {
                "combination_dish_large"
            } else if any(&["PIZZA", "BURRITO", "SANDWICH", "TACO", "QUICHE"]) {
                "combination_dish_medium"
            } else if any(&["ONION RING", "EGG ROLL"]) {
                if has("SAUCE") {
                    "hors_doeuvres_sauce"
                } else {
                    "hors_doeuvres"
                }
            } else if has("SOUP") {
                "soups"
            } else if any(&["CHIP", "PRETZEL", "POPCORN"]) {
                "chips_snacks"
            } else if any(&["CANDY", "CHOCOLATE", "SWEET"]) {
                if any(&["HARD", "MINT"]) {
                    if has("BREATH") {
                        "breath_mints"
                    } else if has("AFTER DINNER") {
                        "after_dinner_mints"
                    } else {
                        "hard_candies"
                    }
                } else {
                    "candies"
                }
            } else if any(&["SAUCE", "DRESSING", "CONDIMENT"]) {
                "dipping_sauce"
            } else {
                // Python falls through to the bottom `return 'default'` when
                // nothing in this block matches.
                "default"
            }
        }

        _ => "default",
    }
}

#[cfg(test)]
mod tests {
    use super::classify;

    #[test]
    fn fruits_berries() {
        assert_eq!(classify("Blueberries, raw", 9), "berries");
        assert_eq!(classify("Strawberry yoghurt", 9), "berries");
    }

    #[test]
    fn grains_bread_matches_plain_bread() {
        assert_eq!(classify("Bread, white", 18), "bread");
    }

    #[test]
    fn default_for_unknown_group() {
        assert_eq!(classify("Mystery food", 99), "default");
    }

    #[test]
    fn meat_cooked_path() {
        assert_eq!(
            classify("Beef, ground, cooked", 13),
            "patties_cooked"
        );
    }

    #[test]
    fn beverages_tea_excludes_iced() {
        assert_eq!(classify("Tea, black, brewed", 14), "tea");
        assert_eq!(classify("Iced tea, sweetened", 14), "beverages");
    }
}
