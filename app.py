import os
import requests
import openai
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime

app = Flask(__name__)

# OpenAI API Key (set this as an environment variable or replace directly)
openai.api_key = "your-openai-api-key"

# Google Sheets setup
SERVICE_ACCOUNT_FILE = "service_account.json"  # Your Google Sheets credentials file
SHEET_NAME = "FoodLog"  # Your Google Sheet name

def append_to_google_sheets(data):
    """Sends processed data to Google Sheets."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    sheet.append_row(data)

@app.route('/upload', methods=['POST'])
def upload_photo():
    """Handles image upload from Apple Shortcuts."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    description = request.form.get("description", "")

    # Save temporarily
    file_path = f"./uploads/{file.filename}"
    file.save(file_path)

    # Process with AI
    result = analyze_food_image(file_path, description)

    # Save to Google Sheets
    append_to_google_sheets(result)

    return jsonify({"message": "Data saved", "analysis": result})

def analyze_food_image(image_path, user_description=""):
    """Uses OpenAI's GPT-4 Vision API to analyze food."""
    with open(image_path, "rb") as image_file:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a food recognition assistant. Identify the meal and estimate calories."},
                {"role": "user", "content": user_description},
                {"role": "user", "content": {"image": image_file.read()}}
            ]
        )

    analysis_text = response["choices"][0]["message"]["content"]

    # Extract relevant info (you may need extra parsing logic)
    meal_name = analysis_text.split("\n")[0]  # Example parsing
    calorie_estimate = "Unknown"  # Can be improved with a database

    return [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meal_name, calorie_estimate]

if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)  # Ensure upload directory exists
    app.run(host='0.0.0.0', port=5000, debug=True)