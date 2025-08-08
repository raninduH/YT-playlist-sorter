import os
import requests
import json
from dotenv import load_dotenv
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser, QRadioButton, QButtonGroup, QMessageBox, QSizePolicy, QTabWidget,
    QScrollArea, QHBoxLayout, QFrame, QSpacerItem
)
from PyQt5.QtCore import Qt
import sys

# Import link colors from config.py
from config import CLICKED_LINK_COLOR, UNCLICKED_LINK_COLOR
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFontMetrics

from helpers import get_config_path, save_api_key, load_api_key, get_playlist_id, fetch_playlist_items, sort_videos, get_number_of_new_videos


API_KEY = load_api_key()


# Worker thread for fetching playlist items
class FetchPlaylistWorker(QThread):
    finished = pyqtSignal(list, object)  # videos, error
    def __init__(self, playlist_id):
        super().__init__()
        self.playlist_id = playlist_id
    def run(self):
        videos, error = fetch_playlist_items(self.playlist_id)
        # Ensure videos is always a list for signal emit
        if videos is None:
            videos = []
        self.finished.emit(videos, error)

class PlaylistSorterQt(QWidget):


    def __init__(self):
        super().__init__()
        self.setWindowTitle('YT Playlist Sorter & Tracker')
        from PyQt5.QtGui import QIcon
        logo_path = os.path.join(os.path.dirname(__file__), 'logo', 'logo.png')
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        self.setGeometry(100, 100, 1200, 800)
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
        self.radio_asc = QRadioButton('Ascending - by added time')
        self.radio_desc = QRadioButton('Descending - by added time')
        self.radio_asc.setChecked(True)
        self.radio_group.addButton(self.radio_asc)
        self.radio_group.addButton(self.radio_desc)
        tab1_layout.addWidget(self.radio_asc)
        tab1_layout.addWidget(self.radio_desc)
        self.sort_button = QPushButton('Sort Playlist')
        self.sort_button.clicked.connect(self.sort_playlist)
        tab1_layout.addWidget(self.sort_button)
        self.new_vids_card = QFrame()
        self.new_vids_card.setVisible(False)
        self.new_vids_card.setStyleSheet('''
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
        self.viewed_scroll = QScrollArea()
        self.viewed_scroll.setWidgetResizable(True)
        self.viewed_container = QWidget()
        self.viewed_layout = QVBoxLayout()
        self.viewed_container.setLayout(self.viewed_layout)
        self.viewed_scroll.setWidget(self.viewed_container)
        tab3_layout.addWidget(self.viewed_scroll)
        tab3.setLayout(tab3_layout)
        self.tabs.addTab(tab3, "Viewed Playlists")

        # Tab 4: Configurations (Professional Layout)
        tab4 = QWidget()
        tab4_outer_layout = QVBoxLayout(tab4)
        tab4_outer_layout.setContentsMargins(0, 0, 0, 0)
        tab4_outer_layout.setSpacing(0)

        # Center everything using a QHBoxLayout
        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        tab4_outer_layout.addLayout(center_layout)

        # Card-style widget for config content
        card = QFrame()
        card.setStyleSheet('''
            QFrame {
                background: #fff;
                border-radius: 16px;
                margin: 0px;
                padding: 0px;
            }
        ''')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 32, 48, 32)
        card_layout.setSpacing(24)

        # Title
        self.api_key_label = QLabel("Google API Key Configuration")
        self.api_key_label.setStyleSheet('font-size:28px; font-weight:700; color:#111; margin-bottom:8px;')
        self.api_key_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.api_key_label)

        # Subtitle
        subtitle = QLabel("Enter your Google API Key below to unlock all features.")
        subtitle.setStyleSheet('font-size:16px; color:#444; margin-bottom:12px;')
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        input_row.setAlignment(Qt.AlignCenter)
        self.api_key_entry = QLineEdit()
        self.api_key_entry.setPlaceholderText("Paste your Google API Key here")
        self.api_key_entry.setMinimumWidth(350)
        self.api_key_entry.setMaximumWidth(500)
        self.api_key_entry.setStyleSheet('font-size:18px; padding:8px 12px; border-radius:6px; border:1.5px solid #b3d8ff;')
        input_row.addWidget(self.api_key_entry)
        self.api_key_save_btn = QPushButton("Save API Key")
        self.api_key_save_btn.setMinimumWidth(140)
        self.api_key_save_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f8cff, stop:1 #357ae8);
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 18px;
                border: none;
                padding: 10px 0px;
            }
            QPushButton:hover {
                background: #357ae8;
            }
        ''')
        input_row.addWidget(self.api_key_save_btn)
        card_layout.addLayout(input_row)

        # Status/Error message
        self.api_key_status = QLabel("")
        self.api_key_status.setStyleSheet('font-size:16px; color:#d32f2f; margin-bottom:8px;')
        self.api_key_status.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.api_key_status)

        # Instructions box
        instructions_box = QFrame()
        instructions_box.setStyleSheet('''
            QFrame {
                background: #eaf6ff;
                border-radius: 12px;
                margin-top: 8px;
            }
        ''')
        instructions_layout = QVBoxLayout(instructions_box)
        instructions_layout.setContentsMargins(24, 18, 24, 18)
        instructions_layout.setSpacing(8)
        instructions = (
            "<div style='font-size:18px; font-weight:600; color:#111; margin-bottom:8px;'>How to get a Google API Key for YouTube Data API v3:</div>"
            "<ol style='font-size:15px; color:#222; margin-left:18px;'>"
            "<li>Go to the <a href='https://console.cloud.google.com/' style='color:#357ae8;'>Google Cloud Console</a>.</li>"
            "<li>Create a new project (or select an existing one).</li>"
            "<li>In the left sidebar, go to <b>APIs & Services &gt; Library</b>.</li>"
            "<li>Search for 'YouTube Data API v3' and click <b>Enable</b>.</li>"
            "<li>Go to <b>APIs & Services &gt; Credentials</b>.</li>"
            "<li>Click <b>Create Credentials &gt; API key</b>.</li>"
            "<li>Copy your API key and paste it above.</li>"
            "</ol>"
            "<div style='font-size:14px; color:#d32f2f; margin-top:8px;'><i>If you see API errors, check your API key and quota.</i></div>"
        )
        instructions_label = QLabel()
        instructions_label.setTextFormat(Qt.RichText)
        instructions_label.setText(instructions)
        instructions_label.setWordWrap(True)
        instructions_layout.addWidget(instructions_label)
        card_layout.addWidget(instructions_box)

        # Add stretch to fill vertical space
        card_layout.addStretch(1)

        # Center card in window
        center_layout.addStretch(1)
        center_layout.addWidget(card, alignment=Qt.AlignCenter)
        center_layout.addStretch(1)

        self.tabs.addTab(tab4, "Configurations")

        self.setLayout(main_layout)

        # For tracking current playlist and clicked links
        self.current_playlist_id = None
        self.clicked_links = set()

        # Load API key from config
        self.api_key_entry.setText(load_api_key() or "")
        self.api_key_save_btn.clicked.connect(self.save_api_key_from_ui)

        # Load viewed playlists
        self.load_viewed_playlists()

        # Connect tab change to refresh viewed playlists
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # If no API key, go to Configurations tab and show error
        if not load_api_key():
            self.tabs.setCurrentIndex(3)  # Configurations tab
            self.api_key_status.setText("<b style='color:#d32f2f;'>Enter Google API Key to unlock the features of this app.</b>")

    def save_api_key_from_ui(self):
        key = self.api_key_entry.text().strip()
        if not key:
            self.api_key_status.setText("<b style='color:#d32f2f;'>API Key cannot be empty.</b>")
            return
        save_api_key(key)
        global API_KEY
        API_KEY = key
        self.api_key_status.setText("<b style='color:#388e3c;'>API Key saved! You can now use all features.</b>")

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
        memory_dir = os.path.join(os.environ['APPDATA'], 'YT-playlist-sorter', 'memory')
        os.makedirs(memory_dir, exist_ok=True)
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

        # Add 'check all' button at the top
        check_all_btn = QPushButton("check all")
        check_all_btn.setFixedSize(100, 32)
        check_all_btn.setStyleSheet('''
            QPushButton {
                background: #f5e6da;
                color: #8d5524;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                border: none;
                margin-bottom: 8px;
            }
            QPushButton:hover {
                background: #ecd3b6;
            }
        ''')
        self.viewed_layout.addWidget(check_all_btn)

        # Make cards start from the top
        self.viewed_layout.setAlignment(Qt.AlignTop)
        # Get available width for playlist name eliding

        def elide_label(label, full_text, max_width):
            fm = QFontMetrics(label.font())
            elided = fm.elidedText(full_text, Qt.ElideRight, max_width)
            label.setText(elided)

        self._viewed_cards = []  # Store card/pl_name for resize event
        self._check_btns = []    # Store check buttons for 'check all'
        for p in playlists:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setFixedHeight(80)
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

            main_layout = QHBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # Left section: Video count
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

            # Dynamic spacer 1
            main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

            # New section: new vids count (hidden initially)
            new_vids_widget = QWidget()
            new_vids_widget.setFixedSize(60, 60)
            new_vids_layout = QVBoxLayout()
            new_vids_layout.setContentsMargins(0, 0, 0, 0)
            new_vids_layout.setSpacing(0)
            new_vids_count_label = QLabel("")
            new_vids_count_label.setStyleSheet('font-size: 20px; font-weight: bold; color: #8d5524;')
            new_vids_count_label.setAlignment(Qt.AlignCenter)
            new_vids_label = QLabel("new vids")
            new_vids_label.setStyleSheet('font-size: 12px; color: #8d5524;')
            new_vids_label.setAlignment(Qt.AlignCenter)
            new_vids_layout.addWidget(new_vids_count_label)
            new_vids_layout.addWidget(new_vids_label)
            new_vids_widget.setLayout(new_vids_layout)
            new_vids_widget.setVisible(False)
            main_layout.addWidget(new_vids_widget)

            # Dynamic spacer 2
            main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

            # Second section: Channel info
            ch_widget = QWidget()
            ch_widget.setFixedWidth(150)  # Fixed width for alignment
            ch_layout = QVBoxLayout()
            ch_layout.setContentsMargins(0, 0, 0, 0)
            ch_layout.setSpacing(0)
            ch_label = QLabel("channel name")
            ch_label.setStyleSheet('font-size: 11px; color: #888; margin: 0px;')
            ch_label.setAlignment(Qt.AlignLeft)
            ch_name_text = p.get('channel_name', 'Unknown Channel')
            ch_name = QLabel(ch_name_text)
            ch_name.setStyleSheet('font-size: 17px; font-weight: bold; color: #222; margin: 0px;')
            ch_name.setAlignment(Qt.AlignLeft)
            elide_label(ch_name, ch_name_text, 140)
            ch_name.setToolTip(ch_name_text)
            ch_layout.addWidget(ch_label)
            ch_layout.addWidget(ch_name)
            ch_widget.setLayout(ch_layout)
            main_layout.addWidget(ch_widget)

            # Dynamic spacer 3
            main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

            # Third section: Playlist info
            pl_widget = QWidget()
            pl_widget.setFixedWidth(150)  # Fixed width for alignment
            pl_layout = QVBoxLayout()
            pl_layout.setContentsMargins(0, 0, 0, 0)
            pl_layout.setSpacing(0)
            pl_label = QLabel("playlist name")
            pl_label.setStyleSheet('font-size: 11px; color: #888; margin: 0px;')
            pl_label.setAlignment(Qt.AlignLeft)
            pl_name_text = p.get('playlist_name', 'Unknown Playlist')
            pl_name = QLabel(pl_name_text)
            pl_name.setStyleSheet('font-size: 17px; font-weight: bold; color: #222; margin: 0px;')
            pl_name.setAlignment(Qt.AlignLeft)
            # Elide based on available width (initial, will update on resize)
            elide_label(pl_name, pl_name_text, 140)
            pl_name.setToolTip(pl_name_text)
            pl_layout.addWidget(pl_label)
            pl_layout.addWidget(pl_name)
            pl_widget.setLayout(pl_layout)
            main_layout.addWidget(pl_widget)

            # Store for resize event
            self._viewed_cards.append((pl_widget, pl_name, pl_name_text))

            # Dynamic spacer 4
            main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

            # New brown check button
            check_btn = QPushButton("check")
            check_btn.setFixedSize(80, 30)
            check_btn.setStyleSheet('''
                QPushButton {
                    background: #a0522d;
                    color: #fff;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 15px;
                    border: none;
                }
                QPushButton:hover {
                    background: #c68642;
                }
            ''')

            def on_check_clicked(checked=False, playlist_link=p.get('playlist_link', None),
                                 count_label=new_vids_count_label,
                                 widget=new_vids_widget):
                if not playlist_link:
                    print("[DEBUG] No playlist_link found in card data.")
                    count_label.setText("N/A")
                    widget.setVisible(True)
                    return
                count_label.setText("...")
                widget.setVisible(True)
                QApplication.processEvents()
                new_vids, error = get_number_of_new_videos(playlist_link)
                print(f"[DEBUG] get_number_of_new_videos returned: new_vids={new_vids}, error={error}")
                if error:
                    count_label.setText("Err")
                    self.show_api_error_popup(error)
                else:
                    count_label.setText(str(new_vids))
            check_btn.clicked.connect(on_check_clicked)
            main_layout.addWidget(check_btn)
            self._check_btns.append(check_btn)

            # Dynamic spacer 5
            main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

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
        # Connect 'check all' button to trigger all check buttons
        def trigger_all_checks():
            for btn in self._check_btns:
                btn.click()
        check_all_btn.clicked.connect(trigger_all_checks)

        # Update eliding on resize using actual label width
        def update_eliding():
            for pl_widget, pl_name, pl_name_text in getattr(self, '_viewed_cards', []):
                # Use the actual width of the label, fallback to 140 if not available
                w = pl_name.width() if pl_name.width() > 10 else 140
                elide_label(pl_name, pl_name_text, w)

        def viewed_container_resize_event(event):
            QWidget.resizeEvent(self.viewed_container, event)
            update_eliding()
        self.viewed_container.resizeEvent = viewed_container_resize_event

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url.toString())
        spacer = QSpacerItem(80, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
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
        memory_dir = os.path.join(os.environ['APPDATA'], 'YT-playlist-sorter', 'memory')
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
        memory_dir = os.path.join(os.environ['APPDATA'], 'YT-playlist-sorter', 'memory')
        os.makedirs(memory_dir, exist_ok=True)
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
        # Get the width of the scroll area for responsive layout
        scroll_width = self.result_scroll.viewport().width() if self.result_scroll else 800
        card_width = scroll_width - 24  # account for margins/padding
        thumb_w = int(card_width * 0.4)
        info_w = int(card_width * 0.6)
        thumb_h = int(thumb_w * 9 / 16)  # 16:9 aspect ratio
        for v in self.sorted_videos:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setStyleSheet('''
                QFrame {
                    background: #fafbfc;
                    border-radius: 8px;
                    margin: 8px 0px;
                    padding: 8px;
                    border: 1px solid #d0d0d0;
                }
            ''')
            card_layout = QHBoxLayout()
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(16)
            card.setLayout(card_layout)

            # Thumbnail section (40% width)
            thumb_label = QLabel()
            thumb_label.setFixedSize(thumb_w, thumb_h)
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
                        thumb_label.setPixmap(pixmap.scaled(thumb_w, thumb_h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                except Exception:
                    pass
            card_layout.addWidget(thumb_label, 2)

            # Info layout (60% width)
            info_widget = QWidget()
            info_widget.setFixedWidth(info_w)
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(6)
            info_widget.setLayout(info_layout)
            # Date/time
            dt_label = QLabel(f"{v['added_at']}")
            dt_label.setTextFormat(Qt.RichText)
            dt_label.setStyleSheet('font-size:13px; color:#666; border:none;')
            info_layout.addWidget(dt_label)
            # Title
            title_label = QLabel(v['title'])
            title_label.setStyleSheet('font-size:16px; font-weight:bold; color:#222; margin-bottom:2px; border:none;')
            info_layout.addWidget(title_label)
            # Link
            link = f"https://www.youtube.com/watch?v={v['video_id']}"
            link_label = QLabel()
            link_label.setText(f"<a href='{link}' style='color:{CLICKED_LINK_COLOR if link in self.clicked_links else UNCLICKED_LINK_COLOR};'>{link}</a>")
            link_label.setTextFormat(Qt.RichText)
            link_label.setOpenExternalLinks(False)
            link_label.setStyleSheet('border:none;')
            def handle_link_click(url=link):
                import webbrowser
                webbrowser.open(url)
                if self.current_playlist_id:
                    self.clicked_links.add(url)
                    self.save_clicked_links()
                    self.update_playlist_display_links()
            link_label.linkActivated.connect(handle_link_click)
            info_layout.addWidget(link_label)
            card_layout.addWidget(info_widget, 3)

            self.result_layout.addWidget(card)

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

    def show_api_error_popup(self, error_text):
        instructions = (
            "<b>API Error Detected</b><br><br>"
            "<span style='color:#d32f2f;'>" + error_text + "</span><br><br>"
            "<b>How to fix:</b><br>"
            "1. Check that your Google API Key is correct and entered in the Configurations tab.<br>"
            "2. If you see a quota error, visit <a href='https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas'>Google Cloud Console Quotas</a> to review your quota.<br>"
            "3. Make sure your API key has access to YouTube Data API v3.<br>"
            "4. If you recently created your API key, wait a few minutes and try again.<br>"
            "5. You can update your API key in the Configurations tab.<br>"
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("API Error")
        msg.setTextFormat(Qt.RichText)
        msg.setText(instructions)
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

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
                self.show_api_error_popup(resp.text)
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
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setStyleSheet('''
                QFrame {
                    background: #fafbfc;
                    border-radius: 8px;
                    margin: 8px 0px;
                    padding: 8px;
                    border: 1px solid #d0d0d0;
                }
            ''')
            card_layout = QHBoxLayout()
            card_layout.setContentsMargins(16, 8, 16, 8)
            card_layout.setSpacing(16)
            card.setLayout(card_layout)

            # Info layout (title and link)
            info_widget = QWidget()
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(6)
            info_widget.setLayout(info_layout)
            title_label = QLabel(f"<b>{p['title']}</b>")
            title_label.setTextFormat(Qt.RichText)
            title_label.setStyleSheet('font-size:16px; font-weight:bold; color:#222; border:none;')
            info_layout.addWidget(title_label)
            link_label = QLabel(f"<a href='{link}'>{link}</a>")
            link_label.setTextFormat(Qt.RichText)
            link_label.setOpenExternalLinks(True)
            link_label.setStyleSheet('font-size:13px; color:#357ae8; border:none;')
            info_layout.addWidget(link_label)
            card_layout.addWidget(info_widget, 3)

            # Load to sorter button
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
            card_layout.addWidget(btn, 1)

            result_layout.addWidget(card)

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
        loading_text.setStyleSheet('font-size:32px; color:#04044b; margin-top:18px; font-weight:bold;')
        loading_layout.addWidget(loading_text)
        self.result_layout.addWidget(loading_frame)
        QApplication.processEvents()

        # Start worker thread to fetch playlist
        self.fetch_thread = FetchPlaylistWorker(playlist_id)
        self.fetch_thread.finished.connect(lambda videos, error: self.on_fetch_complete_with_error_popup(videos, error, url, playlist_id))
        self.fetch_thread.start()

    def on_fetch_complete_with_error_popup(self, videos, error, url, playlist_id):
        # Remove loading animation after fetch
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if error:
            self.show_api_error_popup(error)
            return
        self.on_fetch_complete(videos, error, url, playlist_id)

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
        memory_dir = os.path.join(os.environ['APPDATA'], 'YT-playlist-sorter', 'memory')
        os.makedirs(memory_dir, exist_ok=True)
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
        # Switch to Sort Playlist tab
        self.tabs.setCurrentIndex(0)
        # Clear previous results in Sort Playlist tab
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        # Load the relevant link to the input
        self.url_entry.setText(playlist_link if playlist_link else "")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlaylistSorterQt()
    window.show()
    sys.exit(app.exec_())
