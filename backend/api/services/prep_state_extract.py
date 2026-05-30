"""Regex-based preparation-state extractor for CNF FoodDescription strings.

Returns a two-axis tag aligned with the prep-state lab plan:
  - thermal_state: raw | boiled | fried | baked | roasted | stewed | grilled |
                   steamed | poached | scrambled | heated | cooked | unknown
  - preservation_state: fresh | canned | dried | dehydrated | frozen | salted |
                        smoked | cured | pickled | unknown

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
_THERMAL_PATTERNS = (
    ('scrambled',  re.compile(r'\bscramb|\bbrouill', re.IGNORECASE)),
    ('poached',    re.compile(r'\bpoach|\bpoch[eé]', re.IGNORECASE)),
    ('boiled',     re.compile(
        r'\bboiled\b|\bbouilli\b|\bbouillie\b|hard[- ]cooked',
        re.IGNORECASE)),
    ('steamed',    re.compile(
        r'\bsteamed\b|cuit\s+[aà]\s+la\s+vapeur',
        re.IGNORECASE)),
    ('grilled',    re.compile(r'\bgrilled\b|\bgrill[eé]\b', re.IGNORECASE)),
    ('fried',      re.compile(r'\bfried\b|\bfrit\b|\bfrite\b|\bfrits\b|\bfrites\b', re.IGNORECASE)),
    ('roasted',    re.compile(r'\broasted\b|\br[oô]ti\b|\br[oô]tis\b|\br[oô]tie\b', re.IGNORECASE)),
    ('baked',      re.compile(r'\bbaked\b|cuit\s+au\s+four', re.IGNORECASE)),
    ('stewed',     re.compile(
        r'\bstewed\b|\bsimmered\b|\bmijot[eé]\b|\bmijot[eé]e?\b|à\s+l[\'’]?étuvée?',
        re.IGNORECASE)),
    ('heated',     re.compile(r'\bheated\b|\br[eé]chauff[eé]\b', re.IGNORECASE)),
    ('cooked',     re.compile(r'\bcooked\b|\bcuit\b|\bcuite\b|\bcuits\b|\bcuites\b', re.IGNORECASE)),
    ('raw',        re.compile(
        r'\braw\b|\buncooked\b|\bunheated\b|\bunprepared\b|\bcru\b|\bcrue\b|\bcrus\b|\bcrues\b|\bnon\s+cuit\b|\bnon\s+pr[eé]par[eé]\b',
        re.IGNORECASE)),
)


# Order matters here too. 'fresh' is checked FIRST so phrases like
# "fresh or frozen" (common for animal-product raw rows) tag as fresh — the
# more general state — rather than restricting to frozen.
_PRESERVATION_PATTERNS = (
    ('fresh',       re.compile(r'\bfresh\b|\bfra[iî]s\b|\bfra[iî]che\b', re.IGNORECASE)),
    ('canned',      re.compile(
        r'\bcanned\b|\bconserve\b|\bin\s+(?:water|juice|syrup)\s+pack\b|\bwater\s+pack\b|\bsyrup\s+pack\b',
        re.IGNORECASE)),
    ('dried',       re.compile(r'\bdried\b|\bs[eé]ch[eé]\b|\bs[eé]ch[eé]e\b', re.IGNORECASE)),
    ('dehydrated',  re.compile(r'\bdehydrated\b|\bd[eé]shydrat[eé]\b|\bd[eé]shydrat[eé]e\b', re.IGNORECASE)),
    ('frozen',      re.compile(r'\bfrozen\b|\bcong[eé]l[eé]\b|\bcong[eé]l[eé]e\b', re.IGNORECASE)),
    ('salted',      re.compile(r'\bsalted\b|\bsal[eé]\b|\bsal[eé]e\b', re.IGNORECASE)),
    ('smoked',      re.compile(r'\bsmoked\b|\bfum[eé]\b|\bfum[eé]e\b', re.IGNORECASE)),
    ('cured',       re.compile(r'\bcured\b', re.IGNORECASE)),
    ('pickled',     re.compile(r'\bpickled\b|\bmarin[eé]\b|\bmarin[eé]e\b', re.IGNORECASE)),
)


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

    # Default-fresh heuristic: CNF rows that name an explicit thermal state
    # (raw or a cooking verb) but no preservation are by convention 'fresh'.
    # "Carrot, raw" → no 'fresh' word but it IS fresh. "Egg, fried" → fried
    # FROM fresh. Only override when no preservation regex fired.
    if preservation == 'unknown' and thermal in (
        'raw', 'boiled', 'fried', 'baked', 'roasted', 'stewed',
        'grilled', 'steamed', 'poached', 'scrambled', 'cooked', 'heated',
    ):
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
        grilled/steamed/poached/scrambled/heated/cooked), any-vs-any counts
        as equivalent so "carrot soup → boiled carrot" passes when the GT
        only specifies thermal_state='cooked'.
      - 'raw' is its own equivalence class.
    """
    if expected == 'unknown':
        return True
    if extracted == 'unknown':
        return False
    if extracted == expected:
        return True
    cooked_class = {'boiled', 'fried', 'baked', 'roasted', 'stewed',
                    'grilled', 'steamed', 'poached', 'scrambled',
                    'heated', 'cooked'}
    return extracted in cooked_class and expected in cooked_class


def preservation_states_equivalent(extracted: str, expected: str) -> bool:
    """Asymmetric equivalence for the preservation axis. See ``thermal_states_equivalent``."""
    if expected == 'unknown':
        return True
    if extracted == 'unknown':
        return False
    return extracted == expected
