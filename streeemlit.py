import streamlit as st
import requests
import base64
import os
from gtts import gTTS
import google.generativeai as genai

# Gemini API Key (replace with your own key if needed)
genai.configure(api_key="AIzaSyBi3EkkKKDKNVmrqp85HxL6mrDEX-8vFMg")
model = genai.GenerativeModel('gemini-2.0-flash-lite')

primary_prompt ="""
You are a friendly and helpful AI assistant, specifically designed to provide real-time visual descriptions to a blind user. Your goal is to help them understand the surroundings in the simplest, most accessible way possible.

Respond ONLY with concise, clear descriptions, focusing on the most important and immediate elements in each image.  Prioritize information about:

*   **Objects:** What are the main objects in the scene? Be as specific as possible (e.g., "a red door", "a person wearing a blue shirt", "a white car").
*   **Location:** Where are the objects located relative to each other and the user (e.g., "a table is in front of you", "a chair is to your left").
*   **Action:** What is happening, if anything? (e.g., "the person is walking", "the car is moving").
*   **Potential Hazards:**  If you see a hazard, mention it immediately (e.g., "a curb ahead," "a step down").

Your descriptions should be no more than 2-3 short sentences.

You will receive a series of images. For each image, provide a new and distinct description without repeating yourself unnecessarily. Focus on the most important information.

Do not provide greetings, introductory phrases, or concluding remarks. Respond directly with the visual description. Do not say "I see", just describe what is going on.

Example (illustrative - adjust to your specific use case):
Image: A picture of a hallway with a closed door.
Output: "A hallway. A closed wooden door is directly in front of you. There is a light switch on the wall to your right."

"""
context = [{"role": "user", "parts": [primary_prompt]}]

# Helper functions
def capture_image_from_esp32cam(esp32_ip):
    try:
        url = f"http://{esp32_ip}:8080/photo.jpg"
        response = requests.get(url, stream=True, timeout=5)
        return response.content if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Capture error: {e}")
        return None

def generate_description(image_bytes):
    image_data = base64.b64encode(image_bytes).decode()
    message = {"role": "user", "parts": [{"mime_type": "image/jpeg", "data": image_data}]}
    response = model.generate_content(context + [message])
    return response.text

def text_to_speech(text, filename="response.mp3"):
    tts = gTTS(text, lang='en')
    tts.save(filename)
    return filename

# Streamlit config
st.set_page_config(page_title="Visual Assistant", layout="wide")

# Sidebar for IP address
with st.sidebar:
    st.title("Settings")
    esp32_ip = st.text_input("ESP32-CAM IP", placeholder="192.168.1.29")

# Page styling
st.markdown("""
    <style>
    .big-button-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 1vh;
        width: 50vh;
    }
    .huge-button {
        font-size: 100px;
        padding: 60px 80px;
        width: 99%;
        height: 400px;
        
        max-width: 800px;
    }
    </style>
""", unsafe_allow_html=True)

# Big centered button
st.markdown('<div class="big-button-container">', unsafe_allow_html=True)
if st.button("📸 Capture and Describe", key="capture", help="Tap to capture and get audio", use_container_width=True):
    if not esp32_ip:
        st.warning("Please enter the ESP32-CAM IP in the sidebar.")
    else:
        with st.spinner("Capturing and processing..."):
            image_data = capture_image_from_esp32cam(esp32_ip)
            if image_data:
                desc = generate_description(image_data)
                mp3_file = text_to_speech(desc)
                audio_base64 = base64.b64encode(open(mp3_file, 'rb').read()).decode()
                audio_html = f"""
                    <audio autoplay>
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
            else:
                st.error("Failed to capture image from ESP32-CAM.")
st.markdown('</div>', unsafe_allow_html=True)
