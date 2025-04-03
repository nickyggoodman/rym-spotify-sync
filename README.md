# rym-spotify-sync

## Highlights
* add all your rated albums/tracks to a your own playlist
* add all your rated albums to your user libarary
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
* run rym-spotify-sync.py with path to your csv file as an argument
``` python3 rym-spotify-sync.py path/to/your/exportcsv ``` 

## Installation

## Feedback

