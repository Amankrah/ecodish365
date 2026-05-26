import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")
for line in Path(".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import django

django.setup()

from api.services.ingredient_to_cnf_decomposer import decompose_packaged_food
from api.services.multimodal_client import build_multimodal_client
from api.services.packaged_food_extractor import extract_packaged_food
from environmental_impact_model.src.llm_client import build_chat_json_client

raw = Path("packeged_foods_images/image-asset.webp").read_bytes()
mm = build_multimodal_client()
chat = build_chat_json_client()
ex = extract_packaged_food(raw, use_cache=False, client=mm)
e = ex.extraction
print("extraction_succeeded:", e.extraction_succeeded)
print("has_nf_panel:", e.has_nf_panel, "has_ingredient_list:", e.has_ingredient_list)
print("extraction failure_reason:", e.failure_reason)
if e.nf_panel:
    p = e.nf_panel
    print("net_weight_g:", getattr(p, "net_weight_g", None))
    print("serving_size_g:", getattr(p, "serving_size_g", None))
    print("net_weight_text:", getattr(p, "net_weight_text", None))
if e.ingredient_list:
    ing = e.ingredient_list
    print("ingredients_parsed count:", len(ing.ingredients_parsed or []))
    print("ingredients_text preview:", (ing.ingredients_text or "")[:300])
if e.nf_panel and e.ingredient_list and e.ingredient_list.ingredients_parsed:
    dec = decompose_packaged_food(e.nf_panel, e.ingredient_list, chat_client=chat)
    print("decomposition_succeeded:", dec.decomposition_succeeded)
    print("decomposition failure_reason:", dec.failure_reason)
    print("ingredients:", len(dec.ingredients))
    print("confidence:", dec.decomposition_confidence)
else:
    print("SKIP decompose: missing panel, ingredients, or parsed list")
