"""
Source Manifest and Checksum Generator for LotTrace AI.
Generates cryptographic SHA-256 checksums, dataset volume audits,
and manifests in JSON and Markdown formats.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from config import (
    BASE_DIR,
    GENERATED_DIR,
    CSV_EXPORT_DIR,
    JSON_EXPORT_DIR,
    SQL_EXPORT_DIR,
    GROUND_TRUTH_CSV,
    GROUND_TRUTH_JSON,
    DEFAULT_RANDOM_SEED,
)
from src.analytics.metrics import MetricsCalculator
from src.validation.validator import BusinessValidator
from src.utils.logging_config import logger


def calculate_sha256(file_path: Path) -> str:
    """Computes SHA-256 hex digest for a file."""
    if not file_path.exists():
        return "FILE_NOT_FOUND"
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ManifestGenerator:
    """Produces verified SOURCE_MANIFEST records with file checksums and metrics."""

    def __init__(self, seed: int = DEFAULT_RANDOM_SEED):
        self.seed = seed

    def generate_manifest(self) -> Dict[str, Any]:
        """Scans all generated files, computes checksums, and compiles manifest."""
        logger.info("Compiling source manifest and SHA-256 file checksums...")

        # File audits
        files_manifest: List[Dict[str, Any]] = []

        scan_dirs = [
            ("CSV", CSV_EXPORT_DIR, "*.csv"),
            ("JSON", JSON_EXPORT_DIR, "*.json"),
            ("SQL", SQL_EXPORT_DIR, "*.sql"),
        ]

        for fmt, dir_path, pattern in scan_dirs:
            if dir_path.exists():
                for p in sorted(dir_path.glob(pattern)):
                    size_bytes = p.stat().st_size
                    checksum = calculate_sha256(p)
                    files_manifest.append({
                        "format": fmt,
                        "file_name": p.name,
                        "relative_path": str(p.relative_to(BASE_DIR)).replace("\\", "/"),
                        "size_bytes": size_bytes,
                        "sha256_checksum": checksum,
                    })

        # Ground truth files
        gt_manifest = []
        for p in [GROUND_TRUTH_CSV, GROUND_TRUTH_JSON]:
            if p.exists():
                gt_manifest.append({
                    "file_name": p.name,
                    "relative_path": str(p.relative_to(BASE_DIR)).replace("\\", "/"),
                    "size_bytes": p.stat().st_size,
                    "sha256_checksum": calculate_sha256(p),
                })

        # Metrics and validation
        metrics_calc = MetricsCalculator()
        dataset_metrics = metrics_calc.get_dataset_metrics()
        quality_metrics = metrics_calc.get_data_quality_metrics()

        manifest_data = {
            "project_name": "LotTrace AI",
            "generation_seed": self.seed,
            "manifest_generated_at": datetime.utcnow().isoformat(),
            "dataset_row_counts": dataset_metrics,
            "data_quality_summary": quality_metrics,
            "total_exported_files": len(files_manifest),
            "files": files_manifest,
            "ground_truth_manifest": gt_manifest,
        }

        # Write JSON manifest
        json_path = GENERATED_DIR / "SOURCE_MANIFEST.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        # Write Markdown manifest at project root
        md_path = BASE_DIR / "SOURCE_MANIFEST.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# LotTrace AI — Source Dataset & Cryptographic Manifest\n\n")
            f.write(f"- **Generation Seed:** `{self.seed}`\n")
            f.write(f"- **Manifest Generated At:** `{manifest_data['manifest_generated_at']} UTC`\n")
            f.write(f"- **Overall Validation Pass Rate:** `{quality_metrics.get('overall_validation_pass_rate_pct')}%`\n\n")

            f.write("## 1. Relational Table Row Counts\n\n")
            f.write("| Table / Entity | Row Count |\n")
            f.write("| :--- | :--- |\n")
            for table, count in dataset_metrics.items():
                f.write(f"| `{table}` | {count:,} |\n")

            f.write("\n## 2. Generated File Checksums (SHA-256)\n\n")
            f.write("| Format | File | Size (Bytes) | SHA-256 Checksum |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for file_info in files_manifest:
                f.write(f"| {file_info['format']} | `{file_info['file_name']}` | {file_info['size_bytes']:,} | `{file_info['sha256_checksum'][:16]}...` |\n")

            f.write("\n## 3. Ground Truth Reference Manifest\n\n")
            f.write("| Ground Truth File | Size (Bytes) | SHA-256 Checksum |\n")
            f.write("| :--- | :--- | :--- |\n")
            for gt_info in gt_manifest:
                f.write(f"| `{gt_info['file_name']}` | {gt_info['size_bytes']:,} | `{gt_info['sha256_checksum']}` |\n")

        logger.info(f"Manifest written to {json_path} and {md_path}.")
        return manifest_data
