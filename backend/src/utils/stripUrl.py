import json
from urllib.parse import urlparse

def strip_url_to_domain(url):
    """
    Strips a URL to its domain (e.g., 'https://www.awario.com/' -> 'awario.com').
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace("www.", "")  # Remove 'www.' if present
        return domain
    except Exception as e:
        print(f"Error parsing URL: {url} - {e}")
        return url  # Return the original URL if parsing fails

def test_strip_url_to_domain(json_file_path):
    """
    Reads a JSON file, extracts URLs from 'organic_results', and strips them to their domains.
    """
    try:
        # Load the JSON file
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Extract URLs from 'organic_results'
        organic_results = data.get("organic_results", [])
        print("Original URLs and Stripped Domains:\n")
        
        for result in organic_results:
            url = result.get("url", "")
            stripped_domain = strip_url_to_domain(url)
            print(f"Original URL: {url}\nStripped Domain: {stripped_domain}\n")

    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Test the function with the provided JSON file
if __name__ == "__main__":
    json_file_path = "scrapingbee_results_awario.json"  # Replace with the correct path to your JSON file
    test_strip_url_to_domain(json_file_path)