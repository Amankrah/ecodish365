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
"""
from __future__ import annotations

from threading import Lock
from typing import Optional

from django.conf import settings

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
    return _api_pipeline


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
