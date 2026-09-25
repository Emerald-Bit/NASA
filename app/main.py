from fastapi import FastAPI, HTTPException
import os
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo
from .config import CURRENT_TZ
from .request import api_request
from .llm import chat_response


load_dotenv()

NASA_API_KEY = os.getenv("NASA_API")

# if not NASA_API_KEY:
#     raise Exception("The API key is missing.")

# if type(NASA_API_KEY) != str:
#     raise Exception("The API is malformed, it is not a string type.")

time_zone = ZoneInfo(CURRENT_TZ)
todays_date = datetime.now(tz=time_zone).date()
# apod_url = f"https://science.nasa.gov/wp-json/wp/v2/apod-basic?api_key={NASA_API_KEY}"
apod_parameters = {"date": todays_date,
                   "start_date": None,
                   "end_date": todays_date,
                   "count": None}

app = FastAPI()

# ApodResponseValidation
class ApodResponseValidation(BaseModel):
    final_message: str
    pic_link: str


@app.get("/health", 
         description="Check the health of the server.")
def get_health() -> dict[str, str]:
    return {"health": "okay"}


@app.get("/apod",
         response_model=ApodResponseValidation,
         description="Return NASA's astronomy picture of the day.")
async def get_apod():

    if not NASA_API_KEY:
        raise Exception("The API key is missing.")

    if type(NASA_API_KEY) != str:
        raise Exception("The API is malformed, it is not a string type.")

    apod_url = f"https://science.nasa.gov/wp-json/wp/v2/apod-basic?api_key={NASA_API_KEY}"


    payload = await api_request(url=apod_url, parameters=apod_parameters)

    if payload is None:
        raise Exception("NASA APOD api call returned with no data.")
    else:
        external_llm_context = {
            "pic_title": payload.get("title", ""),
            "pic_long_description": payload.get("explanation", ""),
            "pic_short_description": payload.get("alt", ""),
            "pic_link": payload.get("hdurl", "No image found")
        }

    if external_llm_context["pic_link"] == "No image found":
        raise HTTPException(
            status_code=500,
            detail="NASA APOD did not return an image."
        )

    try:
        final_message = chat_response(external_llm_context)
    except RuntimeError as e:
        raise HTTPException(
            status_code=502,
            detail="Problem with llm"
        )

    return {
        "final_message": final_message,
        "pic_link": external_llm_context["pic_link"]
        }


if __name__ == "__main__":
    uvicorn.run(app=app,
                host="127.0.0.1",
                port=8000)
