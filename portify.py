import json
import requests
import subprocess

from pathlib import Path

AUDIO_TAG_API_KEY = ''
MUSIC_LIBRARY_ROOT = r'D:/Music'

with open('resources/api-key.txt', 'r') as f:
    AUDIO_TAG_API_KEY = f.readline()

def api_call(payload):
    result = requests.post('https://audiotag.info/api', data=payload)
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

def get_remaining_api_credits():
    payload = {'action': 'stat', 'apikey': AUDIO_TAG_API_KEY}
    json = api_call(payload)
    return json['identification_free_sec_remainder']

def test_feasibility():
    required = 10 * get_file_count()
    available = get_remaining_api_credits()
    return required + 100 < available

print(test_feasibility())