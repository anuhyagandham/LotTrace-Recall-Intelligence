"""
Execute all data exporters and compile updated source manifest.
"""

import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.exporters.csv_exporter import CSVExporter
from src.exporters.json_exporter import JSONExporter
from src.exporters.sql_exporter import SQLExporter
from src.exporters.manifest_generator import ManifestGenerator


def run_all_exports():
    print("=" * 80)
    print("RUNNING DATA EXPORTERS FOR FULL-SCALE DATABASE")
    print("=" * 80)
    
    # 1. CSV
    t0 = time.time()
    csv_counts = CSVExporter().export_all()
    print(f"  CSV Export: {len(csv_counts)} tables in {time.time()-t0:.2f}s")
    
    # 2. JSON
    t0 = time.time()
    json_counts = JSONExporter().export_all()
    print(f"  JSON Export: {len(json_counts)} tables in {time.time()-t0:.2f}s")
    
    # 3. SQL
    t0 = time.time()
    sql_counts = SQLExporter().export_all()
    print(f"  SQL Export: {len(sql_counts)} tables in {time.time()-t0:.2f}s")
    
    # 4. Manifest
    t0 = time.time()
    manifest = ManifestGenerator().generate_manifest()
    print(f"  Manifest Compilation: in {time.time()-t0:.2f}s (Audited {len(manifest.get('files', []))} export files)")
    
    print("=" * 80)
    print("EXPORTS AND SOURCE_MANIFEST.md SUCCESSFULLY UPDATED!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_exports()
