#!/usr/bin/env python
"""Profile the slowest meal (fufu, 8 ingredients, 23 candidates) to find the
hotspot now that matcher + per-candidate FCS scoring are both cheap."""
from __future__ import annotations

import cProfile
import io
import os
import pstats
import sys

import dish_project.env_bootstrap  # noqa: F401

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import django  # noqa: E402

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from api.services.substitution_analyzer import analyze_substitutions  # noqa: E402

COMPOSITION = [
    {'food_id': 700194, 'mass_g': 200},
    {'food_id': 1662, 'mass_g': 100},
    {'food_id': 2933, 'mass_g': 160},
    {'food_id': 3399, 'mass_g': 70},
    {'food_id': 648, 'mass_g': 120},
    {'food_id': 2460, 'mass_g': 50},
    {'food_id': 2401, 'mass_g': 30},
    {'food_id': 423, 'mass_g': 15},
]


def main() -> int:
    # Warmup call so embedding cache + pipeline are loaded.
    analyze_substitutions(
        COMPOSITION,
        purpose='general_health',
        max_suggestions=3,
        include_scorecard=True,
        dish_name='fufu with groundnut soup',
    )

    pr = cProfile.Profile()
    pr.enable()
    result = analyze_substitutions(
        COMPOSITION,
        purpose='general_health',
        max_suggestions=3,
        include_scorecard=True,
        dish_name='fufu with groundnut soup',
    )
    pr.disable()

    print(f'elapsed_ms={result["metadata"]["elapsed_ms"]} '
          f'candidates={result["metadata"]["candidates_found"]} '
          f'suggestions={len(result["suggestions"])}')

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
    ps.print_stats(40)
    print(s.getvalue())
    return 0


if __name__ == '__main__':
    sys.exit(main())
