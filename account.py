import os
import json
import sys
import tempfile
from findmy import AppleAccount, LocalAnisetteProvider, LoginState, TrustedDeviceSecondFactorMethod, SmsSecondFactorMethod
from dotenv import load_dotenv
from utils import encrypt_data

load_dotenv()

def _atomic_write_file(filepath: str, data: str):
    """Ensures file is written completely or not at all."""
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath))
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(data)
        os.replace(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

data_dir = os.getenv("DATA_DIR", ".")
ani = LocalAnisetteProvider(libs_path=os.path.join(data_dir, "ani_libs.bin"))
account = AppleAccount(ani)

try:
    state = account.login(os.getenv("EMAIL"), os.getenv("PASSWORD"))
    if state == LoginState.REQUIRE_2FA:
        methods = account.get_2fa_methods()
        for i, method in enumerate(methods):
            label = "Trusted Device" if isinstance(method, TrustedDeviceSecondFactorMethod) else f"SMS ({method.phone_number})"
            print(f"{i} - {label}")

        try:
            ind = int(input("Method index? > "))
            method = methods[ind]
            method.request()
            code = input("Enter Code > ")
            method.submit(code)
        except (ValueError, IndexError):
            print("Invalid selection or code.", file=sys.stderr)
            sys.exit(1)
except Exception as e:
    print(f"Auth failed: {e}", file=sys.stderr)
    sys.exit(1)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    print("ERROR: SECRET_KEY not set.", file=sys.stderr)
    sys.exit(1)

os.makedirs(data_dir, exist_ok=True)
output_path = os.path.join(data_dir, "account.enc")

# Atomic Encryption Step
encrypted_data = encrypt_data(json.dumps(account.to_json()), secret_key)
_atomic_write_file(output_path, encrypted_data)
print(f"Account successfully saved to {output_path}")
