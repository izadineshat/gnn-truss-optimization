"""Unified GitHub Device-Flow, Make Private, and Push script with token caching & retry."""
import http.client
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CLIENT_ID = "178c6fc778ccc68e1d6a"  # GitHub CLI public OAuth app id
SCOPES = "repo"
REPO = "izadineshat/gnn-truss-optimization"
WORKDIR = r"H:\gnn-truss-optimization"
TOKEN_FILE = os.path.join(os.environ.get("TEMP", "."), "dsh_gh_token.txt")

DEVICE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API = "https://api.github.com"


def post_form(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Accept": "application/json",
        "User-Agent": "dsh-device-login",
    })
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected, ConnectionError) as exc:
            if attempt == 4:
                raise
            time.sleep(3)


def api(method, path, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "dsh-gh-helper",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}


def git(*args):
    env = dict(os.environ)
    env["GIT_SSL_BACKEND"] = "openssl"
    proc = subprocess.run(["git", "-C", WORKDIR, *args], env=env,
                          capture_output=True, text=True, timeout=180)
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def main():
    token = None

    # Check if cached token exists and works
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                cached = f.read().strip()
            if cached:
                st, res = api("GET", "/user", cached)
                if st == 200:
                    token = cached
                    print(f"USING_CACHED_TOKEN_FOR: {res.get('login')}")
        except Exception:
            pass

    if not token:
        # 1) Request device code
        try:
            dev = post_form(DEVICE_URL, {"client_id": CLIENT_ID, "scope": SCOPES})
        except Exception as exc:
            print(f"DEVICE_CODE_ERROR: {exc}")
            return 1

        device_code = dev["device_code"]
        user_code = dev["user_code"]
        verification_uri = dev.get("verification_uri", "https://github.com/login/device")
        interval = int(dev.get("interval", 5))
        expires_in = int(dev.get("expires_in", 900))

        print(f"VERIFY_URL: {verification_uri}")
        print(f"USER_CODE: {user_code}")
        print(f"EXPIRES_IN: {expires_in}")
        sys.stdout.flush()

        # 2) Poll for authorization
        deadline = time.time() + expires_in - 30
        while time.time() < deadline:
            time.sleep(interval)
            try:
                tok = post_form(TOKEN_URL, {
                    "client_id": CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                })
            except urllib.error.HTTPError as exc:
                print(f"POLL_HTTP_ERROR: {exc.code}")
                return 1
            except Exception as exc:
                print(f"NETWORK_RETRY: {exc}")
                continue

            if "access_token" in tok:
                token = tok["access_token"]
                print("AUTH_SUCCESS")
                try:
                    with open(TOKEN_FILE, "w") as f:
                        f.write(token)
                except Exception:
                    pass
                sys.stdout.flush()
                break
            if "error" in tok:
                err = tok["error"]
                if err == "authorization_pending":
                    continue
                if err == "slow_down":
                    interval += 5
                    continue
                print(f"OAUTH_ERROR: {err} ({tok.get('error_description', '')})")
                return 1

    if not token:
        print("TIMEOUT: User did not authorize in time")
        return 1

    # 3) Check user
    status, me = api("GET", "/user", token)
    if status == 200:
        print(f"AUTHENTICATED_USER: {me.get('login')}")
    else:
        print(f"USER_CHECK_FAIL: {status} {me}")

    # 4) Make repo private
    status, repo = api("PATCH", f"/repos/{REPO}", token, {"private": True})
    if status == 200 and repo.get("private"):
        print("REPO_SET_PRIVATE_SUCCESS: True")
    else:
        print(f"REPO_SET_PRIVATE_STATUS: {status} {repo}")

    # 5) Setup remote
    git("remote", "remove", "origin")
    git("remote", "add", "origin", f"https://github.com/{REPO}.git")

    # 6) Push with token (ephemeral url)
    push_url = f"https://x-access-token:{token}@github.com/{REPO}.git"
    rc, out, err = git("-c", "http.sslBackend=openssl", "push", "-u", "--force", push_url, "main")
    print(f"PUSH_RETURN_CODE: {rc}")
    if out:
        print(f"PUSH_STDOUT: {out}")
    if err:
        print(f"PUSH_STDERR: {err}")

    if rc == 0:
        print("PUSH_SUCCESS: Repository updated and pushed successfully!")
    else:
        print("PUSH_FAILED")
        return 1

    # 7) Verify final status
    status, final_repo = api("GET", f"/repos/{REPO}", token)
    if status == 200:
        print(f"FINAL_VERIFICATION: private={final_repo.get('private')}, pushed_at={final_repo.get('pushed_at')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())