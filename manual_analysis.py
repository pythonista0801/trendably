import json

# Load and analyze
with open(r'C:\Users\natal\Documents\trendably\cache\fundamentals.json', 'r') as f:
    data = json.load(f)

fields = ['enterpriseToEbitda', 'priceToSalesTrailing12Months', 'revenueGrowth',
          'earningsGrowth', 'profitMargins', 'returnOnEquity', 'freeCashflow', 'debtToEquity']

results = []
for ticker, info in data['stocks'].items():
    missing = [f for f in fields if info.get(f) is None]
    if len(missing) >= 3:
        results.append({
            't': ticker,
            'i': info.get('industry', 'Unknown'),
            'c': len(missing),
            'f': missing
        })

results.sort(key=lambda x: (-x['c'], x['t']))

# Count by industry
from collections import Counter
ind_count = Counter(r['i'] for r in results)

print(f"Total: {len(results)}")
print(f"\nClustered industries (3+):")
for ind, cnt in sorted(ind_count.items(), key=lambda x: x[1], reverse=True):
    if cnt >= 3:
        print(f"  {ind}: {cnt}")

print(f"\nTop 10:")
for i, r in enumerate(results[:10], 1):
    print(f"{i}. {r['t']} | {r['i']} | {r['c']} missing")
    print(f"   {', '.join(r['f'])}")
