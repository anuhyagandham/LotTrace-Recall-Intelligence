"""
Distributions and domain constants for realistic synthetic data generation.
"""

from typing import List, Dict, Any

# Supplier Categories and Names Pool
SUPPLIER_CATEGORIES = [
    "Active Pharmaceutical Ingredients",
    "Specialty Excipients",
    "Sterile Packaging Solutions",
    "Chemical Solvents & Reagents",
    "Biochemical Buffers",
    "Natural Botanical Extracts",
]

SUPPLIER_PREFIXES = [
    "Apex", "BioCore", "Syntho", "Pharmatech", "NanoBio", "PureChem", "GlobalPharma",
    "SoluChem", "Vanguard", "OmniBio", "Helix", "PrimeSource", "Catalyst", "Zenith",
    "MedEquip", "Integra", "Astra", "Thera", "Aegis", "Valida"
]

SUPPLIER_SUFFIXES = [
    "Laboratories", "Chemicals Inc.", "BioSciences", "Life Sciences", "Materials Corp.",
    "Formulations Ltd.", "Holdings", "Active Intermediates", "Solutions"
]

# Raw Material Categories and Catalog
MATERIAL_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "API": [
        {"name": "Acetaminophen USP Micronized", "uom": "KG", "cost": 42.50, "shelf_life_days": 730},
        {"name": "Amoxicillin Trihydrate Powder", "uom": "KG", "cost": 78.00, "shelf_life_days": 540},
        {"name": "Ibuprofen BP Fine Powder", "uom": "KG", "cost": 36.25, "shelf_life_days": 1095},
        {"name": "Metformin Hydrochloride", "uom": "KG", "cost": 29.80, "shelf_life_days": 1095},
        {"name": "Ascorbic Acid USP Grade", "uom": "KG", "cost": 18.50, "shelf_life_days": 730},
        {"name": "Dextromethorphan HBr", "uom": "KG", "cost": 95.00, "shelf_life_days": 730},
    ],
    "EXCIPIENT": [
        {"name": "Microcrystalline Cellulose PH-102", "uom": "KG", "cost": 8.50, "shelf_life_days": 1460},
        {"name": "Lactose Monohydrate Fine", "uom": "KG", "cost": 6.20, "shelf_life_days": 1095},
        {"name": "Magnesium Stearate Vegetable", "uom": "KG", "cost": 14.30, "shelf_life_days": 730},
        {"name": "Croscarmellose Sodium", "uom": "KG", "cost": 16.75, "shelf_life_days": 1095},
        {"name": "Hydroxypropyl Methylcellulose", "uom": "KG", "cost": 22.00, "shelf_life_days": 1095},
    ],
    "PACKAGING": [
        {"name": "High-Density Polyethylene Bottles 150ml", "uom": "UNITS", "cost": 0.35, "shelf_life_days": 1825},
        {"name": "Child-Resistant Induction Seals 38mm", "uom": "UNITS", "cost": 0.08, "shelf_life_days": 1825},
        {"name": "Blister Aluminum Foil Strip 200mm", "uom": "UNITS", "cost": 0.12, "shelf_life_days": 1825},
        {"name": "Sterile Amber Glass Vials 10ml", "uom": "UNITS", "cost": 0.85, "shelf_life_days": 1825},
    ],
    "SOLVENT": [
        {"name": "Purified Water for Injection USP", "uom": "L", "cost": 1.20, "shelf_life_days": 180},
        {"name": "Ethanol 99.5% Denatured", "uom": "L", "cost": 4.50, "shelf_life_days": 730},
        {"name": "Propylene Glycol Pharma Grade", "uom": "L", "cost": 7.80, "shelf_life_days": 730},
    ],
    "FLAVORING": [
        {"name": "Natural Wild Cherry Flavor Powder", "uom": "KG", "cost": 34.00, "shelf_life_days": 540},
        {"name": "Peppermint Oil Extract Pure", "uom": "L", "cost": 62.00, "shelf_life_days": 730},
    ],
    "PRESERVATIVE": [
        {"name": "Sodium Benzoate NF Dense", "uom": "KG", "cost": 11.20, "shelf_life_days": 1095},
        {"name": "Potassium Sorbate Granular", "uom": "KG", "cost": 13.50, "shelf_life_days": 1095},
    ]
}

# Finished Products Catalog
PRODUCT_CATALOG = [
    {
        "sku": "SKU-PHARM-001",
        "name": "Acetaminophen 500mg Extra Strength Tablets",
        "category": "PHARMACEUTICAL",
        "uom": "BOTTLES",
        "shelf_life_days": 730,
        "standard_cost": 6.80,
        "boms": [
            {
                "version": "v1.0",
                "yield": 98.5,
                "materials": [
                    {"category": "API", "name": "Acetaminophen USP Micronized", "qty": 0.05, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Microcrystalline Cellulose PH-102", "qty": 0.03, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Magnesium Stearate Vegetable", "qty": 0.002, "uom": "KG"},
                    {"category": "PACKAGING", "name": "High-Density Polyethylene Bottles 150ml", "qty": 1.0, "uom": "UNITS"},
                ]
            },
            {
                "version": "v2.0",
                "yield": 99.0,
                "materials": [
                    {"category": "API", "name": "Acetaminophen USP Micronized", "qty": 0.05, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Lactose Monohydrate Fine", "qty": 0.03, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Croscarmellose Sodium", "qty": 0.003, "uom": "KG"},
                    {"category": "PACKAGING", "name": "High-Density Polyethylene Bottles 150ml", "qty": 1.0, "uom": "UNITS"},
                ]
            }
        ]
    },
    {
        "sku": "SKU-PHARM-002",
        "name": "Amoxicillin 250mg Oral Suspension",
        "category": "PHARMACEUTICAL",
        "uom": "BOTTLES",
        "shelf_life_days": 365,
        "standard_cost": 9.40,
        "boms": [
            {
                "version": "v1.0",
                "yield": 97.8,
                "materials": [
                    {"category": "API", "name": "Amoxicillin Trihydrate Powder", "qty": 0.03, "uom": "KG"},
                    {"category": "SOLVENT", "name": "Purified Water for Injection USP", "qty": 0.1, "uom": "L"},
                    {"category": "FLAVORING", "name": "Natural Wild Cherry Flavor Powder", "qty": 0.005, "uom": "KG"},
                    {"category": "PRESERVATIVE", "name": "Sodium Benzoate NF Dense", "qty": 0.001, "uom": "KG"},
                    {"category": "PACKAGING", "name": "High-Density Polyethylene Bottles 150ml", "qty": 1.0, "uom": "UNITS"},
                ]
            }
        ]
    },
    {
        "sku": "SKU-PHARM-003",
        "name": "Ibuprofen 200mg Rapid Action Caplets",
        "category": "PHARMACEUTICAL",
        "uom": "BOXES",
        "shelf_life_days": 1095,
        "standard_cost": 5.25,
        "boms": [
            {
                "version": "v1.0",
                "yield": 99.2,
                "materials": [
                    {"category": "API", "name": "Ibuprofen BP Fine Powder", "qty": 0.02, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Microcrystalline Cellulose PH-102", "qty": 0.015, "uom": "KG"},
                    {"category": "PACKAGING", "name": "Blister Aluminum Foil Strip 200mm", "qty": 2.0, "uom": "UNITS"},
                ]
            }
        ]
    },
    {
        "sku": "SKU-PHARM-004",
        "name": "Metformin HCl 500mg Extended Release",
        "category": "PHARMACEUTICAL",
        "uom": "BOTTLES",
        "shelf_life_days": 730,
        "standard_cost": 7.10,
        "boms": [
            {
                "version": "v1.0",
                "yield": 98.0,
                "materials": [
                    {"category": "API", "name": "Metformin Hydrochloride", "qty": 0.05, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Hydroxypropyl Methylcellulose", "qty": 0.02, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Magnesium Stearate Vegetable", "qty": 0.002, "uom": "KG"},
                    {"category": "PACKAGING", "name": "High-Density Polyethylene Bottles 150ml", "qty": 1.0, "uom": "UNITS"},
                ]
            }
        ]
    },
    {
        "sku": "SKU-NUTRA-001",
        "name": "Vitamin C 1000mg Effervescent Boost",
        "category": "NUTRACEUTICAL",
        "uom": "TUBES",
        "shelf_life_days": 730,
        "standard_cost": 4.50,
        "boms": [
            {
                "version": "v1.0",
                "yield": 99.5,
                "materials": [
                    {"category": "API", "name": "Ascorbic Acid USP Grade", "qty": 0.025, "uom": "KG"},
                    {"category": "FLAVORING", "name": "Natural Wild Cherry Flavor Powder", "qty": 0.003, "uom": "KG"},
                    {"category": "EXCIPIENT", "name": "Lactose Monohydrate Fine", "qty": 0.01, "uom": "KG"},
                    {"category": "PACKAGING", "name": "Sterile Amber Glass Vials 10ml", "qty": 1.0, "uom": "UNITS"},
                ]
            }
        ]
    },
    {
        "sku": "SKU-PHARM-005",
        "name": "Pediatric Cough & Cold Elixir 120ml",
        "category": "PHARMACEUTICAL",
        "uom": "BOTTLES",
        "shelf_life_days": 540,
        "standard_cost": 8.15,
        "boms": [
            {
                "version": "v1.0",
                "yield": 97.5,
                "materials": [
                    {"category": "API", "name": "Dextromethorphan HBr", "qty": 0.005, "uom": "KG"},
                    {"category": "SOLVENT", "name": "Propylene Glycol Pharma Grade", "qty": 0.04, "uom": "L"},
                    {"category": "FLAVORING", "name": "Peppermint Oil Extract Pure", "qty": 0.002, "uom": "L"},
                    {"category": "PRESERVATIVE", "name": "Potassium Sorbate Granular", "qty": 0.001, "uom": "KG"},
                    {"category": "PACKAGING", "name": "High-Density Polyethylene Bottles 150ml", "qty": 1.0, "uom": "UNITS"},
                ]
            }
        ]
    }
]

# Warehouse Locations
WAREHOUSES = [
    {"id": "WH-CENTRAL-01", "name": "Central Distribution Center Chicago", "location": "IL, USA"},
    {"id": "WH-EAST-02", "name": "Eastern Logistics Hub New Jersey", "location": "NJ, USA"},
    {"id": "WH-WEST-03", "name": "Pacific Cold-Chain Facility Ontario", "location": "CA, USA"},
    {"id": "WH-SOUTH-04", "name": "Southern Regional Depot Dallas", "location": "TX, USA"},
]

# Carriers
CARRIERS = [
    "FedEx Healthcare Priority",
    "UPS Temperature True",
    "DHL Medical Express",
    "Cardinal Health Direct Logistics",
    "AmerisourceBergen Secure Trans",
]

# Customer Types and Distribution Tiers
CUSTOMER_TYPES = [
    "HOSPITAL_NETWORK",
    "REGIONAL_HEALTH_SYSTEM",
    "NATIONAL_PHARMACY_CHAIN",
    "INDEPENDENT_PHARMACY",
    "SPECIALTY_CLINIC",
    "GOVERNMENT_MEDICAL_DEPOT",
]

CUSTOMER_RISK_TIERS = [
    "CRITICAL_HEALTHCARE",
    "HIGH_VOLUME_COMMERCIAL",
    "STANDARD_RETAIL",
]
