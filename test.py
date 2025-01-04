import requests
import json
import pandas as pd
import time
import logging
from datetime import datetime

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_KEY = "IptWE0nC402R9xTCtrWEaVFUG0efE7VVnHceLNpa"  # Replace with your personal API key
API_URL = "https://api.nasa.gov/planetary/apod"

# API data retrieval with retry logic
def get_apod_data(date: str) -> dict:
    max_retries = 3  # Maximum number of retries
    wait_time = 10   # Time to wait between retries (seconds)

    for attempt in range(max_retries):
        try:
            url = f"{API_URL}?api_key={API_KEY}&date={date}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Check rate limit headers (if available)
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                if remaining == 0:
                    retry_after = int(response.headers.get("Retry-After", wait_time))
                    logger.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Too Many Requests
                logger.warning(f"Rate limit hit for date {date}. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP error for date {date}: {e}")
                break
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for date {date}: {e}")
            break
    return None

# Function to fetch APOD data for a range of dates
def fetch_multiple_apod_data(start_date: str, end_date: str) -> list:
    data = []
    try:
        dates = pd.date_range(start=start_date, end=end_date)
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")  # Correct date format for the API
            apod_data = get_apod_data(date_str)

            if apod_data is not None:
                data.append(apod_data)
            else:
                logger.error(f"Error retrieving data for date: {date_str}")

            time.sleep(5)  # Wait 5 seconds between requests to avoid hitting rate limits
    except Exception as e:
        logger.error(f"Unexpected error in date loop: {e}")
    return data

# Function to save data to a JSON file
def save_data_to_json(data: list, filename: str) -> None:
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
        logger.info(f"JSON file saved successfully: {filename}")
    except Exception as e:
        logger.error(f"Error saving JSON file: {e}")

# Parameters
start_date = "2020-01-01"  # Start date
end_date = "2020-01-10"    # End date (adjust as needed for testing)
filename = "apod_data.json"

# Fetch data and save to JSON
data = fetch_multiple_apod_data(start_date, end_date)
if data:  # Check if data is not empty
    save_data_to_json(data, filename)

logger.info("Task complete")
