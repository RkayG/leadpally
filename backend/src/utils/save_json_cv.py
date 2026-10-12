import csv
import json

def parse_and_write_to_csv(json_file, csv_file):
    """ 
    parse a JSON file and write the relevant data to a CSV file.
    Args:
        json_file (str): Path to the input JSON file.
        csv_file (str): Path to the output CSV file.
    """
    if not json_file or not csv_file:
        print("Invalid file paths provided.")
        return
    
    # Open and load the JSON file
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Extract the relevant data (e.g., organic_results)
    organic_results = data.get("organic_results", [])
    
    # Flatten the data for CSV writing
    flattened_data = []
    for result in organic_results:
        flattened_result = {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "description": result.get("description", ""),
            "position": result.get("position", ""),
            "displayed_url": result.get("displayed_url", ""),
            "domain": result.get("domain", ""),
        }
        # Add additional fields if needed
        flattened_data.append(flattened_result)
    
    # Write the flattened data to a CSV file
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        if flattened_data:
            writer = csv.DictWriter(file, fieldnames=flattened_data[0].keys())
            writer.writeheader()
            writer.writerows(flattened_data)
        else:
            print("No data to write to CSV.")

def save_to_json(data, filename):
    """
    Save a list of dictionaries to a JSON file.
    
    Args:
        data (list of dict): The data to save.
        filename (str): The name of the file to save to.
    """

    if not data:
        return

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)



