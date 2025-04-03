# rym-spotify-sync

## Highlights
* add all your rated albums/tracks to a your own playlist
* add all your rated albums to your user library
* filter by rating (0 - 10)

## Overview
rym-spotify-sync reads a csv file, authorizes with Spotify API, and adds your
albums above a minimum rating to a playlist and/or to your user library
depending on the user's selections. Ratings are based on the current user ratings,
not community ratings. The user may choose to add album tracks to a playlist, 
add albums to their user library, or both.

I decided to create this project since I had recently moved over to Spotify after
downloading albums and streaming from youtube for many years. I wanted a quick
way to add the hundreds of albums I have rated to Spotify for me to listen and
enjoy. 

Since Sonemic (formerly RateYourMusic) API is not complete as of yet (04/2025),
this program requires an export of your ratings. However, in the future I hope to 
utilize their API to make it easier to use (and perhaps have automatic updates)

## Usage
* [Export your music](https://rateyourmusic.com/music_export) from RateYourMusic
* run rym-spotify-sync.py with the path to your csv file as an argument\
``` python3 rym-spotify-sync.py path/to/your/export.csv ``` 
* authorize rym-spotify-sync to use your Spotify data
  - a new tab should open in
  your browser if your browser is already open, otherwise a new window will open.
  - read the required permissions, accept, you will be redirected to a blank page.
  - close the tab
* answer the prompts in your console

## Installation
* clone the repository
``` git clone https://github.com/nickyggoodman/rym-spotify-sync.git ```
* install the necessary packages
``` pip install -r requirements.txt ```

## Feedback

