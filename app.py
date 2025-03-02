import os
import requests
import openai
import base64
import json
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime

app = Flask(__name__)

# Load API Keys from Environment Variables (Set these in Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Google Sheets Setup (Load JSON from an Environment Variable)
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SHEET_NAME = "1Qxkx5vOaJU4st7UnBDRDsWI_nowMYyOKNIB1Mtul91w" 

# Load Google Sheets Credentials
if SERVICE_ACCOUNT_JSON:
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_NAME).sheet1
else:
    raise ValueError("Missing Google Sheets credentials")

def append_to_google_sheets(data):
    """Sends processed data to Google Sheets."""
    sheet.append_row(data)

@app.route('/')
def home():
	return "Flask API is running"

@app.route('/upload', methods=['POST'])
def upload_photo():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    file.save(f"./uploads/{file.filename}")  # Save file
    
    # return jsonify({"message": "File uploaded successfully!"})
    
    description = request.form.get("description", "")

    # Convert image to Base64 (Render does not support local storage)
    image_base64 = base64.b64encode(file.read()).decode("utf-8")

    # Analyze image with AI
    result = analyze_food_image(image_base64, description)

    # Save to Google Sheets
    append_to_google_sheets(result)

    return jsonify({"message": "Data saved", "analysis": result})

def analyze_food_image(image_base64, user_description=""):
    """Uses OpenAI's DALL·E or GPT-Vision API to analyze food images."""
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",  # Use OpenAI’s Vision model
        messages=[
            {"role": "system", "content": "You are a food recognition assistant. Identify the meal and estimate calories."},
            {"role": "user", "content": user_description},
            {"role": "user", "content": [{"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}]}
        ]
    )

    analysis_text = response["choices"][0]["message"]["content"]

    # Extract relevant info (basic parsing)
    meal_name = analysis_text.split("\n")[0]  # First line as meal name
    calorie_estimate = "Unknown"  # Improve this with a calorie database

    return [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meal_name, calorie_estimate]

if __name__ == '__main__':
    import os
    port = int(os.getenv("PORT", 5000))  # Use Render's assigned port or default to 5000
    app.run(host='0.0.0.0', port=port)