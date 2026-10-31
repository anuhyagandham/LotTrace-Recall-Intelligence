"""
JSON Exporter for LotTrace AI.
Dumps all relational database tables to JSON format in data/generated/json/.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from config import JSON_EXPORT_DIR
from src.database.connection import get_db_session, Base
from src.utils.logging_config import logger


class JSONExporter:
    """Exports all entities to individual JSON files."""

    def __init__(self, output_dir: Path = JSON_EXPORT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self) -> Dict[str, int]:
        """Dumps all tables to JSON files. Returns dict of table_name -> row_count."""
        logger.info(f"Exporting all database tables to JSON at {self.output_dir}...")
        counts = {}

        with get_db_session() as session:
            for mapper in Base.registry.mappers:
                model_cls = mapper.class_
                table_name = model_cls.__tablename__
                file_path = self.output_dir / f"{table_name}.json"

                records = session.query(model_cls).all()
                rows = [r.to_dict() for r in records if hasattr(r, "to_dict")]

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "table_name": table_name,
                        "row_count": len(rows),
                        "data": rows,
                    }, f, indent=2)

                counts[table_name] = len(rows)

        logger.info(f"JSON export complete: {len(counts)} tables written.")
        return counts
