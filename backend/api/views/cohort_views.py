"""Multi-lens cohort batch ingest endpoint (PLATFORM-CODE-1.b, 2026-06-26).

POST /api/research/cohort/
    Body: {
        "recalls": [
            {"respondent_id": "S1234", "day_id": "day_1",
             "foods": [{"food_id": 113, "mass_g": 250}, ...]},
            ...
        ],
        "lenses": ["hefi", "heni", "hsr", "fcs", "env",
                   "dietary_pattern", "fped"],
        "options": {
            "parallelism": 4,
            "include_per_respondent": true,
            "anonymize": false
        }
    }

Returns `{meta, per_respondent, distribution_by_lens, coverage, provenance}`
as produced by [`score_cohort`](backend/api/services/cohort_orchestrator.py).
Hard cap: 5,000 recalls per request. Above this the endpoint returns 413
rather than risk OOM on the single-process deployment.

This endpoint is stateless: cohorts are kept client-side in localStorage
(see [`frontend/src/lib/savedCohorts.ts`](frontend/src/lib/savedCohorts.ts)).
No per-cohort persistence, no auth changes — anyone with API access can
score a cohort of their own data without setting up an account.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.services.cohort_orchestrator import (
    ALL_LENSES,
    Recall,
    score_cohort,
)
from api.services.cohort_ingest import parse_upload
from api.services.cohort_compare import compare_cohorts
from api.services.cohort_library import list_cohorts, load_cohort_recalls

logger = logging.getLogger(__name__)

_MAX_RECALLS_PER_REQUEST = 5000
_MAX_FOODS_PER_RECALL = 200
_MAX_PARALLELISM = 8


def _clean_foods(foods_raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(foods_raw, list):
        return []
    cleaned: List[Dict[str, Any]] = []
    for f in foods_raw[:_MAX_FOODS_PER_RECALL]:
        if not isinstance(f, dict):
            continue
        fid_raw = f.get('food_id')
        mass_raw = f.get('mass_g', f.get('amount_g', f.get('grams')))
        try:
            fid = int(fid_raw)
            mass = float(mass_raw)
        except (TypeError, ValueError):
            continue
        if fid > 0 and mass > 0:
            entry = {'food_id': fid, 'mass_g': mass}
            occ = f.get('occasion')
            if occ:
                entry['occasion'] = str(occ)
            cleaned.append(entry)
    return cleaned


def _coerce_recalls(recalls_raw: Any) -> List[Recall]:
    if not isinstance(recalls_raw, list):
        return []
    out: List[Recall] = []
    for i, r in enumerate(recalls_raw[:_MAX_RECALLS_PER_REQUEST]):
        if not isinstance(r, dict):
            continue
        rid = str(r.get('respondent_id') or f'subject_{i}')
        did = str(r.get('day_id') or 'day_1')
        foods = _clean_foods(r.get('foods'))
        if not foods:
            continue
        out.append(Recall(respondent_id=rid, day_id=did, foods=foods))
    return out


def _anonymize(per_respondent: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Replace respondent_id with a sequential alias for individual-mode
    display. Day_id is preserved (it's not PII)."""
    for i, row in enumerate(per_respondent):
        row['respondent_id'] = f'subject_{i + 1:04d}'
    return per_respondent


@api_view(['POST'])
@permission_classes([AllowAny])
def cohort_score(request) -> Response:
    body = request.data if isinstance(request.data, dict) else {}

    recalls_raw = body.get('recalls')
    if not isinstance(recalls_raw, list):
        return Response(
            {'error': 'recalls must be a list of {respondent_id, day_id, foods} objects'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(recalls_raw) > _MAX_RECALLS_PER_REQUEST:
        return Response(
            {'error': f'recalls list too large; limit is {_MAX_RECALLS_PER_REQUEST} per request',
             'received': len(recalls_raw)},
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    recalls = _coerce_recalls(recalls_raw)
    if not recalls:
        return Response(
            {'error': 'no valid recalls after cleaning',
             'hint': 'each recall must include foods=[{food_id, mass_g}, ...] with positive food_id and mass_g'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    lenses_raw = body.get('lenses') or list(ALL_LENSES)
    if not isinstance(lenses_raw, list):
        return Response(
            {'error': 'lenses must be a list of strings'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    lenses = [str(l) for l in lenses_raw if str(l) in ALL_LENSES]
    if not lenses:
        return Response(
            {'error': f'no recognized lenses; valid choices are {list(ALL_LENSES)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    options = body.get('options') if isinstance(body.get('options'), dict) else {}
    try:
        parallelism = int(options.get('parallelism', 4))
    except (TypeError, ValueError):
        parallelism = 4
    parallelism = max(1, min(_MAX_PARALLELISM, parallelism))
    include_per_respondent = bool(options.get('include_per_respondent', True))
    anonymize = bool(options.get('anonymize', False))

    try:
        result = score_cohort(recalls, lenses=lenses, parallelism=parallelism)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        logger.exception('cohort_score: orchestrator raised unexpectedly')
        return Response(
            {'error': 'cohort scoring failed', 'detail': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if anonymize:
        result['per_respondent'] = _anonymize(result.get('per_respondent') or [])
    if not include_per_respondent:
        result['per_respondent'] = []
        result.setdefault('meta', {})['per_respondent_suppressed'] = True

    return Response({'result': result}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def cohort_ingest(request) -> Response:
    """Parse an uploaded cohort file (CSV or NHANES XPT) into a Recall list
    + validation report. Does NOT score — the caller decides whether to
    POST the resulting recalls to `/api/research/cohort/`.

    Multipart body: `{file: <upload>, format: "auto"|"generic_csv"|"nhanes_dr1iff"|"nhanes_dr2iff"}`.

    Returns:
        {
          "format_detected": "nhanes_dr1iff",
          "validation_report": {n_rows_read, n_rows_dropped, ...},
          "recalls": [<first N recalls as JSON, capped for preview>],
          "n_total_recalls": int   // full count, not just the preview
        }
    """
    upload = request.FILES.get('file')
    if not upload:
        return Response(
            {'error': 'multipart field "file" is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    fmt_hint = str(request.data.get('format', 'auto'))
    preview_n = 100
    try:
        preview_n = int(request.data.get('preview_n', 100))
    except (TypeError, ValueError):
        preview_n = 100
    preview_n = max(0, min(500, preview_n))

    try:
        file_bytes = upload.read()
    except Exception as exc:  # noqa: BLE001
        return Response(
            {'error': 'failed to read upload', 'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        recalls, report, detected = parse_upload(
            file_bytes=file_bytes,
            filename=upload.name,
            format_hint=fmt_hint,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('cohort_ingest: parse_upload raised')
        return Response(
            {'error': 'failed to parse upload', 'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    preview = [
        {
            'respondent_id': r.respondent_id,
            'day_id':        r.day_id,
            'n_foods':       len(r.foods),
            'foods':         r.foods[:20],
        }
        for r in recalls[:preview_n]
    ]
    return Response({
        'format_detected':    detected,
        'validation_report':  report.to_dict(),
        'recalls_preview':    preview,
        'n_total_recalls':    len(recalls),
        'recalls':            [{'respondent_id': r.respondent_id,
                                'day_id':        r.day_id,
                                'foods':         r.foods} for r in recalls],
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def cohort_compare(request) -> Response:
    """Compare two already-scored cohorts. Inputs are the per-respondent
    score arrays for each lens (the frontend already has both cohort
    results in localStorage so it doesn't need to re-score). Returns
    per-lens delta + Mann-Whitney U test results.

    Body: {
        "cohort_a": {"name": "Baseline", "per_respondent": [...]},
        "cohort_b": {"name": "Intervention", "per_respondent": [...]},
        "lenses": ["hefi", "heni", ...]   // optional, default: all numeric lenses
    }
    """
    body = request.data if isinstance(request.data, dict) else {}
    a = body.get('cohort_a') or {}
    b = body.get('cohort_b') or {}
    a_rows = a.get('per_respondent') if isinstance(a.get('per_respondent'), list) else None
    b_rows = b.get('per_respondent') if isinstance(b.get('per_respondent'), list) else None
    if not a_rows or not b_rows:
        return Response(
            {'error': 'cohort_a.per_respondent and cohort_b.per_respondent are both required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    lenses = body.get('lenses') if isinstance(body.get('lenses'), list) else None
    try:
        out = compare_cohorts(
            a_rows, b_rows,
            a_name=str(a.get('name') or 'Cohort A'),
            b_name=str(b.get('name') or 'Cohort B'),
            lens_keys=[str(l) for l in lenses] if lenses else None,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('cohort_compare: failed')
        return Response({'error': 'compare failed', 'detail': str(exc)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({'result': out}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def cohort_library_index(request) -> Response:
    """List built-in cohorts shipped with this deployment.

    Each entry includes a `file_present` flag — the registry can list a
    cohort whose raw data isn't on the current host (e.g. NDNS gated by
    UKDS registration), and the UI greys those out.
    """
    return Response({'cohorts': list_cohorts()}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def cohort_library_recalls(request, cohort_id: str) -> Response:
    """Parse a built-in cohort into the same Recall shape the upload
    endpoint returns. Optional `sample_n` (default 200) keeps the round-
    trip + downstream scoring snappy — NHANES Day-1 is ~7,500 recalls
    end-to-end, well above the 5,000-recall scorer cap.
    """
    body = request.data if isinstance(request.data, dict) else {}
    try:
        sample_n = int(body.get('sample_n', 200))
    except (TypeError, ValueError):
        sample_n = 200
    if sample_n <= 0:
        sample_n = 200
    sample_n = min(sample_n, _MAX_RECALLS_PER_REQUEST)

    try:
        recalls, report, entry = load_cohort_recalls(cohort_id, sample_n=sample_n)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    except FileNotFoundError as exc:
        return Response({'error': 'cohort raw file missing on this deployment',
                         'detail': str(exc)},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception('cohort_library_recalls: parse failed')
        return Response({'error': 'failed to parse built-in cohort',
                         'detail': str(exc)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    preview = [
        {
            'respondent_id': r.respondent_id,
            'day_id':        r.day_id,
            'n_foods':       len(r.foods),
            'foods':         r.foods[:20],
        }
        for r in recalls[:50]
    ]
    return Response({
        'cohort':            entry.to_dict(),
        'format_detected':   entry.parse_format,
        'validation_report': report.to_dict(),
        'recalls_preview':   preview,
        'n_total_recalls':   len(recalls),
        'recalls':           [{'respondent_id': r.respondent_id,
                               'day_id':        r.day_id,
                               'foods':         r.foods} for r in recalls],
    }, status=status.HTTP_200_OK)
