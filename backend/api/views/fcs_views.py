import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from api.seo_utils import seo_metadata
from fcs_calculator.fcs.service import (
    cnf_food_description,
    domain_mean_scores,
    extract_and_score,
    get_cnf_integrator,
    per_domain_attribute_breakdown,
)
from .fcs_explanations import get_explanations as get_fcs_explanations

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Food Compass Score Calculator | DISH Research",
    description="Calculate the Food Compass Score (FCS) for your food items. Analyze nutritional content and get detailed FCS results.",
    keywords="FCS, food compass score, nutritional analysis, food science, DISH Research"
)
def fcs_calculate(request):
    try:
        food_ids = request.data.get('food_ids', [])
        food_names = request.data.get('food_names', [])
        user_type = str(request.data.get('user_type', 'individual'))
        if user_type not in ('individual', 'researcher', 'policy'):
            user_type = 'individual'

        if not food_ids:
            return Response({"error": "No food IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

        serving_sizes = request.data.get('serving_sizes') or request.data.get('amounts_g')
        if serving_sizes is not None:
            if not isinstance(serving_sizes, list) or len(serving_sizes) != len(food_ids):
                return Response(
                    {"error": "serving_sizes must be a list with one value per food_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                serving_sizes = [max(0.1, float(s)) for s in serving_sizes]
            except (TypeError, ValueError):
                return Response(
                    {"error": "serving_sizes must be numeric grams"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if len(food_ids) > 1:
            food_name = f"Combined Food ({len(food_ids)} items)"
            if food_names:
                food_name = " + ".join(food_names[:3])
                if len(food_names) > 3:
                    food_name += f" + {len(food_names) - 3} more"
        else:
            food_name = food_names[0] if food_names else "Single Food Item"

        try:
            _, result = extract_and_score(food_ids, food_name, amounts_g=serving_sizes)
        except KeyError as ke:
            logger.error("Data inconsistency in extract_nutrients_enhanced: %s", ke)
            return Response(
                {"error": "An error occurred while processing food data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Unexpected error in extract_nutrients_enhanced: %s", e, exc_info=True)
            return Response(
                {"error": "An unexpected error occurred while processing food data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Audience-aware explanations (AUDIENCE-CODE-1 SHIPPED 2026-05-23).
        # ADDS the previously-missing Mozaffarian 2021 recommendation band
        # (encourage / moderate / limit) per user_type.
        # Narrow handlers (parity with HSR calculate_hsr): a broad ``except``
        # can hide typos like an undefined identifier and silently zero FCS/Nova
        # for explanations.
        try:
            fcs_val = float(result.get('fcs', 0.0))
        except (TypeError, ValueError):
            fcs_val = 0.0
        raw_nova = result.get('nova_category', 'MINIMALLY_PROCESSED')
        nova_cat = str(raw_nova) if raw_nova is not None else 'MINIMALLY_PROCESSED'
        result['explanations'] = get_fcs_explanations(
            fcs=fcs_val, nova_category=nova_cat, user_type=user_type,
        )
        # WAFCT-EXTEND (2026-05-24): per-source caveat (mineral bias).
        try:
            from api.views.wafct_caveat import build_wafct_caveat
            result['explanations'].update(build_wafct_caveat(
                food_ids, indicator='fcs', user_type=user_type,
            ))
        except Exception:  # noqa: BLE001
            pass
        result['user_type'] = user_type

        return Response({
            "success": True,
            "data": result,
            "message": "FCS calculated successfully"
        })

    except Exception as e:
        logger.error("Unexpected error in FCS calculation: %s", e, exc_info=True)
        return Response(
            {"error": "An unexpected error occurred during FCS calculation"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Batch Food Compass Score Calculator | DISH Research",
    description="Calculate Food Compass Scores (FCS) for multiple food items in a single request. Efficient batch processing for nutritional analysis.",
    keywords="FCS, batch calculation, food compass score, nutritional analysis, bulk processing, DISH Research"
)
def fcs_calculate_batch(request):
    try:
        foods_data = request.data.get('foods', [])

        if not foods_data or not isinstance(foods_data, list):
            return Response({"error": "foods array is required"}, status=status.HTTP_400_BAD_REQUEST)

        results = []

        for food_data in foods_data:
            food_name = food_data.get('food_name', f"Food Item {len(results) + 1}")
            try:
                food_ids = food_data.get('food_ids', [])
                if not food_ids:
                    results.append({
                        "food_name": food_name,
                        "error": "No food IDs provided for this item"
                    })
                    continue
                amounts = food_data.get('serving_sizes') or food_data.get('amounts_g')
                _, result = extract_and_score(food_ids, food_name, amounts_g=amounts)
                results.append(result)
            except Exception as e:
                logger.error("Error processing food item %s: %s", food_name, e)
                results.append({
                    "food_name": food_data.get('food_name', f"Food Item {len(results) + 1}"),
                    "error": f"Error processing food item: {str(e)}"
                })

        return Response({
            "success": True,
            "data": {
                "results": results,
                "total_processed": len(results),
                "successful": len([r for r in results if "error" not in r])
            },
            "message": f"Batch FCS calculation completed for {len(results)} items"
        })

    except Exception as e:
        logger.error("Unexpected error in FCS batch calculation: %s", e, exc_info=True)
        return Response(
            {"error": "An unexpected error occurred during batch FCS calculation"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Food Compass Score Profile | DISH Research",
    description="Get detailed Food Compass Score profile for a specific food item including domain breakdown and nutritional insights.",
    keywords="FCS, food profile, compass score, nutritional breakdown, domain analysis, DISH Research"
)
def get_food_fcs_profile(request, food_id):
    try:
        if not food_id:
            return Response({"error": "Food ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            food_item, result = extract_and_score([food_id], f"Food ID {food_id}")
        except ValueError as ve:
            return Response({"error": f"Food not found: {str(ve)}"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error extracting nutrients for food ID %s: %s", food_id, e)
            return Response({"error": "Error processing food data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        integrator = get_cnf_integrator()
        actual_food_name = cnf_food_description(integrator, food_id)
        domain_breakdown = per_domain_attribute_breakdown(food_item)

        return Response({
            "success": True,
            "data": {
                "food_id": food_id,
                "food_name": actual_food_name,
                "fcs_summary": result,
                "domain_breakdown": domain_breakdown,
                "attributes_count": sum(len(scores) for scores in domain_breakdown.values())
            },
            "message": f"FCS profile retrieved for {actual_food_name}"
        })

    except Exception as e:
        logger.error("Unexpected error getting FCS profile for food ID %s: %s", food_id, e, exc_info=True)
        return Response(
            {"error": "An unexpected error occurred while retrieving food profile"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Compare Food Compass Scores | DISH Research",
    description="Compare Food Compass Scores between multiple foods with detailed analysis and recommendations.",
    keywords="FCS, food comparison, compass score, nutritional comparison, food analysis, DISH Research"
)
def compare_foods_fcs(request):
    try:
        foods_data = request.data.get('foods', [])

        if not foods_data or len(foods_data) < 2:
            return Response({"error": "At least 2 foods are required for comparison"}, status=status.HTTP_400_BAD_REQUEST)

        if len(foods_data) > 10:
            return Response({"error": "Maximum 10 foods can be compared at once"}, status=status.HTTP_400_BAD_REQUEST)

        results = []

        for food_data in foods_data:
            try:
                food_ids = food_data.get('food_ids', [])
                food_name = food_data.get('food_name', f"Food {len(results) + 1}")

                if not food_ids:
                    continue

                amounts = food_data.get('serving_sizes') or food_data.get('amounts_g')
                food_item, result = extract_and_score(food_ids, food_name, amounts_g=amounts)
                out = dict(result)
                out['domain_scores'] = domain_mean_scores(food_item)
                results.append(out)

            except Exception as e:
                logger.error("Error processing food for comparison: %s", e)
                continue

        if len(results) < 2:
            return Response({"error": "Could not process enough foods for comparison"}, status=status.HTTP_400_BAD_REQUEST)

        sorted_by_fcs = sorted(results, key=lambda x: x.get('fcs', 0), reverse=True)
        best_food = sorted_by_fcs[0]
        worst_food = sorted_by_fcs[-1]

        comparison_insights = {
            "highest_fcs": {
                "food": best_food['name'],
                "fcs": best_food['fcs'],
                "nova_category": best_food['nova_category']
            },
            "lowest_fcs": {
                "food": worst_food['name'],
                "fcs": worst_food['fcs'],
                "nova_category": worst_food['nova_category']
            },
            "fcs_range": best_food['fcs'] - worst_food['fcs'],
            "average_fcs": round(sum(r['fcs'] for r in results) / len(results), 2)
        }

        return Response({
            "success": True,
            "data": {
                "foods": results,
                "comparison_insights": comparison_insights,
                "foods_count": len(results)
            },
            "message": f"FCS comparison completed for {len(results)} foods"
        })

    except Exception as e:
        logger.error("Unexpected error in FCS food comparison: %s", e, exc_info=True)
        return Response(
            {"error": "An unexpected error occurred during food comparison"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
