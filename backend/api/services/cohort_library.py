"""Built-in cohort library (PLATFORM-CODE-1.k, 2026-06-26).

A small registry of public national-nutrition surveys whose raw data we
already ship on disk under [`backend/raw_nhanes/`](backend/raw_nhanes/)
and similar directories. Lets a researcher score, say, NHANES 2017-18
in one click without re-downloading the 72 MB CDC file or running an
ETL — the very file the manuscript pipeline uses ([`build_nhanes_2017_meal_pool.py`](backend/api/services/etl/build_nhanes_2017_meal_pool.py)).

Each entry is parsed on demand by the existing `cohort_ingest` parsers,
so adding a new survey is just a registry row + a parser call — no per-
survey custom logic. Future cohorts (CCHS-Nutrition 2015 PUMF, INCA3,
NDNS, KNHANES) drop into the same shape.

Public API: `list_cohorts()` + `load_cohort_recalls(cohort_id, sample_n)`.
"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.services.cohort_ingest import (
    Recall,
    ValidationReport,
    parse_nhanes_xpt,
)

logger = logging.getLogger(__name__)


_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class CohortLibraryEntry:
    """A single built-in cohort. `raw_path` is repo-relative."""
    id:              str
    name:            str
    country:         str
    year:            str
    source:          str          # short citation
    source_url:      str          # one-line URL
    parse_format:    str          # 'nhanes_dr1iff' | 'nhanes_dr2iff' | 'generic_csv'
    raw_path:        str          # repo-relative to backend root
    description:     str
    expected_recalls: int         # informational; the parser is the source of truth
    coverage_note:   str = ''     # one-line caveat (e.g. "65% FNDDS bridge coverage")
    survey_weight_note: str = ''  # one-line note re sampling design (we don't apply weights yet)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id':                  self.id,
            'name':                self.name,
            'country':             self.country,
            'year':                self.year,
            'source':              self.source,
            'source_url':          self.source_url,
            'parse_format':        self.parse_format,
            'expected_recalls':    self.expected_recalls,
            'coverage_note':       self.coverage_note,
            'survey_weight_note':  self.survey_weight_note,
            'description':         self.description,
            'file_present':        self.absolute_path().exists(),
        }

    def absolute_path(self) -> Path:
        return _BACKEND_ROOT / self.raw_path


# Registry. Order = display order in the UI. Add new surveys here as
# their raw data arrives in `backend/raw_*/`.
_LIBRARY: List[CohortLibraryEntry] = [
    CohortLibraryEntry(
        id='nhanes_wweia_2017_2018_day1',
        name='NHANES 2017-18, Day 1 (What We Eat in America)',
        country='United States',
        year='2017-2018',
        source='CDC NCHS. NHANES 2017-2018 Public-Use Data Files (DR1IFF_J)',
        source_url='https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DR1IFF_J.htm',
        parse_format='nhanes_dr1iff',
        raw_path='raw_nhanes/DR1IFF_J.xpt',
        description=(
            'Day-1 24-hour dietary recalls from the U.S. National Health and '
            'Nutrition Examination Survey 2017-2018 cycle (~9,000 respondents, '
            'ages 2-80+). Public domain. Parses to ~7,500 respondent-days after '
            'mapping FNDDS food codes to CNF via the existing bridge.'
        ),
        expected_recalls=7500,
        coverage_note='65% FNDDS→CNF mass coverage; the unmatched 35% are mostly composite mixed dishes the bridge does not yet cover (full count shown in the validation report after load).',
        survey_weight_note=(
            'NHANES ships a Day-1 dietary sample weight (WTDR1D) for population-level '
            'estimation; the cohort scorer here treats every respondent equally (unweighted). '
            'NCI / SUDAAN-style survey-weighted distribution estimation is a separate '
            'methodology layer not yet applied.'
        ),
    ),
    # CCHS-Nutrition 2015, INCA3, NDNS, etc. land here as their PUMF / public
    # files are added to backend/raw_*/. The shape is identical for any SAS XPT
    # in the NHANES family; CSV-shaped surveys use parse_format='generic_csv'.
]


# ---------- Public API ----------------------------------------------------

def list_cohorts() -> List[Dict[str, Any]]:
    """Surface every registered cohort + presence flag. The frontend uses
    `file_present=False` to grey-out entries whose raw data is in the
    registry but not on disk in this deployment."""
    return [e.to_dict() for e in _LIBRARY]


def get_cohort(cohort_id: str) -> Optional[CohortLibraryEntry]:
    return next((e for e in _LIBRARY if e.id == cohort_id), None)


def load_cohort_recalls(
    cohort_id: str,
    sample_n: Optional[int] = None,
    sample_seed: int = 20260626,
) -> tuple[List[Recall], ValidationReport, CohortLibraryEntry]:
    """Parse a built-in cohort's raw file into Recall objects.

    `sample_n`: if set, return a random sample of this many recalls (seeded
    for reproducibility). Defaults to no sampling. The cohort scorer caps at
    5,000 recalls per request — so the UI passes `sample_n=5000` (or smaller)
    when loading NHANES, which the parser can build in <2 s.
    """
    entry = get_cohort(cohort_id)
    if entry is None:
        raise ValueError(f'unknown cohort id: {cohort_id!r}')
    path = entry.absolute_path()
    if not path.exists():
        raise FileNotFoundError(
            f'cohort raw file missing on this deployment: {entry.raw_path}'
        )

    if entry.parse_format in ('nhanes_dr1iff', 'nhanes_dr2iff'):
        with path.open('rb') as fh:
            xpt_bytes = fh.read()
        recalls, report = parse_nhanes_xpt(
            xpt_bytes,
            day_id_label='day_2' if entry.parse_format == 'nhanes_dr2iff' else 'day_1',
        )
    elif entry.parse_format == 'generic_csv':
        from api.services.cohort_ingest import parse_generic_csv
        with path.open('r', encoding='utf-8-sig', errors='replace') as fh:
            text = fh.read()
        recalls, report = parse_generic_csv(text)
    else:
        raise ValueError(f'unknown parse_format: {entry.parse_format!r}')

    if sample_n is not None and sample_n > 0 and len(recalls) > sample_n:
        rng = random.Random(sample_seed)
        n_before = len(recalls)
        recalls = rng.sample(recalls, sample_n)
        report.drop_reasons['sampled_down_to_request'] = n_before - sample_n
        report.n_recalls_built = len(recalls)
        report.n_respondents = len({r.respondent_id for r in recalls})

    return recalls, report, entry
