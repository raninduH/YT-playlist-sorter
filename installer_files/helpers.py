import os
import requests
import json


def get_config_path():
    config_dir = os.path.join(os.environ['APPDATA'], 'YT-playlist-sorter')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.json')

def save_api_key(api_key):
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump({'GOOGLE_API_KEY': api_key}, f)

def load_api_key():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('GOOGLE_API_KEY')
        except Exception:
            return None
    return None



def get_playlist_id(url):
    if 'list=' in url:
        return url.split('list=')[1].split('&')[0]
    return None

def fetch_playlist_items(playlist_id):
    videos = []
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    params = {
        'part': 'snippet',
        'maxResults': 50,
        'playlistId': playlist_id,
        'key': API_KEY
    }
    nextPageToken = None
    while True:
        if nextPageToken:
            params['pageToken'] = nextPageToken
        resp = requests.get(base_url, params=params)
        if resp.status_code != 200:
            return None, f"API Error: {resp.text}"
        data = resp.json()
        for item in data.get('items', []):
            snippet = item['snippet']
            video_id = snippet['resourceId']['videoId']
            title = snippet['title']
            added_at = snippet['publishedAt']
            # Get thumbnail URL (prefer medium, fallback to default)
            thumbnails = snippet.get('thumbnails', {})
            thumb_url = thumbnails.get('medium', {}).get('url') or thumbnails.get('default', {}).get('url')
            videos.append({
                'title': title,
                'video_id': video_id,
                'added_at': added_at,
                'thumbnail': thumb_url
            })
        nextPageToken = data.get('nextPageToken')
        if not nextPageToken:
            break
    return videos, None

def sort_videos(videos, ascending=True):
    return sorted(videos, key=lambda x: x['added_at'], reverse=not ascending)


def get_number_of_new_videos(playlist_link):
    """
    Given a YouTube playlist link, fetches the current video count via API,
    loads the relevant playlist JSON from the memory folder, compares counts,
    and returns the number of new videos. Does not update the JSON.
    Returns (number_of_new_videos, error_message) where error_message is None if successful.
    """
    API_KEY = load_api_key()
    playlist_id = get_playlist_id(playlist_link)
    print(f"[DEBUG] Extracted playlist_id: {playlist_id}")
    if not playlist_id:
        print("[DEBUG] Invalid playlist link.")
        return None, "Invalid playlist link."
    # Fetch current video count from YouTube API
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    params = {
        'part': 'snippet',
        'maxResults': 1,  # Need at least 1 to get totalResults
        'playlistId': playlist_id,
        'key': API_KEY
    }
    try:
        resp = requests.get(base_url, params=params)
        if resp.status_code != 200:
            print(f"[DEBUG] API Error: {resp.text}")
            return None, f"API Error: {resp.text}"
        data = resp.json()
        total = data.get('pageInfo', {}).get('totalResults', None)
        print(f"[DEBUG] API returned totalResults: {total}")
        if total is None:
            print("[DEBUG] Could not retrieve video count.")
            return None, "Could not retrieve video count."
    except Exception as e:
        print(f"[DEBUG] API Exception: {str(e)}")
        return None, f"API Exception: {str(e)}"
    # Load previous count from memory JSON
    # memory_dir = os.path.join(os.path.dirname(__file__), 'memory')
    memory_dir = os.path.join(os.environ['APPDATA'], 'YT-playlist-sorter', 'memory')
    os.makedirs(memory_dir, exist_ok=True)
    json_path = os.path.join(memory_dir, f'{playlist_id}.json')
    stored_count = None
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stored_count = data.get('no_of_vids', None)
                print(f"[DEBUG] Loaded stored_count from JSON: {stored_count}")
        except Exception as e:
            print(f"[DEBUG] Error reading playlist JSON: {str(e)}")
            return None, "Error reading playlist JSON."
    else:
        print("[DEBUG] JSON file does not exist.")
    if stored_count is None:
        print("[DEBUG] No stored video count found in JSON.")
        return None, "No stored video count found in JSON."
    new_vids = total - stored_count
    if new_vids < 0:
        new_vids = 0
    return new_vids, None

