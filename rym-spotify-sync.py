'''
Author: Nicholas G Goodman

This script syncronizes a user's Rate Your Music (RYM) ratings with Spotify by
adding each album to a Spotify playlist based on the rating it was given by the
user in RYM. A total of 11 playlists are made. One for unrated albums (albums
with a rating of 0) and ten for albums rating 1 through 10.
'''

import datetime
import csv
import sys
from http import server
import string
import secrets  # "suitable for managing data such as [...] account auth"
import hashlib
import base64
import webbrowser
import urllib
import requests
from urllib.parse import urlparse
import json
import re

BASE_URL = 'https://api.spotify.com/v1'

REDIRECT_URL = 'http://localhost:3000/callback'
CLIENT_ID = '58a65635db43470fa773cba91b820b49'

AUTHORIZATION_ENDPOINT = 'https://accounts.spotify.com/authorize'
TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-read-private playlist-read-private playlist-modify-public playlist-modify-private ugc-image-upload'

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


def request_access_token():
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
    current_token = json.loads(r.text)

    return current_token


# create playlist "rym" with sonemic logo if it does not already exist
def generate_rym_playlist(current_token):

    if not get_playlist_id(current_token):
        headers = {"Authorization": "Bearer " + current_token["access_token"]}

        r = requests.get(BASE_URL + "/me", headers=headers)
        current_user = json.loads(r.text)

        data = {'name': 'rym'}
        headers = {
                    "Authorization": "Bearer " + current_token["access_token"],
                    'Content-Type': 'application/json'
                }
        r = requests.post(BASE_URL + f'/users/{current_user["id"]}/playlists',
                          headers=headers,
                          data=json.dumps(data))

        headers = {
                    "Authorization": "Bearer " + current_token["access_token"],
                    'Content-Type': 'image/jpeg'
                }
        playlist_info = json.loads(r.text)
        with open('sonemic.jpeg', 'rb') as image_file:
            base64_bytes = base64.b64encode(image_file.read())

            r = requests.put(BASE_URL + f'/playlists/{playlist_info["id"]}/images',
                             headers=headers,
                             data=base64_bytes)


# get the playlist id if it exists, otherwise return an empty string
def get_playlist_id(current_token):
    headers = {"Authorization": "Bearer " + current_token["access_token"]}

    r = requests.get(BASE_URL + "/me/playlists", headers=headers)
    current_user_playlists = json.loads(r.text)

    for item in current_user_playlists['items']:
        if item['name'] == 'rym':
            return item['id']

    return ''


# adds albums to the generated playlist, or existing playlist
def add_albums(access_token, csv_filename, playlist_id):

    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        count = 1  # for printing purposes
        match_count = 0

        for row in reader:

            q_album_title = row[5]
            # artist first and last name if present
            q_artist = row[1] + " " + row[2] if row[1] else row[2]

            # print(str(count) + ": ")

            query = q_album_title + ", " + q_artist
            # print("query: " + query)
            # print("")

            # get the first three albums resulting from query q
            payload = {
                    'q': f'{q_album_title} artist:{q_artist}',
                    'type': 'album',
                    'limit': 2
                    }
            headers = {
                    "Authorization": "Bearer " + current_token["access_token"]
                    }
            r = requests.get(BASE_URL + '/search', params=payload, headers=headers)

            if r.status_code == 200:

                res = json.loads(r.text)['albums']['items']

                for album in res:
                    album_title = album['name']
                    m = re.search(r" \(.*((r|R)emaster|(E|e)dition|(L|l)ive|(D|d)eluxe).*\)", album_title)
                    if m:
                        # print('REMASTERED MATCH: ' + m.group())
                        album_title = album_title.replace(m.group(), '')
                    artist = album['artists'][0]['name']
                    # print("q title: " + q_album_title)
                    # print("result title: " + album_title)
                    # print("q artist: " + q_artist)
                    # print("result artist: " + artist)
                    # print("")

                    if album_title.lower() == q_album_title.lower() and artist.lower() == q_artist.lower():

                        # print('match:', album_title + ', ' + artist)
                        # print("")
                        album_id = album['id']
                        r = requests.get(BASE_URL + f'/albums/{album_id}/tracks', headers=headers)
                        track_uris = [f'spotify:track:{track["id"]}' for track in json.loads(r.text)['items']]
                        uris_dict = {'uris': track_uris}
                        uris_json = json.dumps(uris_dict)
                        headers = {
                                "Authorization": "Bearer " + current_token["access_token"],
                                "Content-Type": "application/json"
                                }
                        r = requests.post(BASE_URL + f'/playlists/{playlist_id}/tracks', headers=headers, data=uris_json)
                        match_count += 1
                        break
                

            else:
                print(json.loads(r.text)['error']['message'])

            # print("")

            count += 1  # for printing purposes only

        print(str(match_count) + "/" + str(count))



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Exactly one argument for the rym export filename is required.")
        print("e.g., python3 rym-spotify-sync.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    current_token = request_access_token()

    generate_rym_playlist(current_token)
    playlist_id = get_playlist_id(current_token)

    begin = datetime.datetime.now()
    add_albums(current_token, filename, playlist_id)
    end = datetime.datetime.now()
    print("time to add albums:")
    print(end - begin)


