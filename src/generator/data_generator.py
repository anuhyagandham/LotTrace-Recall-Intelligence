"""
Synthetic Data Generator for LotTrace AI.
Generates fully consistent, normalized relational supply chain datasets
for STARTER and FULL profiles with 100% deterministic reproducibility.
"""

import random
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from faker import Faker

from config import (
    PROFILES,
    DatasetProfile,
    DEFAULT_RANDOM_SEED,
    GROUND_TRUTH_CSV,
    GROUND_TRUTH_JSON,
    ensure_directories,
)
from src.utils.logging_config import logger
from src.database.connection import get_db_session, init_db, drop_db, engine
from src.models import (
    Supplier,
    MaterialLot,
    Product,
    BOM,
    BOMMaterial,
    ProductionOrder,
    ProductionConsumption,
    FinishedLot,
    LotGenealogy,
    Shipment,
    ShipmentItem,
    Customer,
    Delivery,
    Inventory,
    InventoryEvent,
    RecallCase,
    RecallAction,
    RecallEvent,
    CustomerNotification,
    ValidationIssue,
    SupplierStatus,
    QualityStatus,
    ProductionOrderStatus,
    ShipmentStatus,
    DeliveryStatus,
    RecallTriggerType,
    RecallSeverity,
    RecallStatus,
    RecallActionType,
    RecallActionStatus,
    NotificationChannel,
    NotificationStatus,
    InventoryEventType,
    ValidationSeverity,
    ValidationStatus,
)
from src.generator.id_generator import (
    generate_supplier_id,
    generate_supplier_code,
    generate_raw_lot_id,
    generate_product_id,
    generate_sku,
    generate_bom_id,
    generate_production_order_id,
    generate_consumption_id,
    generate_finished_lot_id,
    generate_genealogy_id,
    generate_customer_id,
    generate_shipment_id,
    generate_tracking_number,
    generate_shipment_item_id,
    generate_delivery_id,
    generate_inventory_id,
    generate_inventory_event_id,
    generate_recall_case_id,
    generate_recall_action_id,
    generate_recall_event_id,
    generate_customer_notification_id,
    generate_validation_issue_id,
)
from src.generator.distributions import (
    SUPPLIER_CATEGORIES,
    SUPPLIER_PREFIXES,
    SUPPLIER_SUFFIXES,
    MATERIAL_CATALOG,
    PRODUCT_CATALOG,
    WAREHOUSES,
    CARRIERS,
    CUSTOMER_TYPES,
    CUSTOMER_RISK_TIERS,
)


class DataGenerator:
    """Enterprise Supply Chain Synthetic Data Generation Engine."""

    def __init__(self, profile_name: str = "starter", seed: int = DEFAULT_RANDOM_SEED):
        self.profile_name = profile_name
        self.profile: DatasetProfile = PROFILES.get(profile_name, PROFILES["starter"])
        self.seed = seed
        self.rng = random.Random(seed)
        self.faker = Faker()
        self.faker.seed_instance(seed)

        # Baseline generation calendar anchor: Year 2026
        self.base_date = datetime(2026, 1, 10, 8, 0, 0)

        # In-memory tracking for relationship assembly
        self.suppliers: List[Supplier] = []
        self.products: List[Product] = []
        self.boms: List[BOM] = []
        self.material_lots: List[MaterialLot] = []
        self.production_orders: List[ProductionOrder] = []
        self.finished_lots: List[FinishedLot] = []
        self.customers: List[Customer] = []
        self.shipments: List[Shipment] = []
        self.shipment_items: List[ShipmentItem] = []
        self.deliveries: List[Delivery] = []
        self.inventories: List[Inventory] = []
        self.inventory_events: List[InventoryEvent] = []
        self.consumptions: List[ProductionConsumption] = []
        self.genealogies: List[LotGenealogy] = []
        self.recall_cases: List[RecallCase] = []
        self.recall_actions: List[RecallAction] = []
        self.recall_events: List[RecallEvent] = []
        self.customer_notifications: List[CustomerNotification] = []
        self.validation_issues: List[ValidationIssue] = []
        self.inventory_by_lot: Dict[str, Inventory] = {}

        # Ground truth tracking
        self.ground_truth_records: List[Dict[str, Any]] = []

    def run(self, reset_db: bool = True) -> Dict[str, int]:
        """Executes full end-to-end dataset generation."""
        logger.info(f"Starting data generation with profile '{self.profile.name}', seed {self.seed}...")
        ensure_directories()

        if reset_db:
            drop_db()
            init_db()

        self._generate_suppliers()
        self._generate_products_and_boms()
        self._generate_raw_material_lots()
        self._generate_production_and_genealogy()
        self._generate_customers()
        self._generate_distribution_and_deliveries()
        self._generate_recall_cases()
        self._plant_anomaly_scenarios()
        self._export_ground_truth()
        counts = self._persist_to_database()

        logger.info(f"Data generation complete for profile '{self.profile.name}'! Records persisted: {counts}")
        return counts

    def _generate_suppliers(self):
        """Generates approved master suppliers."""
        logger.info(f"Generating {self.profile.num_suppliers} suppliers...")
        countries = ["USA", "Germany", "Switzerland", "Japan", "India", "Canada", "Ireland", "France"]

        for i in range(1, self.profile.num_suppliers + 1):
            supplier_id = generate_supplier_id(i)
            supplier_code = generate_supplier_code(i)
            prefix = self.rng.choice(SUPPLIER_PREFIXES)
            suffix = self.rng.choice(SUPPLIER_SUFFIXES)
            name = f"{prefix} {suffix} #{i}"
            category = self.rng.choice(SUPPLIER_CATEGORIES)
            email = f"quality@{prefix.lower()}{i}.com"
            phone = f"+1-{self.rng.randint(200, 999)}-555-{self.rng.randint(1000, 9999)}"
            country = self.rng.choice(countries)

            created_date = self.base_date - timedelta(days=self.rng.randint(100, 365))
            supplier = Supplier(
                supplier_id=supplier_id,
                supplier_code=supplier_code,
                name=name,
                category=category,
                contact_email=email,
                contact_phone=phone,
                address=f"{self.rng.randint(100, 9999)} Industrial Parkway",
                country=country,
                status=SupplierStatus.ACTIVE.value,
                created_at=created_date,
                updated_at=created_date,
            )
            self.suppliers.append(supplier)

    def _generate_products_and_boms(self):
        """Generates product catalog and corresponding BOM versions."""
        logger.info(f"Generating {self.profile.num_products} products and BOMs...")
        catalog_len = len(PRODUCT_CATALOG)

        for i in range(1, self.profile.num_products + 1):
            prod_template = PRODUCT_CATALOG[(i - 1) % catalog_len]
            product_id = generate_product_id(i)
            sku = f"SKU-{prod_template['sku'].split('-')[1]}-{i:04d}"
            name = f"{prod_template['name']} [Batch Series {i}]"
            category = prod_template["category"]
            uom = prod_template["uom"]
            shelf_life = prod_template["shelf_life_days"]
            std_cost = prod_template["standard_cost"]

            created_date = self.base_date - timedelta(days=self.rng.randint(90, 200))
            product = Product(
                product_id=product_id,
                sku=sku,
                product_name=name,
                category=category,
                unit_of_measure=uom,
                shelf_life_days=shelf_life,
                standard_cost=std_cost,
                is_active=True,
                created_at=created_date,
                updated_at=created_date,
            )
            self.products.append(product)

            # Generate BOM versions for this product
            boms_templates = prod_template.get("boms", [])
            for b_idx in range(1, self.profile.num_boms_per_product + 1):
                bom_template = boms_templates[(b_idx - 1) % len(boms_templates)]
                bom_id = generate_bom_id(product_id, b_idx)
                eff_from = created_date + timedelta(days=(b_idx - 1) * 60)
                eff_to = eff_from + timedelta(days=365) if b_idx < self.profile.num_boms_per_product else None

                bom = BOM(
                    bom_id=bom_id,
                    product_id=product_id,
                    version=f"v{b_idx}.0",
                    effective_from=eff_from,
                    effective_to=eff_to,
                    is_active=True,
                    yield_percentage=bom_template["yield"],
                    created_at=eff_from,
                    updated_at=eff_from,
                )
                self.boms.append(bom)

                # Materials for this BOM
                for mat_spec in bom_template["materials"]:
                    bom_mat = BOMMaterial(
                        bom_id=bom_id,
                        material_category=mat_spec["category"],
                        material_name=mat_spec["name"],
                        required_quantity=mat_spec["qty"],
                        unit_of_measure=mat_spec["uom"],
                        is_mandatory=True,
                        created_at=eff_from,
                    )
                    bom.materials.append(bom_mat)

    def _generate_raw_material_lots(self):
        """Generates raw material receipts and populates initial inventory."""
        logger.info(f"Generating {self.profile.num_raw_lots} raw material lots...")
        categories = list(MATERIAL_CATALOG.keys())

        inv_counter = 1
        inv_evt_counter = 1

        for i in range(1, self.profile.num_raw_lots + 1):
            supplier = self.suppliers[(i - 1) % len(self.suppliers)]
            category = categories[(i - 1) % len(categories)]
            catalog_items = MATERIAL_CATALOG[category]
            mat_item = catalog_items[(i - 1) % len(catalog_items)]

            lot_id = generate_raw_lot_id(supplier.supplier_id, i)
            received_date = self.base_date + timedelta(days=self.rng.randint(1, 45))
            expiry_date = received_date + timedelta(days=mat_item["shelf_life_days"])

            # Variable realistic quantities
            base_qty = 500.0 if mat_item["uom"] == "KG" else (1000.0 if mat_item["uom"] == "L" else 5000.0)
            initial_qty = round(base_qty * self.rng.uniform(0.8, 1.5), 2)

            raw_lot = MaterialLot(
                lot_id=lot_id,
                supplier_id=supplier.supplier_id,
                material_name=mat_item["name"],
                material_category=category,
                received_date=received_date,
                expiry_date=expiry_date,
                initial_quantity=initial_qty,
                current_quantity=initial_qty,  # Will be deducted during production consumption
                unit_of_measure=mat_item["uom"],
                unit_cost=mat_item["cost"],
                quality_status=QualityStatus.RELEASED.value,
                is_contaminated=False,
                created_at=received_date,
                updated_at=received_date,
            )
            self.material_lots.append(raw_lot)

            # Assign warehouse inventory
            warehouse = self.rng.choice(WAREHOUSES)
            bin_id = f"BIN-RAW-{category[:3]}-{self.rng.randint(10, 99)}"
            inv_id = generate_inventory_id(inv_counter)
            inv_counter += 1

            inventory = Inventory(
                inventory_id=inv_id,
                lot_id=lot_id,
                lot_type="RAW",
                warehouse_id=warehouse["id"],
                location_bin=bin_id,
                quantity_on_hand=initial_qty,
                quantity_reserved=0.0,
                quantity_quarantined=0.0,
                status="AVAILABLE",
                last_audit_date=received_date,
                created_at=received_date,
                updated_at=received_date,
            )
            self.inventories.append(inventory)
            self.inventory_by_lot[lot_id] = inventory

            # Record receipt inventory event
            inv_evt = InventoryEvent(
                event_id=generate_inventory_event_id(inv_evt_counter),
                inventory_id=inv_id,
                lot_id=lot_id,
                event_type=InventoryEventType.RECEIPT.value,
                quantity_change=initial_qty,
                resulting_balance=initial_qty,
                reference_type="PO_RECEIPT",
                reference_id=f"PO-{supplier.supplier_id}-{i:04d}",
                event_date=received_date,
                notes=f"Initial receiving inspection passed for {mat_item['name']}",
                created_at=received_date,
            )
            inv_evt_counter += 1
            self.inventory_events.append(inv_evt)

    def _generate_production_and_genealogy(self):
        """
        Executes production consumption, yield reconciliation, finished lot output,
        and genealogy graph creation.
        """
        logger.info(f"Generating {self.profile.num_production_orders} production orders and {self.profile.num_finished_lots} finished lots...")

        consumption_counter = 1
        genealogy_counter = 1
        inv_counter = len(self.inventories) + 1
        inv_evt_counter = len(self.inventory_events) + 1

        # Group raw material lots by category for consumption matching
        raw_lots_by_cat: Dict[str, List[MaterialLot]] = {}
        for r_lot in self.material_lots:
            raw_lots_by_cat.setdefault(r_lot.material_category, []).append(r_lot)

        orders_count = self.profile.num_production_orders
        finished_lots_count = self.profile.num_finished_lots

        # Each order produces 1 to 2 finished lots
        lots_per_order = max(1, finished_lots_count // orders_count)

        fin_lot_idx = 1
        for wo_idx in range(1, orders_count + 1):
            product = self.products[(wo_idx - 1) % len(self.products)]
            # Find an active BOM for this product
            product_boms = [b for b in self.boms if b.product_id == product.product_id]
            bom = product_boms[(wo_idx - 1) % len(product_boms)]

            order_id = generate_production_order_id(wo_idx)
            order_date = self.base_date + timedelta(days=self.rng.randint(20, 70))
            start_date = order_date + timedelta(days=1)
            completion_date = start_date + timedelta(days=2)

            planned_qty = round(float(self.rng.randint(200, 1000)), 2)
            actual_yield = bom.yield_percentage * self.rng.uniform(0.98, 1.01)
            produced_qty = round(planned_qty * (actual_yield / 100.0), 2)
            scrap_qty = round(planned_qty - produced_qty if planned_qty > produced_qty else 0.0, 2)

            production_order = ProductionOrder(
                order_id=order_id,
                bom_id=bom.bom_id,
                product_id=product.product_id,
                order_date=order_date,
                start_date=start_date,
                completion_date=completion_date,
                planned_quantity=planned_qty,
                produced_quantity=produced_qty,
                scrap_quantity=scrap_qty,
                status=ProductionOrderStatus.COMPLETED.value,
                created_at=order_date,
                updated_at=completion_date,
            )
            self.production_orders.append(production_order)

            # Consume raw materials required by BOM
            consumed_raw_lots_for_order: List[MaterialLot] = []
            for b_mat in bom.materials:
                available_lots = raw_lots_by_cat.get(b_mat.material_category, [])
                if not available_lots:
                    continue

                # Select 1 or 2 lots to satisfy consumption
                req_qty = round(b_mat.required_quantity * planned_qty, 2)
                selected_lot = available_lots[(wo_idx + consumption_counter) % len(available_lots)]

                # Deduct from raw lot
                actual_consumed = min(selected_lot.current_quantity, req_qty)
                if actual_consumed <= 0:
                    actual_consumed = req_qty  # maintain required consumption accounting

                selected_lot.current_quantity = max(0.0, round(selected_lot.current_quantity - actual_consumed, 2))

                consumption = ProductionConsumption(
                    consumption_id=generate_consumption_id(consumption_counter),
                    production_order_id=order_id,
                    material_lot_id=selected_lot.lot_id,
                    quantity_consumed=actual_consumed,
                    unit_of_measure=b_mat.unit_of_measure,
                    consumption_date=start_date,
                    created_at=start_date,
                )
                consumption_counter += 1
                self.consumptions.append(consumption)
                consumed_raw_lots_for_order.append(selected_lot)

                # Record consumption inventory event
                raw_inv = self.inventory_by_lot.get(selected_lot.lot_id)
                raw_inv_id = raw_inv.inventory_id if raw_inv else inv_counter
                raw_inv_evt = InventoryEvent(
                    event_id=generate_inventory_event_id(inv_evt_counter),
                    inventory_id=raw_inv_id,
                    lot_id=selected_lot.lot_id,
                    event_type=InventoryEventType.PRODUCTION_CONSUMPTION.value,
                    quantity_change=-actual_consumed,
                    resulting_balance=selected_lot.current_quantity,
                    reference_type="WORK_ORDER",
                    reference_id=order_id,
                    event_date=start_date,
                    notes=f"Consumed {actual_consumed} {b_mat.unit_of_measure} for WO {order_id}",
                    created_at=start_date,
                )
                inv_evt_counter += 1
                self.inventory_events.append(raw_inv_evt)

            # Generate Finished Lots for this work order
            num_lots_for_this_wo = 1
            if fin_lot_idx < finished_lots_count and (finished_lots_count - fin_lot_idx) > (orders_count - wo_idx):
                num_lots_for_this_wo = min(2, finished_lots_count - fin_lot_idx + 1)

            qty_per_lot = round(produced_qty / num_lots_for_this_wo, 2)

            for _ in range(num_lots_for_this_wo):
                if fin_lot_idx > finished_lots_count:
                    break

                fin_lot_id = generate_finished_lot_id(fin_lot_idx)
                mfg_date = completion_date
                exp_date = mfg_date + timedelta(days=product.shelf_life_days)

                fin_lot = FinishedLot(
                    lot_id=fin_lot_id,
                    production_order_id=order_id,
                    product_id=product.product_id,
                    manufactured_date=mfg_date,
                    expiry_date=exp_date,
                    quantity_produced=qty_per_lot,
                    quantity_available=qty_per_lot,  # Will be decremented by shipments
                    unit_of_measure=product.unit_of_measure,
                    quality_status=QualityStatus.RELEASED.value,
                    is_contaminated=False,
                    created_at=mfg_date,
                    updated_at=mfg_date,
                )
                self.finished_lots.append(fin_lot)

                # Record Lot Genealogy linking all consumed raw lots to this finished lot
                for c_raw_lot in consumed_raw_lots_for_order:
                    genealogy = LotGenealogy(
                        genealogy_id=generate_genealogy_id(genealogy_counter),
                        raw_lot_id=c_raw_lot.lot_id,
                        finished_lot_id=fin_lot_id,
                        production_order_id=order_id,
                        relationship_type="DIRECT_CONSUMPTION",
                        depth_level=1,
                        created_at=mfg_date,
                    )
                    genealogy_counter += 1
                    self.genealogies.append(genealogy)

                # Finished Goods Inventory
                warehouse = self.rng.choice(WAREHOUSES)
                bin_id = f"BIN-FIN-{product.category[:3]}-{self.rng.randint(100, 999)}"
                fin_inv_id = generate_inventory_id(inv_counter)
                inv_counter += 1

                fin_inventory = Inventory(
                    inventory_id=fin_inv_id,
                    lot_id=fin_lot_id,
                    lot_type="FINISHED",
                    warehouse_id=warehouse["id"],
                    location_bin=bin_id,
                    quantity_on_hand=qty_per_lot,
                    quantity_reserved=0.0,
                    quantity_quarantined=0.0,
                    status="AVAILABLE",
                    last_audit_date=mfg_date,
                    created_at=mfg_date,
                    updated_at=mfg_date,
                )
                self.inventories.append(fin_inventory)
                self.inventory_by_lot[fin_lot_id] = fin_inventory

                # Inventory Event for production output
                fin_inv_evt = InventoryEvent(
                    event_id=generate_inventory_event_id(inv_evt_counter),
                    inventory_id=fin_inv_id,
                    lot_id=fin_lot_id,
                    event_type=InventoryEventType.PRODUCTION_OUTPUT.value,
                    quantity_change=qty_per_lot,
                    resulting_balance=qty_per_lot,
                    reference_type="WORK_ORDER",
                    reference_id=order_id,
                    event_date=mfg_date,
                    notes=f"Production output receipt of {qty_per_lot} {product.unit_of_measure}",
                    created_at=mfg_date,
                )
                inv_evt_counter += 1
                self.inventory_events.append(fin_inv_evt)

                fin_lot_idx += 1

    def _generate_customers(self):
        """Generates customer accounts across risk tiers and healthcare verticals."""
        logger.info(f"Generating {self.profile.num_customers} customers...")
        cities_states = [
            ("New York", "NY"), ("Boston", "MA"), ("Philadelphia", "PA"),
            ("Chicago", "IL"), ("Minneapolis", "MN"), ("Cleveland", "OH"),
            ("Dallas", "TX"), ("Houston", "TX"), ("Atlanta", "GA"),
            ("Los Angeles", "CA"), ("San Francisco", "CA"), ("Seattle", "WA"),
            ("Denver", "CO"), ("Phoenix", "AZ"), ("Miami", "FL"),
        ]

        for i in range(1, self.profile.num_customers + 1):
            customer_id = generate_customer_id(i)
            cust_type = self.rng.choice(CUSTOMER_TYPES)
            risk_tier = self.rng.choice(CUSTOMER_RISK_TIERS)
            city, state = self.rng.choice(cities_states)
            name_suffix = cust_type.replace("_", " ").title()
            name = f"{city} {name_suffix} #{i}"
            email = f"procurement@client-{i:04d}.org"
            phone = f"+1-{self.rng.randint(200, 999)}-555-{self.rng.randint(1000, 9999)}"

            created_date = self.base_date - timedelta(days=self.rng.randint(60, 180))
            customer = Customer(
                customer_id=customer_id,
                customer_name=name,
                customer_type=cust_type,
                contact_email=email,
                contact_phone=phone,
                city=city,
                state=state,
                country="USA",
                risk_tier=risk_tier,
                created_at=created_date,
                updated_at=created_date,
            )
            self.customers.append(customer)

    def _generate_distribution_and_deliveries(self):
        """Generates shipments, shipment items, and deliveries to customers."""
        logger.info(f"Generating {self.profile.num_shipments} shipments and {self.profile.num_deliveries} deliveries...")

        shp_item_counter = 1
        delivery_counter = 1
        inv_evt_counter = len(self.inventory_events) + 1

        shipments_count = self.profile.num_shipments
        deliveries_count = self.profile.num_deliveries

        deliveries_per_shipment = max(1, deliveries_count // shipments_count)

        del_idx = 1
        for shp_idx in range(1, shipments_count + 1):
            shipment_id = generate_shipment_id(shp_idx)
            tracking_num = generate_tracking_number(shp_idx)
            ship_date = self.base_date + timedelta(days=self.rng.randint(50, 120))
            carrier = self.rng.choice(CARRIERS)
            warehouse = self.rng.choice(WAREHOUSES)
            region = self.rng.choice(["NorthEast", "MidWest", "SouthEast", "SouthWest", "PacificWest"])

            shipment = Shipment(
                shipment_id=shipment_id,
                tracking_number=tracking_num,
                ship_date=ship_date,
                carrier=carrier,
                status=ShipmentStatus.DELIVERED.value,
                origin_warehouse=warehouse["id"],
                destination_region=region,
                created_at=ship_date,
                updated_at=ship_date,
            )
            self.shipments.append(shipment)

            # Pick 1 to 3 finished lots for this shipment
            fin_lot = self.finished_lots[(shp_idx - 1) % len(self.finished_lots)]
            # Allocate portion of available quantity
            ship_qty = round(min(fin_lot.quantity_available, fin_lot.quantity_produced * 0.4), 2)
            if ship_qty <= 0:
                ship_qty = round(fin_lot.quantity_produced * 0.25, 2)

            fin_lot.quantity_available = max(0.0, round(fin_lot.quantity_available - ship_qty, 2))

            # Update inventory on hand
            for inv in self.inventories:
                if inv.lot_id == fin_lot.lot_id:
                    inv.quantity_on_hand = max(0.0, round(inv.quantity_on_hand - ship_qty, 2))
                    break

            shipment_item = ShipmentItem(
                item_id=generate_shipment_item_id(shp_item_counter),
                shipment_id=shipment_id,
                finished_lot_id=fin_lot.lot_id,
                quantity_shipped=ship_qty,
                unit_of_measure=fin_lot.unit_of_measure,
                created_at=ship_date,
            )
            shp_item_counter += 1
            self.shipment_items.append(shipment_item)

            # Dispatch inventory event
            fin_inv = self.inventory_by_lot.get(fin_lot.lot_id)
            fin_inv_id = fin_inv.inventory_id if fin_inv else self.inventories[0].inventory_id
            inv_evt = InventoryEvent(
                event_id=generate_inventory_event_id(inv_evt_counter),
                inventory_id=fin_inv_id,
                lot_id=fin_lot.lot_id,
                event_type=InventoryEventType.SHIPMENT_DISPATCH.value,
                quantity_change=-ship_qty,
                resulting_balance=fin_lot.quantity_available,
                reference_type="SHIPMENT",
                reference_id=shipment_id,
                event_date=ship_date,
                notes=f"Dispatched {ship_qty} {fin_lot.unit_of_measure} under {shipment_id}",
                created_at=ship_date,
            )
            inv_evt_counter += 1
            self.inventory_events.append(inv_evt)

            # Generate Deliveries for this shipment
            deliveries_for_shp = deliveries_per_shipment
            if del_idx < deliveries_count and (deliveries_count - del_idx) > (shipments_count - shp_idx):
                deliveries_for_shp = min(3, deliveries_count - del_idx + 1)

            qty_per_del = round(ship_qty / deliveries_for_shp, 2)

            for _ in range(deliveries_for_shp):
                if del_idx > deliveries_count:
                    break

                customer = self.customers[(del_idx - 1) % len(self.customers)]
                del_id = generate_delivery_id(del_idx)
                del_date = ship_date + timedelta(days=self.rng.randint(1, 4))

                delivery = Delivery(
                    delivery_id=del_id,
                    shipment_id=shipment_id,
                    customer_id=customer.customer_id,
                    delivery_date=del_date,
                    status=DeliveryStatus.DELIVERED.value,
                    received_by=f"Dr. {self.faker.last_name()} / Receiving Dock",
                    quantity_delivered=qty_per_del,
                    created_at=del_date,
                    updated_at=del_date,
                )
                self.deliveries.append(delivery)
                del_idx += 1

    def _generate_recall_cases(self):
        """Generates realistic recall cases and populates initial event log."""
        logger.info(f"Generating {self.profile.num_recall_cases} baseline recall cases...")

        for r_idx in range(1, self.profile.num_recall_cases + 1):
            recall_id = generate_recall_case_id(r_idx)
            # Alternate between Raw Lot trigger and Finished Lot trigger
            is_raw_trigger = (r_idx % 2 == 1)

            if is_raw_trigger:
                source_lot = self.material_lots[(r_idx - 1) % len(self.material_lots)]
                source_lot.is_contaminated = True
                source_lot.quality_status = QualityStatus.CONTAMINATED.value
                source_id = source_lot.lot_id
                source_type = "RAW"
                title = f"Class I Recall: Bacterial Endotoxin Contamination in {source_lot.material_name}"
                trigger_type = RecallTriggerType.CONTAMINATED_RAW_LOT.value
            else:
                fin_source = self.finished_lots[(r_idx - 1) % len(self.finished_lots)]
                fin_source.is_contaminated = True
                fin_source.quality_status = QualityStatus.CONTAMINATED.value
                source_id = fin_source.lot_id
                source_type = "FINISHED"
                title = f"Class II Recall: Dissolution Specification Failure in Lot {fin_source.lot_id}"
                trigger_type = RecallTriggerType.CONTAMINATED_FINISHED_LOT.value

            init_date = self.base_date + timedelta(days=80 + r_idx * 5)
            target_date = init_date + timedelta(days=30)

            recall = RecallCase(
                recall_id=recall_id,
                title=title,
                trigger_type=trigger_type,
                source_lot_id=source_id,
                source_lot_type=source_type,
                severity=RecallSeverity.CLASS_I.value if is_raw_trigger else RecallSeverity.CLASS_II.value,
                initiated_date=init_date,
                target_completion_date=target_date,
                status=RecallStatus.OPEN.value,
                closure_date=None,
                total_affected_finished_lots=0,
                total_affected_deliveries=0,
                total_affected_customers=0,
                total_recalled_quantity=0.0,
                total_quarantined_quantity=0.0,
                total_recovered_quantity=0.0,
                notification_coverage_pct=0.0,
                recovery_rate_pct=0.0,
                recall_completion_pct=0.0,
                created_at=init_date,
                updated_at=init_date,
            )
            self.recall_cases.append(recall)

            # Record initial RecallEvent
            r_event = RecallEvent(
                event_id=generate_recall_event_id(r_idx),
                recall_id=recall_id,
                previous_status="NONE",
                new_status=RecallStatus.OPEN.value,
                reason=f"Recall initiated following confirmed {trigger_type} for lot {source_id}",
                trigger_source="QUALITY_AUDIT",
                created_at=init_date,
            )
            self.recall_events.append(r_event)

    def _plant_anomaly_scenarios(self):
        """
        Plants the four required deliberate, labelled negative scenarios (Section 9):
        A: Missing input lot
        B: Delivered quantity exceeds produced quantity
        C: Recall misses a downstream customer
        D: Recalled inventory remains available for sale
        """
        logger.info("Planting four controlled, labelled anomaly scenarios...")

        # -------------------------------------------------------------
        # Scenario A: MISSING INPUT LOT
        # A finished lot references a non-existent input material lot in validation audit
        # -------------------------------------------------------------
        target_fin_lot_a = self.finished_lots[0].lot_id
        non_existent_raw_lot = "RAWLOT-SUP-9999-2026-999999"

        anomaly_a = ValidationIssue(
            validation_id=generate_validation_issue_id(1),
            entity_name="FinishedLot",
            entity_id=target_fin_lot_a,
            issue_type="MISSING_INPUT_LOT",
            severity=ValidationSeverity.CRITICAL.value,
            expected_value="Verified upstream MaterialLot in database",
            actual_value=non_existent_raw_lot,
            validation_status=ValidationStatus.FAILED.value,
            detected_at=self.base_date + timedelta(days=95),
            ground_truth_label="ANOMALY_A_MISSING_INPUT_LOT",
        )
        self.validation_issues.append(anomaly_a)

        self.ground_truth_records.append({
            "scenario": "SCENARIO_A",
            "issue_type": "MISSING_INPUT_LOT",
            "ground_truth_label": "ANOMALY_A_MISSING_INPUT_LOT",
            "affected_entity_type": "FinishedLot",
            "affected_entity_id": target_fin_lot_a,
            "expected_business_decision": "Quarantine finished lot and reject release certification due to broken BOM traceability",
            "severity": "CRITICAL",
            "expected_outcome": "REJECTED_GENEALOGY",
            "notes": f"Finished lot {target_fin_lot_a} references phantom raw lot {non_existent_raw_lot}"
        })

        # -------------------------------------------------------------
        # Scenario B: DELIVERED QUANTITY EXCEEDS PRODUCED QUANTITY
        # Delivered quantity exceeds produced quantity for a finished lot
        # -------------------------------------------------------------
        target_fin_lot_b = self.finished_lots[1]
        excess_qty = target_fin_lot_b.quantity_produced + 500.0

        # Find delivery linked to this finished lot
        matching_del = self.deliveries[0]
        original_del_qty = matching_del.quantity_delivered
        matching_del.quantity_delivered = excess_qty

        anomaly_b = ValidationIssue(
            validation_id=generate_validation_issue_id(2),
            entity_name="Delivery",
            entity_id=matching_del.delivery_id,
            issue_type="DELIVERED_EXCEEDS_PRODUCED",
            severity=ValidationSeverity.CRITICAL.value,
            expected_value=f"Delivery quantity <= produced {target_fin_lot_b.quantity_produced}",
            actual_value=f"Delivered quantity {excess_qty}",
            validation_status=ValidationStatus.FAILED.value,
            detected_at=self.base_date + timedelta(days=96),
            ground_truth_label="ANOMALY_B_DELIVERY_EXCEEDS_PRODUCED",
        )
        self.validation_issues.append(anomaly_b)

        self.ground_truth_records.append({
            "scenario": "SCENARIO_B",
            "issue_type": "DELIVERED_EXCEEDS_PRODUCED",
            "ground_truth_label": "ANOMALY_B_DELIVERY_EXCEEDS_PRODUCED",
            "affected_entity_type": "Delivery",
            "affected_entity_id": matching_del.delivery_id,
            "expected_business_decision": "Halt invoice reconciliation, audit physical warehouse stock count and counterfeit investigation",
            "severity": "CRITICAL",
            "expected_outcome": "RECONCILIATION_EXCEPTION",
            "notes": f"Delivery {matching_del.delivery_id} logged {excess_qty} units against batch production of {target_fin_lot_b.quantity_produced}"
        })

        # -------------------------------------------------------------
        # Scenario C: RECALL MISSES A DOWNSTREAM CUSTOMER
        # One affected downstream customer is intentionally omitted from the initial notification set
        # -------------------------------------------------------------
        target_recall = self.recall_cases[0]
        # Identify an affected customer via deliveries
        omitted_customer = self.customers[0]
        omitted_delivery = self.deliveries[0]

        anomaly_c = ValidationIssue(
            validation_id=generate_validation_issue_id(3),
            entity_name="CustomerNotification",
            entity_id=omitted_customer.customer_id,
            issue_type="MISSED_CUSTOMER_NOTIFICATION",
            severity=ValidationSeverity.HIGH.value,
            expected_value=f"CustomerNotification dispatched for delivery {omitted_delivery.delivery_id}",
            actual_value="No notification record found in customer notification ledger",
            validation_status=ValidationStatus.FAILED.value,
            detected_at=self.base_date + timedelta(days=97),
            ground_truth_label="ANOMALY_C_MISSED_CUSTOMER_NOTIFICATION",
        )
        self.validation_issues.append(anomaly_c)

        self.ground_truth_records.append({
            "scenario": "SCENARIO_C",
            "issue_type": "MISSED_CUSTOMER_NOTIFICATION",
            "ground_truth_label": "ANOMALY_C_MISSED_CUSTOMER_NOTIFICATION",
            "affected_entity_type": "Customer",
            "affected_entity_id": omitted_customer.customer_id,
            "expected_business_decision": "Recall engine must independently discover customer through downstream delivery graph and emit high-priority escalation notice",
            "severity": "HIGH",
            "expected_outcome": "DISCOVERED_BY_AUDIT",
            "notes": f"Customer {omitted_customer.customer_id} received recalled lot but was omitted from initial notification set"
        })

        # -------------------------------------------------------------
        # Scenario D: RECALLED INVENTORY REMAINS AVAILABLE FOR SALE
        # Affected stock remains in AVAILABLE status after recall initiation
        # -------------------------------------------------------------
        recalled_fin_lot = self.finished_lots[2]
        recalled_fin_lot.is_contaminated = True
        recalled_fin_lot.quality_status = QualityStatus.CONTAMINATED.value

        # Keep corresponding inventory available
        target_inventory = None
        for inv in self.inventories:
            if inv.lot_id == recalled_fin_lot.lot_id:
                inv.status = "AVAILABLE"  # Deliberate violation: should be QUARANTINED
                inv.quantity_quarantined = 0.0
                target_inventory = inv
                break

        anomaly_d = ValidationIssue(
            validation_id=generate_validation_issue_id(4),
            entity_name="Inventory",
            entity_id=target_inventory.inventory_id if target_inventory else "INV-FIN-000003",
            issue_type="RECALLED_INVENTORY_AVAILABLE_FOR_SALE",
            severity=ValidationSeverity.CRITICAL.value,
            expected_value="Inventory status = QUARANTINED, quantity_quarantined > 0",
            actual_value=f"Inventory status = {target_inventory.status if target_inventory else 'AVAILABLE'}, quarantined = 0.0",
            validation_status=ValidationStatus.FAILED.value,
            detected_at=self.base_date + timedelta(days=98),
            ground_truth_label="ANOMALY_D_RECALLED_STOCK_SALEABLE",
        )
        self.validation_issues.append(anomaly_d)

        self.ground_truth_records.append({
            "scenario": "SCENARIO_D",
            "issue_type": "RECALLED_INVENTORY_AVAILABLE_FOR_SALE",
            "ground_truth_label": "ANOMALY_D_RECALLED_STOCK_SALEABLE",
            "affected_entity_type": "Inventory",
            "affected_entity_id": target_inventory.inventory_id if target_inventory else "INV-FIN-000003",
            "expected_business_decision": "Execute automated ERP inventory hold: lock bin location and set status to QUARANTINED immediately",
            "severity": "CRITICAL",
            "expected_outcome": "SECURITY_VIOLATION_BLOCKED",
            "notes": f"Contaminated lot {recalled_fin_lot.lot_id} had warehouse stock flagged as AVAILABLE"
        })

    def _export_ground_truth(self):
        """Exports ground-truth reference files to CSV and JSON."""
        logger.info(f"Writing ground truth to {GROUND_TRUTH_CSV} and {GROUND_TRUTH_JSON}...")

        # Add recall case expectations to ground truth
        for recall in self.recall_cases:
            self.ground_truth_records.append({
                "scenario": "BASELINE_RECALL",
                "issue_type": "PRODUCT_RECALL_MANDATE",
                "ground_truth_label": f"GROUND_TRUTH_{recall.recall_id}",
                "affected_entity_type": "RecallCase",
                "affected_entity_id": recall.recall_id,
                "expected_business_decision": "Traverse complete upstream/downstream genealogy, quarantine warehouse inventory, and notify 100% of affected customers",
                "severity": recall.severity,
                "expected_outcome": "COMPLETE_CONTAINMENT",
                "notes": f"Source lot {recall.source_lot_id} ({recall.source_lot_type}) requires complete traceability traversal"
            })

        # Write CSV
        if self.ground_truth_records:
            fieldnames = list(self.ground_truth_records[0].keys())
            with open(GROUND_TRUTH_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.ground_truth_records)

        # Write JSON
        with open(GROUND_TRUTH_JSON, "w", encoding="utf-8") as f:
            json.dump({
                "profile": self.profile.name,
                "seed": self.seed,
                "records_count": len(self.ground_truth_records),
                "generated_at": datetime.utcnow().isoformat(),
                "ground_truth": self.ground_truth_records,
            }, f, indent=2)

    def _persist_to_database(self) -> Dict[str, int]:
        """Persists all generated entity collections to SQLite via SQLAlchemy transactional session."""
        logger.info("Persisting entities to database...")

        counts = {}
        with get_db_session() as session:
            # 1. Suppliers
            session.add_all(self.suppliers)
            session.flush()
            counts["suppliers"] = len(self.suppliers)

            # 2. Products
            session.add_all(self.products)
            session.flush()
            counts["products"] = len(self.products)

            # 3. BOMs
            session.add_all(self.boms)
            session.flush()
            counts["boms"] = len(self.boms)

            # 4. Raw Material Lots
            session.add_all(self.material_lots)
            session.flush()
            counts["material_lots"] = len(self.material_lots)

            # 5. Production Orders
            session.add_all(self.production_orders)
            session.flush()
            counts["production_orders"] = len(self.production_orders)

            # 6. Production Consumptions
            session.add_all(self.consumptions)
            session.flush()
            counts["production_consumptions"] = len(self.consumptions)

            # 7. Finished Lots
            session.add_all(self.finished_lots)
            session.flush()
            counts["finished_lots"] = len(self.finished_lots)

            # 8. Lot Genealogy
            session.add_all(self.genealogies)
            session.flush()
            counts["lot_genealogies"] = len(self.genealogies)

            # 9. Customers
            session.add_all(self.customers)
            session.flush()
            counts["customers"] = len(self.customers)

            # 10. Shipments
            session.add_all(self.shipments)
            session.flush()
            counts["shipments"] = len(self.shipments)

            # 11. Shipment Items
            session.add_all(self.shipment_items)
            session.flush()
            counts["shipment_items"] = len(self.shipment_items)

            # 12. Deliveries
            session.add_all(self.deliveries)
            session.flush()
            counts["deliveries"] = len(self.deliveries)

            # 13. Inventories
            session.add_all(self.inventories)
            session.flush()
            counts["inventories"] = len(self.inventories)

            # 14. Inventory Events
            session.add_all(self.inventory_events)
            session.flush()
            counts["inventory_events"] = len(self.inventory_events)

            # 15. Recall Cases
            session.add_all(self.recall_cases)
            session.flush()
            counts["recall_cases"] = len(self.recall_cases)

            # 16. Recall Events
            session.add_all(self.recall_events)
            session.flush()
            counts["recall_events"] = len(self.recall_events)

            # 17. Validation Issues
            session.add_all(self.validation_issues)
            session.flush()
            counts["validation_issues"] = len(self.validation_issues)

        return counts
