# LotTrace AI — Domain Business Rules & Regulatory Specifications

## 1. Master Data & Bill of Materials (BOM) Formulation

### Rule BR-BOM-001: Temporal Formulation Validity
- Every `BOM` record specifies an `effective_from` date and an optional `effective_to` date.
- A manufacturing `ProductionOrder` scheduled on `order_date` may **only** select a BOM where `effective_from <= order_date` and (`effective_to IS NULL` or `effective_to >= order_date`).
- Sunset or superseded BOM revisions cannot be selected for new work orders.

### Rule BR-BOM-002: Ingredient Component Rates
- Each ingredient in `bom_materials` defines a required quantity per single unit of finished good.
- Total required material for a production order is derived:
  $$\text{Required Quantity} = \text{BOM Required Rate} \times \text{Work Order Planned Quantity}$$

---

## 2. Production Consumption & Yield Reconciliation

### Rule BR-PRD-001: Pre-Consumption Availability & FEFO Allocation
- Raw materials must have `quality_status = 'RELEASED'` and `is_contaminated = False` to be eligible for production dispensing.
- Materials are consumed following **First-Expired, First-Out (FEFO)** inventory principles based on `expiry_date`.

### Rule BR-PRD-002: Mass Balance & Yield Tolerances
- For every completed work order:
  $$\text{Total Accounted Output} = \text{Produced Quantity} + \text{Scrap Quantity}$$
- Production yield must satisfy standard manufacturing tolerances:
  $$80.0\% \le \text{Actual Yield} = \left(\frac{\text{Produced Quantity}}{\text{Planned Quantity}}\right) \times 100 \le 105.0\%$$
- Any yield outside this envelope triggers a `PRODUCTION_YIELD_RECONCILIATION` validation flag.

### Rule BR-PRD-003: Genealogy Inheritance
- Every finished lot produced by a work order inherits 100% of the raw material lots consumed into that order.
- Direct consumption links are permanently stamped in `lot_genealogies`.

---

## 3. Inventory Balances & Warehouse Movements

### Rule BR-INV-001: Immutable Inventory Ledger
- Current balances in `inventories` are mirrored by an append-only event ledger in `inventory_events`.
- Overwriting historical inventory transactions is strictly prohibited. Every increment (Receipt, Production Output) or deduction (Consumption, Shipment) creates an immutable event row.

### Rule BR-INV-002: Non-Negative Available Stock
- Available unreserved stock (`quantity_on_hand`) must never drop below 0.0.
- Over-allocation or negative inventory triggers a critical inventory discrepancy exception.

---

## 4. Freight Logistics & Distribution Reconciliation

### Rule BR-LOG-001: Chronological Transit Precedence
- Outbound shipments cannot have a delivery timestamp preceding the dispatch timestamp:
  $$\text{Delivery Date} \ge \text{Shipment Ship Date}$$

### Rule BR-LOG-002: Conservation of Shipped Quantities
- Total physical units delivered across all customer delivery receipts under a shipment cannot exceed the gross quantity allocated on the shipment:
  $$\sum \text{Delivered Quantity} \le \sum \text{Shipped Quantity}$$
- Any delivery logged with quantity greater than the finished lot's total batch production triggers a `DELIVERED_EXCEEDS_PRODUCED` critical validation anomaly (Scenario B).

---

## 5. Product Safety Recall Governance & Containment

### Rule BR-REC-001: Trigger Types & Immediate Contamination Stamping
- Product recalls are initiated upon discovery of either:
  1. `CONTAMINATED_RAW_LOT`: Upstream chemical or microbial contamination in received vendor ingredients.
  2. `CONTAMINATED_FINISHED_LOT`: Out-of-specification (OOS) testing failure during shelf-life stability or customer complaint.
- When a recall is initiated, the source lot's `is_contaminated` flag is immediately set to `True` and `quality_status = 'CONTAMINATED'`.

### Rule BR-REC-002: FDA Hazard Classifications
Recalls are classified into statutory severity tiers:
- **Class I:** High-risk defect presenting reasonable probability of severe health consequences or mortality. Requires **100% customer notification within 24 hours** and mandatory warehouse hold.
- **Class II:** Moderate-risk defect where exposure may cause temporary or medically reversible adverse health consequences.
- **Class III:** Low-risk or technical violation unlikely to cause adverse medical outcomes.

### Rule BR-REC-003: Automated Warehouse Quarantine Hold
- Upon recall declaration, the recall engine executes an automated ERP hold:
  1. Identifies all warehouse inventory holding the source lot and all downstream derived finished lots.
  2. Deducts available balance to zero (`quantity_on_hand = 0.0`).
  3. Transfers balance into quarantine (`quantity_quarantined = previous quantity`).
  4. Changes inventory status to `QUARANTINED`.
  5. Records `InventoryEvent` of type `QUARANTINE`.
- If any contaminated stock remains in `AVAILABLE` status, the validation engine flags `RECALLED_INVENTORY_AVAILABLE_FOR_SALE` (Scenario D).

### Rule BR-REC-004: Customer Notification SLA & Channel Routing
- Every healthcare consignee that received a contaminated batch must receive an official recall advisory notice.
- Priority customer routing:
  - `CRITICAL_HEALTHCARE` institutions (hospitals, trauma centers) are notified via `REGISTERED_MAIL` and urgent direct safety outreach.
  - Commercial retail chains and distributors receive electronic notices (`EMAIL` / `EDI`).
- Any affected customer omitted from initial dispatch triggers `MISSED_CUSTOMER_NOTIFICATION` (Scenario C).

### Rule BR-REC-005: Operational Performance Formulas
1. **Notification Coverage:**
   $$\text{Notification Coverage (\%)} = \left(\frac{\text{Successfully Notified Affected Customers}}{\text{Total Affected Customers}}\right) \times 100$$
2. **Field Recovery Rate:**
   $$\text{Recovery Rate (\%)} = \left(\frac{\text{Recovered Returned Quantity}}{\text{Total Recalled Quantity}}\right) \times 100$$
3. **Recall Completion:**
   $$\text{Recall Completion (\%)} = \left(\frac{\text{Completed Containment Actions}}{\text{Total Required Containment Actions}}\right) \times 100$$
