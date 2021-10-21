import json
import requests
import subprocess
import time

from pathlib import Path

AUDIO_TAG_API_KEY = ''
AUDIO_TAG_API_URL = 'https://audiotag.info/api'
MUSIC_LIBRARY_ROOT = r'D:/Music'
RETRIES_LIMIT = 100
SAMPLE_DIRECTORY = r'samples'
SAMPLE_LENGTH = '15'

with open('resources/api-key.txt', 'r') as f:
    AUDIO_TAG_API_KEY = f.readline()

def api_call(payload, file_path = None, url = AUDIO_TAG_API_URL):
    result = None
    if file_path:
        with open(file_path, 'rb') as f:
            result = requests.post( url,
                                    data = payload,
                                    files = {'file': f})
    else:
        result = requests.post(url, data=payload)
    # print(result.text)
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
            print(retries_count, retry_result)
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

def main():
    if not test_feasibility():
        print("Cannot run the conversion with current (free) budget. Try again")
        exit -1
    print("Starting parsing music files.")
    track_list = get_file_paths()
    sample_size = generate_samples(track_list)
    if sample_size != track_list:
        print("Unable to generate samples for all files. \
            Please check the track list number corresponding to the missing tracks.")

print(get_remaining_api_credits)
# print(fetch_song_details(get_file_paths(SAMPLE_DIRECTORY)[0]))

if __name__ == "__main__" :
    # main()
    pass