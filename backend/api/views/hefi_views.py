import os
import pandas as pd
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../hefi_calculator'))

from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
from hefi_calculator.hefi.models import HEFIInputs
from hefi_calculator.hefi.algorithm import compute_hefi

# Global integrator instance to avoid initialization overhead
_hefi_integrator = None

def get_hefi_integrator():
    global _hefi_integrator
    if _hefi_integrator is None:
        cnf_dir = settings.CNF_FOLDER
        _hefi_integrator = HEFICNFIntegrator(cnf_dir)
    return _hefi_integrator


def _get_food_name(food_id, integrator):
    """Helper function to get food name from CNF database"""
    try:
        food_row = integrator._get_food_rows([food_id])
        if not food_row.empty:
            return food_row.iloc[0]['FoodDescription']
        return f"Food ID {food_id}"
    except:
        return f"Food ID {food_id}"

def _format_hefi_response(result, food_ids=None, food_name=None, integrator=None):
    """Helper function to format HEFI response consistently"""
    def _interpret_hefi(total_score: float):
        # Population-based interpretation (no official grading)
        # Benchmarks from population data: mean ~43.1, p1 ~22.1, p99 ~62.9
        if total_score <= 35:
            category = "Below Average"
            description = (
                "Significantly below Canadian population mean; substantial room for improvement across multiple components."
            )
            color = "red"
        elif 36 <= total_score <= 50:
            category = "Below Average to Average"
            description = (
                "Around or slightly below Canadian population mean (~43); many Canadians fall in this range."
            )
            color = "yellow"
        elif 51 <= total_score <= 65:
            category = "Above Average"
            description = (
                "Above Canadian population mean; upper portion of typical Canadian scores."
            )
            color = "green"
        else:
            category = "Excellent"
            description = (
                "Exceptional adherence to Canada's Food Guide; near-optimal dietary pattern."
            )
            color = "emerald"

        return {
            'category': category,
            'description': description,
            'score': total_score,
            'population_benchmarks': {
                'mean': 43.1,
                'percentile_1': 22.1,
                'percentile_99': 62.9,
            },
            'notes': [
                'No official grading categories; this is a population-based interpretation.',
                'Interpret the total score alongside component scores for a complete picture.'
            ],
            'ui_color': color,
        }
    component_details = {
        'C1_VF': {'score': result.component_scores.c1_vf, 'max_points': 20, 'name': 'Vegetables and Fruits'},
        'C2_WHOLEGR': {'score': result.component_scores.c2_wholegr, 'max_points': 5, 'name': 'Whole-grain Foods'},
        'C3_GRRATIO': {'score': result.component_scores.c3_grratio, 'max_points': 5, 'name': 'Grain Foods Ratio'},
        'C4_PROFOODS': {'score': result.component_scores.c4_profoods, 'max_points': 5, 'name': 'Protein Foods'},
        'C5_PLANTPRO': {'score': result.component_scores.c5_plantpro, 'max_points': 5, 'name': 'Plant-based Protein Foods'},
        'C6_BEVERAGES': {'score': result.component_scores.c6_beverages, 'max_points': 10, 'name': 'Beverages'},
        'C7_FATTYACID': {'score': result.component_scores.c7_fattyacid, 'max_points': 5, 'name': 'Fatty Acids Ratio'},
        'C8_SFAT': {'score': result.component_scores.c8_sfat, 'max_points': 5, 'name': 'Saturated Fats'},
        'C9_FREESUGARS': {'score': result.component_scores.c9_freesugars, 'max_points': 10, 'name': 'Free Sugars'},
        'C10_SODIUM': {'score': result.component_scores.c10_sodium, 'max_points': 10, 'name': 'Sodium'},
    }
    
    data = {
        'food_ids': food_ids,
        'food_name': food_name,
        'total_score': result.total_score,
        'max_total_score': 80,
        'percentage': (result.total_score / 80) * 100,
        'ratios': result.ratios,
        'components': component_details,
        'inputs': {
            'total_foods_ra': result.inputs.total_foods_ra,
            'energy_kcal': result.inputs.energy_kcal,
            'vf_ra': result.inputs.vf_ra,
            'whole_grains_ra': result.inputs.whole_grains_ra,
            'total_grains_ra': result.inputs.total_grains_ra,
            'protein_foods_ra': result.inputs.protein_foods_ra,
            'plant_protein_foods_ra': result.inputs.plant_protein_foods_ra,
            'total_beverages_g': result.inputs.total_beverages_g,
            'recommended_beverages_g': result.inputs.recommended_beverages_g,
            'sfa_g': result.inputs.sfa_g,
            'mufa_g': result.inputs.mufa_g,
            'pufa_g': result.inputs.pufa_g,
            'free_sugars_g': result.inputs.free_sugars_g,
            'sodium_mg': result.inputs.sodium_mg,
        },
        'hefi_interpretation': _interpret_hefi(result.total_score),
    }
    
    return data

@api_view(['POST'])
@permission_classes([AllowAny])
def hefi_calculate(request):
    """
    Calculate HEFI score for foods with specified quantities.
    Expected input: {
        "foods": [
            {"food_id": 3049, "amount_g": 100.0},
            {"food_id": 3725, "amount_g": 75.0}
        ]
    }
    """
    try:
        foods_data = request.data.get('foods')
        
        if not foods_data:
            return Response({"error": "'foods' array with food_id and amount_g is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(foods_data, list) or len(foods_data) == 0:
            return Response({"error": "Foods array cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        food_data = []
        food_ids = []
        total_amount = 0
        
        for food_item in foods_data:
            food_id = food_item.get('food_id')
            amount_g = food_item.get('amount_g')
            
            if not food_id:
                return Response({"error": "Each food item must have a food_id"}, status=status.HTTP_400_BAD_REQUEST)
            
            if amount_g is None:
                return Response({"error": "Each food item must have an amount_g"}, status=status.HTTP_400_BAD_REQUEST)
            
            if amount_g <= 0:
                return Response({"error": "Amount must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
            
            food_data.append((food_id, float(amount_g)))
            food_ids.append(food_id)
            total_amount += amount_g

        integrator = get_hefi_integrator()
        agg = integrator.aggregate_inputs(food_data)
        inputs = HEFIInputs(**agg)
        result = compute_hefi(inputs)

        # Get food name
        if len(food_ids) == 1:
            amount = food_data[0][1]
            base_name = _get_food_name(food_ids[0], integrator)
            food_name = f"{base_name} ({amount}g)"
        else:
            food_name = f"Meal with {len(food_ids)} foods ({total_amount}g total)"

        data = _format_hefi_response(result, food_ids, food_name, integrator)
        
        # Add detailed food breakdown
        food_breakdown = []
        for (food_id, amount_g) in food_data:
            food_info = {
                'food_id': food_id,
                'amount_g': amount_g,
                'name': _get_food_name(food_id, integrator)
            }
            
            # Get RA classification for this food
            try:
                food_rows = integrator._get_food_rows([food_id])
                if not food_rows.empty:
                    food_row = food_rows.iloc[0]
                    food_description = food_row['FoodDescription']
                    food_group_id = int(food_row['FoodGroupID'])
                    
                    ra_category = integrator._classify_food_to_ra_category(food_description, food_group_id)
                    ra_amount_g = integrator._get_ra_amount(ra_category)
                    calculated_ra = amount_g / ra_amount_g
                    
                    # Get conversion factor and measure description
                    conversion_factor = integrator._get_best_conversion_factor(food_id)
                    measure_description = integrator.get_measure_description(food_id, conversion_factor)
                    
                    # Remove debug logging
                    # if measure_description == "Unknown measure":
                    #     print(f"DEBUG: No measure description found for Food ID {food_id}, conversion factor {conversion_factor}")
                    
                    food_info.update({
                        'group_id': food_group_id,
                        'ra_category': ra_category,
                        'ra_amount_g': ra_amount_g,
                        'calculated_ra': round(calculated_ra, 3),
                        'conversion_factor': conversion_factor,
                        'measure_description': measure_description
                    })
            except Exception as e:
                food_info['ra_error'] = f"Could not calculate RA: {str(e)}"
            
            food_breakdown.append(food_info)
        
        data['food_breakdown'] = food_breakdown

        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_food_hefi_profile(request, food_id):
    """
    Get detailed HEFI profile for a specific food ID
    Returns comprehensive breakdown including component scores and nutritional inputs
    """
    try:
        if not food_id:
            return Response({"error": "Food ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        integrator = get_hefi_integrator()
        
        try:
            # Use amount_g from query parameters, require it to be specified
            amount_g = request.GET.get('amount_g')
            if amount_g is None:
                return Response({"error": "amount_g query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            amount_g = float(amount_g)
            if amount_g <= 0:
                return Response({"error": "Amount must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
            
            food_data = [(food_id, amount_g)]
            agg = integrator.aggregate_inputs(food_data)
            inputs = HEFIInputs(**agg)
            result = compute_hefi(inputs)
        except Exception as e:
            return Response({"error": f"Food not found or processing error: {str(e)}"}, status=status.HTTP_404_NOT_FOUND)
        
        base_name = _get_food_name(food_id, integrator)
        food_name = f"{base_name} ({amount_g}g)"
        data = _format_hefi_response(result, [food_id], food_name, integrator)
        
        # Add RA classification details
        try:
            food_rows = integrator._get_food_rows([food_id])
            if not food_rows.empty:
                food_row = food_rows.iloc[0]
                food_description = food_row['FoodDescription']
                food_group_id = int(food_row['FoodGroupID'])
                
                ra_category = integrator._classify_food_to_ra_category(food_description, food_group_id)
                ra_amount_g = integrator._get_ra_amount(ra_category)
                calculated_ra = amount_g / ra_amount_g
                
                data['ra_details'] = {
                    'amount_g': amount_g,
                    'ra_category': ra_category,
                    'ra_amount_g': ra_amount_g,
                    'calculated_ra': round(calculated_ra, 3),
                    'group_id': food_group_id,
                    'description': food_description,
                    'classification_confidence': 'high' if ra_category != 'default' else 'low'
                }
        except Exception as e:
            data['ra_details'] = {'error': f"Could not calculate RA details: {str(e)}"}
        
        # Add conversion factor information
        try:
            conversion_factor = integrator._get_best_conversion_factor(food_id)
            measure_description = integrator.get_measure_description(food_id, conversion_factor)
            
            measure_info = {
                "conversion_factor": conversion_factor,
                "measure_description": measure_description
            }
            
            # Add all available measures for this food
            if not integrator.conversion_factors_df.empty and not integrator.measure_names_df.empty:
                food_factors = integrator.conversion_factors_df[
                    integrator.conversion_factors_df['FoodID'] == food_id
                ].copy()
                
                # Ensure MeasureID columns are the same type for proper merging
                food_factors['MeasureID'] = food_factors['MeasureID'].astype(int)
                measure_names_subset = integrator.measure_names_df[['MeasureID', 'MeasureDescription']].copy()
                measure_names_subset['MeasureID'] = measure_names_subset['MeasureID'].astype(int)
                
                merged_factors = food_factors.merge(
                    measure_names_subset, 
                    on='MeasureID', 
                    how='left'
                )
                
                available_measures = []
                for _, row in merged_factors.iterrows():
                    measure_desc = row.get('MeasureDescription', '')
                    if pd.notna(measure_desc) and str(measure_desc).strip():
                        available_measures.append({
                            'measure_id': int(row.get('MeasureID', 0)),
                            'description': str(measure_desc).strip(),
                            'conversion_factor': float(row['ConversionFactorValue'])
                        })
                
                measure_info['available_measures'] = available_measures
                measure_info['total_measures_found'] = len(available_measures)
        except Exception as e:
            measure_info = {'error': f'Could not get measure info: {str(e)}'}
        
        data['measure_info'] = measure_info
        
        # Add HEFI interpretation based on population benchmarks
        data['hefi_interpretation'] = {
            **_format_hefi_response(result)['hefi_interpretation']
        }
        
        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def compare_foods_hefi(request):
    """
    Compare HEFI scores between multiple meals (or foods)
    Supports two input formats per item:
      1) Meal format (recommended):
         {"food_name": "Meal A", "food_items": [{"food_id": 3049, "amount_g": 120.0}, {"food_id": 3725, "amount_g": 80.0}]}
      2) Legacy format (backward compatible):
         {"food_ids": [3049, 3725], "food_name": "Meal A", "amount_g": 100.0}  # same grams applied to each food
         or {"food_ids": [3049]}  # defaults to 100g
    """
    try:
        foods_data = request.data.get('foods', [])
        
        if not foods_data or len(foods_data) < 2:
            return Response({"error": "At least 2 foods are required for comparison"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(foods_data) > 10:
            return Response({"error": "Maximum 10 foods can be compared at once"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        integrator = get_hefi_integrator()
        
        # Calculate HEFI for each food/meal
        for food_data in foods_data:
            try:
                food_name = food_data.get('food_name')

                food_input_data = []
                food_ids = []

                # Preferred: meal format with explicit amounts per item
                food_items = food_data.get('food_items')
                if isinstance(food_items, list) and len(food_items) > 0:
                    for item in food_items:
                        item_food_id = item.get('food_id')
                        item_amount_g = item.get('amount_g')
                        if item_food_id is None:
                            raise ValueError("Each food item must include 'food_id'")
                        if item_amount_g is None or float(item_amount_g) <= 0:
                            raise ValueError("Each food item must include a positive 'amount_g'")
                        food_input_data.append((int(item_food_id), float(item_amount_g)))
                        food_ids.append(int(item_food_id))
                else:
                    # Backward compatible: food_ids plus optional single amount applied to all
                    food_ids = food_data.get('food_ids', [])
                    if not food_ids:
                        raise ValueError("'food_ids' or 'food_items' is required")
                    if 'amount_g' in food_data and food_data['amount_g']:
                        amount_g = float(food_data.get('amount_g', 100.0))
                        if amount_g <= 0:
                            raise ValueError("amount_g must be greater than 0")
                        food_input_data = [(int(fid), amount_g) for fid in food_ids]
                    else:
                        # default 100g per item
                        food_input_data = [(int(fid), 100.0) for fid in food_ids]

                # If no name provided, generate one
                if not food_name:
                    if len(food_ids) == 1:
                        food_name = _get_food_name(food_ids[0], integrator)
                    else:
                        total_g = sum(amount for _, amount in food_input_data)
                        food_name = f"Meal with {len(food_ids)} foods ({int(total_g)}g)"
                
                agg = integrator.aggregate_inputs(food_input_data)
                inputs = HEFIInputs(**agg)
                result = compute_hefi(inputs)
                
                data = _format_hefi_response(result, food_ids, food_name, integrator)
                results.append(data)
                
            except Exception as e:
                # Add error entry for this food but continue with others
                results.append({
                    'food_ids': food_data.get('food_ids') or [fi.get('food_id') for fi in food_data.get('food_items', [])],
                    'food_name': food_data.get('food_name', 'Unknown'),
                    'error': f"Error processing: {str(e)}",
                    'total_score': 0,
                    'percentage': 0
                })
        
        # Sort by total score (highest first)
        results.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        # Add comparison insights
        valid_results = [r for r in results if 'error' not in r]
        if len(valid_results) >= 2:
            highest_score = max(r['total_score'] for r in valid_results)
            lowest_score = min(r['total_score'] for r in valid_results)
            average_score = sum(r['total_score'] for r in valid_results) / len(valid_results)
            
            comparison_insights = {
                'highest_score': highest_score,
                'lowest_score': lowest_score,
                'average_score': average_score,
                'score_range': highest_score - lowest_score,
                'best_performing': valid_results[0]['food_name'] if valid_results else 'N/A',
                'component_analysis': _analyze_component_differences(valid_results)
            }
        else:
            # Keep response schema stable for clients/tests
            comparison_insights = {
                "message": "Insufficient valid results for comparison",
                "highest_score": None,
                "lowest_score": None,
                "average_score": None,
                "score_range": None,
                "best_performing": None,
                "component_analysis": {}
            }
        
        return Response({
            'success': True,
            'data': {
                'foods': results,
                'comparison_insights': comparison_insights,
                'total_compared': len(results)
            }
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _analyze_component_differences(results):
    """Analyze which components show the most variation between foods"""
    component_names = ['C1_VF', 'C2_WHOLEGR', 'C3_GRRATIO', 'C4_PROFOODS', 'C5_PLANTPRO', 
                      'C6_BEVERAGES', 'C7_FATTYACID', 'C8_SFAT', 'C9_FREESUGARS', 'C10_SODIUM']
    
    component_variations = {}
    for comp in component_names:
        scores = [r['components'][comp]['score'] for r in results]
        if len(scores) > 1:
            variation = max(scores) - min(scores)
            component_variations[comp] = {
                'variation': variation,
                'max_score': max(scores),
                'min_score': min(scores),
                'component_name': results[0]['components'][comp]['name']
            }
    
    # Sort by variation (highest first)
    sorted_variations = dict(sorted(component_variations.items(), 
                                  key=lambda x: x[1]['variation'], reverse=True))
    
    return sorted_variations


