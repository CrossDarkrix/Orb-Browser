import asyncio
import os
import sys
import re
import xml.etree.ElementTree as ET
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor
from PySide6.QtCore import QTimer
import ssl
import urllib.request
from datetime import date as dt
from distutils.util import strtobool

ssl._create_default_https_context = ssl._create_unverified_context
out_adblock_list = []
memory_saver_enabled = [False]
dark_mode_enabled = [False]


def ADBlock280():
    user_agent = 'Mozilla/5.0 (Linux; Android 7.1.2; en-la) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.100 Mobile Safari/537.36 YJApp-ANDROID jp.co.yahoo.android.yjtop/13.91.1'
    if dt.today().month <= 9:
        month = '0{}'.format(dt.today().month)
    else:
        month = '{}'.format(dt.today().month)
    _url = str(dt.today().year) + month
    url = 'https://280blocker.net/files/280blocker_domain_{}.txt'.format(_url) # 280Adblockからリストの取得
    file = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': user_agent}))
    adblock_raw_file = re.sub('(.+#[ ].+)','', '{}'.format(file.read().decode('utf-8', errors='ignore')))
    adblock_list = re.sub('\n{2}', '', re.sub('#[\s\S]', '', re.sub('(#[ ].+)', '', adblock_raw_file.replace('\r', '')))).replace('\n\n', '')
    out_adblock_list[0:] = adblock_list.split('\n')


class WebEngineUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def check_rule(self, url):
        if url in out_adblock_list:
            return True
        else:
            return False

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if self.check_rule(url):
            info.block(True)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setMinimumSize(QSize(1270, 720))
        self.language = "日本語"
        self.setWindowIcon(QIcon("icon.png"))
        self.tabs = QTabWidget()
        self.memory_saver = MemorySaver(self.tabs)
        self.dark_mode = DarkMode(self.tabs)
        self.load_settings()
        self.init_ui()

    def init_ui(self):
        ADBlock280()
        font = QFont()
        font.setPointSize(18)
        font2 = QFont()
        font2.setPointSize(18)
        font3 = QFont()
        font3.setPointSize(16)
        self.tabs = QTabWidget()
        stop_btn = QAction("❌", self)
        stop_btn.setFont(font)
        stop_btn.setStatusTip("Stop loading current page")
        stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.memory_saver = MemorySaver(self.tabs)
        self.dark_mode = DarkMode(self.tabs)
        self.add_tab_button = QPushButton(text="➕")
        self.add_tab_button.setStyleSheet('QPushButton{background: rgba(0, 0, 0, 0);}')
        self.add_tab_button.setFont(font3)
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.vertical_bar = QToolBar("Vertical Bar")
        self.vertical_bar.setOrientation(Qt.Orientation.Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.vertical_bar)
        self.tabs.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        navtb = QToolBar("Navigation")
        navtb.setMinimumWidth(1010)
        self.addToolBar(navtb)
        self.load_shortcuts()
        back_btn = QAction("⬅", self)
        back_btn.setFont(font)
        back_btn.setStatusTip("Back to previous page")
        back_btn.setToolTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)
        next_btn = QAction("➡", self)
        next_btn.setFont(font)
        next_btn.setStatusTip("Forward to next page")
        next_btn.setToolTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)
        reload_btn = QAction("🔄", self)
        reload_btn.setToolTip("Reload page")
        reload_btn.setFont(font)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(stop_btn)
        home_btn = QAction("🏠", self)
        home_btn.setFont(font)
        home_btn.setStatusTip("Go home")
        home_btn.setToolTip("Go home")
        self.toolbar = QToolBar("Actions")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.star_button = QAction("⭐️", self)
        self.star_button.setFont(font)
        self.star_button.setStatusTip("Add shortcut to vertical bar")
        self.star_button.setToolTip("Add shortcut to vertical bar")
        self.star_button.triggered.connect(self.add_shortcut)
        self.toolbar.addAction(self.star_button)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addSeparator()
        self.urlbar = QLineEdit()
        self.urlbar.setFixedWidth(480)
        self.urlbar.setFont(font2)
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)
        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.on_downloadRequested)
        navtb.addAction(reload_btn)
        self.search_bar = QLineEdit()
        self.search_bar.setFont(font2)
        self.search_bar.setMinimumWidth(140)
        self.search_bar.setPlaceholderText('Google Search...')
        self.search_bar.returnPressed.connect(self.search_to_url)
        navtb.addWidget(self.search_bar)
        self.add_new_tab(QUrl('https://takerin-123.github.io/qqqqq.github.io/'), 'Homepage')
        self.vertical_bar = QToolBar("Vertical Bar")
        self.vertical_bar.setOrientation(Qt.Orientation.Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.vertical_bar)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.show()
        self.setWindowTitle("")
        self.setStyleSheet("background-color: black; color: white;")  # 背景色を黒に変更
        self.tabs.setStyleSheet("QTabBar::tab { background-color: white; color: black; }")
        settings_btn = QAction("⚙️", self)
        settings_btn.setFont(font)
        settings_btn.setStatusTip("設定")
        settings_btn.triggered.connect(self.show_settings)
        self.toolbar.addAction(settings_btn)
        self.toolbar.setIconSize(QSize(100, 100))
        self.toolbar.setFixedSize(self.toolbar.size())
        self.update_language()
        navtb.addAction(home_btn)

    def add_new_tab(self, qurl=None, label="ブランク"):
        if qurl is None:
            qurl = QUrl('https://takerin-123.github.io/qqqqq.github.io/')
        elif isinstance(qurl, str):
            qurl = QUrl(qurl)
        elif not isinstance(qurl, QUrl):
            raise TypeError("qurl must be a QUrl or a string")
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(WebEngineUrlRequestInterceptor())
        browser = QWebEngineView()
        browser.page().profile().setHttpUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))
        browser.iconChanged.connect(lambda _, i=i, browser=browser: self.tabs.setTabIcon(i, browser.icon()))

    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

    def current_tab_changed(self, i):
        if self.tabs.currentWidget() is not None:
            qurl = self.tabs.currentWidget().url()
            self.update_urlbar(qurl, self.tabs.currentWidget())
            self.update_title(self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            self.tabs.removeTab(i)
            self.add_new_tab()
        if self.tabs.count() == 1:
            self.tabs.removeTab(1)
            self.add_new_tab()
        self.tabs.removeTab(i)

    def update_title(self, browser):
        if browser != self.tabs.currentWidget():
            return
        title = self.tabs.currentWidget().page().title()
        formatted_title = title[:7] if len(title) > 7 else title.ljust(7)
        self.setWindowTitle("%s OrbBrowser" % formatted_title)
        self.tabs.setTabText(self.tabs.currentIndex(), formatted_title)
        if formatted_title == 'https:/':
            self.tabs.removeTab(0)
            self.add_new_tab()

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl("https://takerin-123.github.io/qqqqq.github.io/"))

    def navigate_to_url(self):
        url = self.urlbar.text()
        if "google.com/search?q=" in url:
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            self.tabs.currentWidget().setUrl(QUrl(url))

    def search_to_url(self):
        url = self.search_bar.text()
        if "google.com/search?q=" in url:
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            google_search_url = "https://www.google.com/search?q={}".format(url)
            self.tabs.currentWidget().setUrl(QUrl(google_search_url))

    def update_urlbar(self, q, browser=None):
        if browser != self.tabs.currentWidget():
            return
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def on_downloadRequested(self, download):
        home_dir = os.path.expanduser("~")
        download_dir = os.path.join(home_dir, "Downloads")
        download_filename = download.suggestedFileName()
        QWebEngineProfile.defaultProfile().setDownloadDirectory(download_dir)
        download.setDownloadFileName(download_filename)
        download.accept()
        self.show_download_progress(download)

    def show_download_progress(self, download):
        progress_bar = QProgressBar(self.status)
        self.status.addPermanentWidget(progress_bar)
        download.downloadProgress.connect(lambda bytesReceived, bytesTotal, progress_bar=progress_bar: progress_bar.setValue(int((bytesReceived / bytesTotal) * 100) if bytesTotal > 0 else 0))
        download.finished.connect(lambda progress_bar=progress_bar: progress_bar.deleteLater())

    def update_progress_bar(self, progress_bar, bytesReceived, bytesTotal):
        if bytesTotal > 0:
            progress = (bytesReceived / bytesTotal) * 100
            progress_bar.setValue(int(progress))

    def remove_progress_bar(self, progress_bar):
        self.status.removeWidget(progress_bar)
        progress_bar.deleteLater()

    def add_shortcut(self):
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, QWebEngineView):
            url = current_tab.page().url().toString()
            title = current_tab.page().title()
            shortcut_button = QAction("", self)
            shortcut_button.setText(current_tab.page().title())
            shortcut_button.setToolTip(url)
            shortcut_button.triggered.connect(lambda: self.open_URL(url))
            self.vertical_bar.addAction(shortcut_button)
            self.tabs.currentWidget().setUrl(QUrl(url))
            self.save_shortcut_to_xml(title, url)

    def open_URL(self, url, name):
        self.tabs.currentWidget().setUrl(QUrl(url))
        self.tabs.currentWidget().loadFinished.connect(self.loaded(name))

    def loaded(self, title):
        formatted_title = title[:7] if len(title) > 7 else title.ljust(7)
        self.setWindowTitle("%s OrbBrowser" % formatted_title)
        self.tabs.setTabText(self.tabs.currentIndex(), formatted_title)

    def save_shortcut_to_xml(self, title, url):
        if not os.path.exists('shortcuts.xml'):
            root = ET.Element("shortcuts")
            tree = ET.ElementTree(root)
            tree.write('shortcuts.xml')
        tree = ET.parse('shortcuts.xml')
        root = tree.getroot()
        for shortcut in root.findall('shortcut'):
            if shortcut.find('url').text == url:
                print("Bookmark already exists.")
                return
        shortcut = ET.SubElement(root, 'shortcut')
        ET.SubElement(shortcut, 'title').text = title
        ET.SubElement(shortcut, 'url').text = url
        tree.write('shortcuts.xml')

    def load_shortcuts(self):
        if not os.path.exists('shortcuts.xml'):
            return
        tree = ET.parse('shortcuts.xml')
        root = tree.getroot()
        added_urls = set()
        for shortcut in root.findall('shortcut'):
            title = shortcut.find('title').text
            url = shortcut.find('url').text
            if url not in added_urls:
                self.add_website_shortcut(url, title)
                added_urls.add(url)

    def add_website_shortcut(self, url, name):
        name = name[:23] + '...' if len(name) > 23 else name
        shortcut_button = QAction(name, self)
        shortcut_button.url = url
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(WebEngineUrlRequestInterceptor())
        view = QWebEngineView()
        view.page().profile().setHttpUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        view.load(QUrl(url))
        view.iconChanged.connect(lambda icon, button=shortcut_button: button.setIcon(icon))
        shortcut_button.triggered.connect(lambda: self.open_URL(url, name))
        self.vertical_bar.addAction(shortcut_button)
        self.save_shortcut_to_xml(name, url)

    def create_database(self):
        if not os.path.exists('shortcuts.xml'):
            root = ET.Element("shortcuts")
            tree = ET.ElementTree(root)
            tree.write('shortcuts.xml')

    def show_settings(self):
        settings_dialog = SettingsDialog(self, self.memory_saver, self.dark_mode, self.language)
        settings_dialog.exec()
        self.language = settings_dialog.language
        self.save_settings()
        self.update_language()

    def save_settings(self):
        root = ET.Element("settings")
        tree = ET.ElementTree(root)
        language_element = ET.SubElement(root, "language")
        language_element.text = self.language
        memory_saver_element = ET.SubElement(root, "memory_saver")
        memory_saver_element.text = str(memory_saver_enabled[0])
        dark_mode_element = ET.SubElement(root, "dark_mode")
        dark_mode_element.text = str(dark_mode_enabled[0])
        tree.write("settings.xml")

    def load_settings(self):
        if not os.path.exists("settings.xml"):
            return
        tree = ET.parse("settings.xml")
        root = tree.getroot()
        language_element = root.find("language")
        if language_element is not None:
            self.language = language_element.text
        memory_saver_element = root.find("memory_saver")
        if memory_saver_element is not None:
            memory_saver_enabled[0] = bool(strtobool(memory_saver_element.text))
        dark_mode_element = root.find("dark_mode")
        if dark_mode_element is not None:
            dark_mode_enabled[0] = bool(strtobool(dark_mode_element.text))
        self.update_language()

    def update_language(self):
        if self.language == "日本語":
            self.setWindowTitle("Orb Browser")
        elif self.language == "English":
            self.setWindowTitle("About Orb Browser")
        elif self.language == "中文":
            self.setWindowTitle("关于 Orb Browser")


class BookmarkAction(QAction, QMenu):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.url = ""

    def showContextMenu(self, point):
        contextMenu = QMenu(self.parent())
        deleteAction = QAction("削除", self)
        deleteAction.triggered.connect(self.deleteBookmark)
        contextMenu.addAction(deleteAction)
        contextMenu.exec_(self.mapToGlobal(point))

    def deleteBookmark(self):
        tree = ET.parse('shortcuts.xml')
        root = tree.getroot()
        for shortcut in root.findall('shortcut'):
            if shortcut.find('url').text == self.url:
                root.remove(shortcut)
                tree.write('shortcuts.xml')
                break
        self.parent().removeAction(self)


class MemorySaver(QObject):
    def __init__(self, tabs):
        super().__init__()
        self.tabs = tabs
        self.tabs.currentChanged.connect(self.save_memory)
        self.memory_saver_enabled = False
        self.last_access_times = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_inactive_tabs)
        self.timer.start(60000)  # 1分ごとにチェック


    def save_memory(self, index):
        if self.memory_saver_enabled:
            current_time = QDateTime.currentDateTime()
            for i in range(self.tabs.count()):
                if i != index:
                    if i not in self.last_access_times:
                        self.last_access_times[i] = current_time
                    self.tabs.widget(i).setVisible(False)
                else:
                    self.last_access_times[i] = current_time
                    self.tabs.widget(i).setVisible(True)
        else:
            for i in range(self.tabs.count()):
                self.tabs.widget(i).setVisible(True)

    def toggle_memory_saver(self, enabled):
        self.memory_saver_enabled = enabled
        memory_saver_enabled[0] = enabled
        self.save_memory(self.tabs.currentIndex())

    def check_inactive_tabs(self):
        if not self.memory_saver_enabled:
            return

        current_time = QDateTime.currentDateTime()
        for i in range(self.tabs.count()):
            if i != self.tabs.currentIndex():
                last_access_time = self.last_access_times.get(i, current_time)
                if last_access_time.secsTo(current_time) > 600:  # 10分以上経過
                    self.tabs.widget(i).setVisible(False)
                else:
                    self.tabs.widget(i).setVisible(True)


class DarkMode(QObject):
    def __init__(self, tabs):
        super().__init__()
        self.tabs = tabs
        self.dark_mode_enabled = False

    def toggle_dark_mode(self, enabled):
        self.dark_mode_enabled = enabled
        dark_mode_enabled[0] = enabled
        for i in range(self.tabs.count()):
            web_view = self.tabs.widget(i)
            if enabled:
                web_view.page().setBackgroundColor(Qt.black)
                self.apply_dark_mode_js(web_view)
            
            else:
                web_view.page().setBackgroundColor(Qt.white)
                self.remove_dark_mode_js(web_view)

    def apply_dark_mode_js(self, web_view):
        js_code = """
        document.body.style.backgroundColor = 'black';
        document.body.style.color = 'white';
        """
        web_view.page().runJavaScript(js_code)

    def remove_dark_mode_js(self, web_view):
        js_code = """
        document.body.style.backgroundColor = 'white';
        document.body.style.color = 'black';
        """
        web_view.page().runJavaScript(js_code)


class SettingsDialog(QDialog):
    def __init__(self, parent, memory_saver, dark_mode, language):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.language = language
        self.memory_saver = memory_saver
        self.dark_mode = dark_mode
        if not os.path.exists("settings.xml"):
            return
        tree = ET.parse("settings.xml")
        root = tree.getroot()
        language_element = root.find("language")
        if language_element is not None:
            self.language = language_element.text
        memory_saver_element = root.find("memory_saver")
        if memory_saver_element is not None:
            memory_saver_enabled[0] = bool(strtobool(memory_saver_element.text))
        dark_mode_element = root.find("dark_mode")
        if dark_mode_element is not None:
            dark_mode_enabled[0] = bool(strtobool(dark_mode_element.text))
        self.init_ui()

    def closeEvent(self, e):
        root = ET.Element("settings")
        tree = ET.ElementTree(root)
        ET.SubElement(root, "language").text = self.language
        ET.SubElement(root, "memory_saver").text = str(self.check_memory_state())
        ET.SubElement(root, "dark_mode").text = str(self.check_darkmode_state())
        tree.write("settings.xml")

    def check_memory_state(self):
        if self.memory_saver_toggle.checkState() == Qt.CheckState.Checked:
            return True
        elif self.memory_saver_toggle.checkState() == Qt.CheckState.Unchecked:
            return False

    def check_darkmode_state(self):
        if self.dark_mode_toggle.checkState() == Qt.CheckState.Checked:
            return True
        elif self.dark_mode_toggle.checkState() == Qt.CheckState.Unchecked:
            return False

    def check_darkmode(self):
        if dark_mode_enabled[0]:
            return Qt.CheckState.Checked
        else:
            return Qt.CheckState.Unchecked

    def check_memory(self):
        if memory_saver_enabled[0]:
            return Qt.CheckState.Checked
        else:
            return Qt.CheckState.Unchecked

    def init_ui(self):
        layout = QVBoxLayout()

        # ダークモードのトグルボタン
        dark_mode_layout = QHBoxLayout()
        dark_mode_toggle = QLabel("ダークモード")
        self.dark_mode_toggle = QCheckBox()
        self.dark_mode_toggle.setChecked(dark_mode_enabled[0])
        self.dark_mode_toggle.setCheckState(self.check_darkmode())
        self.dark_mode_toggle.toggled.connect(self.dark_mode.toggle_dark_mode)
        dark_mode_layout.addWidget(dark_mode_toggle)
        dark_mode_layout.addWidget(self.dark_mode_toggle)
        layout.addLayout(dark_mode_layout)

        # メモリーセイバーのトグルボタン
        memory_saver_layout = QHBoxLayout()
        memory_saver_toggle = QLabel("メモリーセイバー")
        self.memory_saver_toggle = QCheckBox()
        self.memory_saver_toggle.setChecked(memory_saver_enabled[0])
        self.memory_saver_toggle.setCheckState(self.check_memory())
        self.memory_saver_toggle.toggled.connect(self.memory_saver.toggle_memory_saver)
        memory_saver_layout.addWidget(memory_saver_toggle)
        memory_saver_layout.addWidget(self.memory_saver_toggle)
        layout.addLayout(memory_saver_layout)

        language_layout = QHBoxLayout()
        language_label = QLabel("言語設定")
        self.language_toggle = QComboBox()
        self.language_toggle.addItems(["日本語", "English", "中文"])
        self.language_toggle.setCurrentText(self.language)
        self.language_toggle.currentTextChanged.connect(self.update_language)
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_toggle)
        layout.addLayout(language_layout)

        # Orb Browserについて
        self.about_layout = QHBoxLayout()
        self.about_label = QLabel("Orb Browserについて")
        self.about_text = QLabel("Orb Browserは、Python と Qt を使って作られた軽量なブラウザです。")
        self.about_layout.addWidget(self.about_label)
        self.about_layout.addWidget(self.about_text)
        layout.addLayout(self.about_layout)

        self.setLayout(layout)

    def update_language(self, language):
        self.language = language
        if language == "日本語":
            self.about_label.setText("Orb Browserについて")
            self.about_text.setText("Orb Browserは、Python と Qt を使って作られた軽量なブラウザです")
            self.setWindowTitle("設定")
            self.dark_mode_toggle.setText("ダークモード")
            self.memory_saver_toggle.setText("メモリーセイバー")
        elif language == "English":
            self.about_label.setText("About Orb Browser")
            self.about_text.setText("Orb Browser is a lightweight and fast web browser developed using Python and QT.")
            self.setWindowTitle("Settings")
            self.dark_mode_toggle.setText("Dark Mode")
            self.memory_saver_toggle.setText("Memory Saver")
        elif language == "中文":
            self.about_label.setText("关于 Orb 浏览器")
            self.about_text.setText("Orb Browser 是一款使用 Python")
            self.setWindowTitle("设置")
            self.dark_mode_toggle.setText("暗模式")
            self.memory_saver_toggle.setText("内存保护器")

app = QApplication(sys.argv)
app.setApplicationName("OrbBrowser")
window = MainWindow()
window.create_database()
window.show()
app.exec()
