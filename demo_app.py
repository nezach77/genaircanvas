import cv2
import streamlit as st
import numpy as np
from PIL import Image
import requests
from streamlit_autorefresh import st_autorefresh
from configparser import ConfigParser


def classify_aqi(aqi):
    if aqi >= 0 and aqi <= 50:
        return ("Good", "00e400")
    elif aqi >= 51 and aqi <= 100:
        return ("Moderate", "ffff00")
    elif aqi >= 101 and aqi <= 150:
        return ("Unhealthy for sensitive groups", "ff7e00")
    elif aqi >= 151 and aqi <= 200:
        return ("Unhealthy", "ff0000")
    elif aqi >= 201 and aqi <= 300:
        return ("Very Unhealthy", "8f3f97")
    elif aqi >= 301 and aqi <= 350:
        return ("Hazardous", "7e0023")


# col1, col2 ,col3,col4, col5 ,col6= st.columns(6)
# with col1:
#     color1 = st.color_picker('Good', '#00e400',key=1)
# with col2:
#     color2 = st.color_picker('Moderate', '#ffff00',key=2)
# with col3:
#     color3 = st.color_picker('Unhealthy for sensitive groups', '#ff7e00',key=3)
# with col4:
#     color4 = st.color_picker('Unhealthy', '#ff0000',key=4)
# with col5:
#     color5 = st.color_picker('Very Unhealthy', '#8f3f97',key=5)
# with col6:
#     color6 = st.color_picker('Hazardous', '#7e0023',key=6)

# text=st.header(aqi)


def example(color1, color2, color3, AQI):
    st.markdown(
        f'<p style="text-align:center;background-color: linear-gradient(to right,{color1}, {color2});color:{color3};font-size:24px;border-radius:2%;">{st.header(aqi)}</p>',
        unsafe_allow_html=True,
    )


def header(aqi_category, aqi_number, city_name):
    city = city_name.capitalize() + " Air Quality"
    st.title(city)
    aqi_category = aqi_category.capitalize()
    st.markdown(
        f'<p style="text-align:Left;background-color:white;background-size:300px 150px;color:#{aqi_number};font-size:32px;border-radius:2%;margin-bottom:-1em;margin-top:0em;">{aqi_category } with AQI of {aqi}</p>',
        unsafe_allow_html=True,
    )


def brighten_image(image, amount):
    img_bright = cv2.convertScaleAbs(image, beta=amount)
    return img_bright


def aqi_color_mask(image, rgb):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    aqi_mask = cv2.inRange(hsv, (rgb, rgb))
    hsv[:, :, 1] = aqi_mask
    aqi_mask = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return aqi_mask


def blur_image(image, amount):
    blur_img = cv2.GaussianBlur(image, (11, 11), amount)
    return blur_img


def enhance_details(img):
    hdr = cv2.detailEnhance(img, sigma_s=12, sigma_r=0.15)
    return hdr


def hex_to_rgb(hex):
    rgb = []
    for i in (0, 2, 4):
        decimal = int(hex[i : i + 2], 16)
        rgb.append(decimal)

    return tuple(rgb)


config = ConfigParser()
config.read("config.ini")

st_autorefresh(
    interval=config.get("UI", "interval"),
    limit=config.get("UI", "limit"),
    key="counter",
)

city_name = st.text_input("Enter City", "warsaw").lower()

api_key = config.get("API", "api_key")
api_url = config.get("API", "api_url")
api_call = api_url + city_name + "/?token=" + api_key

st.write(api_call)
data = requests.get(api_call).json()
print(data)
if data["status"] == "ok":
    aqi = data["data"]["aqi"]
else:
    st.error("Invalid station name.")

aqi_category, aqi_number = classify_aqi(aqi)

header(aqi_category, aqi_number, city_name)

st.subheader("")
st.text("We use real time AQI data using API from https://aqicn.org/api/ ")

blur_rate = st.sidebar.slider("Blurring", min_value=0.5, max_value=3.5)
brightness_amount = st.sidebar.slider(
    "Brightness", min_value=-50, max_value=50, value=0
)
apply_enhancement_filter = st.sidebar.checkbox("Enhance Details")
rgb = hex_to_rgb(aqi_number)
print(rgb)

uploaded_file = st.file_uploader("Upload Your Mural", type=["jpg", "png", "jpeg"])
if not uploaded_file:
    image_file = "data/image.png"
else:
    image_file = uploaded_file

original_image = Image.open(image_file)
original_image = np.array(original_image)
print(original_image.shape)

processed_image = blur_image(original_image, blur_rate)
processed_image = brighten_image(processed_image, brightness_amount)
# processed_image = aqi_color_mask(processed_image, rgb)

if apply_enhancement_filter:
    processed_image = enhance_details(processed_image)

st.text("Air Quality Mural")
st.image([processed_image])
