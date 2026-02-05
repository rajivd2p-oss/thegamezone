import os
import logging
from os import listdir
from flask import Flask, jsonify, request
from findmy import AppleAccount, FindMyAccessory
from dotenv import load_dotenv
from utils import convert_to_safe_location, decrypt_data

load_dotenv()

AIRTAG_PATH = "devices"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

API_KEY = os.getenv('API_KEY')

@app.before_request
def check_account_status():
    if not account:
        logger.warning(f"Attempted to visit ${request.endpoint} but no account found.")
        return jsonify({"error": "No account loaded"}), 503
    pass

@app.before_request
def check_api_key():
    if request.path.startswith('/static'):
        return
    auth_header = request.headers.get('Authorization')
    print(auth_header)
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401
    token = auth_header.split(' ')[1]
    if token != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

account = None
if os.path.exists("account.enc"):
    try:
        logger.info("Found account data, loading account")
        account = AppleAccount.from_json(decrypt_data("account.enc", os.getenv("SECRET_KEY")), anisette_libs_path="ani_libs.bin")
        logger.info("Successfully loaded account from account.json")
    except Exception as e:
        logger.error(f"Failed to load account: {str(e)}", exc_info=True)
        account = None
else:
    logger.warning("account.json not found. API will not function without this file, check the README!")

@app.route('/devices', methods=['GET'])
def get_all_devices():
    all_airtag_metadata = [f for f in listdir(AIRTAG_PATH)]
    airtags = [FindMyAccessory.from_json(os.path.join(AIRTAG_PATH, path)) for path in all_airtag_metadata]
    locations = account.fetch_location(airtags).values()
    parsed_locations = convert_to_safe_location(zip(all_airtag_metadata, locations))
    return jsonify(parsed_locations)
    

@app.route('/devices/<slug>', methods=['GET'])
def get_device_location(slug):
    try:
        airtag = FindMyAccessory.from_json(os.path.join(AIRTAG_PATH, slug + ".json"))
        location = account.fetch_location(airtag)
        airtag.to_json(os.path.join(AIRTAG_PATH, slug + ".json"))
        return jsonify(convert_to_safe_location(slug, location))
    except:
        return jsonify({"error": "Device slug not found"}), 404

if __name__ == '__main__':
    logger.info("Starting Flask API on port " + os.getenv("PORT"))
    app.run(debug=True, port=os.getenv("PORT"))
