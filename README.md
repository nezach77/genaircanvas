# Project Summary

##Description:
The Generative Air Quality Canvas is a digital product that transforms art into awareness about air pollution , digitizing murals of places and the human lung by coloring it in a way that reflects the real-time air quality of the place. It uses an AI powered image generator to create images based on real-time air quality index (AQI) measurements for a chosen city in countries around the world. The web portal refreshes itself at a set interval which is configurable. The AQI is indicative of the level of pollution the higher it is in a range of 0 – 500 the worse is the air quality and the deeper is the color of the images on the canvas.


## Solution:
* To access air quality data, we use the website World Air Quality Index (WAQI) (https://waqi.imfo/) to retrieve real-time air quality information from around the world

* The AQI is fed to Large language model Claude’s Anthropic to generate the prompt needed for creating images 

* The prompt generated above is Using Amazon Bedrock, Stability AI's Stable Diffusion XL model to automate the process of generating the mural of the visual image in order to evaluate air quality of a city.
* The solution is fully configurable for AWS account , models used etc, via the config file![image](https://github.com/nezach77/genaircanvas/assets/11321882/57f47742-af2f-4081-8f37-0cffa2daacdd)

# How it works
1. Choose the country
2. Choose a city from the country
3. Based on the chosen values the AQI value is retrieved in real-time
4. See the web page displaying the Air Quality. ** See Notes below
5. The Web page displays an image of the city with a color tone of the corresponding AQI value and a human lungs superimposed on the image. As the AQI value increases the images appear to go towards the designated color code. 
6. The Page Auto Refreshes at a set interval![image](https://github.com/nezach77/genaircanvas/assets/11321882/b3b54867-9f4b-4d96-83cb-d1d4f2d94fda)
