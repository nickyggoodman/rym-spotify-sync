'''
Author: Nicholas G Goodman

This script syncronizes a user's Rate Your Music (RYM) ratings with Spotify by
adding each album to a Spotify playlist based on the rating it was given by the
user in RYM. A total of 11 playlists are made. One for unrated albums (albums
with a rating of 0) and ten for albums rating 1 through 10.
'''

from http import server
import string
import secrets  # "suitable for managing data such as [...] account auth"
import hashlib
import base64
import webbrowser
import urllib
import requests
from urllib.parse import urlparse, parse_qs

BASE_URL = 'https://api.spotify.com'

REDIRECT_URL = 'http://localhost:3000/callback'
CLIENT_ID = '58a65635db43470fa773cba91b820b49'

AUTHORIZATION_ENDPOINT = 'https://accounts.spotify.com/authorize'
TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-read-private user-read-email'

running = True
code = ''


class SimpleHTTPRequestHandler(server.BaseHTTPRequestHandler):
    """HTTP request handler with additional properties and functions"""

    def do_GET(self):
        """Handle GET requests"""
        global running
        global code
        running = False
        query = urlparse(self.path).query
        query_components = dict(qc.split("=") for qc in query.split("&"))
        code = query_components['code']
        self.send_response(200)
        self.end_headers()


def run_server(server_class=server.HTTPServer, handler_class=SimpleHTTPRequestHandler):
    server_address = ('', 3000)
    httpd = server_class(server_address, handler_class)
    while running:
        httpd.handle_request()


def generate_random_string(length):
    possible = string.ascii_letters + string.digits
    return ''.join(secrets.choice(possible) for i in range(length))


def sha256(plain):
    m = hashlib.sha256()
    m.update(plain.encode())
    hashed = m.digest()
    return hashed


def base64_encode(input):
    return base64.b64encode(input).replace(b'=', b'').replace(b'+', b'-').replace(b'/', b'_')


if __name__ == "__main__":
    code_verifier = generate_random_string(64)

    hashed = sha256(code_verifier)
    code_challenge = base64_encode(hashed)
    
    payload = {
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'scope': SCOPE,
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge,
            'redirect_uri': REDIRECT_URL
            }

    r = webbrowser.open(AUTHORIZATION_ENDPOINT + "?" + urllib.parse.urlencode(payload))
    run_server()
    headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {
            'client_id': CLIENT_ID,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URL,
            'code_verifier': code_verifier,
    }
    r = requests.post(TOKEN_ENDPOINT, headers=headers, params=payload)
    print(r.text)
