// SEO Configuration for EcoDish365
// Central configuration for all SEO-related settings

export const seoConfig = {
  // Site-wide settings
  siteName: 'EcoDish365',
  siteUrl: 'https://ecodish365.com',
  siteDescription: 'Professional nutrition analysis platform with comprehensive food database and research tools',
  
  // Brand information
  brand: {
    name: 'EcoDish365',
    tagline: 'Professional Nutrition Analysis & Food Research Platform',
    description: 'Advanced nutrition analysis platform with Canadian Nutrient File database, Health Star Rating calculator, Food Compass Score assessment, and environmental impact tools.',
    email: 'contact@ecodish365.com',
    socialMedia: {
      twitter: '@ecodish365',
      linkedin: 'https://linkedin.com/company/ecodish365',
      github: 'https://github.com/ecodish365',
    },
  },

  // Primary keywords for SEO targeting
  primaryKeywords: [
    'nutrition analysis',
    'Canadian Nutrient File',
    'CNF database',
    'Health Star Rating calculator',
    'Food Compass Score',
    'nutritional assessment',
    'food research platform',
    'professional nutrition tools',
  ],

  // Secondary keywords for long-tail targeting
  secondaryKeywords: [
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
    'environmental nutrition',
    'sustainable food analysis',
  ],

  // Target audience segments
  targetAudiences: [
    'nutrition researchers',
    'registered dietitians',
    'food scientists',
    'public health professionals',
    'policy makers',
    'academic researchers',
    'healthcare providers',
    'nutrition students',
    'food industry professionals',
    'health technology developers',
  ],

  // Geographic targeting
  geographicTargeting: {
    primary: ['Canada', 'United States', 'Australia'],
    secondary: ['United Kingdom', 'New Zealand', 'European Union'],
  },

  // Content themes for SEO
  contentThemes: {
    nutrition: {
      title: 'Comprehensive Nutrition Analysis',
      keywords: ['nutrition analysis', 'nutritional assessment', 'diet quality'],
      description: 'Professional nutrition analysis tools and comprehensive food databases',
    },
    research: {
      title: 'Evidence-Based Food Research',
      keywords: ['food research', 'nutrition research', 'evidence-based nutrition'],
      description: 'Research-grade tools for food science and nutrition studies',
    },
    tools: {
      title: 'Professional Nutrition Tools',
      keywords: ['nutrition tools', 'food calculators', 'diet analysis software'],
      description: 'Advanced calculators and analysis tools for nutrition professionals',
    },
    database: {
      title: 'Comprehensive Food Databases',
      keywords: ['food database', 'nutrition database', 'Canadian Nutrient File'],
      description: 'Access to comprehensive food and nutrition databases',
    },
  },

  // Page-specific SEO templates
  pageTemplates: {
    homepage: {
      title: 'EcoDish365 - Professional Nutrition Analysis & Food Research Platform',
      description: 'Advanced nutrition analysis platform with Canadian Nutrient File database, Health Star Rating calculator, Food Compass Score assessment, and environmental impact tools.',
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
        'Nutrition Analysis',
        'Food Science',
        'Health Star Ratings',
        'Food Compass Scores',
        'Canadian Nutrient File',
        'Dietary Assessment',
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