import os
import re
import json
import random
import logging
import datetime
import tempfile
from threading import Lock
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from utils import convert_to_safe_location, decrypt_data

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", ".")
AIRTAG_PATH = os.path.join(DATA_DIR, "devices")
ACCOUNT_PATH = os.path.join(DATA_DIR, "account.enc")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
_state_lock = Lock()
API_KEY = os.getenv('API_KEY')

_MANHATTAN_LAT = (40.7000, 40.8800)
_MANHATTAN_LON = (-74.0200, -73.9100)
_mock_state: dict[str, dict] = {}

def _slugify(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9\-_]', '', name.replace(' ', '')).strip('-_')

def _atomic_write(filepath: str, data: str):
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath))
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(data)
        os.replace(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def _mock_location(slug: str) -> dict:
    with _state_lock:
        state = _mock_state.setdefault(slug, {
            "lat": random.uniform(*_MANHATTAN_LAT),
            "lon": random.uniform(*_MANHATTAN_LON),
        })
        state["lat"] = max(_MANHATTAN_LAT[0], min(_MANHATTAN_LAT[1], state["lat"] + random.uniform(-0.0005, 0.0005)))
        state["lon"] = max(_MANHATTAN_LON[0], min(_MANHATTAN_LON[1], state["lon"] + random.uniform(-0.0005, 0.0005)))
    return {
        "device": slug, "label": slug,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "latitude": state["lat"], "longitude": state["lon"],
    }

if not DEV_MODE:
    from findmy import AppleAccount, FindMyAccessory

account = None
if DEV_MODE:
    logger.warning("DEV_MODE enabled — locations are mocked.")
elif os.path.isfile(ACCOUNT_PATH):
    try:
        account = AppleAccount.from_json(decrypt_data(ACCOUNT_PATH, os.getenv("SECRET_KEY")), 
                                         anisette_libs_path=os.path.join(DATA_DIR, "ani_libs.bin"))
    except Exception as e:
        logger.error(f"Failed to load account: {e}", exc_info=True)

@app.before_request
def check_api_key():
    if request.path.startswith('/static') or request.path == '/health': return
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer ') or auth_header.split(' ')[1] != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

@app.route('/health', methods=['GET'])
def health(): return '', 204

@app.route('/devices', methods=['GET'])
def get_all_devices():
    if not os.path.exists(AIRTAG_PATH): return jsonify([])
    all_files = [f for f in os.listdir(AIRTAG_PATH) if f.endswith(".json")]
    if DEV_MODE:
        return jsonify([_mock_location(f[:-5]) for f in all_files])
    
    airtags = [FindMyAccessory.from_json(os.path.join(AIRTAG_PATH, p)) for p in all_files]
    location_map = account.fetch_location(airtags)
    for airtag, path in zip(airtags, all_files):
        _atomic_write(os.path.join(AIRTAG_PATH, path), airtag.to_json_string())
    return jsonify(convert_to_safe_location(zip(all_files, location_map.values())))

@app.route('/devices', methods=['POST'])
def add_device():
    if request.content_type == 'application/json':
        body = request.get_json(silent=True)
        slug = _slugify(body.get('name', ''))
        data = json.dumps(body)
    else:
        file = request.files.get('file')
        slug = _slugify((file.filename or '').removesuffix('.json'))
        data = file.read().decode('utf-8')
    
    if not slug: return jsonify({"error": "Invalid name"}), 400
    dest = os.path.join(AIRTAG_PATH, slug + ".json")
    if os.path.exists(dest): return jsonify({"error": "Exists"}), 409
    
    os.makedirs(AIRTAG_PATH, exist_ok=True)
    _atomic_write(dest, data)
    return jsonify({"slug": slug}), 201

@app.route('/devices/<slug>', methods=['GET'])
def get_device_location(slug):
    safe_slug = os.path.basename(slug)
    file_path = os.path.join(AIRTAG_PATH, f"{safe_slug}.json")
    if DEV_MODE: return jsonify(_mock_location(safe_slug))
    
    try:
        airtag = FindMyAccessory.from_json(file_path)
        location = account.fetch_location(airtag)
        _atomic_write(file_path, airtag.to_json_string())
        return jsonify(convert_to_safe_location([(f"{safe_slug}.json", location)])[0])
    except FileNotFoundError:
        return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(port=int(os.getenv("PORT", 5000)))
