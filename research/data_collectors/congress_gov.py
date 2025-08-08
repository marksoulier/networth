import requests
import os

def get_congress_gov_bills(api_key, query="enacted", limit=5):
    bill_endpoint = "https://api.congress.gov/v3/bill"
    params = {
        "api_key": api_key,
        "q": query,
        "limit": limit,
        "sort": "dateOfIntroduction:desc"
    }
    response = requests.get(bill_endpoint, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    bills = data.get("bills", [])
    return bills

def get_recent_public_laws(api_key, page_size=10):
    """
    Fetch the most recent enacted Public Laws from Congress.gov API.

    Returns a list of dicts with keys:
      - public_law_number
      - title
      - congress
      - latest_action_date
      - latest_action_text
      - originating_bill_url (if available)
    """
    # Congress.gov does not expose a stable "public-laws" list endpoint for v3.
    # Fetch recent bills and filter for those that became public law using latestAction text.
    bill_endpoint = "https://api.congress.gov/v3/bill"
    params = {
        "api_key": api_key,
        "limit": 100,  # fetch more and then filter down
        "sort": "latestActionDate:desc",
    }
    response = requests.get(bill_endpoint, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json() or {}

    bills = payload.get("bills", []) or []
    results = []
    for b in bills:
        latest_action = b.get("latestAction") or {}
        text = (latest_action.get("text") or "").lower()
        if ("became public law" in text) or ("public law" in text and "became" in text):
            # Extract public law number from action text if possible
            action_text = latest_action.get("text", "")
            public_law_number = None
            if "Public Law No:" in action_text:
                # Extract "118-1" from "Became Public Law No: 118-1."
                parts = action_text.split("Public Law No:")
                if len(parts) > 1:
                    public_law_number = parts[1].strip().rstrip(".")
            
            results.append({
                "public_law_number": public_law_number,
                "title": b.get("title"),
                "congress": b.get("congress"),
                "latest_action_date": latest_action.get("actionDate"),
                "latest_action_text": latest_action.get("text"),
                "originating_bill_url": b.get("url"),
            })
        if len(results) >= page_size:
            break
    return results

def get_laws_by_congress(api_key, congress, limit=20):
    """Simple function to get laws with summary and full text"""
    # Get the list of laws
    law_endpoint = f"https://api.congress.gov/v3/law/{congress}"
    response = requests.get(law_endpoint, params={"api_key": api_key, "limit": limit})
    bills = response.json().get("bills", [])
    
    results = []
    for bill in bills:
        # Get basic info
        result = {
            "congress": bill.get("congress"),
            "bill_number": bill.get("number"),
            "bill_type": bill.get("type"),
            "title": bill.get("title"),
            "law_number": bill.get("laws", [{}])[0].get("number") if bill.get("laws") else None,
            "summary": None,
            "full_text": None
        }
        
        # Get summary from summaries endpoint
        congress_num = bill.get("congress")
        bill_type = bill.get("type", "").lower()
        bill_num = bill.get("number")
        
        summaries_url = f"https://api.congress.gov/v3/bill/{congress_num}/{bill_type}/{bill_num}/summaries"
        summaries_response = requests.get(summaries_url, params={"api_key": api_key})
        summaries_data = summaries_response.json().get("summaries", [])
        if summaries_data:
            result["summary"] = summaries_data[0].get("text")
        
        # Get full text from text endpoint
        text_url = f"https://api.congress.gov/v3/bill/{congress_num}/{bill_type}/{bill_num}/text"
        text_response = requests.get(text_url, params={"api_key": api_key})
        text_versions = text_response.json().get("textVersions", [])
        if text_versions:
            # Get the enrolled version (final law text)
            enrolled_version = None
            for version in text_versions:
                if version.get("type") == "Enrolled Bill":
                    enrolled_version = version
                    break
            if not enrolled_version:
                enrolled_version = text_versions[0]  # fallback to first available
            
            # Get the actual text content
            for fmt in enrolled_version.get("formats", []):
                if fmt.get("type") == "Formatted Text":
                    text_content_response = requests.get(fmt.get("url"))
                    result["full_text"] = text_content_response.text
                    break
        
        results.append(result)
    
    return results

def get_law_full_text(full_text_url, timeout=30):
    """
    Fetch the full text content of a law from its URL.
    
    Args:
        full_text_url: URL to the full text (typically from Congress.gov or GPO)
        timeout: Request timeout in seconds
    
    Returns:
        str: The full text content, or None if unavailable
    """
    if not full_text_url:
        return None
        
    try:
        response = requests.get(full_text_url, timeout=timeout)
        response.raise_for_status()
        
        # Handle different content types
        content_type = response.headers.get('content-type', '').lower()
        
        if 'text/plain' in content_type:
            return response.text
        elif 'text/html' in content_type:
            # For HTML, you might want to parse it to extract just the text
            # For now, return the raw HTML
            return response.text
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            return response.text
        else:
            # For other types (like PDF), return the URL with a note
            return f"Full text available at: {full_text_url} (Format: {content_type})"
            
    except requests.RequestException as e:
        return f"Error fetching full text: {e}"

if __name__ == "__main__":
    API_KEY = os.getenv('CONGRESS_GOV_API_KEY') or '6uD30SiXqMt8DDtfY2hbX2EB5zofuveD7wfqIref'
    
    print("=== Laws from 119th Congress (CURRENT - with summaries and full text) ===")
    laws_119 = get_laws_by_congress(API_KEY, 119, limit=5)
    for law in laws_119:
        print(f"Law {law['law_number']}: {law['title']}")
        print(f"  Bill: {law['bill_type']}-{law['bill_number']}")
        
        if law['summary']:
            print(f"  Summary: {law['summary'][:300]}...")
        else:
            print("  Summary: Not available")
            
        if law['full_text']:
            full_text_length = len(law['full_text'])
            print(f"  Full text length: {full_text_length:,} characters")
            print(f"  Full text (first 500 chars): {law['full_text'][:500]}...")
        else:
            print("  Full text: Not available")
        print("-" * 80)
    
    print("\n=== Recent Public Laws (all congresses) ===")
    recent_laws = get_recent_public_laws(API_KEY, page_size=5)
    for law in recent_laws:
        print(f"Law {law['public_law_number']}: {law['title']}")
        print(f"  Congress: {law['congress']}")
        print(f"  Date: {law['latest_action_date']}")
        print()
    
    # fetched_bills = get_congress_gov_bills(API_KEY)
    # for bill in fetched_bills:
    #     title = bill.get('title', 'No Title')
    #     introduced = bill.get('introducedDate', 'No Date')
    #     bill_url = bill.get('url', 'No URL')
    #     print(f"{title} (Introduced: {introduced})\nURL: {bill_url}\n")