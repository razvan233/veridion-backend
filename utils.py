import time
import requests

MAX_RETRIES = 5
WAIT_SECONDS = 2


def call_api_with_retry(url, data,  headers):
    for attempt in range(MAX_RETRIES):
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response 
        elif response.status_code == 202:
            time.sleep(WAIT_SECONDS * (2 ** attempt))  
        else:
            break  

    return None  

