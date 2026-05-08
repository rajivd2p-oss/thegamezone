import base64
import hashlib
import json
from cryptography.fernet import Fernet


def _derive_key(secret: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())


def convert_to_safe_location(location_pair):
    location_pair = list(location_pair)
    return [
        {
            "device": pairing[0][:-5],
            "label": pairing[0][:-5],
            "timestamp": pairing[1].timestamp.isoformat(),
            "latitude": pairing[1].latitude,
            "longitude": pairing[1].longitude,
        }
        for pairing in location_pair
    ]


def encrypt_data(data: str, secret: str, output_filepath: str) -> str:
    fernet = Fernet(_derive_key(secret))
    encrypted = fernet.encrypt(data.encode())
    with open(output_filepath, "wb") as f:
        f.write(encrypted)
    return output_filepath


def decrypt_data(filepath: str, secret: str) -> dict:
    fernet = Fernet(_derive_key(secret))
    with open(filepath, "rb") as f:
        encrypted = f.read()
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted)
