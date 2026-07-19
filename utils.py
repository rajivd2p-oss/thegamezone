import base64
import hashlib
import json
import os
import tempfile
from cryptography.fernet import Fernet

def _derive_key(secret: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())

def convert_to_safe_location(location_pair):
    # Ensure iteration over pairs
    return [
        {
            "device": p[0].replace(".json", ""),
            "label": p[0].replace(".json", ""),
            "timestamp": p[1].timestamp.isoformat(),
            "latitude": p[1].latitude,
            "longitude": p[1].longitude,
        }
        for p in location_pair
    ]

def encrypt_data(data: str, secret: str, output_filepath: str) -> str:
    """Encrypts data and writes it atomically to the target file."""
    fernet = Fernet(_derive_key(secret))
    encrypted = fernet.encrypt(data.encode())
    
    # Atomic write to ensure the .enc file is never partially written
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(output_filepath))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(encrypted)
        os.replace(temp_path, output_filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
    return output_filepath

def decrypt_data(filepath: str, secret: str) -> dict:
    fernet = Fernet(_derive_key(secret))
    with open(filepath, "rb") as f:
        encrypted = f.read()
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted)

