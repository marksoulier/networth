import requests
import os

def get_bea_rpp(api_key, geo_id='06', year='2022'):
    """
    Fetches the Regional Price Parity (RPP) for a given state or metro area from the BEA API.
    Args:
        api_key (str): Your BEA API key.
        geo_id (str): FIPS code for the state or metro area (e.g., '06' for California).
        year (str): Year of interest (e.g., '2022').
    Returns:
        dict: The BEA API response.
    """
    url = "https://apps.bea.gov/api/data/"
    params = {
        'UserID': api_key,
        'method': 'GetData',
        'datasetname': 'Regional',
        'TableName': 'RPPALL',
        'LineCode': '1',  # 1 = All items RPP
        'GeoFIPS': geo_id,
        'Year': year,
        'ResultFormat': 'json'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    API_KEY = os.getenv('BEA_API_KEY') or 'YOUR_BEA_API_KEY'
    result = get_bea_rpp(API_KEY, geo_id='06', year='2022')
    data = result.get('BEAAPI', {}).get('Results', {}).get('Data', [])
    if data:
        rpp = data[0].get('DataValue', 'N/A')
        geo = data[0].get('GeoName', 'Unknown')
        year = data[0].get('TimePeriod', 'Unknown')
        print(f"RPP for {geo} in {year}: {rpp}")
    else:
        print("No data found.") 