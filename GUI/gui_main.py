import sys
import os
import json
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QRadioButton, QButtonGroup, QComboBox, QGroupBox, QTableWidget, QTableWidgetItem, QProgressBar,
    QStatusBar, QMessageBox, QFileDialog, QTabWidget, QStackedWidget, QToolButton, QStyle, QFormLayout, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Use qt-material for a modern Material Design look
try:
    import qt_material
    MATERIAL_STYLE = True
except ImportError:
    MATERIAL_STYLE = False

# Import backend components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.static import StaticScraper
from scraper.dynamic import DynamicScraper
from utils.data_export import DataExporter

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'default_config.json')

# Custom stylesheet for black/white/red theme, with only supported Qt properties
CUSTOM_STYLE = """
QWidget {
    background-color: #111112;
    color: #fff;
    font-size: 12px;
}
QGroupBox {
    border: 1px solid #333;
    border-radius: 8px;
    margin-top: 10px;
    background-color: #18181a;
    color: #fff;
    font-weight: bold;
    padding-top: 8px;
    padding-bottom: 8px;
    padding-left: 10px;
    padding-right: 10px;
}
QGroupBox:title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px 0 4px;
    color: #fff;
    background: transparent;
    font-size: 13px;
}
QLabel {
    color: #fff;
    font-size: 12px;
}
QLineEdit, QTextEdit, QComboBox {
    background: #18181a;
    color: #fff;
    border: 1.2px solid #333;
    border-radius: 6px;
    padding: 3px 7px;
    font-size: 12px;
    margin-bottom: 4px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1.5px solid #e53935;
    background: #222225;
}
QPushButton {
    background-color: #e53935;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: bold;
    font-size: 12px;
    margin: 2px 0;
}
QPushButton:hover {
    background-color: #ff5252;
}
QPushButton:pressed {
    background-color: #b71c1c;
}
QToolButton {
    background: transparent;
    border: none;
    color: #fff;
    padding: 2px;
    margin: 0 2px;
}
QRadioButton, QCheckBox {
    color: #fff;
    spacing: 6px;
    font-size: 12px;
}
QRadioButton {
    margin-right: 18px;
}
QRadioButton::indicator {
    width: 8px;
    height: 8px;
    border-radius: 4px;
    border: 1.2px solid #888;
    background: #18181a;
    margin-right: 6px;
}
QRadioButton::indicator:checked {
    border: 1.5px solid #e53935;
    background: #fff;
}
QRadioButton::indicator:unchecked {
    border: 1.2px solid #888;
    background: #18181a;
}
QTabWidget::pane {
    border: 1.2px solid #222;
    border-radius: 8px;
    background: #18181a;
    margin-top: 2px;
}
QTabBar::tab {
    background: #18181a;
    color: #fff;
    padding: 6px 14px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background: #111112;
    color: #fff;
    border-bottom: 2.5px solid #e53935;
}
QTabBar::tab:!selected {
    background: #18181a;
    color: #fff;
}
QTabBar::tab:hover {
    background: #222225;
    color: #ff5252;
}
QTableWidget {
    background: #18181a;
    color: #fff;
    gridline-color: #333;
    border-radius: 6px;
    font-size: 12px;
}
QHeaderView::section {
    background: #111112;
    color: #fff;
    border: 1px solid #333;
    padding: 4px;
    font-size: 12px;
}
QProgressBar {
    background: #222225;
    color: #fff;
    border: 1.2px solid #e53935;
    border-radius: 8px;
    text-align: center;
    height: 14px;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #e53935;
    border-radius: 8px;
}
QStatusBar {
    background: #111112;
    color: #fff;
    border-top: 1.2px solid #e53935;
    font-size: 11px;
}
QMessageBox QLabel {
    color: #fff;
    font-size: 12px;
}
QFormLayout {
    margin-top: 6px;
    margin-bottom: 6px;
    margin-left: 2px;
    margin-right: 2px;
    spacing: 8px;
}
QVBoxLayout, QHBoxLayout {
    spacing: 8px;
}
"""

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_valid_url(url):
    return url.startswith('http://') or url.startswith('https://')

class QTextEditLogger:
    def __init__(self, text_edit, orig_stream):
        self.text_edit = text_edit
        self.orig_stream = orig_stream
    def write(self, msg):
        if msg.strip():
            self.text_edit.append(msg.rstrip())
        self.orig_stream.write(msg)
    def flush(self):
        self.orig_stream.flush()

class ScraperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Web Scraper')
        self.setMinimumSize(900, 650)
        self.config = load_config()
        self.static_scraper = StaticScraper(self.config)
        try:
            self.dynamic_scraper = DynamicScraper(self.config)
        except Exception:
            self.dynamic_scraper = None
        self.exporter = DataExporter()
        self.result_data = None
        self.result_file = None
        self.log_messages = []
        self.init_ui()
        self._redirect_stdout_stderr()

    def _redirect_stdout_stderr(self):
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        sys.stdout = QTextEditLogger(self.log_text, self._orig_stdout)
        sys.stderr = QTextEditLogger(self.log_text, self._orig_stderr)

    def closeEvent(self, event):
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr
        super().closeEvent(event)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(12)

        # --- Header ---
        header_layout = QHBoxLayout()
        app_label = QLabel('<b>Web Scraper</b>')
        app_label.setStyleSheet('font-size: 26px; letter-spacing: 1px;')
        header_layout.addWidget(app_label)
        header_layout.addStretch(1)
        self.about_button = QToolButton()
        self.about_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.about_button.setToolTip('About')
        self.about_button.clicked.connect(self.show_about)
        header_layout.addWidget(self.about_button)
        main_layout.addLayout(header_layout)

        # --- Input Section ---
        input_group = QGroupBox('Scrape Setup')
        input_group.setStyleSheet('QGroupBox { font-weight: bold; }')
        input_form = QFormLayout()
        input_form.setLabelAlignment(Qt.AlignRight)
        input_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        input_form.setHorizontalSpacing(18)
        input_form.setVerticalSpacing(10)

        # URL
        url_hbox = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('https://example.com')
        self.url_input.setMinimumWidth(350)
        self.url_input.setToolTip('Enter the URL to scrape (must start with http:// or https://)')
        paste_button = QToolButton()
        paste_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        paste_button.setToolTip('Paste from clipboard')
        paste_button.clicked.connect(self.paste_url)
        url_hbox.addWidget(self.url_input)
        url_hbox.addWidget(paste_button)
        input_form.addRow(QLabel('URL:'), url_hbox)

        # Selector Mode
        selector_mode_hbox = QHBoxLayout()
        self.auto_radio = QRadioButton('Auto')
        self.custom_radio = QRadioButton('Custom')
        self.selector_mode_group = QButtonGroup()
        self.selector_mode_group.addButton(self.auto_radio)
        self.selector_mode_group.addButton(self.custom_radio)
        self.auto_radio.toggled.connect(self.toggle_selector_mode)
        selector_mode_hbox.addWidget(self.auto_radio)
        selector_mode_hbox.addWidget(self.custom_radio)
        selector_mode_hbox.addStretch(1)
        input_form.addRow(QLabel('Selector Mode:'), selector_mode_hbox)

        # Custom Selector Input (hidden if auto)
        self.selector_stack = QStackedWidget()
        self.selector_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.selector_stack.addWidget(QWidget())  # Auto (empty)
        custom_widget = QWidget()
        custom_layout = QVBoxLayout()
        self.selectors_input = QTextEdit()
        self.selectors_input.setPlaceholderText('title=h1\nparagraphs=p\nlinks=a')
        self.selectors_input.setToolTip('Enter CSS selectors as key=selector per line. Example: title=h1')
        self.selectors_input.setMinimumHeight(60)
        help_label = QLabel('<i>Example: title=h1, paragraphs=p</i>')
        custom_layout.addWidget(self.selectors_input)
        custom_layout.addWidget(help_label)
        custom_widget.setLayout(custom_layout)
        self.selector_stack.addWidget(custom_widget)
        input_form.addRow(QLabel('Selectors:'), self.selector_stack)

        # Scraper Type
        scraper_type_hbox = QHBoxLayout()
        self.static_radio = QRadioButton('Static')
        self.dynamic_radio = QRadioButton('Dynamic')
        self.scraper_group = QButtonGroup()
        self.scraper_group.addButton(self.static_radio)
        self.scraper_group.addButton(self.dynamic_radio)
        scraper_type_hbox.addWidget(self.static_radio)
        scraper_type_hbox.addWidget(self.dynamic_radio)
        scraper_type_hbox.addStretch(1)
        input_form.addRow(QLabel('Scraper Type:'), scraper_type_hbox)

        # Export Options
        export_hbox = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(['json', 'csv'])
        self.format_combo.setToolTip('Choose the format for exported data')
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText('scrape_result')
        self.output_input.setMinimumWidth(120)
        self.output_input.setToolTip('Name for the exported file (without extension)')
        browse_button = QToolButton()
        browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        browse_button.setToolTip('Browse for export folder')
        browse_button.clicked.connect(self.browse_export_folder)
        export_hbox.addWidget(QLabel('Format:'))
        export_hbox.addWidget(self.format_combo)
        export_hbox.addSpacing(12)
        export_hbox.addWidget(QLabel('Output:'))
        export_hbox.addWidget(self.output_input)
        export_hbox.addWidget(browse_button)
        export_hbox.addStretch(1)
        input_form.addRow(QLabel('Export:'), export_hbox)

        input_group.setLayout(input_form)
        main_layout.addWidget(input_group)

        # --- Scrape Button, Progress, Status ---
        action_hbox = QHBoxLayout()
        self.scrape_button = QPushButton('Scrape')
        self.scrape_button.setMinimumWidth(120)
        self.scrape_button.setStyleSheet('font-weight: bold; font-size: 16px;')
        self.scrape_button.setToolTip('Start scraping the provided URL')
        self.scrape_button.clicked.connect(self.run_scrape)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(22)
        self.status_label = QLabel('Ready')
        self.status_label.setMinimumWidth(120)
        action_hbox.addWidget(self.scrape_button)
        action_hbox.addWidget(self.progress_bar)
        action_hbox.addWidget(self.status_label)
        action_hbox.addStretch(1)
        main_layout.addLayout(action_hbox)

        # --- Results Section ---
        results_group = QGroupBox('Results')
        results_group.setStyleSheet('QGroupBox { font-weight: bold; }')
        results_layout = QVBoxLayout()
        self.results_tabs = QTabWidget()
        self.results_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Log Tab (now first)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('background: #18181a; color: #fff; font-size: 12px;')
        self.results_tabs.addTab(self.log_text, 'Log')
        # Preview Tab
        self.preview_table = QTableWidget()
        self.preview_table.setVisible(False)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setVisible(True)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.preview_table)
        preview_layout.addWidget(self.preview_text)
        preview_widget.setLayout(preview_layout)
        self.results_tabs.addTab(preview_widget, 'Preview')
        # Exported File Tab
        export_tab = QWidget()
        export_tab_layout = QHBoxLayout()
        self.open_button = QPushButton('Open File')
        self.open_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.open_button.setToolTip('Open exported file')
        self.open_button.clicked.connect(self.open_export_file)
        self.copy_path_button = QPushButton('Copy Path')
        self.copy_path_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogListView))
        self.copy_path_button.setToolTip('Copy exported file path to clipboard')
        self.copy_path_button.clicked.connect(self.copy_export_path)
        export_tab_layout.addWidget(self.open_button)
        export_tab_layout.addWidget(self.copy_path_button)
        export_tab_layout.addStretch(1)
        export_tab.setLayout(export_tab_layout)
        self.results_tabs.addTab(export_tab, 'Exported File')
        results_layout.addWidget(self.results_tabs)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group, stretch=1)
        self.results_tabs.setCurrentIndex(0)  # Log tab as default

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.showMessage('Ready')
        main_layout.addWidget(self.status_bar)
        # Set defaults for selector mode and scraper type
        self.auto_radio.setChecked(True)
        self.dynamic_radio.setChecked(True)
        self.static_radio.setChecked(False)
        self.toggle_selector_mode()  # Set initial selector mode

    def toggle_selector_mode(self):
        if self.auto_radio.isChecked():
            self.selector_stack.setCurrentIndex(0)
        else:
            self.selector_stack.setCurrentIndex(1)

    def paste_url(self):
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())

    def browse_export_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Export Folder', os.getcwd())
        if folder:
            self.exporter.output_dir = folder
            self.status_bar.showMessage(f'Export folder set to: {folder}', 4000)

    def log(self, message):
        self.log_messages.append(message)
        self.log_text.append(message)

    def run_scrape(self):
        self.results_tabs.setCurrentIndex(0)  # Switch to log tab on scrape
        url = self.url_input.text().strip()
        if not url or not is_valid_url(url):
            self.status_bar.showMessage('Invalid URL. Please enter a valid URL starting with http:// or https://', 5000)
            self.log('<span style="color:#e53935;">Invalid URL. Please enter a valid URL starting with http:// or https://</span>')
            return
        use_dynamic = self.dynamic_radio.isChecked()
        selectors = None
        if self.custom_radio.isChecked():
            selectors_text = self.selectors_input.toPlainText()
            selectors = self.parse_selectors(selectors_text)
            if not selectors:
                self.status_bar.showMessage('Please enter at least one selector in custom mode.', 5000)
                self.log('<span style="color:#e53935;">Please enter at least one selector in custom mode.</span>')
                return
        export_format = self.format_combo.currentText()
        output_filename = self.output_input.text().strip() or 'scrape_result'
        self.status_label.setText('Scraping...')
        self.status_bar.showMessage('Scraping in progress...')
        self.progress_bar.setVisible(True)
        self.preview_table.setVisible(False)
        self.preview_text.setVisible(True)
        self.preview_text.clear()
        self.log_text.clear()
        self.log('<b>Scraping started...</b>')
        QApplication.processEvents()
        try:
            if use_dynamic and self.dynamic_scraper:
                if selectors:
                    self.log('Using <b>Dynamic Scraper</b> with custom selectors.')
                    data = self.dynamic_scraper.extract_data(url, selectors)
                else:
                    self.log('Using <b>Dynamic Scraper</b> with auto selectors.')
                    data = self.dynamic_scraper.auto_extract(url)
            else:
                if selectors:
                    self.log('Using <b>Static Scraper</b> with custom selectors.')
                    data = self.static_scraper.extract_data_with_selectors(url, selectors)
                else:
                    self.log('Using <b>Static Scraper</b> with auto selectors.')
                    data = self.static_scraper.extract_data(url)
            if not data:
                self.status_label.setText('No data extracted.')
                self.status_bar.showMessage('No data extracted.', 5000)
                self.log('<span style="color:#e53935;">No data extracted.</span>')
                self.progress_bar.setVisible(False)
                return
            file_path = self.exporter.export_data(data, output_filename, export_format)
            self.result_data = data
            self.result_file = file_path
            self.status_label.setText(f'Exported: {file_path}')
            self.status_bar.showMessage(f'Data exported to: {file_path}', 7000)
            self.log(f'<span style="color:#4caf50;">Data exported to: {file_path}</span>')
            # Preview Tab
            self.show_preview(data)
            self.progress_bar.setVisible(False)
        except Exception as e:
            self.status_label.setText('Error')
            self.status_bar.showMessage(f'Error: {e}', 7000)
            self.preview_text.setText(f'Error: {e}')
            self.log(f'<span style="color:#e53935;">Error: {e}</span>')
            self.progress_bar.setVisible(False)

    def parse_selectors(self, text):
        text = text.strip()
        selectors = {}
        for line in text.splitlines():
            if '=' in line:
                key, selector = line.split('=', 1)
                selectors[key.strip()] = selector.strip()
        return selectors if selectors else None

    def show_preview(self, data):
        # Try to show as table if possible
        if isinstance(data, dict) and 'content' in data and isinstance(data['content'], list) and data['content'] and isinstance(data['content'][0], dict):
            self.show_table(data['content'])
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            self.show_table(data)
        else:
            self.preview_table.setVisible(False)
            self.preview_text.setVisible(True)
            self.preview_text.setText(json.dumps(data, indent=2, ensure_ascii=False)[:5000] + ('... (truncated)' if len(json.dumps(data)) > 5000 else ''))

    def show_table(self, data_list):
        if not data_list:
            self.preview_table.setVisible(False)
            self.preview_text.setVisible(True)
            self.preview_text.setText('No tabular data to display.')
            return
        headers = list(data_list[0].keys())
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setRowCount(len(data_list))
        self.preview_table.setHorizontalHeaderLabels(headers)
        for row_idx, row_data in enumerate(data_list):
            for col_idx, header in enumerate(headers):
                value = str(row_data.get(header, ''))
                self.preview_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        self.preview_table.resizeColumnsToContents()
        self.preview_table.setVisible(True)
        self.preview_text.setVisible(False)

    def open_export_file(self):
        if self.result_file and os.path.exists(self.result_file):
            os.startfile(self.result_file)
        else:
            self.status_bar.showMessage('No exported file to open.', 4000)
            self.log('<span style="color:#e53935;">No exported file to open.</span>')

    def copy_export_path(self):
        if self.result_file:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.result_file)
            self.status_bar.showMessage('Exported file path copied to clipboard.', 3000)
            self.log('<span style="color:#4caf50;">Exported file path copied to clipboard.</span>')

    def show_about(self):
        QMessageBox.information(self, 'About', 'Web Scraper GUI\nModern, advanced, and user-friendly web scraping tool.\nPowered by PyQt5 and qt-material.')


def run_gui():
    app = QApplication(sys.argv)
    if MATERIAL_STYLE:
        qt_material.apply_stylesheet(app, theme='dark_teal.xml')
    app.setStyleSheet(CUSTOM_STYLE)
    window = ScraperGUI()
    window.show()
    sys.exit(app.exec_()) 