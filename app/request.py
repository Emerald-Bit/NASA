import requests
import time
from zoneinfo import ZoneInfo
from datetime import datetime
from .config import CURRENT_TZ

time_zone = ZoneInfo(CURRENT_TZ)
todays_date = datetime.now(tz=time_zone).date()
retries = 3
delay_time = 5
apod_url = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
apod_parameters = {"date": todays_date,
                   "start_date": None,
                   "end_date": todays_date,
                   "count": None}

async def api_request(*, url: str, parameters: dict[str, str|int], retries:int=3, delay_time:int=5) -> dict[str, str] | None:
    """Launches an API request to your chosen URI."""

    if not url:
        raise Exception("The url is missing.")

    payload = None

    for attempts in list(range(1, (retries + 1))):
        try:
            response = requests.get(url=url, params=parameters, timeout=delay_time)

            if 200 <= response.status_code < 300:
                payload = response.json()[0]
                break
            elif 300 <= response.status_code < 400:
                print(f"There was redirect from the server side. Error message: {response.text}")
                break
            elif 400 <= response.status_code < 500:
                print(f"There is an error on the client side. Error message: {response.text}")
                break
            elif response.status_code >= 500:
                print(f"There is an error on the sever side. Error message: {response.text}")
                break
        except Exception as e:
            print("There was an unexpected exception.\n"
                  f"Here's the error message: {e}")

        
        if payload != None:
            break
        else:
            time.sleep(2)

    return payload
