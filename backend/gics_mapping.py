"""
GICS (Global Industry Classification Standard) sub-industry to industry mapping.

The S&P 500 Wikipedia table provides Sector and Sub-Industry, but the breadcrumb
needs Sector › Industry. This maps each sub-industry to its parent industry.

Official GICS hierarchy (4 tiers):
  Sector › Industry Group › Industry › Sub-Industry

Example for Semiconductors:
  Sector: Information Technology
  Industry Group: Semiconductors & Semiconductor Equipment
  Industry: Semiconductors & Semiconductor Equipment
  Sub-Industries: "Semiconductors", "Semiconductor Materials & Equipment"

For Stock Detail breadcrumb, we show: Sector › Industry
"""

# Sub-Industry → Industry mapping
# Source: Official GICS structure from S&P Global and MSCI (effective as of 2023)
GICS_SUB_TO_INDUSTRY = {
    # ===== INFORMATION TECHNOLOGY =====

    # Industry: Semiconductors & Semiconductor Equipment
    "Semiconductors": "Semiconductors & Semiconductor Equipment",
    "Semiconductor Materials & Equipment": "Semiconductors & Semiconductor Equipment",

    # Industry: IT Services
    "IT Consulting & Other Services": "IT Services",
    "Data Processing & Outsourced Services": "IT Services",
    "Internet Services & Infrastructure": "IT Services",

    # Industry: Software
    "Application Software": "Software",
    "Systems Software": "Software",

    # Industry: Technology Hardware, Storage & Peripherals
    "Technology Hardware, Storage & Peripherals": "Technology Hardware, Storage & Peripherals",

    # Industry: Communications Equipment
    "Communications Equipment": "Communications Equipment",

    # Industry: Electronic Equipment, Instruments & Components
    "Electronic Equipment & Instruments": "Electronic Equipment, Instruments & Components",
    "Electronic Components": "Electronic Equipment, Instruments & Components",
    "Electronic Manufacturing Services": "Electronic Equipment, Instruments & Components",
    "Technology Distributors": "Electronic Equipment, Instruments & Components",

    # ===== HEALTH CARE =====

    # Industry: Health Care Equipment & Supplies
    "Health Care Equipment": "Health Care Equipment & Supplies",
    "Health Care Supplies": "Health Care Equipment & Supplies",

    # Industry: Health Care Providers & Services
    "Health Care Distributors": "Health Care Providers & Services",
    "Health Care Services": "Health Care Providers & Services",
    "Health Care Facilities": "Health Care Providers & Services",
    "Managed Health Care": "Health Care Providers & Services",

    # Industry: Health Care Technology
    "Health Care Technology": "Health Care Technology",

    # Industry: Biotechnology
    "Biotechnology": "Biotechnology",

    # Industry: Pharmaceuticals
    "Pharmaceuticals": "Pharmaceuticals",

    # Industry: Life Sciences Tools & Services
    "Life Sciences Tools & Services": "Life Sciences Tools & Services",

    # ===== FINANCIALS =====

    # Industry: Banks
    "Diversified Banks": "Banks",
    "Regional Banks": "Banks",
    "Thrifts & Mortgage Finance": "Banks",

    # Industry: Financial Services
    "Diversified Financial Services": "Financial Services",
    "Multi-Sector Holdings": "Financial Services",
    "Specialized Finance": "Financial Services",
    "Commercial & Residential Mortgage Finance": "Financial Services",
    "Transaction & Payment Processing Services": "Financial Services",

    # Industry: Consumer Finance
    "Consumer Finance": "Consumer Finance",

    # Industry: Capital Markets
    "Asset Management & Custody Banks": "Capital Markets",
    "Investment Banking & Brokerage": "Capital Markets",
    "Diversified Capital Markets": "Capital Markets",
    "Financial Exchanges & Data": "Capital Markets",

    # Industry: Mortgage Real Estate Investment Trusts (REITs)
    "Mortgage REITs": "Mortgage Real Estate Investment Trusts (REITs)",

    # Industry: Insurance
    "Insurance Brokers": "Insurance",
    "Life & Health Insurance": "Insurance",
    "Multi-line Insurance": "Insurance",
    "Property & Casualty Insurance": "Insurance",
    "Reinsurance": "Insurance",

    # ===== CONSUMER DISCRETIONARY =====

    # Industry: Automobiles
    "Automobile Manufacturers": "Automobiles",
    "Motorcycle Manufacturers": "Automobiles",

    # Industry: Auto Components
    "Auto Parts & Equipment": "Auto Components",
    "Tires & Rubber": "Auto Components",

    # Industry: Household Durables
    "Consumer Electronics": "Household Durables",
    "Home Furnishings": "Household Durables",
    "Homebuilding": "Household Durables",
    "Household Appliances": "Household Durables",
    "Housewares & Specialties": "Household Durables",

    # Industry: Leisure Products
    "Leisure Products": "Leisure Products",

    # Industry: Textiles, Apparel & Luxury Goods
    "Apparel, Accessories & Luxury Goods": "Textiles, Apparel & Luxury Goods",
    "Footwear": "Textiles, Apparel & Luxury Goods",
    "Textiles": "Textiles, Apparel & Luxury Goods",

    # Industry: Hotels, Restaurants & Leisure
    "Casinos & Gaming": "Hotels, Restaurants & Leisure",
    "Hotels, Resorts & Cruise Lines": "Hotels, Restaurants & Leisure",
    "Leisure Facilities": "Hotels, Restaurants & Leisure",
    "Restaurants": "Hotels, Restaurants & Leisure",

    # Industry: Diversified Consumer Services
    "Education Services": "Diversified Consumer Services",
    "Specialized Consumer Services": "Diversified Consumer Services",

    # Industry: Distributors
    "Distributors": "Distributors",

    # Industry: Broadline Retail
    "Broadline Retail": "Broadline Retail",
    "Department Stores": "Broadline Retail",
    "General Merchandise Stores": "Broadline Retail",

    # Industry: Specialty Retail
    "Apparel Retail": "Specialty Retail",
    "Automotive Retail": "Specialty Retail",
    "Computer & Electronics Retail": "Specialty Retail",
    "Home Improvement Retail": "Specialty Retail",
    "Homefurnishing Retail": "Specialty Retail",
    "Specialty Stores": "Specialty Retail",
    "Other Specialty Retail": "Specialty Retail",

    # Industry: Internet & Direct Marketing Retail
    "Internet & Direct Marketing Retail": "Internet & Direct Marketing Retail",

    # ===== CONSUMER STAPLES =====

    # Industry: Consumer Staples Distribution & Retail
    "Drug Retail": "Consumer Staples Distribution & Retail",
    "Food Distributors": "Consumer Staples Distribution & Retail",
    "Food Retail": "Consumer Staples Distribution & Retail",
    "Consumer Staples Merchandise Retail": "Consumer Staples Distribution & Retail",

    # Industry: Beverages
    "Brewers": "Beverages",
    "Distillers & Vintners": "Beverages",
    "Soft Drinks & Non-alcoholic Beverages": "Beverages",

    # Industry: Food Products
    "Agricultural Products & Services": "Food Products",
    "Packaged Foods & Meats": "Food Products",

    # Industry: Tobacco
    "Tobacco": "Tobacco",

    # Industry: Household Products
    "Household Products": "Household Products",

    # Industry: Personal Care Products
    "Personal Care Products": "Personal Care Products",

    # ===== ENERGY =====

    # Industry: Energy Equipment & Services
    "Oil & Gas Drilling": "Energy Equipment & Services",
    "Oil & Gas Equipment & Services": "Energy Equipment & Services",

    # Industry: Oil, Gas & Consumable Fuels
    "Integrated Oil & Gas": "Oil, Gas & Consumable Fuels",
    "Oil & Gas Exploration & Production": "Oil, Gas & Consumable Fuels",
    "Oil & Gas Refining & Marketing": "Oil, Gas & Consumable Fuels",
    "Oil & Gas Storage & Transportation": "Oil, Gas & Consumable Fuels",
    "Coal & Consumable Fuels": "Oil, Gas & Consumable Fuels",

    # ===== MATERIALS =====

    # Industry: Chemicals
    "Commodity Chemicals": "Chemicals",
    "Diversified Chemicals": "Chemicals",
    "Fertilizers & Agricultural Chemicals": "Chemicals",
    "Industrial Gases": "Chemicals",
    "Specialty Chemicals": "Chemicals",

    # Industry: Construction Materials
    "Construction Materials": "Construction Materials",

    # Industry: Containers & Packaging
    "Metal, Glass & Plastic Containers": "Containers & Packaging",
    "Paper Packaging": "Containers & Packaging",

    # Industry: Metals & Mining
    "Aluminum": "Metals & Mining",
    "Diversified Metals & Mining": "Metals & Mining",
    "Gold": "Metals & Mining",
    "Precious Metals & Minerals": "Metals & Mining",
    "Silver": "Metals & Mining",
    "Steel": "Metals & Mining",

    # Industry: Paper & Forest Products
    "Forest Products": "Paper & Forest Products",
    "Paper Products": "Paper & Forest Products",

    # ===== INDUSTRIALS =====

    # Industry: Aerospace & Defense
    "Aerospace & Defense": "Aerospace & Defense",

    # Industry: Building Products
    "Building Products": "Building Products",

    # Industry: Construction & Engineering
    "Construction & Engineering": "Construction & Engineering",

    # Industry: Electrical Equipment
    "Electrical Components & Equipment": "Electrical Equipment",
    "Heavy Electrical Equipment": "Electrical Equipment",

    # Industry: Industrial Conglomerates
    "Industrial Conglomerates": "Industrial Conglomerates",

    # Industry: Machinery
    "Agricultural & Farm Machinery": "Machinery",
    "Construction Machinery & Heavy Transportation Equipment": "Machinery",
    "Construction Machinery & Heavy Trucks": "Machinery",
    "Industrial Machinery & Supplies & Components": "Machinery",

    # Industry: Trading Companies & Distributors
    "Trading Companies & Distributors": "Trading Companies & Distributors",

    # Industry: Commercial Services & Supplies
    "Commercial Printing": "Commercial Services & Supplies",
    "Environmental & Facilities Services": "Commercial Services & Supplies",
    "Office Services & Supplies": "Commercial Services & Supplies",
    "Security & Alarm Services": "Commercial Services & Supplies",
    "Diversified Support Services": "Commercial Services & Supplies",

    # Industry: Professional Services
    "Human Resource & Employment Services": "Professional Services",
    "Research & Consulting Services": "Professional Services",
    "Data Processing & Outsourced Services": "Professional Services",

    # Industry: Air Freight & Logistics
    "Air Freight & Logistics": "Air Freight & Logistics",

    # Industry: Passenger Airlines
    "Passenger Airlines": "Passenger Airlines",

    # Industry: Marine Transportation
    "Marine Transportation": "Marine Transportation",

    # Industry: Ground Transportation
    "Cargo Ground Transportation": "Ground Transportation",
    "Passenger Ground Transportation": "Ground Transportation",
    "Railroads": "Ground Transportation",

    # Industry: Transportation Infrastructure
    "Airport Services": "Transportation Infrastructure",
    "Highways & Railtracks": "Transportation Infrastructure",
    "Marine Ports & Services": "Transportation Infrastructure",

    # ===== UTILITIES =====

    # Industry: Electric Utilities
    "Electric Utilities": "Electric Utilities",

    # Industry: Gas Utilities
    "Gas Utilities": "Gas Utilities",

    # Industry: Multi-Utilities
    "Multi-Utilities": "Multi-Utilities",

    # Industry: Water Utilities
    "Water Utilities": "Water Utilities",

    # Industry: Independent Power and Renewable Electricity Producers
    "Independent Power Producers & Energy Traders": "Independent Power and Renewable Electricity Producers",
    "Renewable Electricity": "Independent Power and Renewable Electricity Producers",

    # ===== REAL ESTATE =====

    # Industry: Equity Real Estate Investment Trusts (REITs)
    "Diversified REITs": "Equity Real Estate Investment Trusts (REITs)",
    "Industrial REITs": "Equity Real Estate Investment Trusts (REITs)",
    "Hotel & Resort REITs": "Equity Real Estate Investment Trusts (REITs)",
    "Office REITs": "Equity Real Estate Investment Trusts (REITs)",
    "Health Care REITs": "Equity Real Estate Investment Trusts (REITs)",
    "Residential REITs": "Equity Real Estate Investment Trusts (REITs)",
    "Retail REITs": "Equity Real Estate Investment Trusts (REITs)",
    "Specialized REITs": "Equity Real Estate Investment Trusts (REITs)",

    # Industry: Real Estate Management & Development
    "Diversified Real Estate Activities": "Real Estate Management & Development",
    "Real Estate Operating Companies": "Real Estate Management & Development",
    "Real Estate Development": "Real Estate Management & Development",
    "Real Estate Services": "Real Estate Management & Development",

    # ===== COMMUNICATION SERVICES =====

    # Industry: Diversified Telecommunication Services
    "Alternative Carriers": "Diversified Telecommunication Services",
    "Integrated Telecommunication Services": "Diversified Telecommunication Services",

    # Industry: Wireless Telecommunication Services
    "Wireless Telecommunication Services": "Wireless Telecommunication Services",

    # Industry: Media
    "Advertising": "Media",
    "Broadcasting": "Media",
    "Cable & Satellite": "Media",
    "Movies & Entertainment": "Media",
    "Publishing": "Media",

    # Industry: Entertainment
    "Movies & Entertainment": "Entertainment",

    # Industry: Interactive Media & Services
    "Interactive Home Entertainment": "Interactive Media & Services",
    "Interactive Media & Services": "Interactive Media & Services",
}


def get_industry(sub_industry: str) -> str:
    """
    Get the industry name for a given sub-industry.

    Args:
        sub_industry: GICS sub-industry name

    Returns:
        Industry name, or the sub-industry itself if mapping not found
    """
    return GICS_SUB_TO_INDUSTRY.get(sub_industry, sub_industry)


def get_breadcrumb(sector: str, sub_industry: str) -> str:
    """
    Format sector › industry breadcrumb for display.

    Args:
        sector: GICS sector
        sub_industry: GICS sub-industry

    Returns:
        Formatted breadcrumb like "Information Technology › Semiconductors & Semiconductor Equipment"
    """
    industry = get_industry(sub_industry)
    return f"{sector} › {industry}"


def verify_coverage():
    """
    Verify that all sub-industries in the current S&P 500 are mapped correctly.

    Checks:
    1. All sub-industries have a mapping
    2. Each stock's mapped industry belongs to that stock's sector
    """
    from universe import load_sp500

    sp500 = load_sp500()
    all_subs = set(sp500['gics_sub_industry'].unique())
    mapped_subs = set(GICS_SUB_TO_INDUSTRY.keys())

    unmapped = all_subs - mapped_subs

    print(f"Total sub-industries in S&P 500: {len(all_subs)}")
    print(f"Mapped sub-industries: {len(mapped_subs)}")
    print(f"Coverage: {len(all_subs - unmapped)}/{len(all_subs)} ({100 * len(all_subs - unmapped) / len(all_subs):.1f}%)")

    errors = False

    # Check 1: Missing sub-industries
    if unmapped:
        errors = True
        print(f"\n⚠️  {len(unmapped)} unmapped sub-industries found:")
        for sector in sorted(sp500['gics_sector'].unique()):
            sector_subs = sp500[sp500['gics_sector'] == sector]['gics_sub_industry'].unique()
            sector_unmapped = set(sector_subs) & unmapped
            if sector_unmapped:
                print(f"\n  {sector}:")
                for sub in sorted(sector_unmapped):
                    count = len(sp500[sp500['gics_sub_industry'] == sub])
                    print(f"    - {sub} ({count} stocks)")
    else:
        print("\n✓ All sub-industries are mapped!")

    # Check 2: Validate that industries belong to the correct sector
    # Build sector → industries mapping from actual S&P 500 data
    sector_industries = {}
    for _, row in sp500.iterrows():
        sector = row['gics_sector']
        sub = row['gics_sub_industry']
        industry = get_industry(sub)

        if sector not in sector_industries:
            sector_industries[sector] = set()
        sector_industries[sector].add(industry)

    # Now check for cross-sector industries (industries that appear in multiple sectors)
    print("\n" + "="*70)
    print("Checking that industries don't cross sector boundaries...")

    all_industries = {}
    for sector, industries in sector_industries.items():
        for industry in industries:
            if industry not in all_industries:
                all_industries[industry] = []
            all_industries[industry].append(sector)

    cross_sector = {ind: sectors for ind, sectors in all_industries.items() if len(sectors) > 1}

    if cross_sector:
        errors = True
        print(f"\n⚠️  {len(cross_sector)} industries appear in multiple sectors (likely wrong mappings):")
        for industry, sectors in sorted(cross_sector.items()):
            print(f"\n  '{industry}' appears in:")
            for sector in sectors:
                # Find example stocks
                examples = sp500[
                    (sp500['gics_sector'] == sector) &
                    (sp500['gics_sub_industry'].apply(get_industry) == industry)
                ]['ticker'].head(3).tolist()
                print(f"    - {sector}: {', '.join(examples)}")
    else:
        print("✓ All industries are correctly scoped to single sectors!")

    return not errors


# For universe.py - add industry to the DataFrame
def get_universe():
    """
    Get universe with industry column added.

    Returns:
        List of dicts with ticker, name, gics_sector, gics_sub_industry, gics_industry
    """
    from universe import load_universe as _load_universe

    df = _load_universe()

    # Add industry column
    df['gics_industry'] = df['gics_sub_industry'].apply(get_industry)

    return df.to_dict('records')


if __name__ == '__main__':
    print("Verifying GICS sub-industry to industry mapping...\n")

    # Spot-check key 2023 GICS changes
    print("Spot-checking 2023 GICS reclassifications:")
    from universe import load_sp500
    sp500 = load_sp500()

    test_cases = [
        ('V', 'Financials', 'Transaction & Payment Processing Services'),  # Visa
        ('MA', 'Financials', 'Transaction & Payment Processing Services'),  # Mastercard
        ('PYPL', 'Financials', 'Transaction & Payment Processing Services'),  # PayPal
        ('AMZN', 'Consumer Discretionary', 'Broadline Retail'),  # Amazon
        ('WMT', 'Consumer Staples', 'Consumer Staples Merchandise Retail'),  # Walmart
        ('COST', 'Consumer Staples', 'Consumer Staples Merchandise Retail'),  # Costco
    ]

    all_correct = True
    for ticker, expected_sector, expected_sub in test_cases:
        stock = sp500[sp500['ticker'] == ticker]
        if stock.empty:
            print(f"  {ticker}: Not in S&P 500")
            continue

        actual_sector = stock.iloc[0]['gics_sector']
        actual_sub = stock.iloc[0]['gics_sub_industry']

        if actual_sector == expected_sector and actual_sub == expected_sub:
            print(f"  ✓ {ticker}: {expected_sector} › {expected_sub}")
        else:
            all_correct = False
            print(f"  ✗ {ticker}: Expected {expected_sector} › {expected_sub}")
            print(f"           Got {actual_sector} › {actual_sub}")

    if all_correct:
        print("\n✓ All spot checks passed!")
    print("\n" + "="*70 + "\n")

    # Run full coverage check
    verify_coverage()
