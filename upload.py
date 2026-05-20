#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

DEVICES_DIR = os.path.join(os.getenv("DATA_DIR", "."), "devices")


def upload_device(endpoint: str, path: str, api_key: str) -> bool:
    with open(path) as f:
        data = json.load(f)

    body = json.dumps(data).encode()
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    print(f"  -> POST {endpoint}")
    print(f"  -> name field: {data.get('name')!r}")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"  OK: {result.get('slug')}")
            return True
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"  <- HTTP {e.code} {e.msg}")
        try:
            error = json.loads(raw).get("error", e.reason)
        except Exception:
            error = raw.decode(errors="replace") or e.reason
        print(f"  FAILED: {error}")
        return False
    except urllib.error.URLError as e:
        print(f"  FAILED (connection error): {e.reason}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload all devices to a remote endpoint.")
    parser.add_argument("endpoint", help="URL of the POST /devices endpoint")
    parser.add_argument("--api-key", required=True, help="Bearer token for Authorization header")
    args = parser.parse_args()

    print(f"Devices dir: {DEVICES_DIR}")
    print(f"Endpoint:    {args.endpoint}\n")

    files = [f for f in os.listdir(DEVICES_DIR) if f.endswith(".json")]
    if not files:
        print("No device files found.")
        sys.exit(0)

    ok = 0
    for filename in sorted(files):
        path = os.path.join(DEVICES_DIR, filename)
        print(filename)
        if upload_device(args.endpoint, path, args.api_key):
            ok += 1

    print(f"\n{ok}/{len(files)} uploaded successfully.")
    if ok < len(files):
        sys.exit(1)


if __name__ == "__main__":
    main()
