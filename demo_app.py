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

STREAMLIT_SESSION_VARS = [("city_name", ""), ("aqi", ""), ("image", b""), ("image_lung", b""),("story", "")]
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
    "Good": "Air quality is considered satisfactory, and air pollution poses little or no risk. Your lungs are very healthy.",
    "Moderate": "Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution.	Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion.",
    "Unhealthy for sensitive groups": "Members of sensitive groups may experience health effects. The general public is not likely to be affected.	Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion.",
    "Unhealthy": "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects	Active children and adults, and people with respiratory disease, such as asthma, should avoid prolonged outdoor exertion; everyone else, especially children, should limit prolonged outdoor exertion.",
    "Very Unhealthy": "Health warnings of emergency conditions. The entire population is more likely to be affected.	Active children and adults, and people with respiratory disease, such as asthma, should avoid all outdoor exertion; everyone else, especially children, should limit outdoor exertion.",
    "Harzardous": "Health alert: everyone may experience more serious health effects.	Everyone should avoid all outdoor exertion.",
}

implication_map_intensity = {
    "Good": "Your lungs are very healthy.The lungs have a color intensity of 1 on a scale of 6",
    "Moderate": "Your lungs are very moderately healthy.The lungs have a color intensity of 2 on a scale of 6",
    "Unhealthy for sensitive groups": "The lungs have a color intensity of 3 on a scale of 6",
    "Unhealthy": "The lungs have a color intensity of 4 on a scale of 6",
    "Very Unhealthy": "The lungs have a color intensity of 5 on a scale of 6",
    "Harzardous": "The lungs have a color intensity of 6 on a scale of 6",
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
   # text_aqi_drawing_quide = f"""Draw an image of a pair of lung, depicting a pair of lungs surrounded by people. {text_aqi_drawing_quide}. """
    print(text_aqi_drawing_quide)
    while True:
        body_image = json.dumps(
            {
                "text_prompts": [
                    {"text": f'Draw a mural of {city_name}. ' + text_aqi_drawing_quide}
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

    with st.spinner("See how your lungs will look like..."):
        body_lung_image = json.dumps(
            {
                "text_prompts": [
                    {"text": f"An abstract whole image of a pair of  lungs , when air quality is {aqi_category}. {implication_map_intensity[aqi_category]}"}
                ],
                "cfg_scale": 10,
                "seed": 0,
                "steps": 12,
            }
        )
        response = bedrock_client.invoke_model(
            body=body_lung_image,
            modelId=config.get("Bedrock", "modelIdImage"),
            accept="*/*",
            contentType="application/json",
        )
    response = json.loads(response.get("body").read())
    images_lung = response.get("artifacts")
    image_encoded_lung = images_lung[0].get("base64")
    image_lung = io.BytesIO(base64.b64decode(image_encoded_lung))
    st.session_state["image_lung"] = image_encoded_lung
    st.session_state["story"] = text_aqi_drawing_quide
    text_aqi_drawing_quide = st.session_state["story"]

else:
    print("No changes from the previous mural.")
    image = io.BytesIO(base64.b64decode(st.session_state["image"]))
    image_lung = io.BytesIO(base64.b64decode(st.session_state["image_lung"]))
    text_aqi_drawing_quide = st.session_state["story"]
    widget(aqi_category, aqi_number, aqi, city_name)


rgb = hex_to_rgb(aqi_number)


original_image = Image.open(image)
lung_image = Image.open(image_lung)
blended_image = Image.blend(lung_image,original_image, alpha=0.7)
st.image([np.array(blended_image)])
st.markdown(
        f'<p style="text-align:justify;text-wrap:wrap;color:black;font-size:20px;color:grey;">{text_aqi_drawing_quide}</p>',
        unsafe_allow_html=True,
    )
