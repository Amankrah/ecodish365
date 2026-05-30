"""Regex-based preparation-state extractor for CNF FoodDescription strings.

Returns a two-axis tag aligned with the prep-state lab plan:
  - thermal_state: raw | boiled | fried | baked | roasted | stewed | grilled |
                   steamed | poached | scrambled | heated | cooked | braised |
                   toasted | sauteed | microwaved | blanched | barbecued |
                   stir_fried | broiled | reheated | unknown
  - preservation_state: fresh | canned | dried | dehydrated | frozen | salted |
                        smoked | cured | pickled | fermented | condensed |
                        ready_to_eat | unknown

Anchored on CNF's controlled vocabulary as observed in
``backend/raw_cnf/FOOD_NAME.csv``. Both EN and FR variants are accepted so the
same extractor scores CNF + WAFCT rows + bilingual descriptions consistently.

This module is the regex-prior half of the hybrid tagger. Phase 2 will layer an
LLM fallback on top via ``build_cnf_prep_state.py`` (mirroring the
``build_cnf_food_type.py`` ETL). For the Phase 1 measurement lab we use the
extractor by itself to (a) score matcher accuracy against ground-truth phrases
and (b) measure how often the substitution pipeline crosses prep states.

Treat ``thermal_state='unknown'`` / ``preservation_state='unknown'`` as
"insufficient regex evidence" — NOT "no prep state". Single-ingredient rows
like "Chickpea" or "Salt" legitimately have no thermal verb in the description.

Phase 1.5 (2026-05-30): extended thermal coverage with braised / toasted /
sauteed / microwaved / blanched / barbecued / stir_fried / broiled / reheated
after corpus audit found 113 braised + 72 toasted + 58 sauteed rows tagging
as unknown/unknown. Preservation extended with fermented (WAFCT-critical) and
condensed/concentrated/evaporated. 'pasteurized' / 'UHT' fold into 'fresh'
(default state of fluid dairy — substitution semantics treat pasteurized milk
as fresh milk, not a separate preservation class).

Phase 1.6 (2026-05-30): French plural participles (rôties, bouillies, braisés),
RTE / powder / dry → dried, yogurt → fermented, condensed-before-canned ordering,
frozen-produce → raw default, refrigerated/chilled → fresh.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple


THERMAL_STATES = (
    'raw',
    'boiled',
    'fried',
    'baked',
    'roasted',
    'stewed',
    'grilled',
    'steamed',
    'poached',
    'scrambled',
    'heated',
    'cooked',
    # Phase 1.5 additions
    'braised',
    'toasted',
    'sauteed',
    'microwaved',
    'blanched',
    'barbecued',
    'stir_fried',
    'broiled',
    'reheated',
    # Phase 4 additions (2026-05-30) — sweep up the 15 unlabelled foods
    'popped',         # popcorn, puffed cereals
    'brewed',         # coffee, tea, infusions
    'unknown',
)

PRESERVATION_STATES = (
    'fresh',
    'canned',
    'dried',
    'dehydrated',
    'frozen',
    'salted',
    'smoked',
    'cured',
    'pickled',
    # Phase 1.5 additions
    'fermented',
    'condensed',
    # Phase 1.6
    'ready_to_eat',
    # Phase 4 additions (2026-05-30) — sweep up the 15 unlabelled foods
    'candied',        # candied fruit peels, glaced fruit (sugar-preserved)
    'aged',           # aged blubber, aged meat
    'unknown',
)


@dataclass(frozen=True)
class PrepState:
    thermal_state: str
    preservation_state: str
    confidence: float        # 0.0 / 0.5 / 0.7 / 1.0 — see _compute_confidence
    matched_terms: Tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            'thermal_state': self.thermal_state,
            'preservation_state': self.preservation_state,
            'confidence': self.confidence,
            'matched_terms': list(self.matched_terms),
        }


# Order matters: most-specific first. Each entry maps to a thermal state.
# 'raw' is checked LAST among the thermal patterns so explicit cooking verbs
# win when both are present (e.g. "Apple, raw, without skin, sliced, cooked,
# boiled" → thermal=boiled, not raw — because the apple ends up boiled). The
# 'raw' regex still wins for "uncooked" / "unheated" because \b prevents
# `\bcooked\b` from matching 'uncooked'.
#
# Phase 1.5 ordering: compound terms first (stir-fried before fried, hard-cooked
# already absorbed into boiled). Specific cooking methods before generic 'cooked'.
#
# Phase 1.6: FR participles use optional (?:e(?:s)?|s)? for m/f/pl forms
# (rôti/rôtie/rôtis/rôties; braisé/braisés). \bsauti\b catches accent-less FR.
# \bblanchi…\b deliberately does NOT match 'blanche' (white flour).
_FR_PART = r'(?:e(?:s)?|s)?'
_THERMAL_PATTERNS = (
    # Compound / specific cooking methods (must precede their family generics)
    ('stir_fried', re.compile(r'\bstir[- ]fried\b|\bstir[- ]fry\b|\bstir[- ]frying\b', re.IGNORECASE)),
    ('barbecued',  re.compile(r'\bbarbecued?\b|\bbarbecue\b|\bBBQ\b|\bbarbec', re.IGNORECASE)),
    ('blanched',   re.compile(r'\bblanched\b|\bblanchi' + _FR_PART + r'\b', re.IGNORECASE)),
    ('braised',    re.compile(
        r'\bbraised\b|\bbrais[eé]' + _FR_PART + r'\b',
        re.IGNORECASE)),
    ('sauteed',    re.compile(
        r'\bsaut[eé]ed?\b|\bsaut[eé]' + _FR_PART + r'\b|\bsauti\b',
        re.IGNORECASE)),
    ('toasted',    re.compile(r'\btoasted\b|\btoast[eé]' + _FR_PART + r'\b', re.IGNORECASE)),
    ('microwaved', re.compile(r'\bmicrowaved?\b|\bmicro[- ]ondes\b', re.IGNORECASE)),
    ('reheated',   re.compile(r'\breheated\b|\br[eé]chauff[eé]' + _FR_PART + r'\b', re.IGNORECASE)),
    ('broiled',    re.compile(r'\bbroiled\b', re.IGNORECASE)),  # \b prevents 'broiler' from matching
    # Phase 4 additions
    ('popped',     re.compile(r'\bpopped\b|\bair[- ]popped\b|\bpuffed\b', re.IGNORECASE)),
    ('brewed',     re.compile(r'\bbrewed\b|\binfused\b|\binfus[eé]' + _FR_PART + r'\b', re.IGNORECASE)),
    # Original verbs
    ('scrambled',  re.compile(r'\bscramb|\bbrouill', re.IGNORECASE)),
    ('poached',    re.compile(r'\bpoach|\bpoch[eé]', re.IGNORECASE)),
    ('steamed',    re.compile(
        r'\bsteamed\b|cuit\s+[aà]\s+la\s+vapeur|\b(?:à|a)\s+vapeur\b',
        re.IGNORECASE)),
    ('boiled',     re.compile(
        r'\bboiled\b|\bbouilli' + _FR_PART + r'\b|hard[- ]cooked',
        re.IGNORECASE)),
    ('grilled',    re.compile(r'\bgrilled\b|\bgrill[eé]' + _FR_PART + r'\b', re.IGNORECASE)),
    ('fried',      re.compile(
        r'\bfried\b|\bpan[- ]fried\b|\bdeep[- ]fried\b|\bfrit' + _FR_PART + r'\b',
        re.IGNORECASE)),
    ('roasted',    re.compile(r'\broasted\b|\br[oô]ti' + _FR_PART + r'\b', re.IGNORECASE)),
    ('baked',      re.compile(r'\bbaked\b|cuit\s+au\s+four', re.IGNORECASE)),
    ('stewed',     re.compile(
        r'\bstewed\b|\bsimmered\b|\bmijot[eé]' + _FR_PART + r'\b|à\s+l[\'’]?étuvée?',
        re.IGNORECASE)),
    ('heated',     re.compile(r'\bheated\b|\br[eé]chauff[eé]' + _FR_PART + r'\b', re.IGNORECASE)),
    ('cooked',     re.compile(
        r'\bcooked\b|\bcuit' + _FR_PART + r'\b',
        re.IGNORECASE)),
    ('raw',        re.compile(
        r'\braw\b|\buncooked\b|\bunheated\b|\bunprepared\b|\bcru\b|\bcrue\b|\bcrus\b|\bcrues\b|\bnon\s+cuit\b|\bnon\s+pr[eé]par[eé]\b',
        re.IGNORECASE)),
)


# Order matters here too. 'fresh' is checked FIRST so phrases like
# "fresh or frozen" (common for animal-product raw rows) tag as fresh — the
# more general state — rather than restricting to frozen.
#
# Phase 1.5 additions:
# - 'pasteurized' / 'UHT' fold into 'fresh' (default fluid-dairy state).
# - 'fermented' is its own preservation class (substitution semantics: yogurt
#   is fermented milk; fermented vs unfermented matters for substitution).
# - 'condensed' / 'concentrated' / 'evaporated' fold into 'condensed' (these
#   collapse mass by water removal; substituting condensed for fresh inflates
#   sugar/protein per gram).
#
# Phase 1.6: 'condensed' before 'canned' so evaporated milk tags condensed.
# 'ready_to_eat' for RTE cereals. Powder/instant/poudre/dry fold into 'dried'.
# Yogurt/yogourt/kefir fold into 'fermented'. Refrigerated/chilled → fresh.
_PRESERVATION_PATTERNS = (
    ('fresh',       re.compile(
        r'\bfresh\b|\bfra[iî]s\b|\bfra[iî]che\b|\bpasteurized\b|\bpasteuris[ée]\b|\bUHT\b|'
        r'\brefrigerated\b|\br[eé]frig[eé]r(?:[eé](?:e)?)?\b|\bchilled\b',
        re.IGNORECASE)),
    ('condensed',   re.compile(
        r'\bcondensed\b|\bconcentrated\b|\bevaporated\b|\bconcentr[ée]' + _FR_PART + r'\b|\b[eé]vapor[ée]' + _FR_PART + r'\b',
        re.IGNORECASE)),
    ('canned',      re.compile(
        r'\bcanned\b|\bconserve\b|\bin\s+(?:water|juice|syrup|oil|brine)\s+pack\b|\bwater\s+pack\b|\bsyrup\s+pack\b',
        re.IGNORECASE)),
    ('ready_to_eat', re.compile(
        r'\bready[- ]to[- ](?:eat|serve)\b|\bready to (?:eat|serve)\b|'
        r'\bpr[eê]te[- ]à[- ](?:manger|servir)\b|'
        r'\bpretes?\s+[àa]\s+manger\b|\bpretes?\s+[àa]\s+servir\b',
        re.IGNORECASE)),
    ('fermented',   re.compile(
        r'\bfermented\b|\bferment[eé]' + _FR_PART + r'\b|\bcultured\b|'
        r'\byogurt\b|\byogourt\b|\bkefir\b',
        re.IGNORECASE)),
    ('dried',       re.compile(
        r'\bdried\b|\bs[eé]ch[eé]' + _FR_PART + r'\b|\bpowder(?:ed)?\b|\bpoudre\b|'
        r'\binstant(?:an[eé])?\b|'
        # 'dry' alone is too broad. For an unprocessed grain or seed "dry, raw"
        # just means uncooked, not preserved-by-drying. Exclude well-known
        # food-state phrases ("dry, raw" / "dry curd" / "dry mix" / "dry weight"
        # / "dry roast" / "dry toast" / "dry matter" / "dry run") so the tag
        # only fires for true drying-as-preservation contexts.
        r'\bdry\b(?!\s*(?:,\s*raw|curd|mix|weight|roast|toast|matter|run))',
        re.IGNORECASE)),
    ('dehydrated',  re.compile(r'\bdehydrated\b|\bd[eé]shydrat[eé]' + _FR_PART + r'\b', re.IGNORECASE)),
    ('frozen',      re.compile(r'\bfrozen\b|\bcong[eé]l[eé]' + _FR_PART + r'\b', re.IGNORECASE)),
    ('salted',      re.compile(r'\bsalted\b|\bsal[eé]\b|\bsal[eé]e\b', re.IGNORECASE)),
    ('smoked',      re.compile(r'\bsmoked\b|\bfum[eé]\b|\bfum[eé]e\b', re.IGNORECASE)),
    ('cured',       re.compile(r'\bcured\b', re.IGNORECASE)),
    ('pickled',     re.compile(r'\bpickled\b|\bmarin[eé]\b|\bmarin[eé]e\b', re.IGNORECASE)),
    # Phase 4 additions
    ('candied',     re.compile(r'\bcandied\b|\bglac[eé]' + _FR_PART + r'\s+(?:fruit|peel|cherries)\b|\bconfit\b', re.IGNORECASE)),
    ('aged',        re.compile(r'\baged\b|\bvieilli' + _FR_PART + r'\b', re.IGNORECASE)),
)


# Thermal states whose presence implies the food is in 'fresh' preservation by
# default (used by the default-fresh heuristic). All cooking verbs that imply
# the food was processed from a fresh starting state belong here.
_FRESH_DEFAULT_THERMAL = frozenset({
    'raw', 'boiled', 'fried', 'baked', 'roasted', 'stewed',
    'grilled', 'steamed', 'poached', 'scrambled', 'cooked', 'heated',
    # Phase 1.5 additions
    'braised', 'toasted', 'sauteed', 'microwaved', 'blanched',
    'barbecued', 'stir_fried', 'broiled', 'reheated',
    # Phase 4 additions
    'popped', 'brewed',
})


# Cooking-verb equivalence class used by ``thermal_states_equivalent``. Any
# thermal state in this set is considered equivalent to any other in the set
# (and to the generic 'cooked' tag). 'raw' is in its own class.
_COOKED_CLASS = frozenset({
    'boiled', 'fried', 'baked', 'roasted', 'stewed',
    'grilled', 'steamed', 'poached', 'scrambled',
    'heated', 'cooked',
    # Phase 1.5 additions — all also cooking verbs
    'braised', 'toasted', 'sauteed', 'microwaved', 'blanched',
    'barbecued', 'stir_fried', 'broiled', 'reheated',
    # Phase 4 additions — popcorn-popped and tea/coffee-brewed are both
    # heat-driven transformations from raw kernel / leaf / bean
    'popped', 'brewed',
})


# Frozen IQF produce is raw unless the row names a cooking step or is a composite
# meal (entree / produit:). Skip rows that already name a thermal verb.
_FROZEN_RAW_SKIP = re.compile(
    r'\bentree\b|\bentrée\b|\bmet\s+surgel|\bfrozen\s+entree\b|'
    r'\bheated\b|\br[eé]chauff|\bcooked\b|\bboiled\b|\bfried\b|\broasted\b|'
    r'\bstewed\b|\bgrilled\b|\bbraised\b|\bmicro|\bproduct:\b|\bproduit:\b',
    re.IGNORECASE,
)


def _apply_post_heuristics(
    description: str,
    thermal: str,
    preservation: str,
    matched: list,
) -> tuple[str, str]:
    """Apply corpus-informed defaults after regex passes."""
    if thermal == 'unknown' and preservation == 'frozen':
        if not _FROZEN_RAW_SKIP.search(description):
            thermal = 'raw'
            matched.append('raw(frozen-default)')

    return thermal, preservation


def _compute_confidence(thermal: str, preservation: str) -> float:
    """How strong is the regex evidence for this row?

    1.0 — both axes resolved by an explicit term
    0.7 — exactly one axis resolved
    0.5 — neither resolved BUT the description is non-empty (room for LLM)
    0.0 — empty description
    """
    if thermal != 'unknown' and preservation != 'unknown':
        return 1.0
    if thermal != 'unknown' or preservation != 'unknown':
        return 0.7
    return 0.5


def extract_prep_state(description: str) -> PrepState:
    """Extract (thermal_state, preservation_state) from a CNF FoodDescription.

    Both axes default to ``'unknown'`` when the regex finds no evidence —
    callers should treat this as "delegate to LLM tagger" rather than as a
    confident "no prep state".
    """
    if not description:
        return PrepState('unknown', 'unknown', 0.0, ())

    matched: list = []

    thermal = 'unknown'
    for name, pat in _THERMAL_PATTERNS:
        if pat.search(description):
            thermal = name
            matched.append(name)
            break

    preservation = 'unknown'
    for name, pat in _PRESERVATION_PATTERNS:
        if pat.search(description):
            preservation = name
            matched.append(f'p:{name}')
            break

    thermal, preservation = _apply_post_heuristics(
        description, thermal, preservation, matched,
    )

    # Default-fresh heuristic: CNF rows that name an explicit thermal state
    # (raw or a cooking verb) but no preservation are by convention 'fresh'.
    # "Carrot, raw" → no 'fresh' word but it IS fresh. "Egg, fried" → fried
    # FROM fresh. Only override when no preservation regex fired.
    if preservation == 'unknown' and thermal in _FRESH_DEFAULT_THERMAL:
        preservation = 'fresh'
        matched.append('p:fresh(default)')

    return PrepState(
        thermal_state=thermal,
        preservation_state=preservation,
        confidence=_compute_confidence(thermal, preservation),
        matched_terms=tuple(matched),
    )


def thermal_states_equivalent(extracted: str, expected: str) -> bool:
    """Asymmetric equivalence used by lab probes when scoring axis matches.

    Semantics:
      - ``expected='unknown'`` means the GT did not assert anything → always pass.
      - ``extracted='unknown'`` when ``expected`` IS specific means the regex
        couldn't confirm the prep state from the returned description → FAIL
        (the matcher likely picked a composite-dish row that hides the prep
        state in unstructured text). Honest under-confidence beats false PASS.
      - Within the cooked-verb family (boiled/fried/baked/roasted/stewed/
        grilled/steamed/poached/scrambled/heated/cooked/braised/toasted/
        sauteed/microwaved/blanched/barbecued/stir_fried/broiled/reheated),
        any-vs-any counts as equivalent so "carrot soup → braised carrot"
        passes when the GT only specifies thermal_state='cooked'.
      - 'raw' is its own equivalence class.
    """
    if expected == 'unknown':
        return True
    if extracted == 'unknown':
        return False
    if extracted == expected:
        return True
    return extracted in _COOKED_CLASS and expected in _COOKED_CLASS


def preservation_states_equivalent(extracted: str, expected: str) -> bool:
    """Asymmetric equivalence for the preservation axis. See ``thermal_states_equivalent``."""
    if expected == 'unknown':
        return True
    if extracted == 'unknown':
        return False
    return extracted == expected
