# portify
Add locally stored music to your Spotify library.

## Features
* Does not rely on filename or metadata (detects song using AudioTag API).
* Supports any* file format (*ffmpeg supported).
* Works in any platform that support Python 3 with minimal dependencies.
* Logic in the script is generic enough to allow for simple changes to switch song detection process.

## Prerequisites
* An [AudioTag.info API key](https://audiotag.info/apisection) (free tier for ~1000 requests per month).
* A Spotify account with an app created in [developer dashboard](https://developer.spotify.com/dashboard/applications).
    * Have a **public** playlist (can make private after running the program).
* Computing device with Python 3+ and pip installed (recommended with virtualenv or conda).
* Your music library containing **only** track files under one directory (subdirectories are fine; .ini files filtered by default with option to enhance fiiltering).

## Installation
* Get source code via git or by unzipping archive from this site.
* Install prerequisites using `pip install -r resources/requirements.txt` in default environment, or preferably in a virtual environment (e.g. virtualenv).
    * conda users can create dedicated environment with dependencies using `conda env create -f resources/portify.yml`.
* Install [ffmpeg](https://ffmpeg.org/download.html) in your system (or place the binary in the same folder as `portify.py`).

## How to use
* Replace the prerequisite credentials under `resources/api-key.txt` in the format suggested in the file.
* Edit `portify.py` and assign respective values to the following variables:
    * `MUSIC_LIBRARY_ROOT` - The path to the music folder to scan.
    * `TARGET_PLAYLIST_NAME` - The name of Spotify playlist to add the tracks.
    * Can optionally change other variables at your own risk.
* Run `python portify.py` and come back after a quick break!
    * When running for the first time, you will be prompted to allow the app connect to your Spotify account. Just follow the instructions.
* As the script runs, the following files will be written inside the `resources` folder:
    * `track_list.txt` lists all the files detected and assigns a number (can be later used to track progress).
    * `tag_list.txt` contains the track names detected by AudioTag.
    * `error_list.txt` contains tracks that were not found in Spotify.

## Limitations
* Song detection is heavily dependent on the quality of AudioTag catalogue. Non-English and niche songs may have a tough time getting detected.
    * Kindly consider [improving their database](https://audiotag.info/contribute).
* Spotify search API (used to find the track in the platform) can sometimes have trouble finding the right song:
    * e.g. a more popular track with the same name exists.
    * This can be improved with adding a text-matching algorithm.
* The volume of songs that can be added depend on the AudioTag API limit. If you have a large library, you can either:
    * Run this application in batches,
    * Reduce the sample length (ideal range is 15-30 seconds, can go as low as 10 before you start facing issues),
    * Buy credits (balance check currently not supported).
        * Make sure your songs are getting detected properly before committing.