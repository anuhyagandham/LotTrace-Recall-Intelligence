# LotTrace AI — Enterprise Data Dictionary

## 1. Overview & Data Model Cardinalities

LotTrace AI models an end-to-end pharmaceutical and manufacturing supply chain traceability graph across 20 normalized relational tables:
- **Core Master & Transactional Entities (11):** `suppliers`, `material_lots`, `products`, `boms`, `production_orders`, `finished_lots`, `shipments`, `customers`, `deliveries`, `recall_cases`, `recall_actions`.
- **Bridge, Event-History & Audit Tables (9):** `bom_materials`, `production_consumptions`, `shipment_items`, `lot_genealogies`, `inventories`, `inventory_events`, `recall_events`, `customer_notifications`, `validation_issues`.

### Relationship Cardinalities
- `Supplier` 1 ──< N `MaterialLot`
- `Product` 1 ──< N `BOM` (versioned by `effective_from` / `effective_to`)
- `BOM` 1 ──< N `BOMMaterial`
- `Product` 1 ──< N `ProductionOrder`
- `BOM` 1 ──< N `ProductionOrder`
- `ProductionOrder` 1 ──< N `ProductionConsumption` >── 1 `MaterialLot`
- `ProductionOrder` 1 ──< N `FinishedLot`
- `MaterialLot` 1 ──< N `LotGenealogy` >── 1 `FinishedLot`
- `Shipment` 1 ──< N `ShipmentItem` >── 1 `FinishedLot`
- `Shipment` 1 ──< N `Delivery` >── 1 `Customer`
- `Inventory` 1 ──< N `InventoryEvent`
- `RecallCase` 1 ──< N `RecallAction`
- `RecallCase` 1 ──< N `RecallEvent`
- `RecallCase` 1 ──< N `CustomerNotification` >── 1 `Customer`

---

## 2. Comprehensive Field Specifications

### 2.1 Table: `suppliers`
Master catalog of qualified active pharmaceutical ingredient (API), excipient, and packaging vendors.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `supplier_id` | VARCHAR(50) | No | Primary Key | None | `SUP-0001` .. `SUP-9999` | Format `SUP-XXXX` | Unique system identifier for vendor |
| `supplier_code` | VARCHAR(50) | No | Unique | None | `VENDOR-0001` .. | Alphanumeric unique code | ERP vendor master ledger code |
| `name` | VARCHAR(255) | No | No | None | Text | Non-empty | Registered legal entity name of vendor |
| `category` | VARCHAR(100) | No | No | None | `API`, `Specialty Excipients`, etc. | Valid supplier category | Domain category of materials provided |
| `contact_email` | VARCHAR(255) | No | No | None | Valid email | Regex email validation | Quality assurance contact address |
| `contact_phone` | VARCHAR(50) | Yes | No | None | E.164 phone string | Optional | 24/7 incident response hotline |
| `address` | VARCHAR(500) | Yes | No | None | Street text | Optional | Manufacturing facility physical location |
| `country` | VARCHAR(100) | No | No | None | Country name string | Non-empty | Jurisdiction of origin |
| `status` | VARCHAR(50) | No | No | None | `ACTIVE`, `INACTIVE`, `SUSPENDED` | Enum validation | Vendor compliance approval state |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Date vendor profile was approved |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | >= `created_at` | Date vendor record was last amended |

---

### 2.2 Table: `material_lots`
Physical batches of raw chemical materials, APIs, excipients, and containers received from suppliers.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `lot_id` | VARCHAR(100) | No | Primary Key | None | `RAWLOT-<sup_id>-2026-000001` | Strict format convention | Inbound material batch lot number |
| `supplier_id` | VARCHAR(50) | No | No | `suppliers.supplier_id` | Valid Supplier ID | Must exist in `suppliers` | Origin vendor that manufactured batch |
| `material_name` | VARCHAR(255) | No | No | None | Chemical / Material Name | Non-empty | Technical raw ingredient nomenclature |
| `material_category` | VARCHAR(100) | No | No | None | `API`, `EXCIPIENT`, `PACKAGING`, `SOLVENT` | Enum validation | Functional role in formulation |
| `received_date` | DATETIME | No | No | None | ISO 8601 UTC | Date in calendar | Inbound dock receiving date |
| `expiry_date` | DATETIME | No | No | None | ISO 8601 UTC | `expiry_date` > `received_date` | Date beyond which material is unusable |
| `initial_quantity` | FLOAT | No | No | None | > 0.0 | Positive number | Invoiced gross quantity received |
| `current_quantity` | FLOAT | No | No | None | >= 0.0 | 0.0 <= current <= initial | Unconsumed balance available in warehouse |
| `unit_of_measure` | VARCHAR(20) | No | No | None | `KG`, `L`, `UNITS` | Standard UOM | Measurement unit for weighing/metering |
| `unit_cost` | FLOAT | No | No | None | USD ($) | Positive currency | Standard acquisition cost per unit |
| `quality_status` | VARCHAR(50) | No | No | None | `RELEASED`, `QUARANTINED`, `CONTAMINATED` | Enum validation | Current QA release disposition |
| `is_contaminated` | BOOLEAN | No | No | None | `True`, `False` | Boolean flag | Incident flag indicating safety defect |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Inbound receiving log creation |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Status amendment date |

---

### 2.3 Table: `products`
Finished product catalog and formulation master specifications.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | VARCHAR(50) | No | Primary Key | None | `PRD-0001` .. `PRD-9999` | Strict format | Finished SKU product code |
| `sku` | VARCHAR(100) | No | Unique | None | `SKU-MED-0001` .. | Alphanumeric unique | Stock Keeping Unit identifier |
| `product_name` | VARCHAR(255) | No | No | None | Commercial drug name | Non-empty | Trade name of manufactured good |
| `category` | VARCHAR(100) | No | No | None | `PHARMACEUTICAL`, `NUTRACEUTICAL` | Enum validation | Healthcare vertical classification |
| `unit_of_measure` | VARCHAR(20) | No | No | None | `BOTTLES`, `BOXES`, `TUBES` | Standard UOM | Packaging saleable unit |
| `shelf_life_days` | INTEGER | No | No | None | Days (e.g. 730) | > 0 integer | Labeled product expiration duration |
| `standard_cost` | FLOAT | No | No | None | USD ($) | Positive currency | Bill-of-materials target cost |
| `is_active` | BOOLEAN | No | No | None | `True`, `False` | Boolean | Catalog commercial availability |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | System registration timestamp |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Catalog update timestamp |

---

### 2.4 Table: `boms` (Bill of Materials)
Product formulation revisions with effective start and expiration validity windows.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `bom_id` | VARCHAR(50) | No | Primary Key | None | `BOM-PRD-0001-V1` | Strict format | Formulation master revision identifier |
| `product_id` | VARCHAR(50) | No | No | `products.product_id` | Valid Product ID | Must exist in `products` | Product that this BOM manufactures |
| `version` | VARCHAR(20) | No | No | None | `v1.0`, `v2.0` | Semantic version string | Formulation iteration |
| `effective_from` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Date formulation became valid |
| `effective_to` | DATETIME | Yes | No | None | ISO 8601 UTC | `effective_to` > `effective_from` | Date formulation was sunset |
| `is_active` | BOOLEAN | No | No | None | `True`, `False` | Boolean | Active manufacturing flag |
| `yield_percentage`| FLOAT | No | No | None | Percentage (e.g. 98.5) | 80.0 <= yield <= 100.0 | Expected stoichiometric mass conversion |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Registration timestamp |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Modification timestamp |

---

### 2.5 Table: `bom_materials`
Component ingredient requirement per unit of finished product.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | No | Primary Key | None | Autoincrement | Integer > 0 | Surrogate primary key |
| `bom_id` | VARCHAR(50) | No | No | `boms.bom_id` | Valid BOM ID | Must exist in `boms` | Parent bill of materials |
| `material_category`| VARCHAR(100)| No | No | None | `API`, `EXCIPIENT`, etc. | Enum validation | Component classification |
| `material_name` | VARCHAR(255) | No | No | None | Chemical name | Non-empty | Required ingredient name |
| `required_quantity`| FLOAT | No | No | None | Rate per unit (e.g. 0.05) | > 0.0 | Material quantity needed per finished unit |
| `unit_of_measure` | VARCHAR(20) | No | No | None | `KG`, `L`, `UNITS` | Standard UOM | Ingredient measurement unit |
| `is_mandatory` | BOOLEAN | No | No | None | `True`, `False` | Boolean | Criticality indicator |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Record creation timestamp |

---

### 2.6 Table: `production_orders`
Manufacturing shop-floor work orders executing batch formulation.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | VARCHAR(50) | No | Primary Key | None | `WO-2026-000001` | Strict format `WO-YYYY-XXXXXX` | Work order execution ID |
| `bom_id` | VARCHAR(50) | No | No | `boms.bom_id` | Valid BOM ID | Must exist in `boms` | BOM recipe followed |
| `product_id` | VARCHAR(50) | No | No | `products.product_id` | Valid Product ID | Must exist in `products` | Product produced |
| `order_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Scheduling date |
| `start_date` | DATETIME | No | No | None | ISO 8601 UTC | `start_date` >= `order_date` | Physical blending commencement |
| `completion_date` | DATETIME | No | No | None | ISO 8601 UTC | `completion_date` >= `start_date` | Packaging and QA release date |
| `planned_quantity` | FLOAT | No | No | None | Units | > 0.0 | Target manufacturing output |
| `produced_quantity`| FLOAT | No | No | None | Units | >= 0.0 | Actual units bottled/packaged |
| `scrap_quantity` | FLOAT | No | No | None | Units | >= 0.0 | Unrecoverable loss/spillage |
| `status` | VARCHAR(50) | No | No | None | `PLANNED`, `IN_PROGRESS`, `COMPLETED` | Enum validation | Operational execution state |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Record creation |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Order closure timestamp |

---

### 2.7 Table: `production_consumptions`
Bridge ledger capturing exact material lot quantity consumed into each production work order.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `consumption_id` | VARCHAR(50) | No | Primary Key | None | `PC-2026-000001` | Strict format `PC-YYYY-XXXXXX` | Consumption transaction ID |
| `production_order_id`| VARCHAR(50)| No | No | `production_orders.order_id` | Valid WO ID | Must exist in `production_orders`| Work order receiving raw stock |
| `material_lot_id` | VARCHAR(100)| No | No | `material_lots.lot_id` | Valid Material Lot ID | Must exist in `material_lots` | Specific batch lot consumed |
| `quantity_consumed` | FLOAT | No | No | None | Units | > 0.0 | Mass or volume deducted from lot |
| `unit_of_measure` | VARCHAR(20) | No | No | None | `KG`, `L`, `UNITS` | Standard UOM | Consumption measurement unit |
| `consumption_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Dispensing timestamp |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | System logging timestamp |

---

### 2.8 Table: `finished_lots`
Manufactured lots of saleable goods released for distribution.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `lot_id` | VARCHAR(100) | No | Primary Key | None | `FINLOT-2026-000001` | Strict format `FINLOT-YYYY-XXXXXX` | Finished product batch lot ID |
| `production_order_id`| VARCHAR(50)| No | No | `production_orders.order_id` | Valid WO ID | Must exist in `production_orders`| Generating manufacturing order |
| `product_id` | VARCHAR(50) | No | No | `products.product_id` | Valid Product ID | Must exist in `products` | Product catalog reference |
| `manufactured_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Official packaging completion date |
| `expiry_date` | DATETIME | No | No | None | ISO 8601 UTC | `expiry_date` > `manufactured_date`| End of shelf-life date |
| `quantity_produced` | FLOAT | No | No | None | Units | > 0.0 | Total batch size manufactured |
| `quantity_available`| FLOAT | No | No | None | Units | 0.0 <= available <= produced | Undispatched stock in warehouse |
| `unit_of_measure` | VARCHAR(20) | No | No | None | `BOTTLES`, `BOXES`, `TUBES` | Standard UOM | Commercial unit |
| `quality_status` | VARCHAR(50) | No | No | None | `RELEASED`, `QUARANTINED`, `CONTAMINATED` | Enum validation | Regulatory release status |
| `is_contaminated` | BOOLEAN | No | No | None | `True`, `False` | Boolean | Contamination safety flag |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Receipt into finished inventory |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Modification timestamp |

---

### 2.9 Table: `lot_genealogies`
Material-to-product genealogical bridge capturing upstream-to-downstream relationships.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `genealogy_id` | VARCHAR(50) | No | Primary Key | None | `GEN-2026-000001` | Strict format `GEN-YYYY-XXXXXX` | Unique genealogy relationship edge ID |
| `raw_lot_id` | VARCHAR(100)| No | No | `material_lots.lot_id` | Valid Raw Lot ID | Must exist in `material_lots` | Upstream input ingredient |
| `finished_lot_id` | VARCHAR(100)| No | No | `finished_lots.lot_id` | Valid Finished Lot ID | Must exist in `finished_lots` | Downstream output product |
| `production_order_id`| VARCHAR(50)| No | No | `production_orders.order_id` | Valid Order ID | Must exist in `production_orders`| Work order facilitating conversion |
| `relationship_type` | VARCHAR(50) | No | No | None | `DIRECT_CONSUMPTION` | Enum | Classification of genealogy edge |
| `depth_level` | INTEGER | No | No | None | 1 .. 10 | Integer >= 1 | Echelon depth distance |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Record creation timestamp |

---

### 2.10 Table: `shipments`
Outbound freight movements dispatched from warehouses to regional depots and consignees.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `shipment_id` | VARCHAR(50) | No | Primary Key | None | `SHP-2026-000001` | Strict format `SHP-YYYY-XXXXXX` | Freight shipment number |
| `tracking_number` | VARCHAR(100)| No | Unique | None | `TRK-2026-000001` | Unique carrier string | Common carrier tracking code |
| `ship_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Dispatch handover timestamp |
| `carrier` | VARCHAR(100)| No | No | None | Carrier name | Non-empty | Logistics service provider |
| `status` | VARCHAR(50) | No | No | None | `CREATED`, `IN_TRANSIT`, `DELIVERED`, `RECALLED`| Enum | Shipment transit status |
| `origin_warehouse` | VARCHAR(100)| No | No | None | Warehouse ID | Non-empty | Outbound distribution facility |
| `destination_region`| VARCHAR(100)| No | No | None | Region name | Non-empty | Geographic target zone |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Manifest booking timestamp |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Status update timestamp |

---

### 2.11 Table: `shipment_items`
Specific finished lots allocated to a freight shipment.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `item_id` | VARCHAR(50) | No | Primary Key | None | `SHPITEM-2026-000001`| Strict format | Line item identifier |
| `shipment_id` | VARCHAR(50) | No | No | `shipments.shipment_id`| Valid Shipment ID | Must exist in `shipments` | Freight consignment reference |
| `finished_lot_id` | VARCHAR(100)| No | No | `finished_lots.lot_id`| Valid Finished Lot ID | Must exist in `finished_lots` | Specific finished lot loaded |
| `quantity_shipped` | FLOAT | No | No | None | Units | > 0.0 | Quantity allocated to carrier |
| `unit_of_measure` | VARCHAR(20) | No | No | None | Standard UOM | Non-empty | Package measurement unit |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Loading scan timestamp |

---

### 2.12 Table: `customers`
Downstream healthcare networks, pharmacies, hospitals, and distributors.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | VARCHAR(50) | No | Primary Key | None | `CUST-0001` .. | Strict format `CUST-XXXX` | Healthcare consignee account ID |
| `customer_name` | VARCHAR(255) | No | No | None | Legal facility name | Non-empty | Trade name of client institution |
| `customer_type` | VARCHAR(100) | No | No | None | `HOSPITAL_NETWORK`, `PHARMACY_CHAIN` | Enum validation | Industry segment |
| `contact_email` | VARCHAR(255) | No | No | None | Valid email | Regex email validation | Safety notification target email |
| `contact_phone` | VARCHAR(50) | Yes | No | None | E.164 phone string | Optional | Urgent safety phone hotline |
| `city` | VARCHAR(100) | No | No | None | City name | Non-empty | Consignee municipality |
| `state` | VARCHAR(100) | No | No | None | State abbreviation | Non-empty | Province or state |
| `country` | VARCHAR(100) | No | No | None | Country name | Non-empty | Country jurisdiction |
| `risk_tier` | VARCHAR(50) | No | No | None | `CRITICAL_HEALTHCARE`, `HIGH_VOLUME_COMMERCIAL`, `STANDARD_RETAIL` | Enum validation | Regulatory recall prioritization tier |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Account creation timestamp |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Profile amendment timestamp |

---

### 2.13 Table: `deliveries`
Proof-of-delivery handover of shipment goods to a customer consignee.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `delivery_id` | VARCHAR(50) | No | Primary Key | None | `DEL-2026-000001` | Strict format `DEL-YYYY-XXXXXX` | Delivery receipt transaction ID |
| `shipment_id` | VARCHAR(50) | No | No | `shipments.shipment_id`| Valid Shipment ID | Must exist in `shipments` | Transport consignment |
| `customer_id` | VARCHAR(50) | No | No | `customers.customer_id`| Valid Customer ID | Must exist in `customers` | Destination healthcare consignee |
| `delivery_date` | DATETIME | No | No | None | ISO 8601 UTC | `delivery_date` >= `shipment.ship_date` | Physical receiving timestamp |
| `status` | VARCHAR(50) | No | No | None | `SCHEDULED`, `DELIVERED`, `REJECTED` | Enum validation | Delivery handover status |
| `received_by` | VARCHAR(255) | No | No | None | Person name & title | Non-empty | Signee accepting physical custody |
| `quantity_delivered`| FLOAT | No | No | None | Units | >= 0.0 | Actual physical count delivered |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | POD logged in system |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | POD modification timestamp |

---

### 2.14 Table: `inventories`
Per-lot warehouse stock balance position.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `inventory_id` | VARCHAR(50) | No | Primary Key | None | `INV-2026-000001` | Strict format `INV-YYYY-XXXXXX` | Inventory ledger balance record ID |
| `lot_id` | VARCHAR(100)| No | No | None | Valid lot ID | Must match material or finished lot | Physical batch tracked |
| `lot_type` | VARCHAR(50) | No | No | None | `RAW`, `FINISHED` | Enum validation | Material tier |
| `warehouse_id` | VARCHAR(50) | No | No | None | Warehouse code | Non-empty | Physical warehouse facility |
| `location_bin` | VARCHAR(50) | No | No | None | Bin code string | Non-empty | Racking bin / shelf location |
| `quantity_on_hand`| FLOAT | No | No | None | Units | >= 0.0 | Unreserved available stock |
| `quantity_reserved`| FLOAT | No | No | None | Units | >= 0.0 | Allocated to active orders |
| `quantity_quarantined`| FLOAT | No | No | None | Units | >= 0.0 | Blocked from picking/sale |
| `status` | VARCHAR(50) | No | No | None | `AVAILABLE`, `QUARANTINED`, `BLOCKED`, `CONSUMED` | Enum validation | Stock availability status |
| `last_audit_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Cycle count audit timestamp |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Record creation timestamp |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Last balance change timestamp |

---

### 2.15 Table: `inventory_events`
Immutable transaction ledger of all inventory increments, deductions, and holds.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | VARCHAR(50) | No | Primary Key | None | `INVEVT-2026-000001` | Strict format | Inventory event sequence ID |
| `inventory_id` | VARCHAR(50) | No | No | `inventories.inventory_id`| Valid Inventory ID | Must exist in `inventories` | Parent inventory balance |
| `lot_id` | VARCHAR(100)| No | No | None | Valid lot ID | Non-empty | Batch lot affected |
| `event_type` | VARCHAR(50) | No | No | None | `RECEIPT`, `PRODUCTION_CONSUMPTION`, `PRODUCTION_OUTPUT`, `SHIPMENT_DISPATCH`, `QUARANTINE` | Enum | Transaction operation type |
| `quantity_change` | FLOAT | No | No | None | Units | Non-zero float (+ or -) | Delta applied to balance |
| `resulting_balance`| FLOAT | No | No | None | Units | >= 0.0 | Cumulative stock after delta |
| `reference_type` | VARCHAR(50) | No | No | None | `WORK_ORDER`, `SHIPMENT`, `RECALL_HOLD`, `PO_RECEIPT` | Non-empty | Generating business object |
| `reference_id` | VARCHAR(50) | No | No | None | Entity ID string | Non-empty | Cross-reference identifier |
| `event_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Operational transaction timestamp |
| `notes` | TEXT | Yes | No | None | Narrative text | Optional | Explanatory ledger remarks |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Immutable insertion timestamp |

---

### 2.16 Table: `recall_cases`
Product safety recall investigation and containment docket.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `recall_id` | VARCHAR(50) | No | Primary Key | None | `REC-2026-000001` | Strict format `REC-YYYY-XXXXXX` | Official recall case docket ID |
| `title` | VARCHAR(255) | No | No | None | Descriptive headline | Non-empty | Incident title / public advisory summary |
| `trigger_type` | VARCHAR(50) | No | No | None | `CONTAMINATED_RAW_LOT`, `CONTAMINATED_FINISHED_LOT` | Enum validation | Triggering root cause |
| `source_lot_id` | VARCHAR(100)| No | No | None | Valid Lot ID | Must exist in DB | Contaminated batch under investigation |
| `source_lot_type` | VARCHAR(20) | No | No | None | `RAW`, `FINISHED` | Enum | Classification of triggering lot |
| `severity` | VARCHAR(20) | No | No | None | `CLASS_I`, `CLASS_II`, `CLASS_III` | FDA recall classification | Public health risk severity level |
| `initiated_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Date recall was declared |
| `target_completion_date`| DATETIME| No | No | None | ISO 8601 UTC | `target` > `initiated` | Mandated regulatory containment deadline |
| `status` | VARCHAR(50) | No | No | None | `OPEN`, `INVESTIGATING`, `CONTAINMENT_IN_PROGRESS`, `CUSTOMERS_NOTIFIED`, `RECOVERY_IN_PROGRESS`, `COMPLETED`, `CLOSED` | Enum | Recall operational lifecycle state |
| `closure_date` | DATETIME | Yes | No | None | ISO 8601 UTC | Optional | Official regulatory closure timestamp |
| `total_affected_finished_lots`| INTEGER| No | No | None | Count | >= 0 | Count of downstream finished batches |
| `total_affected_deliveries`| INTEGER| No | No | None | Count | >= 0 | Outbound consignments involved |
| `total_affected_customers`| INTEGER| No | No | None | Count | >= 0 | Healthcare clients requiring notice |
| `total_recalled_quantity`| FLOAT | No | No | None | Units | >= 0.0 | Gross distributed units recalled |
| `total_quarantined_quantity`| FLOAT| No | No | None | Units | >= 0.0 | Units locked in warehouses |
| `total_recovered_quantity`| FLOAT | No | No | None | Units | >= 0.0 | Units returned from consignees |
| `notification_coverage_pct`| FLOAT| No | No | None | Percentage (0 - 100) | Notified / Total Affected * 100 | Customer communication completion |
| `recovery_rate_pct` | FLOAT | No | No | None | Percentage (0 - 100) | Recovered / Recalled * 100 | Field return recovery completion |
| `recall_completion_pct` | FLOAT | No | No | None | Percentage (0 - 100) | Completed Actions / Total Actions * 100 | Containment task milestone progress |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Case opening timestamp |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Latest metric update timestamp |

---

### 2.17 Table: `recall_actions`
Operational containment tasks assigned to staff during recall execution.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `action_id` | VARCHAR(50) | No | Primary Key | None | `ACT-2026-000001` | Strict format `ACT-YYYY-XXXXXX` | Operational action task ID |
| `recall_id` | VARCHAR(50) | No | No | `recall_cases.recall_id` | Valid Recall ID | Must exist in `recall_cases` | Parent recall case |
| `action_type` | VARCHAR(50) | No | No | None | `QUARANTINE_INVENTORY`, `CUSTOMER_NOTIFICATION`, `SHIPMENT_STOP`, `PRODUCT_RECOVERY` | Enum | Task classification |
| `target_entity_type`| VARCHAR(50)| No | No | None | `INVENTORY`, `CUSTOMER`, `SHIPMENT`, `FINISHED_LOT` | Non-empty | Target supply chain entity type |
| `target_entity_id` | VARCHAR(100)| No | No | None | Entity ID string | Non-empty | ID of target to act upon |
| `status` | VARCHAR(50) | No | No | None | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED` | Enum | Task execution status |
| `assigned_to` | VARCHAR(100)| No | No | None | Personnel / Department name | Non-empty | Responsible party |
| `scheduled_date` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Planned execution date |
| `completed_date` | DATETIME | Yes | No | None | ISO 8601 UTC | Optional | Verified completion timestamp |
| `notes` | TEXT | Yes | No | None | Free text | Optional | Operational notes |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Task creation timestamp |
| `updated_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Status update timestamp |

---

### 2.18 Table: `recall_events`
Audit trail of all recall lifecycle state changes.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | VARCHAR(50) | No | Primary Key | None | `RECEVT-2026-000001` | Strict format | Immutable transition sequence ID |
| `recall_id` | VARCHAR(50) | No | No | `recall_cases.recall_id` | Valid Recall ID | Must exist in `recall_cases` | Parent recall docket |
| `previous_status` | VARCHAR(50) | No | No | None | Status string | Enum or 'NONE' | State prior to transition |
| `new_status` | VARCHAR(50) | No | No | None | Status string | Enum | State after transition |
| `reason` | VARCHAR(500)| No | No | None | Explanation text | Non-empty | Business justification for change |
| `trigger_source` | VARCHAR(100)| No | No | None | `RECALL_ENGINE`, `QUALITY_AUDIT` | Non-empty | Originating system or role |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Transition execution timestamp |

---

### 2.19 Table: `customer_notifications`
Statutory recall notices dispatched to affected customer consignees.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `notification_id` | VARCHAR(50) | No | Primary Key | None | `NOTIF-2026-000001` | Strict format `NOTIF-YYYY-XXXXXX` | Safety notice dispatch ID |
| `recall_id` | VARCHAR(50) | No | No | `recall_cases.recall_id` | Valid Recall ID | Must exist in `recall_cases` | Associated recall case |
| `customer_id` | VARCHAR(50) | No | No | `customers.customer_id` | Valid Customer ID | Must exist in `customers` | Healthcare consignee recipient |
| `delivery_id` | VARCHAR(50) | Yes | No | None | Valid Delivery ID | Optional | Delivery consignment reference |
| `finished_lot_id` | VARCHAR(100)| Yes | No | None | Valid Finished Lot ID | Optional | Specific recalled batch delivered |
| `notification_channel`| VARCHAR(50)| No | No | None | `EMAIL`, `REGISTERED_MAIL`, `PHONE`, `EDI` | Enum | Communication medium |
| `notification_status` | VARCHAR(50)| No | No | None | `PENDING`, `SENT`, `DELIVERED`, `ACKNOWLEDGED` | Enum | Regulatory delivery status |
| `sent_at` | DATETIME | Yes | No | None | ISO 8601 UTC | Optional | Dispatch timestamp |
| `acknowledged_at`| DATETIME | Yes | No | None | ISO 8601 UTC | `acknowledged` >= `sent` | Customer receipt acknowledgement timestamp |
| `response_notes` | TEXT | Yes | No | None | Response remarks | Optional | Customer feedback / quarantine confirmation |
| `created_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Notification creation timestamp |

---

### 2.20 Table: `validation_issues`
Auditing and exception log generated by the automated business validation engine.

| Field Name | Data Type | Nullable | Uniqueness | Foreign Key | Allowed Values / Unit | Validation Rule | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `validation_id` | VARCHAR(50) | No | Primary Key | None | `VAL-2026-000001` | Strict format `VAL-YYYY-XXXXXX` | Validation discrepancy issue ID |
| `entity_name` | VARCHAR(100)| No | No | None | Model class name | Non-empty | Table / model failing audit |
| `entity_id` | VARCHAR(100)| No | No | None | Target record ID | Non-empty | Record ID failing audit rule |
| `issue_type` | VARCHAR(100)| No | No | None | `MISSING_INPUT_LOT`, `DELIVERED_EXCEEDS_PRODUCED`, `MISSED_CUSTOMER_NOTIFICATION`, `RECALLED_INVENTORY_AVAILABLE_FOR_SALE` | Non-empty | Category of rule violation |
| `severity` | VARCHAR(20) | No | No | None | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `WARNING` | Enum | Regulatory impact severity |
| `expected_value` | VARCHAR(255)| Yes | No | None | String representation | Optional | Mandated business rule condition |
| `actual_value` | VARCHAR(255)| Yes | No | None | String representation | Optional | Discovered discrepancy condition |
| `validation_status`| VARCHAR(20) | No | No | None | `FAILED`, `WARNING`, `PASSED` | Enum | Audit evaluation outcome |
| `detected_at` | DATETIME | No | No | None | ISO 8601 UTC | Timestamp | Detection audit timestamp |
| `ground_truth_label`| VARCHAR(100)| Yes | No | None | `ANOMALY_A_...` .. | Optional | Planted scenario evaluation tag |
