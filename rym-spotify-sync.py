'''
Author: Nicholas G Goodman

This script syncronizes a user's Rate Your Music (RYM) ratings with Spotify by 
adding each album to a Spotify playlist based on the rating it was given by the 
user in RYM. A total of 11 playlists are made. One for unrated albums (albums
with a rating of 0) and ten for albums rating 1 through 10.
'''

import sys
import csv

# base url for Spotify API
BASE_URL = 'https://api.spotify.com'

CLIENT_ID = ''
REDIRECT_URL = 'http://localhost:8080'
AUTHORIZATION_ENDPOINT = 'https://accounts.spotify.com/authorize'
TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-read-private user-read-email'

if __name__ == "__main__":
    with  open(sys.argv[1], newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row['Rating'])
