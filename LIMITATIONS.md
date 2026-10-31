# LotTrace AI — System Limitations & Engineering Constraints

## 1. Relational Persistence & Concurrency
- **SQLite Engine:** LotTrace AI utilizes SQLite with write-ahead logging (`PRAGMA journal_mode=WAL`) and synchronous normal mode for zero-dependency local Windows execution. While capable of sustaining thousands of concurrent reads, SQLite serializes write transactions with database-level locking. For distributed enterprise environments with high-frequency concurrent writes from multiple shop-floor production lines, the system is designed to seamlessly transition to PostgreSQL or MySQL by setting the `DATABASE_URL` environment variable.

## 2. Integration & Telemetry Boundaries
- **Carrier Telemetry:** Freight shipments are simulated through realistic carrier routes (FedEx, UPS, DHL). Live production deployment would connect carrier EDI 214 shipment status messages and GS1-128 barcode scanning.
- **Customer Notification Dispatch:** Customer notifications simulate delivery via registered mail and email receipts. Actual SMTP or EDI 856 dispatch is decoupled to avoid external API key dependencies and costs during technical evaluations.
- **Physical Barcode / RFID Hardware:** The platform manages deterministic lot identifiers and serial keys logically. Physical 2D DataMatrix scanning is represented via software REST ingestion endpoints.

## 3. Regulatory Scope (FDA 21 CFR Part 11)
- **Electronic Signatures:** While immutable audit logs (`inventory_events`, `recall_events`) capture every state change, user cryptographic signing (digital certificates / PKI tokens) is not yet integrated into the local Streamlit UI.
- **Computer System Validation (CSV):** The project implements comprehensive automated regression tests (`pytest`), but formal GxP IQ/OQ/PQ certification protocols would be required for FDA manufacturing compliance.

## 4. Planned Roadmap & Future Extensions
1. **PostgreSQL Migration Driver:** Native connection pooling using SQLAlchemy `QueuePool`.
2. **GS1 EPCIS Standard Integration:** Standardized XML/JSON serialization for GS1 Electronic Product Code Information Services.
3. **Graph Neural Network (GNN) Risk Scoring:** Machine learning model to predict supplier contamination likelihood based on historical defect rates and weather logistics disruptions.
