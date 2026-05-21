# HEFI-2019 Scoring Algorithm: Technical Expert Report

## Executive Summary

The Healthy Eating Food Index (HEFI)-2019 is a scoring tool developed to measure adherence to recommendations on healthy food choices in Canada's Food Guide 2019. The HEFI-2019 has 10 components, of which 5 are based on the intake of foods, 1 on beverages, and 4 on nutrients. The total HEFI-2019 score has a maximum of 80 points.

## 1. Overview and Architecture

### 1.1 Core Components Structure

The HEFI-2019 includes 10 components: Vegetables and fruits (20 points), Whole-grain foods (5 points), Grain foods ratio (5 points), Protein foods (5 points), Plant-based protein foods (5 points), Beverages (10 points), Fatty acids ratio (5 points), Saturated fats (5 points), Free sugars (10 points), and Sodium (10 points). All components are expressed as ratios (e.g., proportions of total foods, total beverages, or total energy).

### 1.2 Component Categories

**Adequacy Components (7 components):**
- Vegetables and fruits (/20 points)
- Whole-grain foods (/5 points)
- Grain foods ratio (/5 points)
- Protein foods (/5 points)
- Plant-based protein foods (/5 points)
- Beverages (/10 points)
- Fatty acids ratio (/5 points)

**Moderation Components (3 components):**
- Saturated fats (/5 points)
- Free sugars (/10 points)
- Sodium (/10 points)

## 2. Pre-Processing and Data Preparation

### 2.1 Food Classification Protocol

First, foods and beverages consumed are classified according to the various food and beverage categories used to calculate the numerator and denominator of each of the HEFI-2019 components. Second, the amount of food and beverages for each category, measured in RAs for foods and in grams for beverages, is determined. Third, total intakes of nutrients (mono- and polyunsaturated fats, saturated fats, free sugars measured in grams; sodium, measured in milligrams) and energy (measured in calories) are calculated.

### 2.2 Reference Amount (RA) System

The amount for total foods is calculated by adding up the number of RAs of all foods consumed. Culinary ingredients (e.g., spices, baking soda), beverages without protein (e.g., water, coffee, tea, almond, cashew, rice, coconut) as well as oils and spreads are not included in the calculation of total foods.

### 2.3 Database Integration Requirements

The calculation requires concurrent use of:
- Canadian Nutrient File 2015
- Reference Amounts database
- Free sugars content database

## 3. Core Algorithm Structure

### 3.1 Ratio Construction Phase

The scoring algorithm creates 10 variables for density of intakes: RATIO_VF, RATIO_WGTOT, RATIO_WGGR, RATIO_PRO, RATIO_PLANT, RATIO_BEV, RATIO_UNSFAT, RATIO_FA, SFA_PERC, SUG_PERC, and SODDEN.

**Mathematical Foundation:**
- Food-based components: Expressed as ratios of specific food groups to total foods (RAs)
- Beverage components: Expressed as ratios relative to total beverages
- Nutrient components: Expressed as percentages of total energy or specific ratios

### 3.2 Component-Specific Calculation Methods

#### Component 1: Vegetables and Fruits (20 points)
**Formula:** VF_Ratio = Vegetables_and_Fruits_RAs / Total_Foods_RAs

The component is calculated as the ratio of vegetables and fruits (expressed in RAs) to total foods (also expressed in RAs). The 50% proportion of vegetables and fruits in the CFG-2019 snapshot is used as a benchmark to assess adherence to this recommendation.

**Scoring Thresholds:**
- Maximum points (20): Ratio ≥ 0.50
- Minimum points (0): Ratio = 0
- Points between the minimum and maximum scores are attributed proportionately for all components.

#### Component 2: Whole-grain Foods (5 points)
**Formula:** WG_Ratio = Whole_Grain_Foods_RAs / Total_Foods_RAs

#### Component 3: Grain Foods Ratio (5 points)
**Formula:** GR_Ratio = Whole_Grain_Foods_RAs / Total_Grain_Foods_RAs

#### Component 4: Protein Foods (5 points)
**Formula:** Pro_Ratio = Protein_Foods_RAs / Total_Foods_RAs

#### Component 5: Plant-based Protein Foods (5 points)
**Formula:** Plant_Pro_Ratio = Plant_Protein_Foods_RAs / Total_Foods_RAs

#### Component 6: Beverages (10 points)
**Formula:** Bev_Ratio = Recommended_Beverages_g / Total_Beverages_g

#### Component 7: Fatty Acids Ratio (5 points)
**Formula:** FA_Ratio = (MUFA_g + PUFA_g) / SFA_g

The score of this component is based on the ratio of unsaturated fat to saturated fat (both measured in grams). A ratio of unsaturated to saturated fat ≥2.6 is given 5 points. This threshold for maximum points corresponds to the 1st percentile of the unsaturated to saturated fat ratio in simulated diets that align with CFG-2019 recommendations.

#### Component 8: Saturated Fats (5 points)
**Formula:** SFA_Percent = (SFA_g × 9) / Total_Energy_kcal × 100

#### Component 9: Free Sugars (10 points)
**Formula:** Sugar_Percent = (Free_Sugars_g × 4) / Total_Energy_kcal × 100

#### Component 10: Sodium (10 points)
**Formula:** Sodium_Density = Sodium_mg / Total_Energy_kcal (units: mg/kcal)

**Source.** Brassard et al. 2022a APNM 47(5):595-610, Table 2 p. 600. Linear interpolation between the max-score threshold < 0.9 mg/kcal (10 pts) and the zero-score threshold ≥ 2.0 mg/kcal (0 pts). The CFG-2019 recommended limit for sodium is the 2300 mg/day chronic disease risk reduction threshold from the National Academies of Sciences, Engineering, and Medicine (NASEM); Brassard derived the 0.9 mg/kcal max-score threshold from 2300 mg/day ÷ 2600 kcal/day (the 90th percentile of usual energy intake among Canadians ≥ 2 y in the 2015 CCHS-Nutrition).

**Audit history (2026-05-21, HEFI-CODE-1).** Earlier versions of this report had a stray `× 1000` (yielding mg/1000-kcal) and a 1.0 mg/kcal max-score threshold. The ×1000 multiplier propagated into [`backend/rust_core/src/hefi/scoring.rs`](backend/rust_core/src/hefi/scoring.rs) where it produced a SODDEN ratio 1000× larger than the threshold band, causing C10 to return 0 points for every realistic meal. Both the formula and the threshold (0.9, not 1.0) now match Brassard 2022a Table 2 verbatim.

## 4. Scoring Algorithm Implementation

### 4.1 Proportional Scoring Function

For each component, the scoring follows a linear interpolation between minimum and maximum thresholds:

```
Score = Min_Points + ((Ratio - Min_Threshold) / (Max_Threshold - Min_Threshold)) × (Max_Points - Min_Points)
```

Where:
- Score is constrained between Min_Points and Max_Points
- Ratio is the calculated component ratio
- Thresholds are component-specific

### 4.2 Zero Intake Handling

Of note, when no foods, beverages or energy is reported, ratios are not calculated and a score of 0 is assigned to the corresponding components.

### 4.3 Total Score Calculation

The variable corresponding to the total HEFI-2019 is HEFI2019_TOTAL_SCORE and the 10 variables corresponding to each component of the HEFI-2019 are HEFI2019C1_VF, HEFI2019C2_WHOLEGR, HEFI2019C3_GRRATIO, HEFI2019C4_PROFOODS, HEFI2019C5_PLANTPRO, HEFI2019C6_BEVERAGES, HEFI2019C7_FATTYACID, HEFI2019C8_SFAT, HEFI2019C9_FREESUGARS, and HEFI2019C10_SODIUM.

**Total Score Formula:**
```
HEFI2019_TOTAL_SCORE = Σ(Component_i_Score) for i = 1 to 10
```

## 5. Advanced Calculation Methods

### 5.1 Simple Scoring Algorithm Method

The simple HEI scoring algorithm method is applied to calculate scores using computed amounts of each component in the HEI. To use the simple HEI scoring method, first the ratio of the dietary constituent to energy is constructed and scored according to the scoring standards.

### 5.2 Population Ratio Method

The population ratio method is used to calculate the mean intakes of dietary constituents, and scoring standards are applied to arrive at scores at the level of a group of persons.

### 5.3 Mean Ratio Method

In the mean ratio method, as in the simple HEI scoring algorithm method, first compute the ratio of each dietary constituent to energy. However, rather than scoring these ratios for each individual as in the simple scoring algorithm method, the means of the ratios over individuals are then computed.

### 5.4 Usual Intake Methods

**Bivariate Method:**
The bivariate method is a computational modeling approach that is used to simultaneously model two dietary constituents. This creates predicted ratios and the application of scoring standards to predict component and total scores, as well as distributions of component scores.

**Multivariate MCMC Method:**
The multivariate Markov Chain Monte Carlo (MCMC) approach is similar to the bivariate approach, but extends the methodology to jointly model all components of the HEI simultaneously, accounting for the correlation among all components.

## 6. Technical Implementation Specifications

### 6.1 Data Format Requirements

The scoring algorithm should ideally be applied to a dataset in the "long" format, where observations are rows and dietary constituents are columns. Other layouts are also possible.

### 6.2 Software Implementations

SAS and R versions of the scoring algorithm are available. Both versions will yield the same HEFI-2019 scores and output when applied to the same data.

### 6.3 Validation Framework

For example, when considering food categories related to the Grain foods ratio component, it is necessary to separate total grains into 2 different food categories: whole grains and non-whole grains. Usual intakes were generated for a pre-specified number of pseudo-individuals (i.e., 500 simulations per survey respondent) during the Monte Carlo simulation step.

## 7. Performance Metrics and Validation

### 7.1 Population Statistics

The estimated mean HEFI-2019 score (/80) was 43.1 (95% CI, 42.7 to 43.6) among Canadians aged 2 years and older. The first and 99th percentiles were 22.1 and 62.9 points.

### 7.2 Reliability Measures

Cronbach's alpha was 0.66 (95% CI, 0.63 to 0.69). Evidence of construct validity and internal consistency support the use of the HEFI-2019 to assess adherence to CFG-2019's recommendations on healthy food choices.

### 7.3 Energy Correlation

The HEFI-2019 was weakly correlated with energy intake (r = –0.13; 95% CI, –0.20 to –0.06).

## 8. Implementation Workflow

### 8.1 Data Preprocessing Pipeline
1. **Food Classification**: Categorize all consumed foods according to HEFI component categories
2. **RA Conversion**: Convert food amounts to Reference Amounts using Health Canada database
3. **Nutrient Extraction**: Extract macro/micronutrient data from Canadian Nutrient File
4. **Free Sugar Calculation**: Apply free sugar estimation methodology
5. **Quality Control**: Validate data completeness and logical consistency

### 8.2 Calculation Sequence
1. **Ratio Construction**: Calculate all 10 component ratios
2. **Threshold Application**: Apply component-specific scoring thresholds
3. **Proportional Scoring**: Calculate intermediate scores using linear interpolation
4. **Component Summation**: Sum all component scores for total HEFI-2019 score
5. **Output Generation**: Generate component and total scores with metadata

### 8.3 Quality Assurance Protocol
1. **Range Validation**: Ensure all component scores fall within expected ranges
2. **Distribution Analysis**: Compare calculated scores to population norms
3. **Missing Data Handling**: Apply appropriate zero-score assignments
4. **Cross-validation**: Compare results across different calculation methods

## 9. Computational Complexity and Performance

### 9.1 Algorithm Efficiency
- **Time Complexity**: O(n×m) where n = number of individuals, m = number of food items
- **Space Complexity**: O(n×k) where k = number of dietary constituents
- **Scalability**: Linear scaling with dataset size

### 9.2 Critical Decision Points
1. **Missing Data Treatment**: Zero assignment vs. exclusion strategies
2. **Threshold Selection**: Population-specific vs. guideline-based cutoffs
3. **Weighting Schemes**: Equal weighting vs. evidence-based weighting
4. **Temporal Aggregation**: Single-day vs. usual intake methodologies

## 10. Applications and Limitations

### 10.1 Validated Use Cases
- Population surveillance and monitoring
- Research applications for diet quality assessment
- Policy evaluation and intervention studies
- Cohort studies investigating diet-disease relationships

### 10.2 Technical Limitations
- Interpretation of the total HEFI-2019 score must be accompanied by its components' scores, considering it assesses multiple dimensions of food choices.
- Requires comprehensive food composition databases
- Dependent on accurate food classification systems
- Limited to populations following similar dietary patterns

This technical report provides the comprehensive algorithmic framework for implementing the HEFI-2019 scoring system, enabling researchers and practitioners to accurately assess adherence to Canada's Food Guide 2019 recommendations.