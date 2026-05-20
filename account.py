import os
import json
import sys
from findmy import AppleAccount, LocalAnisetteProvider, LoginState, TrustedDeviceSecondFactorMethod, SmsSecondFactorMethod
from dotenv import load_dotenv
from utils import encrypt_data

load_dotenv()

data_dir = os.getenv("DATA_DIR", ".")
ani = LocalAnisetteProvider(libs_path=os.path.join(data_dir, "ani_libs.bin"))
account = AppleAccount(ani)

state = account.login(os.getenv("EMAIL"), os.getenv("PASSWORD"))

if state == LoginState.REQUIRE_2FA:
    methods = account.get_2fa_methods()

    for i, method in enumerate(methods):
        if isinstance(method, TrustedDeviceSecondFactorMethod):
            print(f"{i} - Trusted Device")
        elif isinstance(method, SmsSecondFactorMethod):
            print(f"{i} - SMS ({method.phone_number})")

    ind = int(input("Method? > "))
    method = methods[ind]
    method.request()
    code = input("Code? > ")
    method.submit(code)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    print("ERROR: SECRET_KEY environment variable is not set.", file=sys.stderr)
    sys.exit(1)

os.makedirs(data_dir, exist_ok=True)
output_path = os.path.join(data_dir, "account.enc")
encrypt_data(json.dumps(account.to_json()), secret_key, output_path)
print(f"Account saved to {output_path}")
