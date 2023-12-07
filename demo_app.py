import streamlit as st
import numpy as np
from PIL import Image
import requests
from streamlit_autorefresh import st_autorefresh
from configparser import ConfigParser
import boto3
import json
import base64
import io

from image_functions import *

# Initialize
config = ConfigParser()
config.read("config.ini")
st.set_page_config(page_title="Air Quality", page_icon=":world_map:", layout="centered")

STREAMLIT_SESSION_VARS = [("city_name", ""), ("aqi", ""), ("image", b"")]
_ = [st.session_state.setdefault(k, v) for k, v in STREAMLIT_SESSION_VARS]

background_color_map = {
    "Good": "green",
    "Moderate": "yellow",
    "Unhealthy for sensitive groups": "orange",
    "Unhealthy": "red",
    "Very Unhealthy": "purple",
    "Harzardous": "maroon",
}

implication_map = {
    "Good": "Air quality is considered satisfactory, and air pollution poses little or no risk.",
    "Moderate": "Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution.	Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion.",
    "Unhealthy for sensitive groups": "Members of sensitive groups may experience health effects. The general public is not likely to be affected.	Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion.",
    "Unhealthy": "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects	Active children and adults, and people with respiratory disease, such as asthma, should avoid prolonged outdoor exertion; everyone else, especially children, should limit prolonged outdoor exertion.",
    "Very Unhealthy": "Health warnings of emergency conditions. The entire population is more likely to be affected.	Active children and adults, and people with respiratory disease, such as asthma, should avoid all outdoor exertion; everyone else, especially children, should limit outdoor exertion.",
    "Harzardous": "Health alert: everyone may experience more serious health effects.	Everyone should avoid all outdoor exertion.",
}

st_autorefresh(
    interval=config.get("UI", "interval"),
    limit=config.get("UI", "limit"),
    key="counter",
)
with st.sidebar:
    map_file = open("data/worldcities_map.json")
    city_map = json.load(map_file)
    country = st.selectbox("Country", options = ["Poland"] + sorted(city_map.keys()), index=0)
    city_name = st.selectbox("City", options = ["Warsaw"] + sorted(city_map[country])).lower()
    #with st.expander("Image options"):
    #    blur_rate = st.slider("Blurring", min_value=0.5, max_value=3.5)
    #    brightness_amount = st.slider(
    #        "Brightness", min_value=-50, max_value=50, value=0
    #    )
    #    apply_enhancement_filter = st.checkbox("Enhance Details")

# API Query

api_key = config.get("API", "api_key")
api_url = config.get("API", "api_url")
api_call = api_url + city_name + "/?token=" + api_key

data = requests.get(api_call).json()
print(data)
if type(data["data"]) == str:
    st.error("Invalid city name.")
    city_name = st.session_state["city_name"]
    aqi = st.session_state["city_name"]
else:
    aqi = data["data"]["aqi"]

aqi_category, aqi_number, alpha = classify_aqi(aqi)


# Bedrock
if (st.session_state["city_name"], st.session_state["aqi"]) != (city_name, aqi):
    (st.session_state["city_name"], st.session_state["aqi"]) = (city_name, aqi)
    print("State changes to: ", (city_name, aqi))
    bedrock_client = boto3.client(
        "bedrock-runtime", region_name=config.get("Bedrock", "region")
    )
    # {implication_map[aqi_category]}
    # LLM
    prompt = f"""

Human: Describe a life in {city_name} when air quality condition is {implication_map[aqi_category]}.
I want to see a lot of {background_color_map[aqi_category]} color in the scene. Make your description not to exceed 80 words.


Assistant:
"""

    body_llm = json.dumps(
        {
            "prompt": prompt,
            "max_tokens_to_sample": 1024,
            "temperature": 0.2,
            "top_k": 150,
            "top_p": 0.8,
            "stop_sequences": ["\n\nHuman:"],
            "anthropic_version": "bedrock-2023-05-31",
        }
    )
    with st.spinner(
        f"Checking current Air Quality Index of {city_name[0].upper()}{city_name[1:]}."
    ):
        response = bedrock_client.invoke_model(
            body=body_llm,
            modelId=config.get("Bedrock", "modelIdLlm"),
            accept="application/json",
            contentType="application/json",
        )
    widget(aqi_category, aqi_number, aqi, city_name)

    prompt_input_for_image = response["body"].read()
    # print("Description", prompt_input_for_image)
    # Image
    text_aqi_drawing_quide = json.loads(prompt_input_for_image.decode())[
        "completion"
    ].split("\n\n")[1]
    text_aqi_drawing_quide = f"""Draw a mural. {text_aqi_drawing_quide}. """
    print(text_aqi_drawing_quide)
    while True:
        body_image = json.dumps(
            {
                "text_prompts": [
                    {"text": text_aqi_drawing_quide},
                ],
                "cfg_scale": 10,
                "seed": 0,
                "steps": 15,
            }
        )
        print("Description", body_image)

        try:
            with st.spinner("See how it will look like..."):
                response = bedrock_client.invoke_model(
                    body=body_image,
                    modelId=config.get("Bedrock", "modelIdImage"),
                    accept="*/*",
                    contentType="application/json",
                )
            response = json.loads(response.get("body").read())
            images = response.get("artifacts")
            image_encoded = images[0].get("base64")
            image = io.BytesIO(base64.b64decode(image_encoded))
            st.session_state["image"] = image_encoded
            break
        except Exception as e:
            print("Exception", e)
            with st.spinner("Trying again..."):
                body_llm = json.dumps(
                    {
                        "prompt": prompt,
                        "max_tokens_to_sample": 1024,
                        "temperature": 0.2,
                        "top_k": 150,
                        "top_p": 0.8,
                        "stop_sequences": ["\n\nHuman:"],
                        "anthropic_version": "bedrock-2023-05-31",
                    }
                )
                response = bedrock_client.invoke_model(
                    body=body_llm,
                    modelId=config.get("Bedrock", "modelIdLlm"),
                    accept="application/json",
                    contentType="application/json",
                )
                prompt_input_for_image = response["body"].read()
                # print("Description", prompt_input_for_image)
                # Image
                text_aqi_drawing_quide = json.loads(prompt_input_for_image.decode())[
                    "completion"
                ].split("\n\n")[1]
                print(text_aqi_drawing_quide)
else:
    print("No changes from the previous mural.")
    image = io.BytesIO(base64.b64decode(st.session_state["image"]))
    widget(aqi_category, aqi_number, aqi, city_name)


rgb = hex_to_rgb(aqi_number)

# st.subheader("")
# st.text("We use real time AQI data using API call to https://api.waqi.info ")

original_image = Image.open(image)

original_image = np.array(original_image)

#processed_image = blur_image(original_image, blur_rate)
#processed_image = brighten_image(processed_image, brightness_amount)
# processed_image = aqi_color_mask(processed_image, rgb, alpha, aqi_category)

#if apply_enhancement_filter:
#    processed_image = enhance_details(processed_image)

# st.text("Air Quality Mural")
st.image([original_image])
