import os
import json
import random
import logging
import datetime
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from utils import convert_to_safe_location, decrypt_data

load_dotenv()

AIRTAG_PATH = "devices"
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

API_KEY = os.getenv('API_KEY')

# Manhattan bounding box (approximate)
_MANHATTAN_LAT = (40.7000, 40.8800)
_MANHATTAN_LON = (-74.0200, -73.9100)

# Seeded per-device state so locations drift plausibly between requests
_mock_state: dict[str, dict] = {}

def _mock_location(slug: str) -> dict:
    state = _mock_state.setdefault(slug, {
        "lat": random.uniform(*_MANHATTAN_LAT),
        "lon": random.uniform(*_MANHATTAN_LON),
    })
    # Drift up to ~50 metres per call (roughly 0.0005 degrees)
    state["lat"] = max(_MANHATTAN_LAT[0], min(_MANHATTAN_LAT[1], state["lat"] + random.uniform(-0.0005, 0.0005)))
    state["lon"] = max(_MANHATTAN_LON[0], min(_MANHATTAN_LON[1], state["lon"] + random.uniform(-0.0005, 0.0005)))
    return {
        "device": slug,
        "label": slug,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "latitude": state["lat"],
        "longitude": state["lon"],
    }

if not DEV_MODE:
    from findmy import AppleAccount, FindMyAccessory

account = None
if DEV_MODE:
    logger.warning("DEV_MODE is enabled — Apple account auth bypassed, locations are mocked.")
elif os.path.exists("account.enc"):
    try:
        logger.info("Found account data, loading account")
        account = AppleAccount.from_json(decrypt_data("account.enc", os.getenv("SECRET_KEY")), anisette_libs_path="ani_libs.bin")
        logger.info("Successfully loaded account")
    except Exception as e:
        logger.error(f"Failed to load account: {str(e)}", exc_info=True)
        account = None
else:
    logger.warning("account.enc not found. API will not function without this file, check the README!")

@app.before_request
def check_api_key():
    if request.path.startswith('/static') or request.path == '/health':
        return
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401
    token = auth_header.split(' ')[1]
    if token != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

@app.before_request
def check_account_status():
    if not DEV_MODE and not account:
        logger.warning(f"Attempted to visit {request.endpoint} but no account found.")
        return jsonify({"error": "No account loaded"}), 503

@app.route('/health', methods=['GET'])
def health():
    return '', 204


@app.route('/devices', methods=['GET'])
def get_all_devices():
    if not os.path.exists(AIRTAG_PATH):
        return jsonify([])
    all_airtag_metadata = os.listdir(AIRTAG_PATH)
    if DEV_MODE:
        slugs = [f[:-5] for f in all_airtag_metadata if f.endswith(".json")]
        return jsonify([_mock_location(s) for s in slugs])
    airtags = [FindMyAccessory.from_json(os.path.join(AIRTAG_PATH, path)) for path in all_airtag_metadata]
    locations = account.fetch_location(airtags).values()
    parsed_locations = convert_to_safe_location(zip(all_airtag_metadata, locations))
    return jsonify(parsed_locations)


@app.route('/devices', methods=['POST'])
def add_device():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    slug = request.form.get('name', '').strip()
    if not slug:
        return jsonify({"error": "Missing 'name' field"}), 400
    if not all(c.isalnum() or c in ('-', '_') for c in slug):
        return jsonify({"error": "Name may only contain alphanumeric characters, hyphens, and underscores"}), 400
    if DEV_MODE:
        # In dev mode accept any valid-looking JSON without writing to disk
        try:
            json.loads(file.read().decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return jsonify({"error": "Invalid JSON file"}), 400
        logger.info(f"[DEV] Registered mock device '{slug}'")
        _mock_state.setdefault(slug, {
            "lat": random.uniform(*_MANHATTAN_LAT),
            "lon": random.uniform(*_MANHATTAN_LON),
        })
        return jsonify({"slug": slug}), 201
    try:
        data = file.read().decode('utf-8')
        json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return jsonify({"error": "Invalid JSON file"}), 400
    os.makedirs(AIRTAG_PATH, exist_ok=True)
    dest = os.path.join(AIRTAG_PATH, slug + ".json")
    if os.path.exists(dest):
        return jsonify({"error": f"Device '{slug}' already exists"}), 409
    with open(dest, 'w') as f:
        f.write(data)
    logger.info(f"Added device '{slug}'")
    return jsonify({"slug": slug}), 201


@app.route('/devices/<slug>', methods=['GET'])
def get_device_location(slug):
    if DEV_MODE:
        if not os.path.exists(AIRTAG_PATH) or not os.path.exists(os.path.join(AIRTAG_PATH, slug + ".json")):
            # In dev mode, auto-create a mock entry if the file doesn't exist
            if slug not in _mock_state:
                return jsonify({"error": "Device slug not found"}), 404
        return jsonify(_mock_location(slug))
    try:
        airtag = FindMyAccessory.from_json(os.path.join(AIRTAG_PATH, slug + ".json"))
        location = account.fetch_location(airtag)
        airtag.to_json(os.path.join(AIRTAG_PATH, slug + ".json"))
        return jsonify(convert_to_safe_location([(slug + ".json", location)])[0])
    except FileNotFoundError:
        return jsonify({"error": "Device slug not found"}), 404
    except Exception as e:
        logger.error(f"Failed to fetch location for {slug}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch device location"}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"Starting Flask API on port {port}")
    app.run(debug=debug, port=port)
