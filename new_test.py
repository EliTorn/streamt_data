import requests
import urllib.parse
import json
import logging
from typing import List, Dict


# To install required libraries, run:
# pip install requests

class Config:
    SEARCH_URL = "https://recording.seminoleclerk.org/DuProcessWebInquiry/Home/CriteriaSearch"
    IMAGE_URL = "https://recording.seminoleclerk.org/DuProcessWebInquiry/Home/GetDocumentPage/undefined"
    ADDITIONAL_INFO_URL = "https://recording.seminoleclerk.org/DuProcessWebInquiry/Home/LoadInstrument"
    ENCODE_KEY = "JABCDEFGHI"  # Obfuscation key from JS URL


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_additional_info(access_key: str) -> Dict[str, any]:
    request_url = f"{Config.ADDITIONAL_INFO_URL}/?access_key={access_key}!0-0-0"
    logger.info(f"Sending request for Additional Info access_key = {access_key}")
    try:
        response = requests.get(request_url)
        response.raise_for_status()
        try:
            records_list = response.json()
        except Exception as e:
            logger.error(f"Failed to decode JSON from API response {e}")
            return {"from": [], "to": [], "record_date": None}
        record_date_str = records_list.get("FileDate", "")
        record_date = None
        if record_date_str:
            record_date = int(record_date_str.strip('/Date()'))
        parties = records_list.get("PartyCollection", [])
        from_parties = [p.get("PartyName", "") for p in parties if p.get("Direction", "") == 1]
        to_parties = [p.get("PartyName", "") for p in parties if p.get("Direction", "") == 0]
        return {"from": from_parties, "to": to_parties, "record_date": record_date}
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return {"from": [], "to": [], "record_date": None}


def save_records_to_json(records, filename):
    with open(f"{filename}.json", "w") as json_file:
        json.dump(records, json_file, indent=4)
    logger.info(f"Saved {len(records)} records to '{filename}.json'")


def get_access_key(gin: str) -> str:
    return ''.join(Config.ENCODE_KEY[int(digit)] for digit in gin)


def check_for_error(records_list):
    if isinstance(records_list, str):
        return json.loads(records_list).get("Error")
    return None


def get_images_links(get_id: str, num_images: str) -> List[str]:
    return [f"{Config.IMAGE_URL},{get_id},{i}" for i in range(int(num_images))]


def process_item(item: dict) -> dict:
    gin = item.get("gin", "")
    access_key = get_access_key(gin=gin)
    # info = get_additional_info(access_key=access_key)
    return {
        "instrument_number": item.get("inst_num", ""),
        "from": item.get("from_party", ""),
        "to": item.get("to_party", ""),
        "record_date": item.get("file_date", ""),
        "doc_type": item.get("instrument_type", ""),
        "image_links": get_images_links(access_key, item.get("num_pages", "0"))
    }


def fetch_records(first_name: str, last_name: str, from_date: str, thru_date: str):
    full_name = f"{last_name} {first_name}"  # last name first
    criteria = [{
        "full_name": full_name,
        "file_date_start": from_date,
        "file_date_end": thru_date,
    }]
    request_url = f"{Config.SEARCH_URL}?criteria_array={urllib.parse.quote(json.dumps(criteria))}"
    logger.info("Sending request to API:")
    try:
        response = requests.get(request_url)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None


def parse_results(response):
    try:
        records_list = response.json()
    except Exception as e:
        logger.error(f"JSON decoding failed: {e}")
        return []
    error_message = check_for_error(records_list=records_list)
    if error_message:
        logger.error(f"API error: {error_message}")
        return []
    logger.info(f"Received {len(records_list)} records")
    return records_list


def get_records(first_name: str, last_name: str, from_date: str, thru_date: str):
    response = fetch_records(first_name, last_name, from_date, thru_date)
    records = parse_results(response) if response else []
    processed_records = [process_item(item) for item in records]
    return processed_records


def runner():
    first_name = 'ben'
    last_name = 'smith'
    from_date = '01/10/2023'
    thru_date = '01/06/2024'
    output = get_records(first_name, last_name, from_date, thru_date)
    save_records_to_json(records=output, filename=f"{first_name}_{last_name}")
    print(output)


if __name__ == "__main__":
    runner()
