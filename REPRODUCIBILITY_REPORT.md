# LotTrace AI — Reproducibility & Determinism Verification Report

- **Verification Seed:** `20261022`
- **Verification Timestamp:** `2026-10-31T17:53:45.867810 UTC`
- **Overall Status:** `PASSED — 100% DETERMINISTIC`

## 1. Dual-Pass Dataset Entity Comparison

| Entity / Collection | Pass 1 Count | Pass 2 Count | Content Equivalence | Status |
| :--- | :--- | :--- | :--- | :--- |
| Suppliers | 25 | 25 | 100% Identical | ✅ MATCH |
| Products | 10 | 10 | 100% Identical | ✅ MATCH |
| BOMs | 20 | 20 | 100% Identical | ✅ MATCH |
| Raw Material Lots | 200 | 200 | 100% Identical | ✅ MATCH |
| Production Orders | 100 | 100 | 100% Identical | ✅ MATCH |
| Finished Lots | 150 | 150 | 100% Identical | ✅ MATCH |
| Customers | 50 | 50 | 100% Identical | ✅ MATCH |
| Shipments | 120 | 120 | 100% Identical | ✅ MATCH |
| Deliveries | 360 | 360 | 100% Identical | ✅ MATCH |
| Recall Cases | 3 | 3 | 100% Identical | ✅ MATCH |
| Validation Issues | 4 | 4 | 100% Identical | ✅ MATCH |
| Ground Truth Records | 4 | 4 | 100% Identical | ✅ MATCH |

## 2. Determinism Verification Methodology

1. **Deterministic Random Seeding:** Python's built-in `random.Random(seed)` and `Faker.seed_instance(seed)` initialize independent, isolated RNG streams.
2. **Zero-Padded Identifiers:** All primary keys and business identifiers (`RAWLOT-...`, `WO-...`, `FINLOT-...`, `REC-...`) are strictly derived from deterministic counter functions.
3. **Normalized Chronology:** Generation dates anchor from a fixed calendar base (`2026-01-10T08:00:00`) with deterministic timedelta increments.
4. **Ground-Truth Preservation:** The four planted anomaly scenarios (A, B, C, D) maintain constant entity mappings across generation iterations.
