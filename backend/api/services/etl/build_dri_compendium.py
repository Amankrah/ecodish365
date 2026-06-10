"""Build the Health Canada / IOM DRI compendium for the research deep-dive.

Generates two artefacts:

1. `backend/api/data/dri_compendium.json`: canonical lookup table keyed by
   CNF NutrientID. Each nutrient carries one cell per life-stage code with
   EAR / RDA / AI / UL values in the same unit the CNF nutrient registry
   already uses.
2. `backend/api/data/dri_compendium_manifest.csv`: per-cell provenance
   manifest. Each row pairs a (nutrient_id, life_stage, reference_type)
   triple with the published IOM / NASEM table citation a reviewer can
   look up directly.

Primary sources:
  * Institute of Medicine (IOM), Dietary Reference Intakes (DRI) series
    1997-2011 (calcium and phosphorus 1997; B-complex 1998; vitamins C/E
    and selenium 2000; vitamin A, K, B6, B12, folate, choline and trace
    minerals 2001; energy / macronutrients 2005; calcium and vitamin D
    2011). National Academies Press, Washington DC.
  * National Academies of Sciences, Engineering, and Medicine (NASEM).
    Dietary Reference Intakes for Sodium and Potassium. National
    Academies Press, Washington DC, 2019.
  * Health Canada. Dietary Reference Intakes - reference tables, updated
    2023. Government of Canada, Ottawa.

Adult life-stage cells (males and females 19-30, 31-50, 51-70, 71+) and
the pregnant / lactating cells (19-30, 31-50) are populated from the
published IOM / NASEM tables. Child and infant life-stage cells ship with
`status='pending_curation'` and null values; the loader returns None for
those cells so the deep-dive endpoint gracefully reports "no DRI on file"
rather than imputing a wrong value. The child / infant cells can be
populated in a separate curation pass without touching the loader or the
endpoint contract.

Units. Every DRI value is stored in the same unit the CNF nutrient
registry uses for the same NutrientID, so the percent-of-DRI division
needs no per-call unit conversion. The compendium loader checks the unit
field on first call and raises if a CNF nutrient unit ever diverges
from the compendium unit (a defensive guard against silent table drift).

Run from `backend/`:
    python -m api.services.etl.build_dri_compendium
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_OUT_DIR = Path(__file__).resolve().parent.parent.parent / 'data'
_OUT_JSON = _OUT_DIR / 'dri_compendium.json'
_OUT_MANIFEST = _OUT_DIR / 'dri_compendium_manifest.csv'


# Life-stage code registry. Adult codes carry full DRI cells; child and
# infant codes ship with null cells until a curation pass fills them.
LIFE_STAGES: Dict[str, Dict[str, Any]] = {
    'infants_0_6m':       {'label': 'Infants, 0-6 months',     'age_min':  0.0, 'age_max':  0.5, 'sex': 'either', 'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'infants_7_12m':      {'label': 'Infants, 7-12 months',    'age_min':  0.6, 'age_max':  1.0, 'sex': 'either', 'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'children_1_3y':      {'label': 'Children, 1-3 years',     'age_min':  1.0, 'age_max':  3.9, 'sex': 'either', 'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'children_4_8y':      {'label': 'Children, 4-8 years',     'age_min':  4.0, 'age_max':  8.9, 'sex': 'either', 'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'males_9_13y':        {'label': 'Males, 9-13 years',       'age_min':  9.0, 'age_max': 13.9, 'sex': 'male',   'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'males_14_18y':       {'label': 'Males, 14-18 years',      'age_min': 14.0, 'age_max': 18.9, 'sex': 'male',   'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'males_19_30y':       {'label': 'Males, 19-30 years',      'age_min': 19.0, 'age_max': 30.9, 'sex': 'male',   'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'males_31_50y':       {'label': 'Males, 31-50 years',      'age_min': 31.0, 'age_max': 50.9, 'sex': 'male',   'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'males_51_70y':       {'label': 'Males, 51-70 years',      'age_min': 51.0, 'age_max': 70.9, 'sex': 'male',   'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'males_71plus':       {'label': 'Males, 71+ years',        'age_min': 71.0, 'age_max': 130.0, 'sex': 'male',  'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'females_9_13y':      {'label': 'Females, 9-13 years',     'age_min':  9.0, 'age_max': 13.9, 'sex': 'female', 'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'females_14_18y':     {'label': 'Females, 14-18 years',    'age_min': 14.0, 'age_max': 18.9, 'sex': 'female', 'pregnancy': False, 'lactation': False, 'status': 'pending_curation'},
    'females_19_30y':     {'label': 'Females, 19-30 years',    'age_min': 19.0, 'age_max': 30.9, 'sex': 'female', 'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'females_31_50y':     {'label': 'Females, 31-50 years',    'age_min': 31.0, 'age_max': 50.9, 'sex': 'female', 'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'females_51_70y':     {'label': 'Females, 51-70 years',    'age_min': 51.0, 'age_max': 70.9, 'sex': 'female', 'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'females_71plus':     {'label': 'Females, 71+ years',      'age_min': 71.0, 'age_max': 130.0, 'sex': 'female', 'pregnancy': False, 'lactation': False, 'status': 'populated'},
    'pregnant_19_30y':    {'label': 'Pregnant, 19-30 years',   'age_min': 19.0, 'age_max': 30.9, 'sex': 'female', 'pregnancy': True,  'lactation': False, 'status': 'populated'},
    'pregnant_31_50y':    {'label': 'Pregnant, 31-50 years',   'age_min': 31.0, 'age_max': 50.9, 'sex': 'female', 'pregnancy': True,  'lactation': False, 'status': 'populated'},
    'lactating_19_30y':   {'label': 'Lactating, 19-30 years',  'age_min': 19.0, 'age_max': 30.9, 'sex': 'female', 'pregnancy': False, 'lactation': True,  'status': 'populated'},
    'lactating_31_50y':   {'label': 'Lactating, 31-50 years',  'age_min': 31.0, 'age_max': 50.9, 'sex': 'female', 'pregnancy': False, 'lactation': True,  'status': 'populated'},
}


# Adult life-stage codes the DRI cell tables below cover. Curation-pending
# stages get every cell stamped null with status='pending_curation' downstream.
_ADULT_CODES = (
    'males_19_30y', 'males_31_50y', 'males_51_70y', 'males_71plus',
    'females_19_30y', 'females_31_50y', 'females_51_70y', 'females_71plus',
    'pregnant_19_30y', 'pregnant_31_50y',
    'lactating_19_30y', 'lactating_31_50y',
)


# DRI cell tables. Per nutrient, per adult life-stage, per reference type.
# Values are in the unit named alongside the NutrientID; the loader
# verifies the unit against the CNF nutrient registry on first call.
#
# Cell tuple: (EAR, RDA, AI, UL). Null values mean "not published": the
# loader returns None for any null cell so a downstream caller never
# fabricates a percent-of-DRI from a missing reference value.
#
# All citations to IOM / NASEM tables are recorded in the manifest CSV
# emitted by this ETL alongside the JSON.

# Standard convention: M = males, F = females, P = pregnant, L = lactating.

# CARBOHYDRATE (NutrientID 205): IOM 2005 Ch 6, Table 6-2 p. 275
_CARB: Dict[str, Tuple] = {
    'males_19_30y':     (100, 130, None, None),
    'males_31_50y':     (100, 130, None, None),
    'males_51_70y':     (100, 130, None, None),
    'males_71plus':     (100, 130, None, None),
    'females_19_30y':   (100, 130, None, None),
    'females_31_50y':   (100, 130, None, None),
    'females_51_70y':   (100, 130, None, None),
    'females_71plus':   (100, 130, None, None),
    'pregnant_19_30y':  (135, 175, None, None),
    'pregnant_31_50y':  (135, 175, None, None),
    'lactating_19_30y': (160, 210, None, None),
    'lactating_31_50y': (160, 210, None, None),
}

# PROTEIN (NutrientID 203): IOM 2005 Ch 10, Table 10-13 p. 685
# Reference body weights: 70 kg M, 57 kg F (IOM 2005 Table 1-1).
_PROTEIN: Dict[str, Tuple] = {
    'males_19_30y':     (46, 56, None, None),
    'males_31_50y':     (46, 56, None, None),
    'males_51_70y':     (46, 56, None, None),
    'males_71plus':     (46, 56, None, None),
    'females_19_30y':   (38, 46, None, None),
    'females_31_50y':   (38, 46, None, None),
    'females_51_70y':   (38, 46, None, None),
    'females_71plus':   (38, 46, None, None),
    'pregnant_19_30y':  (50, 71, None, None),
    'pregnant_31_50y':  (50, 71, None, None),
    'lactating_19_30y': (60, 71, None, None),
    'lactating_31_50y': (60, 71, None, None),
}

# FIBRE, TOTAL DIETARY (NutrientID 291): IOM 2005 Ch 7, Table 7-4 p. 380
_FIBER: Dict[str, Tuple] = {
    'males_19_30y':     (None, None, 38, None),
    'males_31_50y':     (None, None, 38, None),
    'males_51_70y':     (None, None, 30, None),
    'males_71plus':     (None, None, 30, None),
    'females_19_30y':   (None, None, 25, None),
    'females_31_50y':   (None, None, 25, None),
    'females_51_70y':   (None, None, 21, None),
    'females_71plus':   (None, None, 21, None),
    'pregnant_19_30y':  (None, None, 28, None),
    'pregnant_31_50y':  (None, None, 28, None),
    'lactating_19_30y': (None, None, 29, None),
    'lactating_31_50y': (None, None, 29, None),
}

# CALCIUM (NutrientID 301, mg): IOM 2011 Tables S-3 and S-5
_CALCIUM: Dict[str, Tuple] = {
    'males_19_30y':     (800, 1000, None, 2500),
    'males_31_50y':     (800, 1000, None, 2500),
    'males_51_70y':     (800, 1000, None, 2000),
    'males_71plus':     (1000, 1200, None, 2000),
    'females_19_30y':   (800, 1000, None, 2500),
    'females_31_50y':   (800, 1000, None, 2500),
    'females_51_70y':   (1000, 1200, None, 2000),
    'females_71plus':   (1000, 1200, None, 2000),
    'pregnant_19_30y':  (800, 1000, None, 2500),
    'pregnant_31_50y':  (800, 1000, None, 2500),
    'lactating_19_30y': (800, 1000, None, 2500),
    'lactating_31_50y': (800, 1000, None, 2500),
}

# IRON (NutrientID 303, mg): IOM 2001 Table S-7
_IRON: Dict[str, Tuple] = {
    'males_19_30y':     (6, 8, None, 45),
    'males_31_50y':     (6, 8, None, 45),
    'males_51_70y':     (6, 8, None, 45),
    'males_71plus':     (6, 8, None, 45),
    'females_19_30y':   (8.1, 18, None, 45),
    'females_31_50y':   (8.1, 18, None, 45),
    'females_51_70y':   (5, 8, None, 45),
    'females_71plus':   (5, 8, None, 45),
    'pregnant_19_30y':  (22, 27, None, 45),
    'pregnant_31_50y':  (22, 27, None, 45),
    'lactating_19_30y': (6.5, 9, None, 45),
    'lactating_31_50y': (6.5, 9, None, 45),
}

# MAGNESIUM (NutrientID 304, mg): IOM 1997 Table S-3 (UL applies to
# supplemental Mg only; we expose it as the published UL)
_MAGNESIUM: Dict[str, Tuple] = {
    'males_19_30y':     (330, 400, None, 350),
    'males_31_50y':     (350, 420, None, 350),
    'males_51_70y':     (350, 420, None, 350),
    'males_71plus':     (350, 420, None, 350),
    'females_19_30y':   (255, 310, None, 350),
    'females_31_50y':   (265, 320, None, 350),
    'females_51_70y':   (265, 320, None, 350),
    'females_71plus':   (265, 320, None, 350),
    'pregnant_19_30y':  (290, 350, None, 350),
    'pregnant_31_50y':  (300, 360, None, 350),
    'lactating_19_30y': (300, 310, None, 350),
    'lactating_31_50y': (310, 320, None, 350),
}

# PHOSPHORUS (NutrientID 305, mg): IOM 1997 Table S-2
_PHOSPHORUS: Dict[str, Tuple] = {
    'males_19_30y':     (580, 700, None, 4000),
    'males_31_50y':     (580, 700, None, 4000),
    'males_51_70y':     (580, 700, None, 4000),
    'males_71plus':     (580, 700, None, 3000),
    'females_19_30y':   (580, 700, None, 4000),
    'females_31_50y':   (580, 700, None, 4000),
    'females_51_70y':   (580, 700, None, 4000),
    'females_71plus':   (580, 700, None, 3000),
    'pregnant_19_30y':  (580, 700, None, 3500),
    'pregnant_31_50y':  (580, 700, None, 3500),
    'lactating_19_30y': (580, 700, None, 4000),
    'lactating_31_50y': (580, 700, None, 4000),
}

# POTASSIUM (NutrientID 306, mg): NASEM 2019 Table S-3 (AI only; no EAR/RDA/UL)
_POTASSIUM: Dict[str, Tuple] = {
    'males_19_30y':     (None, None, 3400, None),
    'males_31_50y':     (None, None, 3400, None),
    'males_51_70y':     (None, None, 3400, None),
    'males_71plus':     (None, None, 3400, None),
    'females_19_30y':   (None, None, 2600, None),
    'females_31_50y':   (None, None, 2600, None),
    'females_51_70y':   (None, None, 2600, None),
    'females_71plus':   (None, None, 2600, None),
    'pregnant_19_30y':  (None, None, 2900, None),
    'pregnant_31_50y':  (None, None, 2900, None),
    'lactating_19_30y': (None, None, 2800, None),
    'lactating_31_50y': (None, None, 2800, None),
}

# SODIUM (NutrientID 307, mg): NASEM 2019 Tables S-3, S-5 (AI only; CDRR at 2300 mg/d
# replaces the prior UL conceptually but is not stored here as UL because the
# percent-of-UL semantics do not match CDRR semantics; the deep-dive surfaces it as
# a separate CDRR flag at the endpoint layer)
_SODIUM: Dict[str, Tuple] = {
    'males_19_30y':     (None, None, 1500, None),
    'males_31_50y':     (None, None, 1500, None),
    'males_51_70y':     (None, None, 1500, None),
    'males_71plus':     (None, None, 1500, None),
    'females_19_30y':   (None, None, 1500, None),
    'females_31_50y':   (None, None, 1500, None),
    'females_51_70y':   (None, None, 1500, None),
    'females_71plus':   (None, None, 1500, None),
    'pregnant_19_30y':  (None, None, 1500, None),
    'pregnant_31_50y':  (None, None, 1500, None),
    'lactating_19_30y': (None, None, 1500, None),
    'lactating_31_50y': (None, None, 1500, None),
}

# ZINC (NutrientID 309, mg): IOM 2001 Table S-9
_ZINC: Dict[str, Tuple] = {
    'males_19_30y':     (9.4, 11, None, 40),
    'males_31_50y':     (9.4, 11, None, 40),
    'males_51_70y':     (9.4, 11, None, 40),
    'males_71plus':     (9.4, 11, None, 40),
    'females_19_30y':   (6.8, 8, None, 40),
    'females_31_50y':   (6.8, 8, None, 40),
    'females_51_70y':   (6.8, 8, None, 40),
    'females_71plus':   (6.8, 8, None, 40),
    'pregnant_19_30y':  (9.5, 11, None, 40),
    'pregnant_31_50y':  (9.5, 11, None, 40),
    'lactating_19_30y': (10.4, 12, None, 40),
    'lactating_31_50y': (10.4, 12, None, 40),
}

# COPPER (NutrientID 312, mcg): IOM 2001 Table S-9
_COPPER: Dict[str, Tuple] = {
    'males_19_30y':     (700, 900, None, 10000),
    'males_31_50y':     (700, 900, None, 10000),
    'males_51_70y':     (700, 900, None, 10000),
    'males_71plus':     (700, 900, None, 10000),
    'females_19_30y':   (700, 900, None, 10000),
    'females_31_50y':   (700, 900, None, 10000),
    'females_51_70y':   (700, 900, None, 10000),
    'females_71plus':   (700, 900, None, 10000),
    'pregnant_19_30y':  (800, 1000, None, 10000),
    'pregnant_31_50y':  (800, 1000, None, 10000),
    'lactating_19_30y': (1000, 1300, None, 10000),
    'lactating_31_50y': (1000, 1300, None, 10000),
}

# MANGANESE (NutrientID 315, mg): IOM 2001 Table S-9 (AI + UL)
_MANGANESE: Dict[str, Tuple] = {
    'males_19_30y':     (None, None, 2.3, 11),
    'males_31_50y':     (None, None, 2.3, 11),
    'males_51_70y':     (None, None, 2.3, 11),
    'males_71plus':     (None, None, 2.3, 11),
    'females_19_30y':   (None, None, 1.8, 11),
    'females_31_50y':   (None, None, 1.8, 11),
    'females_51_70y':   (None, None, 1.8, 11),
    'females_71plus':   (None, None, 1.8, 11),
    'pregnant_19_30y':  (None, None, 2.0, 11),
    'pregnant_31_50y':  (None, None, 2.0, 11),
    'lactating_19_30y': (None, None, 2.6, 11),
    'lactating_31_50y': (None, None, 2.6, 11),
}

# SELENIUM (NutrientID 317, mcg): IOM 2000 Table S-3
_SELENIUM: Dict[str, Tuple] = {
    'males_19_30y':     (45, 55, None, 400),
    'males_31_50y':     (45, 55, None, 400),
    'males_51_70y':     (45, 55, None, 400),
    'males_71plus':     (45, 55, None, 400),
    'females_19_30y':   (45, 55, None, 400),
    'females_31_50y':   (45, 55, None, 400),
    'females_51_70y':   (45, 55, None, 400),
    'females_71plus':   (45, 55, None, 400),
    'pregnant_19_30y':  (49, 60, None, 400),
    'pregnant_31_50y':  (49, 60, None, 400),
    'lactating_19_30y': (59, 70, None, 400),
    'lactating_31_50y': (59, 70, None, 400),
}

# VITAMIN A RAE (NutrientID 320, mcg RAE): IOM 2001 Table S-9
_VIT_A: Dict[str, Tuple] = {
    'males_19_30y':     (625, 900, None, 3000),
    'males_31_50y':     (625, 900, None, 3000),
    'males_51_70y':     (625, 900, None, 3000),
    'males_71plus':     (625, 900, None, 3000),
    'females_19_30y':   (500, 700, None, 3000),
    'females_31_50y':   (500, 700, None, 3000),
    'females_51_70y':   (500, 700, None, 3000),
    'females_71plus':   (500, 700, None, 3000),
    'pregnant_19_30y':  (550, 770, None, 3000),
    'pregnant_31_50y':  (550, 770, None, 3000),
    'lactating_19_30y': (900, 1300, None, 3000),
    'lactating_31_50y': (900, 1300, None, 3000),
}

# VITAMIN E (NutrientID 323, mg alpha-tocopherol): IOM 2000 Table S-3
_VIT_E: Dict[str, Tuple] = {
    'males_19_30y':     (12, 15, None, 1000),
    'males_31_50y':     (12, 15, None, 1000),
    'males_51_70y':     (12, 15, None, 1000),
    'males_71plus':     (12, 15, None, 1000),
    'females_19_30y':   (12, 15, None, 1000),
    'females_31_50y':   (12, 15, None, 1000),
    'females_51_70y':   (12, 15, None, 1000),
    'females_71plus':   (12, 15, None, 1000),
    'pregnant_19_30y':  (12, 15, None, 1000),
    'pregnant_31_50y':  (12, 15, None, 1000),
    'lactating_19_30y': (16, 19, None, 1000),
    'lactating_31_50y': (16, 19, None, 1000),
}

# VITAMIN D (NutrientID 328, mcg): IOM 2011 Tables S-3, S-5
_VIT_D: Dict[str, Tuple] = {
    'males_19_30y':     (10, 15, None, 100),
    'males_31_50y':     (10, 15, None, 100),
    'males_51_70y':     (10, 15, None, 100),
    'males_71plus':     (10, 20, None, 100),
    'females_19_30y':   (10, 15, None, 100),
    'females_31_50y':   (10, 15, None, 100),
    'females_51_70y':   (10, 15, None, 100),
    'females_71plus':   (10, 20, None, 100),
    'pregnant_19_30y':  (10, 15, None, 100),
    'pregnant_31_50y':  (10, 15, None, 100),
    'lactating_19_30y': (10, 15, None, 100),
    'lactating_31_50y': (10, 15, None, 100),
}

# VITAMIN K (NutrientID 430, mcg): IOM 2001 Table S-9 (AI only)
_VIT_K: Dict[str, Tuple] = {
    'males_19_30y':     (None, None, 120, None),
    'males_31_50y':     (None, None, 120, None),
    'males_51_70y':     (None, None, 120, None),
    'males_71plus':     (None, None, 120, None),
    'females_19_30y':   (None, None, 90, None),
    'females_31_50y':   (None, None, 90, None),
    'females_51_70y':   (None, None, 90, None),
    'females_71plus':   (None, None, 90, None),
    'pregnant_19_30y':  (None, None, 90, None),
    'pregnant_31_50y':  (None, None, 90, None),
    'lactating_19_30y': (None, None, 90, None),
    'lactating_31_50y': (None, None, 90, None),
}

# VITAMIN C (NutrientID 401, mg): IOM 2000 Table S-3
_VIT_C: Dict[str, Tuple] = {
    'males_19_30y':     (75, 90, None, 2000),
    'males_31_50y':     (75, 90, None, 2000),
    'males_51_70y':     (75, 90, None, 2000),
    'males_71plus':     (75, 90, None, 2000),
    'females_19_30y':   (60, 75, None, 2000),
    'females_31_50y':   (60, 75, None, 2000),
    'females_51_70y':   (60, 75, None, 2000),
    'females_71plus':   (60, 75, None, 2000),
    'pregnant_19_30y':  (70, 85, None, 2000),
    'pregnant_31_50y':  (70, 85, None, 2000),
    'lactating_19_30y': (100, 120, None, 2000),
    'lactating_31_50y': (100, 120, None, 2000),
}

# THIAMIN (B1) (NutrientID 404, mg): IOM 1998 Table S-3
_THIAMIN: Dict[str, Tuple] = {
    'males_19_30y':     (1.0, 1.2, None, None),
    'males_31_50y':     (1.0, 1.2, None, None),
    'males_51_70y':     (1.0, 1.2, None, None),
    'males_71plus':     (1.0, 1.2, None, None),
    'females_19_30y':   (0.9, 1.1, None, None),
    'females_31_50y':   (0.9, 1.1, None, None),
    'females_51_70y':   (0.9, 1.1, None, None),
    'females_71plus':   (0.9, 1.1, None, None),
    'pregnant_19_30y':  (1.2, 1.4, None, None),
    'pregnant_31_50y':  (1.2, 1.4, None, None),
    'lactating_19_30y': (1.2, 1.4, None, None),
    'lactating_31_50y': (1.2, 1.4, None, None),
}

# RIBOFLAVIN (B2) (NutrientID 405, mg): IOM 1998 Table S-3
_RIBOFLAVIN: Dict[str, Tuple] = {
    'males_19_30y':     (1.1, 1.3, None, None),
    'males_31_50y':     (1.1, 1.3, None, None),
    'males_51_70y':     (1.1, 1.3, None, None),
    'males_71plus':     (1.1, 1.3, None, None),
    'females_19_30y':   (0.9, 1.1, None, None),
    'females_31_50y':   (0.9, 1.1, None, None),
    'females_51_70y':   (0.9, 1.1, None, None),
    'females_71plus':   (0.9, 1.1, None, None),
    'pregnant_19_30y':  (1.2, 1.4, None, None),
    'pregnant_31_50y':  (1.2, 1.4, None, None),
    'lactating_19_30y': (1.3, 1.6, None, None),
    'lactating_31_50y': (1.3, 1.6, None, None),
}

# NIACIN (NutrientID 406, mg NE): IOM 1998 Table S-3
_NIACIN: Dict[str, Tuple] = {
    'males_19_30y':     (12, 16, None, 35),
    'males_31_50y':     (12, 16, None, 35),
    'males_51_70y':     (12, 16, None, 35),
    'males_71plus':     (12, 16, None, 35),
    'females_19_30y':   (11, 14, None, 35),
    'females_31_50y':   (11, 14, None, 35),
    'females_51_70y':   (11, 14, None, 35),
    'females_71plus':   (11, 14, None, 35),
    'pregnant_19_30y':  (14, 18, None, 35),
    'pregnant_31_50y':  (14, 18, None, 35),
    'lactating_19_30y': (13, 17, None, 35),
    'lactating_31_50y': (13, 17, None, 35),
}

# PANTOTHENIC ACID (NutrientID 410, mg): IOM 1998 Table S-3 (AI only)
_PANTOTHENIC: Dict[str, Tuple] = {
    'males_19_30y':     (None, None, 5, None),
    'males_31_50y':     (None, None, 5, None),
    'males_51_70y':     (None, None, 5, None),
    'males_71plus':     (None, None, 5, None),
    'females_19_30y':   (None, None, 5, None),
    'females_31_50y':   (None, None, 5, None),
    'females_51_70y':   (None, None, 5, None),
    'females_71plus':   (None, None, 5, None),
    'pregnant_19_30y':  (None, None, 6, None),
    'pregnant_31_50y':  (None, None, 6, None),
    'lactating_19_30y': (None, None, 7, None),
    'lactating_31_50y': (None, None, 7, None),
}

# VITAMIN B6 (NutrientID 415, mg): IOM 1998 Table S-3
_VIT_B6: Dict[str, Tuple] = {
    'males_19_30y':     (1.1, 1.3, None, 100),
    'males_31_50y':     (1.1, 1.3, None, 100),
    'males_51_70y':     (1.4, 1.7, None, 100),
    'males_71plus':     (1.4, 1.7, None, 100),
    'females_19_30y':   (1.1, 1.3, None, 100),
    'females_31_50y':   (1.1, 1.3, None, 100),
    'females_51_70y':   (1.3, 1.5, None, 100),
    'females_71plus':   (1.3, 1.5, None, 100),
    'pregnant_19_30y':  (1.6, 1.9, None, 100),
    'pregnant_31_50y':  (1.6, 1.9, None, 100),
    'lactating_19_30y': (1.7, 2.0, None, 100),
    'lactating_31_50y': (1.7, 2.0, None, 100),
}

# VITAMIN B12 (NutrientID 418, mcg): IOM 1998 Table S-3
_VIT_B12: Dict[str, Tuple] = {
    'males_19_30y':     (2.0, 2.4, None, None),
    'males_31_50y':     (2.0, 2.4, None, None),
    'males_51_70y':     (2.0, 2.4, None, None),
    'males_71plus':     (2.0, 2.4, None, None),
    'females_19_30y':   (2.0, 2.4, None, None),
    'females_31_50y':   (2.0, 2.4, None, None),
    'females_51_70y':   (2.0, 2.4, None, None),
    'females_71plus':   (2.0, 2.4, None, None),
    'pregnant_19_30y':  (2.2, 2.6, None, None),
    'pregnant_31_50y':  (2.2, 2.6, None, None),
    'lactating_19_30y': (2.4, 2.8, None, None),
    'lactating_31_50y': (2.4, 2.8, None, None),
}

# CHOLINE (NutrientID 421, mg): IOM 1998 Table S-3 (AI + UL)
_CHOLINE: Dict[str, Tuple] = {
    'males_19_30y':     (None, None, 550, 3500),
    'males_31_50y':     (None, None, 550, 3500),
    'males_51_70y':     (None, None, 550, 3500),
    'males_71plus':     (None, None, 550, 3500),
    'females_19_30y':   (None, None, 425, 3500),
    'females_31_50y':   (None, None, 425, 3500),
    'females_51_70y':   (None, None, 425, 3500),
    'females_71plus':   (None, None, 425, 3500),
    'pregnant_19_30y':  (None, None, 450, 3500),
    'pregnant_31_50y':  (None, None, 450, 3500),
    'lactating_19_30y': (None, None, 550, 3500),
    'lactating_31_50y': (None, None, 550, 3500),
}

# FOLATE DFE (NutrientID 435, mcg DFE): IOM 1998 Table S-3
_FOLATE: Dict[str, Tuple] = {
    'males_19_30y':     (320, 400, None, 1000),
    'males_31_50y':     (320, 400, None, 1000),
    'males_51_70y':     (320, 400, None, 1000),
    'males_71plus':     (320, 400, None, 1000),
    'females_19_30y':   (320, 400, None, 1000),
    'females_31_50y':   (320, 400, None, 1000),
    'females_51_70y':   (320, 400, None, 1000),
    'females_71plus':   (320, 400, None, 1000),
    'pregnant_19_30y':  (520, 600, None, 1000),
    'pregnant_31_50y':  (520, 600, None, 1000),
    'lactating_19_30y': (450, 500, None, 1000),
    'lactating_31_50y': (450, 500, None, 1000),
}


# Master nutrient registry: NutrientID -> (display name, unit, AMDR pct-kcal range or None, cell table)
NUTRIENT_REGISTRY: List[Tuple[int, str, str, Optional[Tuple[int, int]], Dict[str, Tuple]]] = [
    (203, 'PROTEIN', 'Gram', (10, 35), _PROTEIN),
    (205, 'CARBOHYDRATE, TOTAL (BY DIFFERENCE)', 'Gram', (45, 65), _CARB),
    (291, 'FIBRE, TOTAL DIETARY', 'Gram', None, _FIBER),
    (301, 'CALCIUM', 'Milligram', None, _CALCIUM),
    (303, 'IRON', 'Milligram', None, _IRON),
    (304, 'MAGNESIUM', 'Milligram', None, _MAGNESIUM),
    (305, 'PHOSPHORUS', 'Milligram', None, _PHOSPHORUS),
    (306, 'POTASSIUM', 'Milligram', None, _POTASSIUM),
    (307, 'SODIUM', 'Milligram', None, _SODIUM),
    (309, 'ZINC', 'Milligram', None, _ZINC),
    (312, 'COPPER', 'Microgram', None, _COPPER),
    (315, 'MANGANESE', 'Milligram', None, _MANGANESE),
    (317, 'SELENIUM', 'Microgram', None, _SELENIUM),
    (320, 'RETINOL ACTIVITY EQUIVALENTS (RAE)', 'Microgram', None, _VIT_A),
    (323, 'ALPHA-TOCOPHEROL', 'Milligram', None, _VIT_E),
    (328, 'VITAMIN D (D2 + D3)', 'Microgram', None, _VIT_D),
    (401, 'VITAMIN C', 'Milligram', None, _VIT_C),
    (404, 'THIAMIN', 'Milligram', None, _THIAMIN),
    (405, 'RIBOFLAVIN', 'Milligram', None, _RIBOFLAVIN),
    (406, 'NIACIN (NIACIN EQUIVALENT NE)', 'NE', None, _NIACIN),
    (410, 'PANTOTHENIC ACID', 'Milligram', None, _PANTOTHENIC),
    (415, 'VITAMIN B6', 'Milligram', None, _VIT_B6),
    (418, 'VITAMIN B12', 'Microgram', None, _VIT_B12),
    (421, 'CHOLINE, TOTAL', 'Milligram', None, _CHOLINE),
    (430, 'VITAMIN K', 'Microgram', None, _VIT_K),
    (435, 'FOLATE, DFE', 'Microgram', None, _FOLATE),
]


# Top-level AMDR ranges (not per-nutrient cells; macronutrient-pct-of-kcal).
# IOM 2005 Table S-1 p. 22.
ADULT_AMDR_RANGES: Dict[str, Dict[str, float]] = {
    'carbohydrate': {'pct_kcal_min': 45.0, 'pct_kcal_max': 65.0},
    'protein':      {'pct_kcal_min': 10.0, 'pct_kcal_max': 35.0},
    'fat':          {'pct_kcal_min': 20.0, 'pct_kcal_max': 35.0},
    'linoleic_acid':           {'pct_kcal_min': 5.0,  'pct_kcal_max': 10.0},
    'alpha_linolenic_acid':    {'pct_kcal_min': 0.6,  'pct_kcal_max': 1.2},
    'added_sugars_dga_2020':   {'pct_kcal_min': 0.0,  'pct_kcal_max': 10.0},   # DGA 2020-2025
    'saturated_fat_dga_2020':  {'pct_kcal_min': 0.0,  'pct_kcal_max': 10.0},   # DGA 2020-2025
}


# CDRR (chronic disease risk reduction) thresholds. NASEM 2019 set sodium
# CDRR at 2300 mg/d for adults. Stored top-level so the deep-dive can flag
# above-CDRR sodium intake separately from the AI comparison.
CDRR_THRESHOLDS: Dict[int, Dict[str, Any]] = {
    307: {  # SODIUM
        'cdrr_mg_per_day': 2300.0,
        'source': 'NASEM 2019 Sodium and Potassium DRIs, Chapter 7 p. 322.',
        'note': 'Intake above the CDRR is expected to reduce chronic disease risk if reduced; not a tolerable upper limit.',
    },
}


def _cell_to_dict(cell: Tuple) -> Dict[str, Optional[float]]:
    """Convert a (EAR, RDA, AI, UL) tuple to a dict; None preserved."""
    ear, rda, ai, ul = cell
    return {'EAR': ear, 'RDA': rda, 'AI': ai, 'UL': ul}


def _empty_cell() -> Dict[str, Optional[float]]:
    return {'EAR': None, 'RDA': None, 'AI': None, 'UL': None}


def build_compendium() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Construct the JSON payload and the per-cell manifest rows."""
    nutrients_block: Dict[str, Dict[str, Any]] = {}
    manifest_rows: List[Dict[str, Any]] = []

    for nid, name, unit, amdr, cell_table in NUTRIENT_REGISTRY:
        cells: Dict[str, Dict[str, Optional[float]]] = {}
        for ls_code in LIFE_STAGES:
            if ls_code in cell_table:
                cells[ls_code] = _cell_to_dict(cell_table[ls_code])
                manifest_rows.append({
                    'nutrient_id': nid,
                    'nutrient_name': name,
                    'unit': unit,
                    'life_stage': ls_code,
                    'EAR': cells[ls_code]['EAR'],
                    'RDA': cells[ls_code]['RDA'],
                    'AI': cells[ls_code]['AI'],
                    'UL': cells[ls_code]['UL'],
                    'status': 'populated',
                    'source_citation': _source_citation_for(nid),
                })
            else:
                cells[ls_code] = _empty_cell()
                manifest_rows.append({
                    'nutrient_id': nid,
                    'nutrient_name': name,
                    'unit': unit,
                    'life_stage': ls_code,
                    'EAR': None, 'RDA': None, 'AI': None, 'UL': None,
                    'status': 'pending_curation',
                    'source_citation': '',
                })
        nutrients_block[str(nid)] = {
            'nutrient_id': nid,
            'name': name,
            'unit': unit,
            'amdr_pct_kcal': (
                {'pct_kcal_min': float(amdr[0]), 'pct_kcal_max': float(amdr[1])}
                if amdr is not None else None
            ),
            'cdrr': CDRR_THRESHOLDS.get(nid),
            'cells': cells,
        }

    compendium = {
        '_meta': {
            'version': '2026-06-09',
            'description': (
                'IOM / NASEM / Health Canada DRI compendium keyed by CNF '
                'NutrientID. Adult life-stage cells (males / females 19-30, '
                '31-50, 51-70, 71+) plus pregnant / lactating (19-30, 31-50) '
                'are fully populated from the published IOM and NASEM '
                'tables. Child and infant cells ship as null with '
                'status=pending_curation pending a separate curation pass; '
                'the loader returns None for null cells so no false DRI '
                'percent is ever fabricated.'
            ),
            'primary_sources': [
                'IOM 1997 Dietary Reference Intakes for Calcium, Phosphorus, Magnesium, Vitamin D, and Fluoride.',
                'IOM 1998 Dietary Reference Intakes for Thiamin, Riboflavin, Niacin, Vitamin B6, Folate, Vitamin B12, Pantothenic Acid, Biotin, and Choline.',
                'IOM 2000 Dietary Reference Intakes for Vitamin C, Vitamin E, Selenium, and Carotenoids.',
                'IOM 2001 Dietary Reference Intakes for Vitamin A, Vitamin K, Arsenic, Boron, Chromium, Copper, Iodine, Iron, Manganese, Molybdenum, Nickel, Silicon, Vanadium, and Zinc.',
                'IOM 2005 Dietary Reference Intakes for Energy, Carbohydrate, Fiber, Fat, Fatty Acids, Cholesterol, Protein, and Amino Acids.',
                'IOM 2011 Dietary Reference Intakes for Calcium and Vitamin D.',
                'NASEM 2019 Dietary Reference Intakes for Sodium and Potassium.',
                'Health Canada 2023 Dietary Reference Intakes - reference tables.',
            ],
            'reference_types': ['EAR', 'RDA', 'AI', 'UL'],
            'amdr_block': ADULT_AMDR_RANGES,
            'cdrr_block': CDRR_THRESHOLDS,
            'life_stages_populated': list(_ADULT_CODES),
            'life_stages_pending': [c for c in LIFE_STAGES if c not in _ADULT_CODES],
            'nutrient_count': len(NUTRIENT_REGISTRY),
        },
        'life_stages': LIFE_STAGES,
        'nutrients': nutrients_block,
    }
    return compendium, manifest_rows


def _source_citation_for(nid: int) -> str:
    """Return the canonical IOM / NASEM citation for a NutrientID's published
    DRI table. Conservative one-line citation per cell."""
    return {
        203: 'IOM 2005 Table 10-13 p. 685 (protein RDA/EAR by age and sex)',
        205: 'IOM 2005 Table 6-2 p. 275 (carbohydrate EAR/RDA)',
        291: 'IOM 2005 Table 7-4 p. 380 (total fibre AI by age and sex)',
        301: 'IOM 2011 Tables S-3 and S-5 (calcium EAR/RDA/UL)',
        303: 'IOM 2001 Table S-7 (iron EAR/RDA/UL)',
        304: 'IOM 1997 Table S-3 (magnesium EAR/RDA/UL)',
        305: 'IOM 1997 Table S-2 (phosphorus EAR/RDA/UL)',
        306: 'NASEM 2019 Table S-3 (potassium AI)',
        307: 'NASEM 2019 Tables S-3 and S-5 (sodium AI; CDRR at 2300 mg/d)',
        309: 'IOM 2001 Table S-9 (zinc EAR/RDA/UL)',
        312: 'IOM 2001 Table S-9 (copper EAR/RDA/UL)',
        315: 'IOM 2001 Table S-9 (manganese AI/UL)',
        317: 'IOM 2000 Table S-3 (selenium EAR/RDA/UL)',
        320: 'IOM 2001 Table S-9 (vitamin A RAE EAR/RDA/UL)',
        323: 'IOM 2000 Table S-3 (vitamin E alpha-tocopherol EAR/RDA/UL)',
        328: 'IOM 2011 Tables S-3 and S-5 (vitamin D EAR/RDA/UL)',
        401: 'IOM 2000 Table S-3 (vitamin C EAR/RDA/UL)',
        404: 'IOM 1998 Table S-3 (thiamin EAR/RDA)',
        405: 'IOM 1998 Table S-3 (riboflavin EAR/RDA)',
        406: 'IOM 1998 Table S-3 (niacin NE EAR/RDA/UL)',
        410: 'IOM 1998 Table S-3 (pantothenic acid AI)',
        415: 'IOM 1998 Table S-3 (vitamin B6 EAR/RDA/UL)',
        418: 'IOM 1998 Table S-3 (vitamin B12 EAR/RDA)',
        421: 'IOM 1998 Table S-3 (choline AI/UL)',
        430: 'IOM 2001 Table S-9 (vitamin K AI)',
        435: 'IOM 1998 Table S-3 (folate DFE EAR/RDA/UL)',
    }.get(nid, '')


def write_artefacts() -> None:
    compendium, manifest_rows = build_compendium()
    os.makedirs(_OUT_DIR, exist_ok=True)

    with open(_OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(compendium, f, indent=2, sort_keys=False)
    print(f'Wrote {_OUT_JSON}')

    with open(_OUT_MANIFEST, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'nutrient_id', 'nutrient_name', 'unit',
                'life_stage',
                'EAR', 'RDA', 'AI', 'UL',
                'status', 'source_citation',
            ],
        )
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)
    print(f'Wrote {_OUT_MANIFEST}')
    print(
        f'  Nutrients: {len(NUTRIENT_REGISTRY)}; '
        f'life-stages: {len(LIFE_STAGES)} '
        f'({len(_ADULT_CODES)} populated, '
        f'{len(LIFE_STAGES) - len(_ADULT_CODES)} pending curation); '
        f'total cells: {len(manifest_rows)}.'
    )


if __name__ == '__main__':
    write_artefacts()
