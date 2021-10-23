import json
import re
import requests
import spotipy
import subprocess
import time

from pathlib import Path
from spotipy import util
from spotipy.oauth2 import SpotifyClientCredentials

AUDIO_TAG_API_KEY = ''
SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''
SPOTIFY_USERNAME = ''
SPOTIFY_SCOPE = 'playlist-modify-public'
SPOTIFY_TOKEN = ''
AUDIO_TAG_API_URL = 'https://audiotag.info/api'
MUSIC_LIBRARY_ROOT = r'D:/Music'
RETRIES_LIMIT = 10
SAMPLE_DIRECTORY = r'samples'
SAMPLE_LENGTH = '15'
TARGET_PLAYLIST_NAME = 'portify'
SPOTIFY_CLIENT = None

with open('resources/api-key.txt', 'r') as f:
    if AUDIO_TAG_API_KEY == '':
        AUDIO_TAG_API_KEY = f.readline().rstrip()
    if SPOTIFY_USERNAME == '':
        SPOTIFY_USERNAME = f.readline().rstrip()
    if SPOTIFY_CLIENT_ID == '':
        SPOTIFY_CLIENT_ID = f.readline().rstrip()
    if SPOTIFY_CLIENT_SECRET == '':
        SPOTIFY_CLIENT_SECRET = f.readline().rstrip()

# SPOTIFY_CLIENT = spotipy.Spotify(auth_manager = SpotifyClientCredentials(   client_id = SPOTIFY_CLIENT_ID,
#                                                                             client_secret = SPOTIFY_CLIENT_SECRET))

SPOTIFY_TOKEN = util.prompt_for_user_token( SPOTIFY_USERNAME,
                                            SPOTIFY_SCOPE,
                                            client_id = SPOTIFY_CLIENT_ID,
                                            client_secret = SPOTIFY_CLIENT_SECRET,
                                            redirect_uri='http://localhost/')

SPOTIFY_CLIENT = spotipy.Spotify(auth = SPOTIFY_TOKEN)

def api_call(payload, file_path = None, url = AUDIO_TAG_API_URL):
    result = None
    if file_path:
        with open(file_path, 'rb') as f:
            result = requests.post( url,
                                    data = payload,
                                    files = {'file': f},
                                    timeout = 120)
    else:
        result = requests.post(url, data = payload, timeout = 120)
    return json.loads(result.text)

def api_test():
    test_payload = {'action': 'info', 'apikey': AUDIO_TAG_API_KEY}
    test_json = api_call(test_payload)
    print("API test success = " + str(test_json['success']))

def get_file_paths(root_path = MUSIC_LIBRARY_ROOT):
    return [p.__str__() for p in Path(root_path).rglob("*.*") if p.__str__()[-4:] != '.ini']

def get_file_count(root_path = MUSIC_LIBRARY_ROOT):
    files = get_file_paths(root_path)
    return len(files)

def get_remaining_api_credits(apikey = AUDIO_TAG_API_KEY):
    payload = {'action': 'stat', 'apikey': apikey}
    json = api_call(payload)
    return json['identification_free_sec_remainder']

def test_feasibility(length = SAMPLE_LENGTH):
    required = int(length) * get_file_count()
    available = get_remaining_api_credits()
    return required + 100 < available

# ffmpeg format:
# ffmpeg -i <file> -ss 00:00:30 -ar 8000 -ac 1 -vn -t <length> <target>/<target_name>.wav
def generate_sample(file, target_name, length, target):
    target_path = target + '/' + target_name + '.wav'
    call_parameters = ['ffmpeg', '-y', '-i', file, '-ss', '00:00:30', '-ar', '8000', '-ac', '1', '-vn', '-t', length, target_path]
    print(call_parameters)
    subprocess.call(call_parameters, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def generate_samples(files, length = SAMPLE_LENGTH, target = SAMPLE_DIRECTORY):
    print("Generating samples for files in: " + target)
    for i in range(len(files)):
        generate_sample(files[i], str(i), length, target)
    return get_file_count(target)

def fetch_song_details(track, apikey = AUDIO_TAG_API_KEY):
    print('Processing track: ' + track)
    output = {}
    payload = {'action': 'identify', 'apikey': apikey}
    result = api_call(payload, track)
    if result['success'] and result['job_status'] == 'wait':
        retry_payload = {'action': 'get_result', 'token': result['token'], 'apikey': apikey}
        for retries_count in range(RETRIES_LIMIT):
            time.sleep(0.5)
            retry_result = api_call(retry_payload)
            if 'success' in retry_result and retry_result['success']:
                if retry_result['result'] == 'found':
                    best_song = retry_result['data'][0]['tracks'][0]
                    song_name = best_song[0]
                    song_artist = best_song[1]
                    output['found'] = True
                    output['name'] = song_name
                    output['artist'] = song_artist
                    return output
                if retry_result['result'] == 'not found':
                    output['found'] = False
                    return output
        output['error'] = result
        return output

def tag_all_songs(track_list):
    print("Starting free credits: " + str(get_remaining_api_credits()))
    tag_list = []
    error_list = []
    for track in track_list:
        track_result = fetch_song_details(track)
        if track_result['found']:
            tag_list.append((track_result['name'], track_result['artist']))
        elif 'error' in track_result:
            error_list.append((track, track_result['error']))
        else:
            error_list.append((track, False))
    with open('resources/tag_list.txt', 'w', encoding = 'utf-8') as f:
        print(tag_list, file = f)
    with open('resources/error_list.txt', 'w', encoding = 'utf-8') as f:
        print(error_list, file = f)
    print("Remaining free credits: " + str(get_remaining_api_credits()))
    return tag_list

def get_playlist_id(playlist_name, username = SPOTIFY_USERNAME, client = SPOTIFY_CLIENT):
    playlists = client.user_playlists(username)
    print(playlists)
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            print('Found playlist.')
            return playlist['id']

def get_track_id(track, client = SPOTIFY_CLIENT):
    name, artist = track
    search_term = ''
    if '(CD Series)' in artist or '(2010->)':
        search_term = name
    else:
        search_term = f'{name} {artist}'
    search_term = re.sub(r'\([^()]*\)', '', search_term)
    search_term = re.sub(r'[`-]', '', search_term)
    search_result = client.search(q = search_term, limit = 1, type = 'track')
    if search_result['tracks']['total'] == 0:
        print(f'track {name} - {artist} not found in Spotify.')
        return ''
    else:
        return search_result['tracks']['items'][0]['id']

def get_track_ids(track_list, client = SPOTIFY_CLIENT):
    id_list = []
    for track in track_list:
        id = get_track_id(track)
        if id != '':
            id_list.append(id)
    return id_list

def add_tracks_to_playlist(id_list, playlist_id, username = SPOTIFY_USERNAME, client = SPOTIFY_CLIENT):
    if len(id_list) < 100:
        client.user_playlist_add_tracks(username, playlist_id, id_list)
    else:
        start = 0
        for i in range(1, len(id_list), 100):
            client.user_playlist_add_tracks(username, playlist_id, id_list[start : i])
            start = i
        if len(id_list) % 100 != 0:
            client.user_playlist_add_tracks(username, playlist_id, id_list[start :])

def main():
    if not test_feasibility():
        print("Cannot run the conversion with current (free) budget. Try again")
        exit -1
    print("Starting parsing music files.")
    track_list = get_file_paths()
    track_dict = {track_list.index(track):track for track in track_list}
    with open('resources/track_list.txt', 'w', encoding = 'utf-8') as f:
        print(track_dict, file = f)
    sample_size = generate_samples(track_list)
    if sample_size != track_list:
        print("Unable to generate samples for all files. \
            Please check the track list number corresponding to the missing tracks.")
    tag_list = tag_all_songs(track_list)
    if tag_list != track_list:
        print("Unable to fetch song details for all tracks. \
            Please check the error list for the untagged tracks.")
    playlist_id = get_playlist_id(TARGET_PLAYLIST_NAME)
    id_list = get_track_ids(tag_list)
    add_tracks_to_playlist(id_list, playlist_id)

if __name__ == "__main__" :
    main()