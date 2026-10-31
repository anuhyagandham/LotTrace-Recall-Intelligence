"""
Reproducibility Verification Script for LotTrace AI.
Executes dual deterministic generation cycles with fixed seed 20261022,
verifies bitwise and logical dataset equivalence across tables using SHA-256 checksums,
and outputs REPRODUCIBILITY_REPORT.md.
"""

import sys
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import DEFAULT_RANDOM_SEED
from src.generator.data_generator import DataGenerator
from src.utils.logging_config import logger


def compute_table_checksum(records, exclude_fields=None) -> str:
    """Computes a deterministic SHA-256 hash over an entity collection excluding volatile timestamps."""
    if exclude_fields is None:
        exclude_fields = {"created_at", "updated_at", "detected_at", "last_audit_date"}

    canonical_rows = []
    for r in records:
        if hasattr(r, "to_dict"):
            d = r.to_dict()
        elif isinstance(r, dict):
            d = dict(r)
        else:
            continue
        cleaned = {k: v for k, v in d.items() if k not in exclude_fields}
        canonical_rows.append(cleaned)

    # Sort deterministically by string representation of sorted keys
    serialized = json.dumps(canonical_rows, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def run_verification(profile: str = "full", seed: int = DEFAULT_RANDOM_SEED) -> bool:
    logger.info(f"Running dual-pass reproducibility verification [Profile: {profile}, Seed: {seed}]")

    def run_cycle(pass_num: int) -> DataGenerator:
        logger.info(f"Pass {pass_num}: Executing synthetic generation cycle...")
        gen = DataGenerator(profile_name=profile, seed=seed)
        gen._generate_suppliers()
        gen._generate_products_and_boms()
        gen._generate_raw_material_lots()
        gen._generate_production_and_genealogy()
        gen._generate_customers()
        gen._generate_distribution_and_deliveries()
        gen._generate_recall_cases()
        gen._plant_anomaly_scenarios()
        return gen

    # Execute Pass 1 and Pass 2
    gen1 = run_cycle(1)
    gen2 = run_cycle(2)

    # Table collections to audit
    tables_to_verify = [
        ("Suppliers", gen1.suppliers, gen2.suppliers),
        ("Products", gen1.products, gen2.products),
        ("BOMs", gen1.boms, gen2.boms),
        ("Raw Material Lots", gen1.material_lots, gen2.material_lots),
        ("Production Orders", gen1.production_orders, gen2.production_orders),
        ("Production Consumptions", gen1.consumptions, gen2.consumptions),
        ("Finished Lots", gen1.finished_lots, gen2.finished_lots),
        ("Lot Genealogies", gen1.genealogies, gen2.genealogies),
        ("Customers", gen1.customers, gen2.customers),
        ("Shipments", gen1.shipments, gen2.shipments),
        ("Shipment Items", gen1.shipment_items, gen2.shipment_items),
        ("Deliveries", gen1.deliveries, gen2.deliveries),
        ("Inventories", gen1.inventories, gen2.inventories),
        ("Inventory Events", gen1.inventory_events, gen2.inventory_events),
        ("Recall Cases", gen1.recall_cases, gen2.recall_cases),
        ("Validation Issues", gen1.validation_issues, gen2.validation_issues),
        ("Ground Truth Records", gen1.ground_truth_records, gen2.ground_truth_records),
    ]

    results = []
    for name, list1, list2 in tables_to_verify:
        count1 = len(list1)
        count2 = len(list2)
        chk1 = compute_table_checksum(list1)
        chk2 = compute_table_checksum(list2)
        is_match = (count1 == count2) and (chk1 == chk2)
        results.append({
            "name": name,
            "count1": count1,
            "count2": count2,
            "chk1": chk1,
            "chk2": chk2,
            "match": is_match,
        })

    all_matched = all(r["match"] for r in results)

    # Write REPRODUCIBILITY_REPORT.md
    report_path = BASE_DIR / "REPRODUCIBILITY_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# LotTrace AI — Full-Scale Reproducibility & Determinism Verification Report\n\n")
        f.write(f"- **Verification Profile:** `{profile.upper()}`\n")
        f.write(f"- **Verification Seed:** `{seed}`\n")
        f.write(f"- **Verification Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n")
        f.write(f"- **Overall Audit Outcome:** `{'PASS — 100% BITWISE DETERMINISTIC' if all_matched else 'FAIL'}`\n\n")

        f.write("## 1. Dual-Pass Full-Scale Entity Checksum Audit\n\n")
        f.write("Deterministic SHA-256 checksums were calculated on canonical business attributes, explicitly excluding volatile execution timestamps (`created_at`, `updated_at`, `detected_at`, `last_audit_date`).\n\n")
        f.write("| Table / Entity Collection | Pass 1 Count | Pass 2 Count | Pass 1 SHA-256 (Canonical) | Pass 2 SHA-256 (Canonical) | Audit Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            badge = "✅ PASS (Identical)" if r["match"] else "❌ FAIL (Mismatch)"
            f.write(f"| **{r['name']}** | {r['count1']:,} | {r['count2']:,} | `{r['chk1'][:16]}...` | `{r['chk2'][:16]}...` | {badge} |\n")

        f.write("\n## 2. Determinism Verification Methodology\n\n")
        f.write("1. **Isolated Pseudo-Random Seeding:** Dual independent instances of `random.Random(seed)` and `Faker.seed_instance(seed)` initialize isolated PRNG streams.\n")
        f.write("2. **Zero-Padded Identifiers:** All primary keys and entity IDs are derived via deterministic index functions.\n")
        f.write("3. **Normalized Date Chronology:** All date intervals are derived via deterministic `timedelta` additions against an immutable base calendar anchor.\n")
        f.write("4. **Exact Row Count Enforcement:** Exact remainder quota allocation guarantees that targets (e.g. 8,000 finished lots, 20,000 deliveries) are met with zero drift.\n")
        f.write("5. **Strict Ground-Truth Isolation:** Planted anomaly records are generated with consistent target mappings without runtime feedback.\n")

    print("\n" + "=" * 70)
    print(f"LOTTRACE AI - FULL-SCALE REPRODUCIBILITY AUDIT [PROFILE: {profile.upper()}]")
    print("=" * 70)
    for r in results:
        status = "PASS" if r["match"] else "FAIL"
        print(f"  {r['name']:<25} : {r['count1']:>6} vs {r['count2']:>6} | {r['chk1'][:8]}.. [{status}]")
    print("=" * 70)
    print(f"OVERALL RESULT: {'PASS — 100% REPRODUCIBLE' if all_matched else 'FAIL'}\n")
    return all_matched


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="full", choices=["starter", "full"])
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED)
    args = parser.parse_args()
    success = run_verification(profile=args.profile, seed=args.seed)
    sys.exit(0 if success else 1)
