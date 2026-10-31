"""
CSV Exporter for LotTrace AI.
Dumps all relational database tables to CSV format in data/generated/csv/.
"""

import csv
from pathlib import Path
from typing import Dict, List, Any
from sqlalchemy import inspect
from config import CSV_EXPORT_DIR
from src.database.connection import get_db_session, Base
from src.utils.logging_config import logger


class CSVExporter:
    """Exports all entities to individual CSV files."""

    def __init__(self, output_dir: Path = CSV_EXPORT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self) -> Dict[str, int]:
        """Dumps all tables to CSV files. Returns dict of table_name -> row_count."""
        logger.info(f"Exporting all database tables to CSV at {self.output_dir}...")
        counts = {}

        with get_db_session() as session:
            # Iterate through all declared model classes
            for mapper in Base.registry.mappers:
                model_cls = mapper.class_
                table_name = model_cls.__tablename__
                file_path = self.output_dir / f"{table_name}.csv"

                records = session.query(model_cls).all()
                rows = [r.to_dict() for r in records if hasattr(r, "to_dict")]

                if rows:
                    fieldnames = list(rows[0].keys())
                    with open(file_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)
                    counts[table_name] = len(rows)
                else:
                    # Create empty CSV with column headers from table inspection
                    columns = [c.name for c in model_cls.__table__.columns]
                    with open(file_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader()
                    counts[table_name] = 0

        logger.info(f"CSV export complete: {len(counts)} tables written.")
        return counts
