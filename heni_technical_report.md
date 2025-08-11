# HENI Score: Technical Expert Report on Core Algorithms and Calculation Methods

## Executive Summary

The HEalth Nutritional Index (HENI) is a health burden-based scoring system in disability adjusted life years (DALYs) that uses epidemiological evidence from the Global Burden of Disease (GBD) to rank and evaluate food items and diets. HENI calculates the net beneficial or detrimental health burden in minutes of healthy life associated with a serving of food consumed.

## 1. Fundamental Methodology

### 1.1 Conceptual Framework

HENI accounts for the health effects of 8 major food groups (nuts and seeds, whole grains, fruits, vegetables, milk, sugar-sweetened beverages, red meat, and processed meat) and 6 nutrients (omega-3, calcium, fiber, polyunsaturated fatty acids, trans fat, and sodium), identified by the GBD as dietary risk factors.

The index fundamentally operates on the principle of quantifying health burden through:
- **Disability Adjusted Life Years (DALYs)** as the core metric
- **Epidemiological evidence** from Global Burden of Disease studies
- **Risk factor analysis** for 14-16 dietary components

### 1.2 Core Algorithm Structure

For each food item, HENI quantifies the marginal reduction (+) or increase (–) in all-cause disease burden, in avoided disability adjusted life years per serving. It is calculated as the weighted sum of the amount of each the 15 risk factors in each food item (grisk factor/srv), weighted by the marginal impact per grisk factor (avoided µDALY/grisk factor).

**Mathematical Foundation:**
```
HENI_score = Σ(Risk_Factor_Amount × HENI_Factor)
```

Where:
- Risk_Factor_Amount = grams of specific risk factor per serving
- HENI_Factor = avoided μDALY/gram for that risk factor

## 2. Detailed Calculation Methodology

### 2.1 HENI Factor Estimation

The HENI factors are estimated by coupling age- and gender-adjusted outcome-specific incidence rates with risk ratios (RR) and severity factors, measuring positive or detrimental effects in avoided μDALY/g.

**Step-by-Step Process:**

1. **Incidence Rate Calculation**
   - Age-specific incidence rates for target diseases
   - Gender-adjusted disease occurrence data
   - Population-level health statistics from GBD

2. **Risk Ratio Integration**
   - Epidemiological risk ratios from meta-analyses
   - Outcome-specific relative risk calculations
   - Disease-nutrient association strengths

3. **Severity Factor Application**
   - Disease burden weighting (disability weights)
   - Life years lost calculations
   - Quality of life impact assessments

### 2.2 DALY Calculation Framework

**Core DALY Formula:**
```
DALY = YLL + YLD
```

Where:
- **YLL (Years of Life Lost)** = Number of Deaths × Life expectancy at age of death
- **YLD (Years Lived with Disability)** = Number of Cases × Disease Duration × Disability Weight

DALYs represent the incident number of healthy life years lost due to disease or disability, and do so by incorporating non-fatal and fatal health outcomes.

### 2.3 Age and Gender Adjustments

Age- and gender-adjusted weights are calculated through the use of information on disease incidence rates, disease severity, and GBD risk ratios.

**Adjustment Methodology:**
- Population-weighted incidence rates by age group
- Gender-specific disease prevalence factors  
- Demographic standardization to reference populations

## 3. Data Sources and Food Composition Analysis

### 3.1 Primary Databases

We determine the food group and nutrient profile for each of the 5000+ consumed food items in the What We Eat in America 2009-2014 dataset, using multiple databases such as the Food Patterns Equivalents Database (FPED), the Food and Nutrient Database for Dietary Studies (FNDDS), and the USDA National Nutrient Database for Standard Reference (SR).

**Database Integration:**
- **FPED**: Food pattern equivalents and groupings
- **FNDDS**: Detailed nutritional composition data
- **USDA SR**: Standard reference nutrient values
- **NHANES**: Population consumption patterns

### 3.2 Food Item Processing

Food item composition is determined based on publically available databases.

**Compositional Analysis Steps:**
1. Food disaggregation into constituent components
2. Nutrient profile mapping to risk factors
3. Portion size standardization
4. Database linkage and validation

## 4. Scoring Algorithm Implementation

### 4.1 Score Derivation Process

We then derive the HENI scores for 100 kcal, 100 grams or 1 serving of each food item by multiplying the food group and nutrient composition by their respective HENI factors.

**Mathematical Implementation:**
```
HENI_final = Σ(Nutrient_i × Factor_i) + Σ(FoodGroup_j × Factor_j)
```

For standardized portions:
- **Per 100 kcal**: Energy-normalized scoring
- **Per 100 grams**: Weight-normalized scoring  
- **Per serving**: Standard portion-based scoring

### 4.2 Factor Range and Interpretation

HENI factors for food group and nutrient range between -8 μDALY/g for sodium, up to 57 μDALY/g for omega-3 from fish and seafood.

**Score Interpretation:**
- **Positive values**: Health benefits (avoided disease burden)
- **Negative values**: Health detriments (increased disease burden)
- **Units**: μDALY (micro-Disability Adjusted Life Years)

HENI score typically ranges from -30 avoided μDALY/100kcal for e.g. soft drinks, up to +50 avoided μDALY/100kcal, for beneficial food items such as fish, fruits, vegetables, and nuts.

## 5. Disease Burden Attribution

### 5.1 Primary Health Outcomes

The majority of the health effect is associated with cardiovascular diseases, with some food items affecting certain cancers (e.g. health benefit for colorectal cancer with milk).

**Disease Categories:**
- Cardiovascular diseases (primary contributor)
- Certain cancers (colorectal, others)
- Metabolic disorders
- All-cause mortality impacts

### 5.2 Practical Application Examples

Every hotdog you eat shortens your life by 36 minutes. However, you could also add minutes to your healthy life expectancy by eating better foods. A portion of nuts, for example, adds almost 26 minutes, while a peanut butter and jam sandwich gives a person more than half an hour extra life.

**Score Examples:**
- **Processed meat (hotdog)**: -36 minutes per serving
- **Nuts**: +26 minutes per serving
- **Fish**: Up to +100 avoided μDALY/serving
- **Soft drinks**: -30 μDALY/100kcal

## 6. Technical Limitations and Assumptions

### 6.1 Methodological Constraints

The HENI factors are applicable under the assumption that the overall dietary intake of each GBD food group and nutrient is within the effective intake range, below the theoretical risk level limit.

**Key Assumptions:**
- Linear dose-response relationships within effective ranges
- Population-level risk factors apply to individuals
- Current epidemiological evidence remains valid
- Food composition databases are accurate

### 6.2 Scoring Variability

Absolute HENI scores and ranking of food items vary substantially when using 100 kcal, 100 grams or 1 serving as a basis for comparison.

**Consideration Factors:**
- Portion size impacts relative rankings
- Energy density affects per-calorie scores
- Mass-based versus energy-based comparisons yield different insights

## 7. Advanced Applications

### 7.1 Dietary Pattern Analysis

Current diets in females were associated with a gain of 5 minutes of heathy life/day while in males current diets were associated with a decrease of 4 minutes of healthy life/day.

**Application Scope:**
- Individual food item assessment
- Complete dietary pattern evaluation
- Population health impact modeling
- Policy intervention analysis

### 7.2 Environmental Integration

The HENI methodology has been extended to include environmental impact assessments, creating combined nutritional-environmental scoring systems for comprehensive food sustainability evaluation.

## 8. Future Developments

### 8.1 Methodological Enhancements

- Integration of bioavailability factors
- Dynamic risk ratio updating with new evidence  
- Personalized scoring based on individual characteristics
- Expanded nutrient and food group coverage

### 8.2 Application Expansion

- Integration with food labeling systems
- Public health policy applications
- Clinical nutrition guidance tools
- Consumer education platforms

## Conclusion

The HENI Score represents a sophisticated epidemiologically-based approach to food health assessment, utilizing established DALY methodology combined with comprehensive nutritional databases and Global Burden of Disease evidence. Its algorithm provides quantitative health impact estimates in meaningful units (minutes of healthy life), making it valuable for both research applications and practical dietary guidance. The methodology's strength lies in its evidence-based foundation and standardized approach to health burden quantification, while its limitations include assumptions about population-level risk factors and linear dose-response relationships.