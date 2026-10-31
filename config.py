"""
Configuration Module for LotTrace AI.
Contains paths, dataset profiles, database settings, and global constants.
"""

import os
from pathlib import Path
from dataclasses import dataclass

# Root directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Data Directories
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "lottrace.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")

GENERATED_DIR = DATA_DIR / "generated"
CSV_EXPORT_DIR = GENERATED_DIR / "csv"
JSON_EXPORT_DIR = GENERATED_DIR / "json"
SQL_EXPORT_DIR = GENERATED_DIR / "sql"

GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
GROUND_TRUTH_CSV = GROUND_TRUTH_DIR / "ground_truth.csv"
GROUND_TRUTH_JSON = GROUND_TRUTH_DIR / "ground_truth.json"

REPORTS_DIR = DATA_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

# Default Random Seed for Deterministic Generation
DEFAULT_RANDOM_SEED = 20261022

# API Server Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 5000))

# Streamlit Port
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))


@dataclass(frozen=True)
class DatasetProfile:
    """Configuration profile for synthetic data generation scale."""
    name: str
    num_suppliers: int
    num_products: int
    num_boms_per_product: int
    num_raw_lots: int
    num_production_orders: int
    num_finished_lots: int
    num_customers: int
    num_shipments: int
    num_deliveries: int
    num_recall_cases: int


# Dataset Profiles
PROFILES = {
    "starter": DatasetProfile(
        name="starter",
        num_suppliers=25,
        num_products=10,
        num_boms_per_product=2,
        num_raw_lots=200,
        num_production_orders=100,
        num_finished_lots=150,
        num_customers=50,
        num_shipments=120,
        num_deliveries=400,
        num_recall_cases=3,
    ),
    "full": DatasetProfile(
        name="full",
        num_suppliers=500,
        num_products=40,
        num_boms_per_product=2,
        num_raw_lots=10000,
        num_production_orders=5000,
        num_finished_lots=8000,
        num_customers=1500,
        num_shipments=7500,
        num_deliveries=20000,
        num_recall_cases=10,
    ),
}


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        DATA_DIR,
        GENERATED_DIR,
        CSV_EXPORT_DIR,
        JSON_EXPORT_DIR,
        SQL_EXPORT_DIR,
        GROUND_TRUTH_DIR,
        REPORTS_DIR,
        DOCS_DIR / "schema",
        DOCS_DIR / "api",
        DOCS_DIR / "architecture",
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
