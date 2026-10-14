import json
from collections import defaultdict

# Load the fundamentals data
with open(r'C:\Users\natal\Documents\trendably\cache\fundamentals.json', 'r') as f:
    data = json.load(f)

# Fields to check
required_fields = [
    'enterpriseToEbitda',
    'priceToSalesTrailing12Months',
    'revenueGrowth',
    'earningsGrowth',
    'profitMargins',
    'returnOnEquity',
    'freeCashflow',
    'debtToEquity'
]

partial_data_stocks = []
industry_counts = defaultdict(list)

# Analyze each stock
for ticker, stock_data in data['stocks'].items():
    missing_fields = []

    for field in required_fields:
        if field not in stock_data or stock_data[field] is None:
            missing_fields.append(field)

    # If 3 or more fields are missing
    if len(missing_fields) >= 3:
        industry = stock_data.get('industry', 'Unknown')
        partial_data_stocks.append({
            'ticker': ticker,
            'industry': industry,
            'missing_count': len(missing_fields),
            'missing_fields': missing_fields
        })
        industry_counts[industry].append(ticker)

# Sort by missing count (descending) then by ticker
partial_data_stocks.sort(key=lambda x: (-x['missing_count'], x['ticker']))

# Print summary
print("=" * 80)
print("SUMMARY OF STOCKS WITH PARTIAL DATA")
print("=" * 80)
print(f"\nTotal stocks with partial data (3+ missing fields): {len(partial_data_stocks)}")
print(f"Total stocks analyzed: {data['count']}")
print(f"Percentage with partial data: {len(partial_data_stocks) / data['count'] * 100:.1f}%")

# Find industries with clustering (3+ stocks)
clustered_industries = {industry: tickers for industry, tickers in industry_counts.items() if len(tickers) >= 3}

print(f"\n" + "=" * 80)
print("INDUSTRIES WITH CLUSTERING (3+ stocks with partial data)")
print("=" * 80)

if clustered_industries:
    for industry in sorted(clustered_industries.keys()):
        tickers = clustered_industries[industry]
        print(f"\n{industry}: {len(tickers)} stocks")
        print(f"  Tickers: {', '.join(sorted(tickers))}")
else:
    print("\nNo industries with significant clustering (3+ stocks)")

# Print first 10 stocks with partial data
print(f"\n" + "=" * 80)
print("FIRST 10 STOCKS WITH PARTIAL DATA")
print("=" * 80)

for i, stock in enumerate(partial_data_stocks[:10]):
    print(f"\n{i+1}. {stock['ticker']}")
    print(f"   Industry: {stock['industry']}")
    print(f"   Missing fields: {stock['missing_count']}")
    print(f"   Fields missing: {', '.join(stock['missing_fields'])}")

# Detailed breakdown by industry
print(f"\n" + "=" * 80)
print("FULL BREAKDOWN BY INDUSTRY")
print("=" * 80)

industry_summary = defaultdict(int)
for stock in partial_data_stocks:
    industry_summary[stock['industry']] += 1

for industry in sorted(industry_summary.keys(), key=lambda x: industry_summary[x], reverse=True):
    count = industry_summary[industry]
    tickers = industry_counts[industry]
    print(f"\n{industry}: {count} stock(s)")
    print(f"  {', '.join(sorted(tickers))}")

# Analysis: Determine if clustering or random
print(f"\n" + "=" * 80)
print("CLUSTERING ANALYSIS")
print("=" * 80)

total_industries = len(industry_summary)
industries_with_clustering = len(clustered_industries)

print(f"\nTotal industries affected: {total_industries}")
print(f"Industries with 3+ affected stocks: {industries_with_clustering}")
print(f"Industries with 1-2 affected stocks: {total_industries - industries_with_clustering}")

if industries_with_clustering > 0:
    stocks_in_clusters = sum(len(tickers) for tickers in clustered_industries.values())
    print(f"\nStocks in clustered industries: {stocks_in_clusters} ({stocks_in_clusters / len(partial_data_stocks) * 100:.1f}%)")
    print(f"\nConclusion: Partial data shows CLUSTERING pattern")
    print("Key clustered industries:")
    for industry in sorted(clustered_industries.keys(), key=lambda x: len(clustered_industries[x]), reverse=True):
        print(f"  - {industry}: {len(clustered_industries[industry])} stocks")
else:
    print(f"\nConclusion: Partial data appears RANDOMLY DISTRIBUTED")
    print("No single industry has 3 or more stocks with partial data")

# Export detailed list to file
output_file = r'C:\Users\natal\Documents\trendably\partial_data_analysis.txt'
with open(output_file, 'w') as f:
    f.write("COMPLETE LIST OF STOCKS WITH PARTIAL DATA\n")
    f.write("=" * 80 + "\n\n")

    for stock in partial_data_stocks:
        f.write(f"Ticker: {stock['ticker']}\n")
        f.write(f"Industry: {stock['industry']}\n")
        f.write(f"Missing count: {stock['missing_count']}\n")
        f.write(f"Missing fields: {', '.join(stock['missing_fields'])}\n")
        f.write("-" * 80 + "\n")

print(f"\n\nDetailed analysis written to: {output_file}")
