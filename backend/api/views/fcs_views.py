import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from fcs_calculator.fcs.models.food_item import FoodItem
from fcs_calculator.fcs.utils.cnf_data_integrator import create_cnf_integrator
from fcs_calculator.fcs.analyzers.food_analyzer import FoodAnalyzer
from api.seo_utils import seo_metadata

logger = logging.getLogger(__name__)

class InvalidScoreError(ValueError):
    pass

@api_view(['POST'])
@seo_metadata(
    title="Food Compass Score Calculator | DISH Research",
    description="Calculate the Food Compass Score (FCS) for your food items. Analyze nutritional content and get detailed FCS results.",
    keywords="FCS, food compass score, nutritional analysis, food science, DISH Research"
)
def fcs_calculate(request):
    try:
        food_ids = request.data.get('food_ids', [])
        food_names = request.data.get('food_names', [])
        
        if not food_ids:
            return Response({"error": "No food IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create descriptive name for combined foods
        if len(food_ids) > 1:
            food_name = f"Combined Food ({len(food_ids)} items)"
            if food_names:
                food_name = " + ".join(food_names[:3])  # Show first 3 names
                if len(food_names) > 3:
                    food_name += f" + {len(food_names)-3} more"
        else:
            food_name = food_names[0] if food_names else "Single Food Item"
        
        food_item = FoodItem(food_name)
        
        try:
            # Use enhanced CNF integrator with FCS 2.0 implementation
            cnf_integrator = create_cnf_integrator()
            cnf_integrator.extract_nutrients_enhanced(food_ids, food_item)
        except KeyError as ke:
            logger.error(f"Data inconsistency in extract_nutrients_enhanced: {str(ke)}")
            return Response({"error": "An error occurred while processing food data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in extract_nutrients_enhanced: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred while processing food data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        analyzer = FoodAnalyzer()
        try:
            result = analyzer.analyze_food_item(food_item)
        except InvalidScoreError as ise:
            logger.error(f"Invalid score error in analyze_food_item: {str(ise)}")
            return Response({"error": "An error occurred while analyzing the food item"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "success": True,
            "data": result,
            "message": "FCS calculated successfully"
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in FCS calculation: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred during FCS calculation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@seo_metadata(
    title="Batch Food Compass Score Calculator | DISH Research",
    description="Calculate Food Compass Scores (FCS) for multiple food items in a single request. Efficient batch processing for nutritional analysis.",
    keywords="FCS, batch calculation, food compass score, nutritional analysis, bulk processing, DISH Research"
)
def fcs_calculate_batch(request):
    """
    Calculate FCS for multiple food items in batch
    Expected input: {
        "foods": [
            {"food_ids": [2003, 3580], "food_name": "Salmon with Rice"},
            {"food_ids": [2892], "food_name": "Broccoli"}
        ]
    }
    """
    try:
        foods_data = request.data.get('foods', [])
        
        if not foods_data or not isinstance(foods_data, list):
            return Response({"error": "foods array is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        cnf_integrator = create_cnf_integrator()
        analyzer = FoodAnalyzer()
        
        for food_data in foods_data:
            try:
                food_ids = food_data.get('food_ids', [])
                food_name = food_data.get('food_name', f"Food Item {len(results) + 1}")
                
                if not food_ids:
                    results.append({
                        "food_name": food_name,
                        "error": "No food IDs provided for this item"
                    })
                    continue
                
                # Create and populate food item
                food_item = FoodItem(food_name)
                cnf_integrator.extract_nutrients_enhanced(food_ids, food_item)
                
                # Analyze food item
                result = analyzer.analyze_food_item(food_item)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing food item {food_name}: {str(e)}")
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
        logger.error(f"Unexpected error in FCS batch calculation: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred during batch FCS calculation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@seo_metadata(
    title="Food Compass Score Profile | DISH Research", 
    description="Get detailed Food Compass Score profile for a specific food item including domain breakdown and nutritional insights.",
    keywords="FCS, food profile, compass score, nutritional breakdown, domain analysis, DISH Research"
)
def get_food_fcs_profile(request, food_id):
    """
    Get detailed FCS profile for a specific food ID
    Returns comprehensive breakdown including domain scores and nutritional attributes
    """
    try:
        if not food_id:
            return Response({"error": "Food ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create food item with single food ID
        food_item = FoodItem(f"Food ID {food_id}")
        
        try:
            cnf_integrator = create_cnf_integrator()
            cnf_integrator.extract_nutrients_enhanced([food_id], food_item)
        except ValueError as ve:
            return Response({"error": f"Food not found: {str(ve)}"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error extracting nutrients for food ID {food_id}: {str(e)}")
            return Response({"error": "Error processing food data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Analyze with detailed breakdown
        analyzer = FoodAnalyzer()
        result = analyzer.analyze_food_item(food_item)
        
        # Add detailed domain breakdown
        domain_breakdown = {}
        for domain, attributes in food_item.attributes.items():
            domain_scores = {}
            for attribute, value in attributes.items():
                if value > 0:  # Only include non-zero values
                    try:
                        attribute_type = analyzer.get_attribute_type(attribute)
                        score = analyzer.score_attribute(value, attribute, attribute_type)
                        domain_scores[attribute] = {
                            "value": round(value, 3),
                            "score": round(score, 2),
                            "type": attribute_type.name
                        }
                    except ValueError:
                        continue
            
            if domain_scores:
                domain_breakdown[domain] = domain_scores
        
        # Get food name from CNF if available
        try:
            cnf_integrator = create_cnf_integrator()
            food_info = cnf_integrator.cnf_pipeline.food_name_df[
                cnf_integrator.cnf_pipeline.food_name_df['FoodID'] == food_id
            ]
            actual_food_name = food_info['FoodDescription'].iloc[0] if not food_info.empty else f"Food ID {food_id}"
        except:
            actual_food_name = f"Food ID {food_id}"
        
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
        logger.error(f"Unexpected error getting FCS profile for food ID {food_id}: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred while retrieving food profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@seo_metadata(
    title="Compare Food Compass Scores | DISH Research",
    description="Compare Food Compass Scores between multiple foods with detailed analysis and recommendations.",
    keywords="FCS, food comparison, compass score, nutritional comparison, food analysis, DISH Research"
)
def compare_foods_fcs(request):
    """
    Compare FCS scores between multiple foods
    Expected input: {
        "foods": [
            {"food_ids": [2003], "food_name": "Salmon"},
            {"food_ids": [2892], "food_name": "Broccoli"},
            {"food_ids": [3580], "food_name": "Brown Rice"}
        ]
    }
    """
    try:
        foods_data = request.data.get('foods', [])
        
        if not foods_data or len(foods_data) < 2:
            return Response({"error": "At least 2 foods are required for comparison"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(foods_data) > 10:
            return Response({"error": "Maximum 10 foods can be compared at once"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        cnf_integrator = create_cnf_integrator()
        analyzer = FoodAnalyzer()
        
        # Calculate FCS for each food
        for food_data in foods_data:
            try:
                food_ids = food_data.get('food_ids', [])
                food_name = food_data.get('food_name', f"Food {len(results) + 1}")
                
                if not food_ids:
                    continue
                
                food_item = FoodItem(food_name)
                cnf_integrator.extract_nutrients_enhanced(food_ids, food_item)
                result = analyzer.analyze_food_item(food_item)
                
                # Add domain scores for comparison
                domain_scores = {}
                raw_domain_scores = {domain: [] for domain in food_item.attributes.keys()}
                
                for domain, attributes in food_item.attributes.items():
                    for attribute, value in attributes.items():
                        try:
                            attribute_type = analyzer.get_attribute_type(attribute)
                            score = analyzer.score_attribute(value, attribute, attribute_type)
                            raw_domain_scores[domain].append(score)
                        except ValueError:
                            continue
                
                # Calculate domain averages (simplified)
                for domain, scores in raw_domain_scores.items():
                    if scores:
                        domain_scores[domain] = round(sum(scores) / len(scores), 2)
                    else:
                        domain_scores[domain] = 0
                
                result['domain_scores'] = domain_scores
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing food for comparison: {str(e)}")
                continue
        
        if len(results) < 2:
            return Response({"error": "Could not process enough foods for comparison"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate comparison insights
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
        logger.error(f"Unexpected error in FCS food comparison: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred during food comparison"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)