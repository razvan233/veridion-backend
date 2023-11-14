import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
from utils import call_api_with_retry as make_request
from scrape import get_reviews_summary

load_dotenv()
VERIDION_API_KEY = os.environ.get("VERIDION_API_KEY")
CHATGPT_V4_KEY = os.environ.get("CHATGPT_V4_KEY")
VERIDION_BASE_URL = "https://data.soleadify.com"

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
auth = HTTPBasicAuth()

users = {
    "dashboard-backend": "ec90afa2-a299-4ab3-9b10-baab83becddf",
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route('/enrich-company', methods=['POST'])
@auth.login_required
def enrich_company():
    data = request.json
    headers = {"x-api-key": VERIDION_API_KEY}
    response = make_request(f"{VERIDION_BASE_URL}/match/v4/companies", data, headers)
    if response and response.status_code == 200:
        enriched_data = response.json()
        company_name = enriched_data['company_legal_names'][0]
        company_lat = enriched_data['main_latitude']
        company_long = enriched_data['main_longitude']
        reviews_summary = get_reviews_summary(company_name, company_lat, company_long, CHATGPT_V4_KEY)
        result = {
            'company_data': enriched_data,
            'reviews_summary':reviews_summary
        }
        return jsonify(result)
    else:
        error_message = response.json().get('message', 'Failed to retrieve data') if response else "No response"
        return jsonify({"error": error_message}), response.status_code if response else 500

if __name__ == '__main__':
    app.run(debug=True)
