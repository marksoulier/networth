import requests
import os

def get_openstates_bills(api_key, jurisdiction='California', query='tax', per_page=5):
    url = 'https://v3.openstates.org/bills'
    headers = {
        'X-API-KEY': api_key
    }
    params = {
        'jurisdiction': jurisdiction,
        'q': query,
        'sort': '-updated_at',
        'per_page': per_page
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get('results', [])

if __name__ == "__main__":
    API_KEY = os.getenv('OPENSTATES_API_KEY') or 'YOUR_OPENSTATES_API_KEY'
    bills = get_openstates_bills(API_KEY)
    for bill in bills:
        title = bill.get('title', 'No Title')
        jurisdiction = bill.get('jurisdiction', 'Unknown')
        session = bill.get('session', {}).get('identifier', 'Unknown')
        url = bill.get('openstates_url', 'No URL')
        print(f"{title}\nJurisdiction: {jurisdiction} | Session: {session}\nURL: {url}\n") 