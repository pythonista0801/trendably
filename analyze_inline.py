#!/usr/bin/env python3
"""
Inline analysis - prints directly without external execution
"""
import json
from collections import defaultdict

def analyze_partial_data():
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

    return {
        'total_count': len(partial_data_stocks),
        'total_analyzed': data['count'],
        'stocks': partial_data_stocks,
        'industry_counts': dict(industry_counts)
    }

if __name__ == '__main__':
    result = analyze_partial_data()

    # Print JSON output for easy parsing
    print(json.dumps(result, indent=2))
