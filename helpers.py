import os
import requests
import json


def get_config_path():
    print('[DEBUG] get_config_path called')
    config_dir = os.path.join(os.environ['APPDATA'], 'YT-playlist-sorter')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.json')
    print(f'[DEBUG] config_path: {config_path}')
    return config_path

def save_api_key(api_key):
    print(f'[DEBUG] save_api_key called with api_key: {api_key}')
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump({'GOOGLE_API_KEY': api_key}, f)
    print('[DEBUG] API key saved')

def load_api_key():
    print('[DEBUG] load_api_key called')
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('GOOGLE_API_KEY')
                print(f'[DEBUG] Loaded API key: {api_key}')
                return api_key
        except Exception as e:
            print(f'[DEBUG] Error loading API key: {e}')
            return None
    print('[DEBUG] No config file found for API key')
    return None



def get_playlist_id(url):
    print(f'[DEBUG] get_playlist_id called with url: {url}')
    if 'list=' in url:
        playlist_id = url.split('list=')[1].split('&')[0]
        print(f'[DEBUG] Extracted playlist_id: {playlist_id}')
        return playlist_id
    print('[DEBUG] No playlist_id found in url')
    return None

def fetch_playlist_items(playlist_id):
    print(f'[DEBUG] fetch_playlist_items called with playlist_id: {playlist_id}')
    videos = []
    API_KEY = load_api_key()
    print(f'[DEBUG] Using API_KEY: {API_KEY}')
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
            print(f'[DEBUG] Using nextPageToken: {nextPageToken}')
        print(f'[DEBUG] Sending request to {base_url} with params: {params}')
        resp = requests.get(base_url, params=params)
        print(f'[DEBUG] Response status code: {resp.status_code}')
        if resp.status_code != 200:
            print(f'[DEBUG] API Error: {resp.text}')
            return None, f"API Error: {resp.text}"
        data = resp.json()
        print(f'[DEBUG] Received data: {json.dumps(data)[:300]}...')
        for item in data.get('items', []):
            snippet = item['snippet']
            video_id = snippet['resourceId']['videoId']
            title = snippet['title']
            added_at = snippet['publishedAt']
            thumbnails = snippet.get('thumbnails', {})
            thumb_url = thumbnails.get('medium', {}).get('url') or thumbnails.get('default', {}).get('url')
            print(f'[DEBUG] Appending video: {title} ({video_id})')
            videos.append({
                'title': title,
                'video_id': video_id,
                'added_at': added_at,
                'thumbnail': thumb_url
            })
        nextPageToken = data.get('nextPageToken')
        print(f'[DEBUG] nextPageToken for next loop: {nextPageToken}')
        if not nextPageToken:
            break
    print(f'[DEBUG] Total videos fetched: {len(videos)}')
    return videos, None

def sort_videos(videos, ascending=True, by_published=False):
    print(f'[DEBUG] sort_videos called with ascending={ascending}, by_published={by_published}')
    if not videos:
        print('[DEBUG] No videos to sort')
        return []
    if by_published:
        def get_published(x):
            return x.get('publishedAt') or x.get('added_at')
        sorted_videos = sorted(videos, key=get_published, reverse=not ascending)
        print(f'[DEBUG] Sorted {len(sorted_videos)} videos by published time')
        return sorted_videos
    else:
        sorted_videos = sorted(videos, key=lambda x: x['added_at'], reverse=not ascending)
        print(f'[DEBUG] Sorted {len(sorted_videos)} videos by added time')
        return sorted_videos


def get_number_of_new_videos(playlist_link):
    print(f'[DEBUG] get_number_of_new_videos called with playlist_link: {playlist_link}')
    API_KEY = load_api_key()
    playlist_id = get_playlist_id(playlist_link)
    print(f"[DEBUG] Extracted playlist_id: {playlist_id}")
    if not playlist_id:
        print("[DEBUG] Invalid playlist link.")
        return None, "Invalid playlist link."
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    params = {
        'part': 'snippet',
        'maxResults': 1,
        'playlistId': playlist_id,
        'key': API_KEY
    }
    try:
        print(f'[DEBUG] Sending request to {base_url} with params: {params}')
        resp = requests.get(base_url, params=params)
        print(f'[DEBUG] Response status code: {resp.status_code}')
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
    print(f'[DEBUG] Calculated new_vids: {new_vids}')
    if new_vids < 0:
        new_vids = 0
    return new_vids, None

