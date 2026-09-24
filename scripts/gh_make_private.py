"""Make the GitHub repo private and push the local commit (stdlib only)."""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "izadineshat/gnn-truss-optimization"
WORKDIR = r"H:\gnn-truss-optimization"
TOKEN_PATH = os.path.join(os.environ.get("TEMP", "."), "dsh_gh_token.txt")

API = "https://api.github.com"


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


def git(*args, token=None, env_extra=None):
    env = dict(os.environ)
    env["GIT_SSL_BACKEND"] = "openssl"
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(["git", "-C", WORKDIR, *args], env=env,
                          capture_output=True, text=True, timeout=180)
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def main():
    if not os.path.exists(TOKEN_PATH):
        print(f"ERROR: token file not found at {TOKEN_PATH}")
        return 1
    with open(TOKEN_PATH) as fh:
        token = fh.read().strip()
    if not token:
        print("ERROR: empty token")
        return 1

    # 1) who am I
    status, me = api("GET", "/user", token)
    if status != 200:
        print(f"ERROR: auth failed ({status}): {me}")
        return 1
    print(f"AUTHENTICATED_AS: {me.get('login')}")

    # 2) flip repo to private
    status, repo = api("PATCH", f"/repos/{REPO}", token, {"private": True})
    if status != 200:
        print(f"ERROR: could not set private ({status}): {repo}")
        return 1
    print(f"REPO: {repo.get('full_name')} | private={repo.get('private')}")
    if not repo.get("private"):
        print("ERROR: repo is still public")
        return 1
    print("PRIVATE_OK")

    # 3) wire up the remote (token embedded only in the push command env, not in config)
    rc, out, err = git("remote", "get-url", "origin")
    if rc == 0:
        print(f"REMOTE_EXISTS: {out}")
    else:
        rc, out, err = git("remote", "add", "origin",
                           f"https://github.com/{REPO}.git")
        print(f"REMOTE_ADDED: rc={rc} {err or out}")

    # 4) push using an ephemeral credential helper
    askpass = os.path.join(os.environ.get("TEMP", "."), "dsh_askpass.cmd")
    with open(askpass, "w") as fh:
        fh.write("@echo off\r\necho %GIT_ASKPASS_SECRET%\r\n")
    env_extra = {
        "GIT_ASKPASS": askpass,
        "GIT_ASKPASS_SECRET": token,
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "never",
    }
    # Username must be the login; askpass only answers the password prompt.
    rc, out, err = git("-c", "credential.helper=",
                       "-c", "http.sslBackend=openssl",
                       "push", "-u", "origin", "main",
                       env_extra=env_extra)
    print(f"PUSH_RC: {rc}")
    if out:
        print("PUSH_STDOUT:", out)
    if err:
        print("PUSH_STDERR:", err)
    if rc != 0:
        return 1
    print("PUSH_OK")

    # 5) verify
    status, repo = api("GET", f"/repos/{REPO}", token)
    print(f"FINAL: private={repo.get('private')} "
          f"pushed_at={repo.get('pushed_at')} size={repo.get('size')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())