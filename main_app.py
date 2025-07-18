import os
import requests
from dotenv import load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser, QRadioButton, QButtonGroup, QMessageBox, QSizePolicy, QTabWidget
)
import sys

load_dotenv()
API_KEY = os.getenv('GOOGLE_API_KEY')

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
            videos.append({
                'title': title,
                'video_id': video_id,
                'added_at': added_at
            })
        nextPageToken = data.get('nextPageToken')
        if not nextPageToken:
            break
    return videos, None

def sort_videos(videos, ascending=True):
    return sorted(videos, key=lambda x: x['added_at'], reverse=not ascending)

class PlaylistSorterQt(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('YouTube Playlist Sorter (PyQt5)')
        self.setGeometry(100, 100, 800, 600)
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Playlist Sorter
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()

        self.url_label = QLabel('YouTube Playlist URL:')
        tab1_layout.addWidget(self.url_label)
        self.url_entry = QLineEdit()
        tab1_layout.addWidget(self.url_entry)

        self.radio_group = QButtonGroup(self)
        self.radio_asc = QRadioButton('Ascending')
        self.radio_desc = QRadioButton('Descending')
        self.radio_asc.setChecked(True)
        self.radio_group.addButton(self.radio_asc)
        self.radio_group.addButton(self.radio_desc)
        tab1_layout.addWidget(self.radio_asc)
        tab1_layout.addWidget(self.radio_desc)

        self.sort_button = QPushButton('Sort Playlist')
        self.sort_button.clicked.connect(self.sort_playlist)
        tab1_layout.addWidget(self.sort_button)

        self.result_box = QTextBrowser()
        self.result_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tab1_layout.addWidget(self.result_box)

        self.result_box.setOpenExternalLinks(False)
        self.result_box.anchorClicked.connect(self.open_link)

        tab1.setLayout(tab1_layout)
        self.tabs.addTab(tab1, "Sort Playlist")

        # Tab 2: Channel Playlists
        tab2 = QWidget()
        tab2_layout = QVBoxLayout()

        self.channel_label = QLabel('YouTube Channel URL:')
        tab2_layout.addWidget(self.channel_label)
        self.channel_entry = QLineEdit()
        tab2_layout.addWidget(self.channel_entry)

        self.channel_button = QPushButton('List Channel Playlists')
        self.channel_button.clicked.connect(self.list_channel_playlists)
        tab2_layout.addWidget(self.channel_button)

        self.channel_result_box = QTextBrowser()
        self.channel_result_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tab2_layout.addWidget(self.channel_result_box)

        self.channel_result_box.setOpenExternalLinks(False)
        self.channel_result_box.anchorClicked.connect(self.open_link)

        tab2.setLayout(tab2_layout)
        self.tabs.addTab(tab2, "Channel Playlists")

        self.setLayout(main_layout)

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url.toString())
        # Clear internal navigation to suppress warning
        self.result_box.setSource(url.fromUserInput(''))
        self.channel_result_box.setSource(url.fromUserInput(''))
    def get_channel_id(self, url):
        # Accepts channel URL in the form https://www.youtube.com/channel/CHANNEL_ID or /@handle
        if '/channel/' in url:
            return url.split('/channel/')[1].split('/')[0]
        elif '/@' in url:
            # Need to resolve handle to channel ID
            handle = url.split('/@')[1].split('/')[0]
            # Use YouTube Data API to resolve handle
            api_url = f'https://www.googleapis.com/youtube/v3/channels'
            params = {
                'part': 'id',
                'forHandle': f'@{handle}',
                'key': API_KEY
            }
            resp = requests.get(api_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('items', [])
                if items:
                    return items[0]['id']
            return None
        return None

    def list_channel_playlists(self):
        url = self.channel_entry.text().strip()
        channel_id = self.get_channel_id(url)
        if not channel_id:
            QMessageBox.critical(self, 'Error', 'Invalid channel URL or unable to resolve channel ID.')
            return
        self.channel_result_box.setText('Fetching playlists...')
        QApplication.processEvents()
        playlists = []
        base_url = 'https://www.googleapis.com/youtube/v3/playlists'
        params = {
            'part': 'snippet',
            'maxResults': 50,
            'channelId': channel_id,
            'key': API_KEY
        }
        nextPageToken = None
        while True:
            if nextPageToken:
                params['pageToken'] = nextPageToken
            resp = requests.get(base_url, params=params)
            if resp.status_code != 200:
                self.channel_result_box.setText(f"API Error: {resp.text}")
                return
            data = resp.json()
            for item in data.get('items', []):
                title = item['snippet']['title']
                playlist_id = item['id']
                playlists.append({'title': title, 'playlist_id': playlist_id})
            nextPageToken = data.get('nextPageToken')
            if not nextPageToken:
                break
        html = ''
        for p in playlists:
            link = f"https://www.youtube.com/playlist?list={p['playlist_id']}"
            html += f"<b>{p['title']}</b><br><a href='{link}'>{link}</a><br><br>"
        self.channel_result_box.setHtml(html)

    def sort_playlist(self):
        url = self.url_entry.text().strip()
        playlist_id = get_playlist_id(url)
        if not playlist_id:
            QMessageBox.critical(self, 'Error', 'Invalid playlist URL.')
            return
        self.result_box.setText('Fetching playlist...')
        QApplication.processEvents()
        videos, error = fetch_playlist_items(playlist_id)
        if error:
            QMessageBox.critical(self, 'API Error', error)
            return
        ascending = self.radio_asc.isChecked()
        sorted_videos = sort_videos(videos, ascending)
        html = ''
        for v in sorted_videos:
            link = f"https://www.youtube.com/watch?v={v['video_id']}"
            html += f"<b>{v['added_at']}</b> - {v['title']}<br><a href='{link}'>{link}</a><br><br>"
        self.result_box.setHtml(html)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlaylistSorterQt()
    window.show()
    sys.exit(app.exec_())
