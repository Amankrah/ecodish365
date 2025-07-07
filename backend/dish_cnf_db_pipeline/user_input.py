import pandas as pd
from django.core.exceptions import ValidationError
import logging

class FoodInputValidator:
    def __init__(self, cnf_pipeline):
        self.data_loader = cnf_pipeline.data_loader
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Valid Nutrient Source IDs: {set(self.data_loader.nutrient_source_df['NutrientSourceID'].tolist())}")

    def validate_food_description(self, description):
        if not description or len(description.strip()) < 3:
            raise ValidationError("Food description must be at least 3 characters long.")
        return description.strip()

    def validate_food_group_ids(self, food_group_ids):
        valid_ids = set(self.data_loader.food_group_df['FoodGroupID'].tolist())
        invalid_ids = set(food_group_ids) - valid_ids
        if invalid_ids:
            raise ValidationError(f"Invalid Food Group ID(s) provided: {', '.join(map(str, invalid_ids))}")
        return food_group_ids

    def validate_food_source_id(self, food_source_id):
        if food_source_id not in self.data_loader.food_source_df['FoodSourceID'].tolist():
            raise ValidationError(f"Invalid Food Source ID provided: {food_source_id}")
        return food_source_id

    def validate_country_code(self, country_code):
        if not country_code or len(country_code) != 2:
            raise ValidationError("Country code must be a 2-letter code.")
        return country_code.upper()

    def validate_nutrient_values(self, nutrient_values):
        valid_nutrient_ids = set(self.data_loader.nutrient_name_df['NutrientID'].tolist())
        errors = []
        for nv in nutrient_values:
            if nv['NutrientID'] not in valid_nutrient_ids:
                errors.append(f"Invalid Nutrient ID: {nv['NutrientID']}")
            try:
                nutrient_value = float(nv['NutrientValue'])
                if nutrient_value < 0:
                    errors.append(f"Nutrient Value must be non-negative for Nutrient ID {nv['NutrientID']}")
            except ValueError:
                errors.append(f"Nutrient Value must be a number for Nutrient ID {nv['NutrientID']}")
        if errors:
            raise ValidationError(errors)
        return nutrient_values

    def process_new_food_input(self, data):
        try:
            validated_data = {
                'FoodDescription': self.validate_food_description(data.get('FoodDescription', '')),
                'FoodDescriptionF': data.get('FoodDescriptionF', '').strip(),
                'FoodGroupIDs': self.validate_food_group_ids(data.get('FoodGroupIDs', [])),
                'FoodSourceID': self.validate_food_source_id(data.get('FoodSourceID', '')),
                'CountryCode': self.validate_country_code(data.get('CountryCode', '')),
                'NutrientValues': self.validate_nutrient_values(data.get('NutrientValues', [])),
                'ConversionFactors': data.get('ConversionFactors', []),
                'ScientificName': data.get('ScientificName', '').strip()  # Making ScientificName optional
            }
            return validated_data
        except ValidationError as e:
            self.logger.error(f"Validation error in process_new_food_input: {str(e)}")
            raise ValidationError(f"Invalid input: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in process_new_food_input: {str(e)}")
            raise e

def get_food_groups(food_group_df):
    return food_group_df[['FoodGroupID', 'FoodGroupName']].to_dict('records')

def get_nutrient_info(nutrient_name_df):
    return nutrient_name_df[['NutrientID', 'NutrientName']].to_dict('records')

def get_conversion_factors(measure_name_df):
    return measure_name_df[['MeasureID', 'MeasureDescription']].to_dict('records')

def get_food_sources(food_source_df):
    return food_source_df[['FoodSourceID', 'FoodSourceDescription']].to_dict('records')

def get_nutrient_sources(nutrient_source_df):
    return nutrient_source_df[['NutrientSourceID', 'NutrientSourceDescription']].to_dict('records')