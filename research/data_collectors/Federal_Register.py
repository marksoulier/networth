import requests

def get_federal_register_updates(keyword, agency_slug=None, per_page=5):
    url = "https://www.federalregister.gov/api/v1/documents.json"
    params = {
        "per_page": per_page,
        "order": "newest",
        "conditions[term]": keyword,
    }
    if agency_slug:
        params["conditions[agencies]"] = agency_slug
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["results"]

if __name__ == "__main__":
    updates = get_federal_register_updates("tax", agency_slug="internal-revenue-service")
    for doc in updates:
        print(f"{doc['title']} ({doc['publication_date']})\nURL: {doc['html_url']}\n") 