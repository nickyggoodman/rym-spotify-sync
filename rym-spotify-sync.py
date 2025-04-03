'''
Author: Nicholas G Goodman

This script syncronizes a user's Rate Your Music (RYM) ratings with Spotify by
adding each album to a Spotify playlist based on the rating it was given by the
user in RYM. A total of 11 playlists are made. One for unrated albums (albums
with a rating of 0) and ten for albums rating 1 through 10.
'''
import survey
import csv
import sys
import string
import secrets  # "suitable for managing data such as [...] account auth"
import hashlib
import base64
import webbrowser
import urllib
import requests
import json
import re
from urllib.parse import urlparse
from http import server


BASE_URL = 'https://api.spotify.com/v1'

REDIRECT_URL = 'http://localhost:3000/callback'
CLIENT_ID = '58a65635db43470fa773cba91b820b49'

AUTHORIZATION_ENDPOINT = 'https://accounts.spotify.com/authorize'
TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-read-private playlist-read-private playlist-modify-public playlist-modify-private ugc-image-upload user-library-modify'

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

    def log_message(self, format, *args):
        pass


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
        with survey.graphics.SpinProgress(prefix='Creating RYM playlist', epilogue='RYM playlist created!') as progress:        
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


def get_album_id(current_token, album_title, album_artist):

    # get the first two albums resulting for the search query q
    payload = {
            'q': f'{album_title} artist:{album_artist}',
            'type': 'album',
            'limit': 2
            }
    headers = {
            "Authorization": "Bearer " + current_token["access_token"]
            }
    r = requests.get(BASE_URL + '/search',
                     params=payload,
                     headers=headers)

    # if there was no issue with our request
    if r.status_code == 200:

        # get the resulting most relavent albums to match (num=limit)
        res = json.loads(r.text)['albums']['items']

        # get the first matching album from the search results
        for album in res:

            # get the album title without the extraneous labels like
            # 'remaster', 'deluxe', 'live', 'edition'
            res_title = album['name']
            m = re.search(r" \(.*((r|R)emaster|(E|e)dition|(L|l)ive|(D|d)eluxe).*\)", res_title)
            if m:
                res_title = res_title.replace(m.group(), '')
            # get the artist
            res_artist = album['artists'][0]['name']

            if res_title.lower() == album_title.lower() and res_artist.lower() == album_artist.lower():

                # get track uris from the album
                return album['id']

    return ''


def add_albums_to_library(current_token, csv_filename, min_rating):

    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the first line containing labels

        # populate list with  albums above minimum rating
        albums = []
        for row in reader:
            if int(row[7]) >= min_rating:
                albums.append({
                    'album_title': row[5],
                    'album_artist': row[1] + " " + row[2] if row[1] else row[2]
                    })


        with survey.graphics.SpinProgress(prefix='Getting album ids', epilogue='Album ids retrieved') as progress:        
            # create a list of album ids to pass to api
            album_ids = []
            for i in albums:
                album_id = get_album_id(current_token, i['album_title'], i['album_artist'])
                if album_id:
                    album_ids.append(album_id)

        headers = {
                "Authorization": "Bearer " + current_token["access_token"],
                "Content-Type": "application/json"
                }


        with survey.graphics.SpinProgress(prefix='Batch adding albums', epilogue='Albums added to user library') as progress:        
            # adding albums in chunks of 20
            i = 0
            j = 20 if 20 < len(album_ids) else len(album_ids)
            while i < j:
                album_ids_dict = {'ids': album_ids[i:j]}
                album_ids_json = json.dumps(album_ids_dict)
                r = requests.put(BASE_URL + '/me/albums', headers=headers, data=album_ids_json)
                j = j + 20 if j + 20 < len(album_ids) else len(album_ids)
                i = i + 20 if i + 20 < len(album_ids) else len(album_ids)


# adds albums to the generated playlist, or existing playlist
def add_albums_to_playlist(access_token, csv_filename, playlist_id, min_rating):

    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the first line containing labels

        # populate list albums above minimum rating
        albums = []
        for row in reader:
            if int(row[7]) >= min_rating:
                albums.append({
                    'album_title': row[5],
                    'album_artist': row[1] + " " + row[2] if row[1] else row[2]
                    })

        # use a loading bar to indicate progress to user
        with survey.graphics.LineProgress(len(albums), prefix='Adding albums to RYM playlist', epilogue='done!') as progress:

            for i in albums:

                # get album title and artist for the search query q
                album_id = get_album_id(current_token, i['album_title'], i['album_artist'])
                if album_id:
                    headers = {
                            "Authorization": "Bearer " + current_token["access_token"]
                            }
                    r = requests.get(BASE_URL + f'/albums/{album_id}/tracks', headers=headers)
                    track_uris = [f'spotify:track:{track["id"]}' for track in json.loads(r.text)['items']]
                    uris_dict = {'uris': track_uris}
                    uris_json = json.dumps(uris_dict)

                    # add the tracks to the playlist
                    headers = {
                            "Authorization": "Bearer " + current_token["access_token"],
                            "Content-Type": "application/json"
                            }
                    r = requests.post(BASE_URL + f'/playlists/{playlist_id}/tracks', headers=headers, data=uris_json)

                progress.move(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Exactly one argument for the rym export filename is required.")
        print("e.g., python3 rym-spotify-sync.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    survey.printers.info('Authorize this tool through your browser...')

    current_token = request_access_token()

    # select the minimum rating an album should have to be added to spotify
    min_rating = survey.routines.numeric('What minimum rating should albums have to be transferred (0 - 10)? ', decimal=False, value=6)
    while min_rating > 10 or min_rating < 0:
        print('enter value 0 - 10')
        min_rating = survey.routines.numeric('Rating threshold: ', decimal=False, value=6)

    # options for how we add and sort music from rym file
    options = ('add songs to rym playlist',
               'add albums to library')
    indexes = survey.routines.basket('how would you like your music added?', options=options)
    if 0 in indexes:
        generate_rym_playlist(current_token)
        playlist_id = get_playlist_id(current_token)
        add_albums_to_playlist(current_token, filename, playlist_id, min_rating)
    if 1 in indexes:
        add_albums_to_library(current_token, filename, min_rating)


