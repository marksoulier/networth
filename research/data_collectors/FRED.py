import requests
import os

def FRED_data(series_id, api_key=None):
    """
    Fetches the latest observation for a given FRED series ID.
    Args:
        series_id (str): The FRED series ID (e.g., 'CPIAUCSL' for Consumer Price Index).
        api_key (str, optional): Your FRED API key. If not provided, will look for 'FRED_API_KEY' in environment variables.
    Returns:
        dict: Latest observation data or error message.
    """
    if api_key is None:
        api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        raise ValueError("FRED API key not provided. Set FRED_API_KEY env variable or pass as argument.")
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 1
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    data = response.json()
    if 'observations' in data and data['observations']:
        return data['observations'][0]
    else:
        return {"error": "No data found for this series."}


def run_fred():
    API_KEY = os.getenv('FRED_API_KEY') or '34ee2b790e357716dbb3e351fbd4e4c0'
    series = 'CPIAUCSL'  # Consumer Price Index for All Urban Consumers: All Items
    result = FRED_data(series, api_key=API_KEY)
    print(f"Latest CPI data: {result}") 


if __name__ == "__main__":
    run_fred()