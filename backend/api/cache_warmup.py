"""Boot-time cache warmup for the heavy, lazily-loaded singletons.

The substitution / scorecard path loads the environmental LCA model, the
dietary-pattern matcher, the HENI categorizer, the Rust scorers, the CNF
pipeline, and the food-pattern profiles on first use. Measured cold-start cost
of that first call is ~17 s, which lands on the first real user request after a
process (re)start. Warming these at boot moves the cost off the critical path.

Everything warmed here is deterministic (no LLM / network calls), so warmup is
cheap-ish and safe to run unattended. It is opt-in via the ECODISH_WARM_ON_BOOT
environment variable so it never slows tests, migrations, or other management
commands — only the deployed server process sets it.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

# A stable, always-present CNF food (apple, raw) to drive the scorers once.
_WARM_FOOD = [{'food_id': 1696, 'mass_g': 100}]


def warm_caches() -> None:
    """Preload the heavy singletons. Each step is isolated so one failure never
    aborts the rest (or the app)."""
    t0 = time.perf_counter()
    steps = [
        ('cnf_pipeline', _warm_cnf_pipeline),
        ('cnf_matcher', _warm_matcher),
        ('scorers', _warm_scorers),       # HEFI/HENI/HSR/FCS/environmental/dietary-pattern
        ('fped', _warm_fped),
    ]
    for name, fn in steps:
        s = time.perf_counter()
        try:
            fn()
            logger.info('cache warmup: %s ready (%.0f ms)', name, (time.perf_counter() - s) * 1000)
        except Exception as exc:  # noqa: BLE001
            logger.warning('cache warmup: %s failed (non-fatal): %s', name, exc)
    logger.info('cache warmup complete (%.0f ms total)', (time.perf_counter() - t0) * 1000)


def _warm_cnf_pipeline() -> None:
    from api.cnf_cache import get_api_cnf_pipeline
    get_api_cnf_pipeline()


def _warm_matcher() -> None:
    # Wires the matcher + its embedding index (no LLM call).
    from api.services.cnf_matcher import get_default_matcher
    get_default_matcher()


def _warm_scorers() -> None:
    # One deterministic scorecard pass loads the environmental DataLoader/LCA +
    # factor packs, the dietary-pattern prototype matcher, the HENI categorizer,
    # and the Rust HSR/FCS/HENI cores — the bulk of the measured cold-start.
    from api.services.substitution_scorecard import score_composition
    score_composition(_WARM_FOOD)


def _warm_fped() -> None:
    from api.services.fped_aggregator import aggregate_fped
    aggregate_fped(_WARM_FOOD)
