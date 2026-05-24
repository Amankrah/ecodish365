"""Process-wide CNF pipeline cache.

Before this module existed, every HEFI/FCS/HENI integrator plus the HSR
views, CNF views, and `meals.services.MealService` each defined their own
`_cnf_pipeline_instance` module-global. A single Django process ended up
with up to six independent copies of the CNF DataFrames (~35 MB each after
the REFUSE/YIELD trim), each paying the ~30 s cold load.

These helpers are the single source of truth. Every caller that needs a
CNF pipeline goes through here, so the first request to any calculator
eats the cost once and every subsequent request — across all calculators —
reuses the same instance.

Two getters exist temporarily because there are two legacy pipeline
classes (`api.cnf_data_pipeline.CNFDataPipeline` and
`dish_cnf_db_pipeline.cnf_pipeline.CNFDataPipeline`). Fix #6 will merge
them; until then callers should pick the one they already used.

Loading is deliberately **lazy**, not fired from `AppConfig.ready()`:
`ready()` runs for every management command (migrate, collectstatic,
makemigrations, …) and eagerly loading ~60 s of CSVs during `migrate`
serves nothing.

WAFCT-EXTEND (2026-05-24): on first pipeline access we ALSO run a one-time
WAFCT 2019 ingest that appends ~1,028 West African foods at FoodIDs
700,000+ into the same in-memory DataFrames (per WAFCT_EXPLORATION.md
Option B). Graceful degrade: if `raw_wafct/WAFCT_2019.xlsx` is missing,
the platform runs CNF-only.
"""
from __future__ import annotations

import logging
from threading import Lock
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

_api_pipeline = None  # type: Optional[object]
_api_pipeline_lock = Lock()

_dish_pipeline = None  # type: Optional[object]
_dish_pipeline_lock = Lock()


def get_api_cnf_pipeline():
    """Return the shared `api.cnf_data_pipeline.CNFDataPipeline` instance.

    Used by HEFI / FCS / HENI integrators and the Rust-backed scoring paths.
    """
    global _api_pipeline
    if _api_pipeline is None:
        with _api_pipeline_lock:
            if _api_pipeline is None:
                from api.cnf_data_pipeline import CNFDataPipeline
                _api_pipeline = CNFDataPipeline(settings.CNF_FOLDER)
                # WAFCT-EXTEND (2026-05-24): append West African foods at
                # FoodIDs 700,000+ with source='wafct'. No-op if the workbook
                # is missing — `workbook_present()` guard returns False.
                _maybe_ingest_wafct(_api_pipeline)
    return _api_pipeline


def _maybe_ingest_wafct(pipeline) -> None:
    """One-shot WAFCT ingest. Safe to skip if the workbook isn't present
    (deployment may legitimately ship CNF-only)."""
    try:
        from api.services.etl.wafct_ingest import (
            ingest_wafct, append_to_pipeline, workbook_present,
        )
    except ImportError as exc:
        logger.warning('WAFCT ingest module not importable; CNF-only mode: %s', exc)
        return
    if not workbook_present():
        logger.info('raw_wafct/WAFCT_2019.xlsx not present; CNF-only mode.')
        return
    try:
        result = ingest_wafct(pipeline)
        append_to_pipeline(pipeline, result)
        logger.info(
            'WAFCT ingest appended %d foods (FoodIDs %d-%d); '
            '%d nutrient rows across %d CNF NutrientIDs; '
            'dropped tags=%s; unmapped in-wild=%s',
            result.stats.get('foods_emitted', 0),
            result.stats.get('wafct_food_id_min', -1),
            result.stats.get('wafct_food_id_max', -1),
            result.stats.get('nutrient_rows_emitted', 0),
            result.stats.get('unique_tags_used', 0),
            result.dropped_tags,
            result.unmapped_tags,
        )
    except Exception as exc:  # noqa: BLE001
        # WAFCT ingest failure must NEVER take down the CNF-only pipeline.
        logger.exception('WAFCT ingest failed; continuing CNF-only: %s', exc)


def get_dish_cnf_pipeline():
    """Return the shared `dish_cnf_db_pipeline.cnf_pipeline.CNFDataPipeline` instance.

    Used by HSR views, CNF views, and the meals service. The dish pipeline
    is a thin wrapper over the api pipeline's already-loaded dataframes —
    no CSV re-reading, no second 35 MB copy. `api.cnf_cache` is now the
    single place the CNF dataset is materialised in memory, even though
    two pipeline classes still exist as different API shapes over the
    same data.
    """
    global _dish_pipeline
    if _dish_pipeline is None:
        with _dish_pipeline_lock:
            if _dish_pipeline is None:
                from dish_cnf_db_pipeline.cnf_pipeline import CNFDataPipeline
                _dish_pipeline = CNFDataPipeline(
                    settings.CNF_FOLDER,
                    shared_source=get_api_cnf_pipeline(),
                )
    return _dish_pipeline
