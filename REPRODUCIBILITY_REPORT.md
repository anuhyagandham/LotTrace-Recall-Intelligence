# LotTrace AI — Full-Scale Reproducibility & Determinism Verification Report

- **Verification Profile:** `FULL`
- **Verification Seed:** `20261022`
- **Verification Date:** `2026-10-31 23:52:43 UTC`
- **Overall Audit Outcome:** `PASS — 100% BITWISE DETERMINISTIC`

## 1. Dual-Pass Full-Scale Entity Checksum Audit

Deterministic SHA-256 checksums were calculated on canonical business attributes, explicitly excluding volatile execution timestamps (`created_at`, `updated_at`, `detected_at`, `last_audit_date`).

| Table / Entity Collection | Pass 1 Count | Pass 2 Count | Pass 1 SHA-256 (Canonical) | Pass 2 SHA-256 (Canonical) | Audit Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Suppliers** | 500 | 500 | `afd3fc363c271015...` | `afd3fc363c271015...` | ✅ PASS (Identical) |
| **Products** | 40 | 40 | `3421b988bedeec90...` | `3421b988bedeec90...` | ✅ PASS (Identical) |
| **BOMs** | 80 | 80 | `a2e7f338d2df8f15...` | `a2e7f338d2df8f15...` | ✅ PASS (Identical) |
| **Raw Material Lots** | 10,000 | 10,000 | `4e251b6fdfcd5458...` | `4e251b6fdfcd5458...` | ✅ PASS (Identical) |
| **Production Orders** | 5,000 | 5,000 | `be398f91a6ae16fd...` | `be398f91a6ae16fd...` | ✅ PASS (Identical) |
| **Production Consumptions** | 20,750 | 20,750 | `d1bc453fe168ef51...` | `d1bc453fe168ef51...` | ✅ PASS (Identical) |
| **Finished Lots** | 8,000 | 8,000 | `8d7b98d5d1f61c90...` | `8d7b98d5d1f61c90...` | ✅ PASS (Identical) |
| **Lot Genealogies** | 33,200 | 33,200 | `647a19defab07c14...` | `647a19defab07c14...` | ✅ PASS (Identical) |
| **Customers** | 1,500 | 1,500 | `f0d59ecaac042905...` | `f0d59ecaac042905...` | ✅ PASS (Identical) |
| **Shipments** | 7,500 | 7,500 | `e232b47753448e25...` | `e232b47753448e25...` | ✅ PASS (Identical) |
| **Shipment Items** | 7,500 | 7,500 | `85c9927b5b025c44...` | `85c9927b5b025c44...` | ✅ PASS (Identical) |
| **Deliveries** | 20,000 | 20,000 | `c27411da78cef4e4...` | `c27411da78cef4e4...` | ✅ PASS (Identical) |
| **Inventories** | 18,000 | 18,000 | `15610371695753d5...` | `15610371695753d5...` | ✅ PASS (Identical) |
| **Inventory Events** | 46,250 | 46,250 | `ebf7a0316d710b91...` | `ebf7a0316d710b91...` | ✅ PASS (Identical) |
| **Recall Cases** | 10 | 10 | `e6c1dcf833941f95...` | `e6c1dcf833941f95...` | ✅ PASS (Identical) |
| **Validation Issues** | 4 | 4 | `739f1e6b3e394bfb...` | `739f1e6b3e394bfb...` | ✅ PASS (Identical) |
| **Ground Truth Records** | 4 | 4 | `76c24dc977ae6fd2...` | `76c24dc977ae6fd2...` | ✅ PASS (Identical) |

## 2. Determinism Verification Methodology

1. **Isolated Pseudo-Random Seeding:** Dual independent instances of `random.Random(seed)` and `Faker.seed_instance(seed)` initialize isolated PRNG streams.
2. **Zero-Padded Identifiers:** All primary keys and entity IDs are derived via deterministic index functions.
3. **Normalized Date Chronology:** All date intervals are derived via deterministic `timedelta` additions against an immutable base calendar anchor.
4. **Exact Row Count Enforcement:** Exact remainder quota allocation guarantees that targets (e.g. 8,000 finished lots, 20,000 deliveries) are met with zero drift.
5. **Strict Ground-Truth Isolation:** Planted anomaly records are generated with consistent target mappings without runtime feedback.
