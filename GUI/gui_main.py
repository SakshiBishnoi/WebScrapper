import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt

# Import backend components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.static import StaticScraper
from scraper.dynamic import DynamicScraper
from utils.data_export import DataExporter

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'default_config.json')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

class ScraperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Web Scraper GUI')
        self.setGeometry(100, 100, 600, 500)
        self.config = load_config()
        self.static_scraper = StaticScraper(self.config)
        try:
            self.dynamic_scraper = DynamicScraper(self.config)
        except Exception:
            self.dynamic_scraper = None
        self.exporter = DataExporter()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # URL input
        self.url_label = QLabel('URL:')
        self.url_input = QLineEdit()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)

        # Scraper type
        self.scraper_type_label = QLabel('Scraper Type:')
        self.static_radio = QRadioButton('Static')
        self.dynamic_radio = QRadioButton('Dynamic')
        self.static_radio.setChecked(True)
        self.scraper_group = QButtonGroup()
        self.scraper_group.addButton(self.static_radio)
        self.scraper_group.addButton(self.dynamic_radio)
        scraper_type_layout = QHBoxLayout()
        scraper_type_layout.addWidget(self.static_radio)
        scraper_type_layout.addWidget(self.dynamic_radio)
        layout.addWidget(self.scraper_type_label)
        layout.addLayout(scraper_type_layout)

        # Selectors input
        self.selectors_label = QLabel('Selectors (key=selector per line, or "auto"):')
        self.selectors_input = QTextEdit()
        self.selectors_input.setPlaceholderText('title=h1\nparagraphs=p\nlinks=a\n... or type auto')
        layout.addWidget(self.selectors_label)
        layout.addWidget(self.selectors_input)

        # Export format
        self.format_label = QLabel('Export Format:')
        self.format_combo = QComboBox()
        self.format_combo.addItems(['json', 'csv'])
        layout.addWidget(self.format_label)
        layout.addWidget(self.format_combo)

        # Output filename
        self.output_label = QLabel('Output Filename (without extension):')
        self.output_input = QLineEdit()
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_input)

        # Scrape button
        self.scrape_button = QPushButton('Scrape')
        self.scrape_button.clicked.connect(self.run_scrape)
        layout.addWidget(self.scrape_button)

        # Results area
        self.results_label = QLabel('Results:')
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        layout.addWidget(self.results_label)
        layout.addWidget(self.results_area)

        self.setLayout(layout)

    def parse_selectors(self, text):
        text = text.strip()
        if text.lower() == 'auto':
            return None
        selectors = {}
        for line in text.splitlines():
            if '=' in line:
                key, selector = line.split('=', 1)
                selectors[key.strip()] = selector.strip()
        return selectors if selectors else None

    def run_scrape(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, 'Input Error', 'Please enter a URL.')
            return
        use_dynamic = self.dynamic_radio.isChecked()
        selectors_text = self.selectors_input.toPlainText()
        selectors = self.parse_selectors(selectors_text)
        export_format = self.format_combo.currentText()
        output_filename = self.output_input.text().strip() or f'scrape_result'

        self.results_area.clear()
        self.results_area.append(f'Scraping {url}...')
        QApplication.processEvents()
        try:
            if use_dynamic and self.dynamic_scraper:
                if selectors:
                    data = self.dynamic_scraper.extract_data(url, selectors)
                else:
                    data = self.dynamic_scraper.auto_extract(url)
            else:
                if selectors:
                    data = self.static_scraper.extract_data_with_selectors(url, selectors)
                else:
                    data = self.static_scraper.extract_data(url)
            if not data:
                self.results_area.append('No data extracted.')
                return
            file_path = self.exporter.export_data(data, output_filename, export_format)
            self.results_area.append(f'Data exported to: {file_path}')
            self.results_area.append(json.dumps(data, indent=2, ensure_ascii=False)[:2000] + ('... (truncated)' if len(json.dumps(data)) > 2000 else ''))
        except Exception as e:
            self.results_area.append(f'Error: {e}')

def run_gui():
    app = QApplication(sys.argv)
    window = ScraperGUI()
    window.show()
    sys.exit(app.exec_()) 