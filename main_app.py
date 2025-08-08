import os
import requests
import json
from dotenv import load_dotenv
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser, QRadioButton, QButtonGroup, QMessageBox, QSizePolicy, QTabWidget,
    QScrollArea, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
import sys

# Import link colors from config.py
from config import CLICKED_LINK_COLOR, UNCLICKED_LINK_COLOR
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFontMetrics

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





# Worker thread for fetching playlist items
class FetchPlaylistWorker(QThread):
    finished = pyqtSignal(list, object)  # videos, error
    def __init__(self, playlist_id):
        super().__init__()
        self.playlist_id = playlist_id
    def run(self):
        videos, error = fetch_playlist_items(self.playlist_id)
        self.finished.emit(videos, error)

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
        # Modern info card for new videos
        self.new_vids_card = QFrame()
        self.new_vids_card.setVisible(False)
        self.new_vids_card.setStyleSheet('''
            /* Outer QFrame styling removed to keep only inner QLabel rectangle */
            QLabel {
                color: #357ae8;
                font-size: 16px;
                font-weight: bold;
                background: #eaf6ff;
                border-radius: 8px;
                padding: 12px 18px;
                margin: 8px 0px;
                border: 1px solid #b3d8ff;
            }
        ''')
        self.new_vids_layout = QVBoxLayout()
        self.new_vids_card.setLayout(self.new_vids_layout)
        tab1_layout.addWidget(self.new_vids_card)

        # Widget-based video list for thumbnails
        self.result_scroll = QScrollArea()
        self.result_scroll.setWidgetResizable(True)
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout()
        self.result_widget.setLayout(self.result_layout)
        self.result_scroll.setWidget(self.result_widget)
        tab1_layout.addWidget(self.result_scroll)

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

        # Tab 3: Viewed Playlists
        tab3 = QWidget()
        tab3_layout = QVBoxLayout()

        # All required PyQt5 widgets are already imported at the top
        self.viewed_scroll = QScrollArea()
        self.viewed_scroll.setWidgetResizable(True)
        self.viewed_container = QWidget()
        self.viewed_layout = QVBoxLayout()
        self.viewed_container.setLayout(self.viewed_layout)
        self.viewed_scroll.setWidget(self.viewed_container)
        tab3_layout.addWidget(self.viewed_scroll)

        tab3.setLayout(tab3_layout)
        self.tabs.addTab(tab3, "Viewed Playlists")

        self.setLayout(main_layout)

        # For tracking current playlist and clicked links
        self.current_playlist_id = None
        self.clicked_links = set()

        # Load viewed playlists
        self.load_viewed_playlists()

        # Connect tab change to refresh viewed playlists
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, idx):
        # If viewed playlists tab is selected, refresh
        if self.tabs.tabText(idx) == "Viewed Playlists":
            self.load_viewed_playlists()

    def load_viewed_playlists(self):
        # Clear layout
        while self.viewed_layout.count():
            item = self.viewed_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        # Scan memory folder for playlist JSONs
        memory_dir = os.path.join(os.path.dirname(__file__), 'memory')
        if not os.path.exists(memory_dir):
            return
        files = [f for f in os.listdir(memory_dir) if f.endswith('.json')]
        playlists = []
        for fname in files:
            try:
                with open(os.path.join(memory_dir, fname), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    playlists.append(data)
            except Exception:
                continue
        
        def elide_label(label, max_width):
            fm = QFontMetrics(label.font())
            text = label.text()
            elided = fm.elidedText(text, Qt.ElideRight, max_width)
            label.setText(elided)
        
        for p in playlists:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setFixedHeight(80)  # Reduced height for better fit
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            card.setStyleSheet('''
                QFrame {
                    background: #f5f7fa;
                    border-radius: 8px;
                    margin: 4px;
                    padding: 8px;
                    border: 1px solid #e0e0e0;
                }
                QLabel {
                    border: none;
                    margin: 0px;
                    padding: 0px;
                }
            ''')
            
            # Main horizontal layout
            main_layout = QHBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(12)
            
            # Left section: Video count (compact)
            vid_count_widget = QWidget()
            vid_count_widget.setFixedSize(60, 60)
            vid_count_layout = QVBoxLayout()
            vid_count_layout.setContentsMargins(0, 0, 0, 0)
            vid_count_layout.setSpacing(0)
            
            vid_count = QLabel(str(p.get('no_of_vids', 'N/A')))
            vid_count.setStyleSheet('font-size: 20px; font-weight: bold; color: #222;')
            vid_count.setAlignment(Qt.AlignCenter)
            
            vid_label = QLabel("videos")
            vid_label.setStyleSheet('font-size: 12px; color: #888;')
            vid_label.setAlignment(Qt.AlignCenter)
            
            vid_count_layout.addWidget(vid_count)
            vid_count_layout.addWidget(vid_label)
            vid_count_widget.setLayout(vid_count_layout)
            main_layout.addWidget(vid_count_widget)
            
            # Center section: Channel and playlist info
            info_widget = QWidget()
            info_layout = QHBoxLayout()  # Changed to horizontal layout
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(0)  # Remove spacing, use stretch instead
            
            # Channel section
            ch_section = QWidget()
            ch_layout = QVBoxLayout()
            ch_layout.setContentsMargins(0, 0, 0, 0)
            ch_layout.setSpacing(1)
            
            ch_label = QLabel("channel name")
            ch_label.setStyleSheet('font-size: 11px; color: #888; margin: 0px;')
            ch_label.setAlignment(Qt.AlignLeft)
            
            ch_name = QLabel(p.get('channel_name', 'Unknown Channel'))
            ch_name.setStyleSheet('font-size: 17px; font-weight: bold; color: #222; margin: 0px;')
            ch_name.setAlignment(Qt.AlignLeft)
            elide_label(ch_name, 120)  # Reduced width for side-by-side layout
            
            ch_layout.addWidget(ch_label)
            ch_layout.addWidget(ch_name)
            ch_layout.addStretch()
            ch_section.setLayout(ch_layout)
            
            # Playlist section
            pl_section = QWidget()
            pl_layout = QVBoxLayout()
            pl_layout.setContentsMargins(0, 0, 0, 0)
            pl_layout.setSpacing(1)
            
            pl_label = QLabel("playlist name")
            pl_label.setStyleSheet('font-size: 11px; color: #888; margin: 0px;')  # Same size as channel label
            pl_label.setAlignment(Qt.AlignLeft)
            
            pl_name = QLabel(p.get('playlist_name', 'Unknown Playlist'))
            pl_name.setStyleSheet('font-size: 17px; font-weight: bold; color: #222; margin: 0px;')  # Same size as channel name
            pl_name.setAlignment(Qt.AlignLeft)
            elide_label(pl_name, 120)  # Reduced width for side-by-side layout
            
            pl_layout.addWidget(pl_label)
            pl_layout.addWidget(pl_name)
            pl_layout.addStretch()
            pl_section.setLayout(pl_layout)
            
            info_layout.addStretch(1)  # Add stretch before channel
            info_layout.addWidget(ch_section)
            info_layout.addStretch(1)  # Larger stretch between channel and playlist
            info_layout.addWidget(pl_section)
            info_layout.addStretch(1)  # Add stretch after playlist
            info_widget.setLayout(info_layout)
            main_layout.addWidget(info_widget)
            
            # Right section: Load button
            btn = QPushButton("Load to sorter")
            btn.setFixedSize(120, 30)
            btn.setStyleSheet('''
                QPushButton {
                    background: #4f8cff;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 15px;
                    border: none;
                }
                QPushButton:hover {
                    background: #357ae8;
                }
            ''')
            playlist_link = p.get('playlist_link', None)
            btn.clicked.connect(lambda checked, link=playlist_link: self.load_playlist_to_sorter(link))
            main_layout.addWidget(btn)
            
            card.setLayout(main_layout)
            self.viewed_layout.addWidget(card)

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url.toString())
        # Mark link as clicked and update display
        if self.current_playlist_id:
            video_url = url.toString()
            self.clicked_links.add(video_url)
            self.save_clicked_links()
            self.update_playlist_display_links()
        # Clear internal navigation to suppress warning
        self.result_box.setSource(url.fromUserInput(''))
        self.channel_result_box.setSource(url.fromUserInput(''))

    def save_clicked_links(self, new_vids_count=None):
        if not self.current_playlist_id:
            return
        memory_dir = os.path.join(os.path.dirname(__file__), 'memory')
        os.makedirs(memory_dir, exist_ok=True)
        json_path = os.path.join(memory_dir, f'{self.current_playlist_id}.json')

        # Try to get playlist and channel name
        playlist_name = getattr(self, 'current_playlist_name', None)
        channel_name = getattr(self, 'current_channel_name', None)
        playlist_link = getattr(self, 'current_playlist_link', None)
        no_of_vids = getattr(self, 'current_no_of_vids', None)

        # Load previous data if exists
        prev_data = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    prev_data = json.load(f)
            except Exception:
                pass

        data = {
            'clicked_vids': list(self.clicked_links)
        }
        if playlist_name:
            data['playlist_name'] = playlist_name
        if channel_name:
            data['channel_name'] = channel_name
        if playlist_link:
            data['playlist_link'] = playlist_link
        if no_of_vids is not None:
            data['no_of_vids'] = no_of_vids
        # If new vids count is provided, store for UI
        if new_vids_count is not None:
            data['new_vids_count'] = new_vids_count

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def load_clicked_links(self, playlist_id):
        memory_dir = os.path.join(os.path.dirname(__file__), 'memory')
        json_path = os.path.join(memory_dir, f'{playlist_id}.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Optionally set playlist/channel name if present
                    self.current_playlist_name = data.get('playlist_name', None)
                    self.current_channel_name = data.get('channel_name', None)
                    return set(data.get('clicked_vids', []))
            except Exception:
                return set()
        return set()

    def update_playlist_display_links(self):
        # Clear previous widgets
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not hasattr(self, 'sorted_videos') or not self.sorted_videos:
            return
        for v in self.sorted_videos:
            row = QFrame()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(4, 4, 4, 4)
            row_layout.setSpacing(12)
            row.setLayout(row_layout)

            # Thumbnail
            thumb_label = QLabel()
            thumb_label.setFixedSize(90, 60)
            thumb_label.setStyleSheet('border-radius:6px; background:#eee;')
            thumb_url = v.get('thumbnail')
            if thumb_url:
                try:
                    import requests
                    from PyQt5.QtGui import QPixmap
                    resp = requests.get(thumb_url, timeout=5)
                    if resp.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(resp.content)
                        thumb_label.setPixmap(pixmap.scaled(90, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                except Exception:
                    pass
            row_layout.addWidget(thumb_label)

            # Info and link
            info_widget = QWidget()
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(2)
            info_widget.setLayout(info_layout)
            # Date/time
            dt_label = QLabel(f"{v['added_at']}")
            dt_label.setTextFormat(Qt.RichText)
            info_layout.addWidget(dt_label)
            # Title
            title_label = QLabel(v['title'])
            title_label.setStyleSheet('font-size:15px; font-weight:bold; color:#222; margin-bottom:2px;')
            info_layout.addWidget(title_label)
            # Link
            link = f"https://www.youtube.com/watch?v={v['video_id']}"
            # Use a clickable QLabel for the link
            link_label = QLabel()
            link_label.setText(f"<a href='{link}' style='color:{CLICKED_LINK_COLOR if link in self.clicked_links else UNCLICKED_LINK_COLOR};'>{link}</a>")
            link_label.setTextFormat(Qt.RichText)
            link_label.setOpenExternalLinks(False)
            # Connect click to open_link and update clicked_links
            def handle_link_click(url=link):
                import webbrowser
                webbrowser.open(url)
                if self.current_playlist_id:
                    self.clicked_links.add(url)
                    self.save_clicked_links()
                    self.update_playlist_display_links()
            link_label.linkActivated.connect(handle_link_click)
            info_layout.addWidget(link_label)
            row_layout.addWidget(info_widget)

            self.result_layout.addWidget(row)

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
        # Clear previous results
        self.channel_result_box.clear()
        # Create a widget to hold playlist entries
        result_widget = QWidget()
        result_layout = QVBoxLayout()
        result_widget.setLayout(result_layout)

        for p in playlists:
            link = f"https://www.youtube.com/playlist?list={p['playlist_id']}"
            entry_frame = QFrame()
            entry_layout = QHBoxLayout()
            entry_frame.setLayout(entry_layout)

            # Left: Vertical layout for title and link
            left_widget = QWidget()
            left_layout = QVBoxLayout()
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(2)
            left_widget.setLayout(left_layout)

            title_label = QLabel(f"<b>{p['title']}</b>")
            title_label.setTextFormat(Qt.RichText)
            left_layout.addWidget(title_label)

            link_label = QLabel(f"<a href='{link}'>{link}</a>")
            link_label.setTextFormat(Qt.RichText)
            link_label.setOpenExternalLinks(True)
            left_layout.addWidget(link_label)

            entry_layout.addWidget(left_widget)

            # Right: Load to sorter button
            btn = QPushButton("Load to sorter")
            btn.setFixedSize(120, 30)
            btn.setStyleSheet('''
                QPushButton {
                    background: #4f8cff;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 15px;
                    border: none;
                }
                QPushButton:hover {
                    background: #357ae8;
                }
            ''')
            btn.clicked.connect(lambda checked, lnk=link: self.load_playlist_to_sorter(lnk))
            entry_layout.addWidget(btn)

            result_layout.addWidget(entry_frame)

        # Set the widget in the QTextBrowser using setCentralWidget if available, else fallback to HTML
        # QTextBrowser does not support widgets directly, so use a QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(result_widget)
        # Replace the QTextBrowser with the scroll area
        parent_layout = self.channel_result_box.parentWidget().layout()
        parent_layout.removeWidget(self.channel_result_box)
        self.channel_result_box.setParent(None)
        parent_layout.addWidget(scroll)
        self.channel_result_scroll = scroll

    def sort_playlist(self):
        url = self.url_entry.text().strip()
        playlist_id = get_playlist_id(url)
        if not playlist_id:
            QMessageBox.critical(self, 'Error', 'Invalid playlist URL.')
            return
        # Show loading animation and text in widget-based layout
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        loading_frame = QFrame()
        loading_layout = QVBoxLayout()
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_frame.setLayout(loading_layout)
        gif_label = QLabel()
        gif_label.setAlignment(Qt.AlignCenter)
        gif_label.setFixedSize(64, 64)
        try:
            from PyQt5.QtGui import QMovie
            gif_path = os.path.join(os.path.dirname(__file__), 'loading.gif')
            if os.path.exists(gif_path):
                movie = QMovie(gif_path)
                movie.setScaledSize(QSize(64, 64))
                gif_label.setMovie(movie)
                movie.start()
            else:
                gif_label.setText('⏳')
                gif_label.setStyleSheet('font-size:48px;')
        except Exception:
            gif_label.setText('⏳')
            gif_label.setStyleSheet('font-size:48px;')
        loading_layout.addWidget(gif_label)
        loading_text = QLabel('fetching...')
        loading_text.setAlignment(Qt.AlignCenter)
        loading_text.setStyleSheet('font-size:32px; color:#357ae8; margin-top:18px; font-weight:bold;')
        loading_layout.addWidget(loading_text)
        self.result_layout.addWidget(loading_frame)
        QApplication.processEvents()

        # Start worker thread to fetch playlist
        self.fetch_thread = FetchPlaylistWorker(playlist_id)
        self.fetch_thread.finished.connect(lambda videos, error: self.on_fetch_complete(videos, error, url, playlist_id))
        self.fetch_thread.start()

    def on_fetch_complete(self, videos, error, url, playlist_id):
        # Remove loading animation after fetch
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if error:
            QMessageBox.critical(self, 'API Error', error)
            return
        ascending = self.radio_asc.isChecked()
        self.sorted_videos = sort_videos(videos, ascending)
        self.current_playlist_id = playlist_id

        # Save the playlist link for later use
        self.current_playlist_link = url

        # Try to get playlist and channel name from first video snippet
        playlist_name = None
        channel_name = None
        if videos:
            playlist_name = videos[0].get('playlist_title', None)
            channel_name = videos[0].get('channel_title', None)
        # Fallback: Try to get from API
        try:
            playlist_api = 'https://www.googleapis.com/youtube/v3/playlists'
            params = {
                'part': 'snippet',
                'id': playlist_id,
                'key': API_KEY
            }
            resp = requests.get(playlist_api, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('items', [])
                if items:
                    snippet = items[0]['snippet']
                    playlist_name = snippet.get('title', None)
                    channel_name = snippet.get('channelTitle', None)
        except Exception:
            pass
        self.current_playlist_name = playlist_name
        self.current_channel_name = channel_name

        # Save video count
        self.current_no_of_vids = len(videos)

        # Load previous count for this playlist
        memory_dir = os.path.join(os.path.dirname(__file__), 'memory')
        json_path = os.path.join(memory_dir, f'{playlist_id}.json')
        prev_count = None
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    prev_data = json.load(f)
                    prev_count = prev_data.get('no_of_vids', None)
            except Exception:
                pass
        new_vids_count = None
        if prev_count is not None:
            new_vids_count = self.current_no_of_vids - prev_count
            if new_vids_count < 0:
                new_vids_count = 0

        # Show new videos info card if new videos found
        if new_vids_count is not None and new_vids_count > 0:
            for i in reversed(range(self.new_vids_layout.count())):
                widget = self.new_vids_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            info_label = QLabel(f"{new_vids_count} new video{'s' if new_vids_count > 1 else ''} found since last retrieval!")
            info_label.setAlignment(Qt.AlignCenter)
            self.new_vids_layout.addWidget(info_label)
            self.new_vids_card.setVisible(True)
        else:
            self.new_vids_card.setVisible(False)
        self.clicked_links = self.load_clicked_links(playlist_id)
        self.update_playlist_display_links()
        self.save_clicked_links(new_vids_count=new_vids_count)

    def load_playlist_to_sorter(self, playlist_link):
        # Switch to Sort Playlist tab and set the playlist link
        self.tabs.setCurrentIndex(0)
        self.url_entry.setText(playlist_link if playlist_link else "")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlaylistSorterQt()
    window.show()
    sys.exit(app.exec_())
