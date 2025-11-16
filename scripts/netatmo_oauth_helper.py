import os
import sys
import urllib.parse
import webbrowser

import requests


def build_authorize_url(client_id: str, redirect_uri: str, scope: str = "read_station", state: str = "xyz") -> str:
    base = "https://api.netatmo.com/oauth2/authorize"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "response_type": "code",
        "state": state,
    }
    return f"{base}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    url = "https://api.netatmo.com/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    resp = requests.post(url, data=data, timeout=20)
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    url = "https://api.netatmo.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    resp = requests.post(url, data=data, timeout=20)
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) < 2:
        print("Usage:\n"
              "  python scripts/netatmo_oauth_helper.py auth-url <CLIENT_ID> <REDIRECT_URI>\n"
              "  python scripts/netatmo_oauth_helper.py exchange <CLIENT_ID> <CLIENT_SECRET> <CODE> <REDIRECT_URI>\n"
              "  python scripts/netatmo_oauth_helper.py refresh <CLIENT_ID> <CLIENT_SECRET> <REFRESH_TOKEN>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "auth-url":
        client_id, redirect_uri = sys.argv[2], sys.argv[3]
        url = build_authorize_url(client_id, redirect_uri)
        print(url)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    elif cmd == "exchange":
        client_id, client_secret, code, redirect_uri = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        tokens = exchange_code_for_tokens(client_id, client_secret, code, redirect_uri)
        print(tokens)
    elif cmd == "refresh":
        client_id, client_secret, refresh_token = sys.argv[2], sys.argv[3], sys.argv[4]
        tokens = refresh_access_token(client_id, client_secret, refresh_token)
        print(tokens)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()


