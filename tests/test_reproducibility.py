"""
Tests for Fixed-Seed Deterministic Reproducibility.
Verifies identical row counts, IDs, and anomaly labels across multiple generator runs.
"""

from src.generator.data_generator import DataGenerator
from config import DEFAULT_RANDOM_SEED


def test_generator_deterministic_reproducibility():
    """Verifies that two independent runs with seed 20261022 generate identical data."""
    def populate(gen):
        gen._generate_suppliers()
        gen._generate_products_and_boms()
        gen._generate_raw_material_lots()
        gen._generate_production_and_genealogy()
        gen._generate_customers()
        gen._generate_distribution_and_deliveries()
        gen._generate_recall_cases()
        gen._plant_anomaly_scenarios()

    gen1 = DataGenerator(profile_name="starter", seed=DEFAULT_RANDOM_SEED)
    gen2 = DataGenerator(profile_name="starter", seed=DEFAULT_RANDOM_SEED)
    populate(gen1)
    populate(gen2)

    # 1. Exact count matches
    assert len(gen1.suppliers) == len(gen2.suppliers)
    assert len(gen1.products) == len(gen2.products)
    assert len(gen1.material_lots) == len(gen2.material_lots)
    assert len(gen1.production_orders) == len(gen2.production_orders)
    assert len(gen1.finished_lots) == len(gen2.finished_lots)
    assert len(gen1.validation_issues) == len(gen2.validation_issues)

    # 2. Exact ID matches across all entities
    assert [s.supplier_id for s in gen1.suppliers] == [s.supplier_id for s in gen2.suppliers]
    assert [l.lot_id for l in gen1.material_lots] == [l.lot_id for l in gen2.material_lots]
    assert [o.order_id for o in gen1.production_orders] == [o.order_id for o in gen2.production_orders]
    assert [f.lot_id for f in gen1.finished_lots] == [f.lot_id for f in gen2.finished_lots]

    # 3. Exact Anomaly Ground-Truth Label matches
    assert [i.ground_truth_label for i in gen1.validation_issues] == [i.ground_truth_label for i in gen2.validation_issues]
