import json

with open(r'C:\Users\natal\Documents\trendably\cache\fundamentals.json', 'r') as f:
    data = json.load(f)

fields = ['enterpriseToEbitda', 'priceToSalesTrailing12Months', 'revenueGrowth',
          'earningsGrowth', 'profitMargins', 'returnOnEquity', 'freeCashflow', 'debtToEquity']

partial = []
for ticker, info in data['stocks'].items():
    missing = [f for f in fields if info.get(f) is None]
    if len(missing) >= 3:
        partial.append({'ticker': ticker, 'industry': info.get('industry', 'Unknown'),
                       'count': len(missing), 'fields': missing})

partial.sort(key=lambda x: (-x['count'], x['ticker']))

# Group by industry
from collections import Counter
industries = Counter(p['industry'] for p in partial)

print(f"Total with 3+ missing: {len(partial)}")
print(f"\nIndustries with 3+ stocks:")
for ind, cnt in industries.items():
    if cnt >= 3:
        print(f"  {ind}: {cnt}")

print(f"\nFirst 10:")
for i, p in enumerate(partial[:10], 1):
    print(f"{i}. {p['ticker']} - {p['industry']} - {p['count']} missing: {', '.join(p['fields'])}")
