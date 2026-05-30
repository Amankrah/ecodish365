// SEO Configuration for EcoDish365
// Central configuration for all SEO-related settings

export const seoConfig = {
  // Site-wide settings
  siteName: 'EcoDish365',
  siteUrl: 'https://ecodish365.com',
  siteDescription: 'The world\'s first integrated environmental nutrition platform combining nutrition science, environmental impact, and health outcomes for individuals, researchers, and policy makers',
  
  // Brand information
  brand: {
    name: 'EcoDish365',
    tagline: 'Integrated Environmental Nutrition Platform',
    description: 'The world\'s first platform to integrate nutrition science, environmental impact, and health outcomes. Empowering individuals to make healthier food choices, researchers to make breakthrough discoveries, and policy makers to create evidence-based policies.',
    email: 'contact@ecodish365.com',
    socialMedia: {
      twitter: '@ecodish365',
      linkedin: 'https://linkedin.com/company/ecodish365',
      github: 'https://github.com/ecodish365',
    },
  },

  // Primary keywords for SEO targeting
  primaryKeywords: [
    'environmental nutrition',
    'nutrition decision system',
    'integrated nutrition environment health',
    'sustainable food choices',
    'Canadian Nutrient File',
    'CNF database',
    'Health Star Rating calculator',
    'Food Compass Score',
    'Healthy Eating Food Index',
    'HEFI 2019',
    'HEalth Nutritional Index',
    'HENI health impact',
    'environmental food impact',
    'nutrition research platform',
    'food policy tools',
  ],

  // Secondary keywords for long-tail targeting
  secondaryKeywords: [
    'healthy environmentally friendly food choices',
    'integrated nutrition environmental health',
    'food decision support system',
    'sustainable nutrition platform',
    'integrated food analysis',
    'nutrition research discoveries',
    'evidence-based food policy',
    'environmental nutrition research',
    'food impact assessment',
    'nutrition database search',
    'food comparison tool',
    'dietary analysis software',
    'nutrition research tools',
    'food science database',
    'nutritional profiling',
    'diet quality assessment',
    'evidence-based nutrition',
    'professional dietitian tools',
    'nutrition calculator',
    'food nutrients analysis',
    'Canadian food data',
    'HSR calculator online',
    'FCS scoring system',
    'sustainable food analysis',
    'DALY-based nutrition',
    'health impact of foods',
    'micro-DALY',
    'GBD risk factors',
  ],

  // Target audience segments
  targetAudiences: [
    'individuals seeking healthy food choices',
    'families making sustainable food decisions',
    'nutrition researchers',
    'registered dietitians',
    'food scientists',
    'public health professionals',
    'policy makers',
    'government nutrition agencies',
    'academic researchers',
    'healthcare providers',
    'nutrition students',
    'food industry professionals',
    'environmental health experts',
    'sustainability consultants',
  ],

  // Geographic targeting
  geographicTargeting: {
    primary: ['Canada', 'United States', 'Australia'],
    secondary: ['United Kingdom', 'New Zealand', 'European Union'],
  },

  // Content themes for SEO
  contentThemes: {
    integration: {
      title: 'Integrated Nutrition Environment Health Platform',
      keywords: ['integrated environmental nutrition', 'unified platform', 'comprehensive food analysis', 'all-in-one nutrition tools'],
      description: 'The world\'s first platform integrating nutrition science, environmental impact, and health outcomes',
    },
    individuals: {
      title: 'Healthy Environmentally Friendly Food Choices',
      keywords: ['healthy food choices', 'sustainable eating', 'environmental food impact', 'personal nutrition'],
      description: 'Tools for individuals and families to make informed, healthy, and environmentally friendly food choices',
    },
    research: {
      title: 'Environmental Nutrition Research',
      keywords: ['nutrition research', 'environmental food research', 'evidence-based nutrition', 'food science discoveries'],
      description: 'Research-grade tools for breakthrough discoveries at the intersection of nutrition, health, and environment',
    },
    policy: {
      title: 'Evidence-Based Food Policy Tools',
      keywords: ['food policy', 'nutrition policy', 'environmental policy', 'evidence-based decisions'],
      description: 'Data-driven tools for policy makers to create nutrition, health, and environmental policies',
    },
    database: {
      title: 'Comprehensive Food Databases',
      keywords: ['food database', 'nutrition database', 'Canadian Nutrient File'],
      description: 'Access to comprehensive food and nutrition databases',
    },
    environmental: {
      title: 'Environmental Impact Analysis',
      keywords: ['environmental impact', 'life cycle assessment', 'carbon footprint', 'sustainability'],
      description: 'Analyze carbon, water, land use and more with evidence-based LCA methods',
    },
    meals: {
      title: 'Meal Creation & Analysis',
      keywords: ['meal creator', 'recipe nutrition', 'meal environmental impact', 'healthy meals'],
      description: 'Create, analyze, and share meals with nutrition and environmental insights',
    },
  },

  // Page-specific SEO templates
  pageTemplates: {
    homepage: {
      title: 'EcoDish365 - Environmental Nutrition Decision System | Harmony for Health, Nutrition & Environment',
      description: 'The world\'s first environmental nutrition decision system harmonizing nutrition, environment, and health. Empowering individuals, researchers, and policy makers with integrated food analysis tools.',
    },
    cnf: {
      title: 'Canadian Nutrient File (CNF) Database Explorer',
      description: 'Explore Canada\'s comprehensive nutrition database with 5000+ foods and 150+ nutrients. Advanced search, comparison, and analysis tools.',
    },
    hsr: {
      title: 'Health Star Rating Calculator - Official HSR Algorithm',
      description: 'Calculate Health Star Ratings using Australia\'s official front-of-pack labeling system. Professional food quality assessment tool.',
    },
    fcs: {
      title: 'Food Compass Score Calculator - Professional FCS Analysis',
      description: 'Calculate Food Compass Scores using the scientifically validated algorithm with 54 nutritional attributes across 9 domains.',
    },
    hefi: {
      title: 'Healthy Eating Score Calculator (HEFI)',
      description:
        "See how closely a day of eating matches Canada's Food Guide. Ten components, plain-language results, score from 0 to 80.",
    },
    heni: {
      title: 'Health Impact Calculator (HENI)',
      description:
        'Estimate minutes of healthy life foods may add or subtract, based on population research.',
    },
    environmental: {
      title: 'Environmental Impact Calculator - Carbon, Water, and Land Use',
      description:
        'Analyze the environmental footprint of foods and meals using life cycle assessment, including carbon footprint, water use, land use, and more.',
    },
    meals: {
      title: 'Personal Food Journey - Healthy & Environmentally Friendly Meal Planning',
      description:
        'Create personalized meals that are both nutritious and environmentally sustainable. Discover the harmony of health, nutrition, and environmental impact in your daily food choices.',
    },
  },

  // Schema.org structured data templates
  structuredData: {
    organization: {
      '@type': 'Organization',
      name: 'EcoDish365',
      url: 'https://ecodish365.com',
      description: 'Professional nutrition analysis platform and food research tools',
      foundingDate: '2024',
      industry: 'Health Technology',
      areaServed: 'Worldwide',
      knowsAbout: [
        'Environmental Nutrition',
        'Nutrition Decision Systems',
        'Food Science',
        'Health Star Ratings',
        'Food Compass Scores',
        'Canadian Nutrient File',
        'Dietary Assessment',
        'HEFI-2019',
        'HENI',
        'DALY methodology',
        'Sustainable Food Choices',
        'Integrated Nutrition Platform',
        'Food Policy Research',
      ],
    },
    website: {
      '@type': 'WebSite',
      name: 'EcoDish365',
      url: 'https://ecodish365.com',
      potentialAction: {
        '@type': 'SearchAction',
        target: 'https://ecodish365.com/cnf/search?q={search_term_string}',
        'query-input': 'required name=search_term_string',
      },
    },
  },

  // Social media optimization
  social: {
    openGraph: {
      type: 'website',
      locale: 'en_US',
      siteName: 'EcoDish365',
      imageWidth: 1200,
      imageHeight: 630,
    },
    twitter: {
      card: 'summary_large_image',
      site: '@ecodish365',
      creator: '@ecodish365',
    },
  },
};