import os
import pandas as pd
from chardet import detect
from datetime import datetime

class CNFDataPipeline:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.load_all_dataframes()

    def load_all_dataframes(self):
        csv_files = [
            'FOOD_NAME', 'NUTRIENT_AMOUNT', 'CONVERSION_FACTOR', 'FOOD_GROUP',
            'FOOD_SOURCE', 'NUTRIENT_NAME', 'NUTRIENT_SOURCE', 'MEASURE_NAME',
            'REFUSE_AMOUNT', 'YIELD_AMOUNT', 'REFUSE_NAME', 'YIELD_NAME'
        ]
        for file in csv_files:
            setattr(self, f"{file.lower()}_df", self._load_csv(f"{file}.csv"))

    def _detect_encoding(self, file_path):
        with open(file_path, 'rb') as f:
            result = detect(f.read())
            return result['encoding']

    def _load_csv(self, file_name):
        file_path = os.path.join(self.data_dir, file_name)
        encoding = self._detect_encoding(file_path)
        
        # Define dtypes for columns that might have mixed types
        dtypes = {
            'FoodID': 'Int64',
            'FoodCode': 'str',
            'FoodGroupID': 'Int64',
            'FoodSourceID': 'Int64',
            'NutrientID': 'Int64',
            'NutrientSourceID': 'Int64',
            'MeasureID': 'Int64',
            'RefuseID': 'Int64',
            'YieldID': 'Int64'
        }
        
        # Read CSV with low_memory=False and specified dtypes
        df = pd.read_csv(file_path, encoding=encoding, low_memory=False, dtype=dtypes)
        
        # Convert date columns to datetime
        date_columns = [col for col in df.columns if 'Date' in col]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df

    def _save_csv(self, df, file_name):
        file_path = os.path.join(self.data_dir, file_name)
        encoding = self._detect_encoding(file_path)
        df.to_csv(file_path, index=False, encoding=encoding)

    def _get_next_unique_id(self, column_name, dataframe):
        if pd.api.types.is_integer_dtype(dataframe[column_name]):
            max_id = dataframe[column_name].max()
            return max_id + 1 if not pd.isnull(max_id) else 1
        else:
            raise ValueError(f"Column {column_name} must be of integer type.")

    def get_next_id(self, id_type):
        id_mappings = {
            'FoodID': ('food_name_df', 'FoodID'),
            'NutrientID': ('nutrient_name_df', 'NutrientID'),
            'MeasureID': ('measure_name_df', 'MeasureID'),
            'FoodGroupID': ('food_group_df', 'FoodGroupID'),
            'FoodSourceID': ('food_source_df', 'FoodSourceID'),
            'NutrientSourceID': ('nutrient_source_df', 'NutrientSourceID'),
            'RefuseID': ('refuse_name_df', 'RefuseID'),
            'YieldID': ('yield_name_df', 'YieldID')
        }
        
        if id_type not in id_mappings:
            raise ValueError(f"Unknown ID type: {id_type}")
        
        df_name, column_name = id_mappings[id_type]
        return self._get_next_unique_id(column_name, getattr(self, df_name))

    def validate_new_food(self, new_food):
        required_fields = [
            'FoodDescription', 'FoodDescriptionF', 'FoodGroupID', 'FoodSourceID',
            'CountryCode', 'ScientificName', 'NutrientValues'
        ]
        
        for field in required_fields:
            if field not in new_food:
                raise ValueError(f"Missing required field: {field}")

        if new_food['FoodGroupID'] not in self.food_group_df['FoodGroupID'].values:
            raise ValueError("Invalid FoodGroupID.")
        if new_food['FoodSourceID'] not in self.food_source_df['FoodSourceID'].values:
            raise ValueError("Invalid FoodSourceID.")
        
        for nutrient in new_food['NutrientValues']:
            if nutrient['NutrientID'] not in self.nutrient_name_df['NutrientID'].values:
                raise ValueError(f"Invalid NutrientID: {nutrient['NutrientID']}")
            if nutrient['NutrientSourceID'] not in self.nutrient_source_df['NutrientSourceID'].values:
                raise ValueError(f"Invalid NutrientSourceID: {nutrient['NutrientSourceID']}")

    def add_new_food(self, new_food):
        self.validate_new_food(new_food)
        
        new_food['FoodID'] = self.get_next_id('FoodID')
        new_food['FoodCode'] = new_food.get('FoodCode', str(new_food['FoodID']).zfill(8))
        
        new_food_entry = pd.DataFrame({
            'FoodID': [new_food['FoodID']],
            'FoodCode': [new_food['FoodCode']],
            'FoodGroupID': [new_food['FoodGroupID']],
            'FoodSourceID': [new_food['FoodSourceID']],
            'FoodDescription': [new_food['FoodDescription']],
            'FoodDescriptionF': [new_food['FoodDescriptionF']],
            'CountryCode': [new_food['CountryCode']],
            'FoodDateOfEntry': [datetime.today().strftime('%Y/%m/%d')],
            'FoodDateOfPublication': [new_food.get('FoodDateOfPublication', '')],
            'ScientificName': [new_food['ScientificName']]
        })
        self.food_name_df = pd.concat([self.food_name_df, new_food_entry], ignore_index=True)
        
        for nutrient in new_food['NutrientValues']:
            new_nutrient_entry = pd.DataFrame({
                'FoodID': [new_food['FoodID']],
                'NutrientID': [nutrient['NutrientID']],
                'NutrientValue': [nutrient['NutrientValue']],
                'StandardError': [nutrient.get('StandardError', '')],
                'NumberOfObservations': [nutrient.get('NumberOfObservations', '')],
                'NutrientSourceID': [nutrient['NutrientSourceID']],
                'NutrientDateEntry': [datetime.today().strftime('%Y/%m/%d')]
            })
            self.nutrient_amount_df = pd.concat([self.nutrient_amount_df, new_nutrient_entry], ignore_index=True)
        
        if 'ConversionFactors' in new_food:
            for factor in new_food['ConversionFactors']:
                new_conversion_entry = pd.DataFrame({
                    'FoodID': [new_food['FoodID']],
                    'MeasureID': [factor['MeasureID']],
                    'ConversionFactorValue': [factor['ConversionFactorValue']],
                    'ConvFactorDateOfEntry': [datetime.today().strftime('%Y/%m/%d')]
                })
                self.conversion_factor_df = pd.concat([self.conversion_factor_df, new_conversion_entry], ignore_index=True)
        
        if 'RefuseAmount' in new_food:
            new_refuse_entry = pd.DataFrame({
                'FoodID': [new_food['FoodID']],
                'RefuseID': [new_food['RefuseAmount']['RefuseID']],
                'RefuseAmount': [new_food['RefuseAmount']['RefuseAmount']],
                'RefuseDateOfEntry': [datetime.today().strftime('%Y/%m/%d')]
            })
            self.refuse_amount_df = pd.concat([self.refuse_amount_df, new_refuse_entry], ignore_index=True)

        if 'YieldAmount' in new_food:
            new_yield_entry = pd.DataFrame({
                'FoodID': [new_food['FoodID']],
                'YieldID': [new_food['YieldAmount']['YieldID']],
                'YieldAmount': [new_food['YieldAmount']['YieldAmount']],
                'YieldDateOfEntry': [datetime.today().strftime('%Y/%m/%d')]
            })
            self.yield_amount_df = pd.concat([self.yield_amount_df, new_yield_entry], ignore_index=True)

        self._save_all_dataframes()
        return new_food['FoodID']

    def _save_all_dataframes(self):
        dataframes = [
            ('food_name_df', 'FOOD_NAME.csv'),
            ('nutrient_amount_df', 'NUTRIENT_AMOUNT.csv'),
            ('conversion_factor_df', 'CONVERSION_FACTOR.csv'),
            ('refuse_amount_df', 'REFUSE_AMOUNT.csv'),
            ('yield_amount_df', 'YIELD_AMOUNT.csv')
        ]
        for df_name, file_name in dataframes:
            self._save_csv(getattr(self, df_name), file_name)

    def add_food_interactive(self):
        new_food = {}
        
        new_food['FoodDescription'] = input("Enter food description in English: ")
        new_food['FoodDescriptionF'] = input("Enter food description in French: ")
        
        print("\nAvailable Food Groups:")
        print(self.food_group_df[['FoodGroupID', 'FoodGroupName']])
        new_food['FoodGroupID'] = int(input("Enter FoodGroupID: "))
        
        print("\nAvailable Food Sources:")
        print(self.food_source_df[['FoodSourceID', 'FoodSourceDescription']])
        new_food['FoodSourceID'] = int(input("Enter FoodSourceID: "))
        
        new_food['CountryCode'] = input("Enter Country Code (e.g., CA for Canada): ")
        new_food['ScientificName'] = input("Enter Scientific Name (if applicable): ")
        
        new_food['NutrientValues'] = []
        while True:
            print("\nAvailable Nutrients:")
            try:
                print(self.nutrient_name_df[['NutrientID', 'NutrientName']])
            except KeyError as e:
                print(f"Warning: Column {e} not found in nutrient_name_df. Displaying available columns.")
                print(self.nutrient_name_df.columns)
                print(self.nutrient_name_df)
            
            nutrient_id = input("Enter NutrientID (or press Enter to finish adding nutrients): ")
            if not nutrient_id:
                break
            try:
                nutrient_value = float(input("Enter Nutrient Value: "))
                print("\nAvailable Nutrient Sources:")
                print(self.nutrient_source_df[['NutrientSourceID', 'NutrientSourceDescription']])
                nutrient_source_id = int(input("Enter NutrientSourceID: "))
                new_food['NutrientValues'].append({
                    'NutrientID': int(nutrient_id),
                    'NutrientValue': nutrient_value,
                    'NutrientSourceID': nutrient_source_id
                })
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        
        # Add conversion factors
        new_food['ConversionFactors'] = []
        while True:
            print("\nAvailable Measures:")
            try:
                columns_to_display = ['MeasureID']
                if 'MeasureName' in self.measure_name_df.columns:
                    columns_to_display.append('MeasureName')
                print(self.measure_name_df[columns_to_display])
            except KeyError as e:
                print(f"Warning: Column {e} not found in measure_name_df. Displaying available columns.")
                print(self.measure_name_df.columns)
                print(self.measure_name_df)
            
            measure_id = input("Enter MeasureID for conversion factor (or press Enter to finish): ")
            if not measure_id:
                break
            try:
                conversion_value = float(input("Enter Conversion Factor Value: "))
                new_food['ConversionFactors'].append({
                    'MeasureID': int(measure_id),
                    'ConversionFactorValue': conversion_value
                })
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        
        # Add refuse amount
        add_refuse = input("Do you want to add refuse amount? (y/n): ").lower()
        if add_refuse == 'y':
            print("\nAvailable Refuse Types:")
            try:
                print(self.refuse_name_df[['RefuseID', 'RefuseName']])
            except KeyError as e:
                print(f"Warning: Column {e} not found in refuse_name_df. Displaying available columns.")
                print(self.refuse_name_df.columns)
                print(self.refuse_name_df)
            
            refuse_id = int(input("Enter RefuseID: "))
            refuse_amount = float(input("Enter Refuse Amount (%): "))
            new_food['RefuseAmount'] = {
                'RefuseID': refuse_id,
                'RefuseAmount': refuse_amount
            }
        
        # Add yield amount
        add_yield = input("Do you want to add yield amount? (y/n): ").lower()
        if add_yield == 'y':
            print("\nAvailable Yield Types:")
            try:
                print(self.yield_name_df[['YieldID', 'YieldName']])
            except KeyError as e:
                print(f"Warning: Column {e} not found in yield_name_df. Displaying available columns.")
                print(self.yield_name_df.columns)
                print(self.yield_name_df)
            
            yield_id = int(input("Enter YieldID: "))
            yield_amount = float(input("Enter Yield Amount: "))
            new_food['YieldAmount'] = {
                'YieldID': yield_id,
                'YieldAmount': yield_amount
            }
        
        food_id = self.add_new_food(new_food)
        print(f"\nNew food added successfully with FoodID: {food_id}")

# Example usage
if __name__ == "__main__":
    data_dir = 'raw_cnf'
    cnf_pipeline = CNFDataPipeline(data_dir)
    
    # Interactive food addition
    cnf_pipeline.add_food_interactive()