import hashlib
import json 

def convert_to_safe_location(location_pair):
   # locations is a zipped list of file name, location
   location_pair = list(location_pair)
   safe_locations = [
        {
            "device": pairing[0][:-5],
            "timestamp": pairing[1].timestamp.isoformat(),
            "lat": pairing[1].latitude,
            "long": pairing[1].longitude
        } for pairing in location_pair
   ]
   return safe_locations


def encrypt_data(data, secret, output_filepath):
    key = hashlib.sha256(secret.encode()).digest()

    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data.encode()))
    
    with open(output_filepath, "wb") as f:
        f.write(encrypted)
    
    return output_filepath


def decrypt_data(filepath, secret):
    key = hashlib.sha256(secret.encode()).digest()

    with open(filepath, "rb") as f:
        encrypted = f.read()

    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
    return json.loads(decrypted)

