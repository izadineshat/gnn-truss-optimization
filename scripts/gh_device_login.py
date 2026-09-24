"""GitHub device-flow login helper (Python stdlib only, no deps)."""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CLIENT_ID = "178c6fc778ccc68e1d6a"  # GitHub CLI public OAuth app id
SCOPES = "repo"

DEVICE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"
STATE_PATH = os.path.join(os.environ.get("TEMP", "."), "dsh_gh_device.json")


def post_json(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Accept": "application/json",
        "User-Agent": "dsh-device-login",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    # 1) Ask GitHub for a device code + user code
    dev = post_json(DEVICE_URL, {"client_id": CLIENT_ID, "scope": SCOPES})
    device_code = dev["device_code"]
    user_code = dev["user_code"]
    verification_uri = dev.get("verification_uri", "https://github.com/login/device")
    interval = int(dev.get("interval", 5))
    expires_in = int(dev.get("expires_in", 900))

    with open(STATE_PATH, "w") as fh:
        json.dump(dev, fh)

    # Print the info the user needs (first lines of job output)
    print(f"VERIFY_URL: {verification_uri}")
    print(f"USER_CODE: {user_code}")
    print(f"EXPIRES_IN: {expires_in}")
    sys.stdout.flush()

    # 2) Poll until the user authorizes in the browser
    deadline = time.time() + expires_in - 30
    while time.time() < deadline:
        time.sleep(interval)
        try:
            tok = post_json(TOKEN_URL, {
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            })
        except urllib.error.HTTPError as exc:
            print(f"POLL_HTTP_ERROR: {exc.code}")
            return 1

        if "access_token" in tok:
            print(f"ACCESS_TOKEN: {tok['access_token']}")
            print("LOGIN_OK")
            return 0
        if "error" in tok:
            err = tok["error"]
            if err == "authorization_pending":
                continue
            if err == "slow_down":
                interval += 5
                continue
            print(f"OAUTH_ERROR: {err} ({tok.get('error_description', '')})")
            return 1

    print("TIMEOUT: user did not authorize in time")
    return 1


if __name__ == "__main__":
    sys.exit(main())