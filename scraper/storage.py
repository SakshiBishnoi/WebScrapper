import pandas as pd
import json
import csv
from sqlalchemy import create_engine
from typing import List, Dict
from pathlib import Path

class DataStorage:
    def __init__(self, config: dict):
        self.output_format = config.get('output_format', 'json')
        self.db_engine = create_engine(config['database_url']) if 'database_url' in config else None

    def save(self, data: List[Dict], filename: str) -> None:
        """Main entry point for saving data in configured format"""
        clean_data = self._clean_data(data)
        {
            'csv': self._save_csv,
            'json': self._save_json,
            'xlsx': self._save_excel,
            'db': self._save_db
        }[self.output_format](clean_data, filename)

    def _clean_data(self, data: List[Dict]) -> List[Dict]:
        """Data sanitization and validation"""
        return [
            {k: v.strip() if isinstance(v, str) else v 
             for k, v in item.items()
             if v is not None}
            for item in data
        ]

    def _save_csv(self, data: List[Dict], filename: str) -> None:
        Path(filename).parent.mkdir(exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def _save_json(self, data: List[Dict], filename: str) -> None:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def _save_excel(self, data: List[Dict], filename: str) -> None:
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, engine='openpyxl')

    def _save_db(self, data: List[Dict], table_name: str) -> None:
        if self.db_engine:
            pd.DataFrame(data).to_sql(
                name=table_name,
                con=self.db_engine,
                if_exists='append',
                index=False
            )