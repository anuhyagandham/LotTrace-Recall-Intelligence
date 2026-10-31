# LotTrace AI — System Architecture & Technical Design

## 1. Executive Architecture Summary

**LotTrace AI** is an enterprise-grade, locally deployable supply chain traceability and product recall intelligence platform. It models multi-echelon pharmaceutical and chemical manufacturing networks to trace contaminated materials through suppliers, manufacturing work orders, finished lots, warehouses, carrier freight shipments, and healthcare consignees.

```mermaid
flowchart TD
    subgraph UI ["User Experience Layer"]
        A[Streamlit Business Dashboard :8501]
        B[Interactive Plotly Visual Analytics]
    end

    subgraph API ["REST API Layer"]
        C[Flask REST API :5000]
        D[Endpoint Routing & Pagination]
        E[Error Handling & JSON Serialization]
    end

    subgraph CORE ["Core Engine Services"]
        F[Genealogy Traversal Engine]
        G[Recall Containment Engine]
        H[Business Validation Engine]
        I[Quantity Reconciler]
        J[Metrics & Analytics Engine]
    end

    subgraph DATA ["Persistence & Exporter Layer"]
        K[(SQLite Relational Database)]
        L[CSV Exporters]
        M[JSON Exporters]
        N[SQL Exporters]
        O[SHA-256 Manifest Generator]
        P[Ground Truth Separation]
    end

    A -->|Direct ORM Query| K
    A -->|HTTP Requests| C
    C --> CORE
    CORE --> K
    CORE --> P
    K --> L
    K --> M
    K --> N
    L & M & N --> O
```

---

## 2. Multi-Echelon Relational Entity Model (ERD)

The database schema is fully normalized in third normal form (3NF) across 20 tables with enforced foreign-key integrity (`PRAGMA foreign_keys=ON`) and indexing on all query dimensions:

```mermaid
erDiagram
    SUPPLIER ||--o{ MATERIAL_LOT : supplies
    PRODUCT ||--o{ BOM : versions
    BOM ||--o{ BOM_MATERIAL : requires
    PRODUCT ||--o{ PRODUCTION_ORDER : defines
    BOM ||--o{ PRODUCTION_ORDER : prescribes
    PRODUCTION_ORDER ||--o{ PRODUCTION_CONSUMPTION : consumes
    MATERIAL_LOT ||--o{ PRODUCTION_CONSUMPTION : "consumed in"
    PRODUCTION_ORDER ||--o{ FINISHED_LOT : produces
    MATERIAL_LOT ||--o{ LOT_GENEALOGY : maps
    FINISHED_LOT ||--o{ LOT_GENEALOGY : "traced from"
    FINISHED_LOT ||--o{ SHIPMENT_ITEM : "allocated to"
    SHIPMENT ||--o{ SHIPMENT_ITEM : carries
    SHIPMENT ||--o{ DELIVERY : dispatches
    CUSTOMER ||--o{ DELIVERY : receives
    INVENTORY ||--o{ INVENTORY_EVENT : logs
    RECALL_CASE ||--o{ RECALL_ACTION : mandates
    RECALL_CASE ||--o{ RECALL_EVENT : audits
    RECALL_CASE ||--o{ CUSTOMER_NOTIFICATION : dispatches
    CUSTOMER ||--o{ CUSTOMER_NOTIFICATION : alerts
```

---

## 3. Bidirectional Genealogy Traversal Algorithm

Genealogy traversal operates recursively in two fundamental directions:

```mermaid
flowchart LR
    subgraph DOWNSTREAM ["Downstream Scope Tracing (Recall Explosion)"]
        R1[Contaminated Raw Material Lot] --> WO1[Consuming Work Orders]
        WO1 --> FL1[Manufactured Finished Lots]
        FL1 --> SH1[Freight Shipments]
        SH1 --> DEL1[Customer Deliveries]
        DEL1 --> CUST1[Healthcare Consignees]
    end

    subgraph UPSTREAM ["Upstream Root-Cause Tracing (Implosion)"]
        FL2[Defective Finished Lot] --> WO2[Parent Production Order]
        WO2 --> R2[Consumed Ingredient Batches]
        R2 --> SUP2[Master Supplier Accounts]
    end
```

### Algorithm Complexity & Loop Prevention
- **Cycle Prevention:** A visited set `visited_nodes: Set[str]` tracks traversed lots and orders, preventing infinite loops in cyclic dependencies or rework loops.
- **Complexity:** Time complexity is $O(V + E)$ where $V$ represents entities (lots, orders, shipments, customers) and $E$ represents edges (consumptions, outputs, deliveries). With indexed foreign keys in SQLite, downstream traversal across thousands of records executes in under 15 milliseconds.

---

## 4. Product Recall Lifecycle State Machine

Recalls strictly transition across validated lifecycle stages, logging every transition to `recall_events`:

```mermaid
stateDiagram-v2
    [*] --> OPEN: Incident Declared
    OPEN --> INVESTIGATING: Scope Explosion
    INVESTIGATING --> CONTAINMENT_IN_PROGRESS: ERP Hold Active
    CONTAINMENT_IN_PROGRESS --> CUSTOMERS_NOTIFIED: Notices Sent
    CUSTOMERS_NOTIFIED --> RECOVERY_IN_PROGRESS: Field Returns Active
    RECOVERY_IN_PROGRESS --> COMPLETED: >= 90% Milestones Met
    COMPLETED --> CLOSED: Audit Sign-Off
```

### Idempotent Action Dispatch
The recall engine guarantees **idempotency**:
1. Checks for existing `RecallAction` of type `QUARANTINE_INVENTORY` before creating duplicate warehouse holds.
2. Deduplicates `CustomerNotification` records by `(recall_id, customer_id)`.
3. Ensures repeated executions update metrics without corrupting ledger event history.

---

## 5. Ground Truth & Anomaly Separation Design

```mermaid
flowchart TD
    subgraph DATA_GEN ["Deterministic Synthetic Generator"]
        G1[Random Seed 20261022] --> G2[Operational Relational DB]
        G1 --> G3[Planted Negative Scenarios]
        G3 --> G4[(data/ground_truth/)]
    end

    subgraph RUNTIME ["Execution & Evaluation"]
        G2 --> V1[Business Validation Engine]
        G2 --> R1[Recall Containment Engine]
        V1 --> AUDIT[Validation Audit Discrepancies]
        G4 -.->|Strictly Post-Hoc Evaluation| EVAL[Comparison & Scoring]
        AUDIT --> EVAL
    end
```

- Ground truth records (`ground_truth.csv` and `ground_truth.json`) are generated in a completely isolated directory.
- The operational database, validation engine, and recall engine do **NOT** read ground truth labels during execution.
- This enforces zero data leakage, enabling true blind auditing and objective QA testing.
