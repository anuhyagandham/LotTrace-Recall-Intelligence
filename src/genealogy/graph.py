"""
Graph data structures and utilities for Supply Chain Lot Traceability.
Provides node/edge representations, cycle detection, and graph formatting.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str  # SUPPLIER, RAW_LOT, WORK_ORDER, FINISHED_LOT, SHIPMENT, CUSTOMER
    is_contaminated: bool = False
    is_affected: bool = False
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "node_type": self.node_type,
            "is_contaminated": self.is_contaminated,
            "is_affected": self.is_affected,
            "attributes": self.attributes,
        }


@dataclass
class GraphEdge:
    source: str
    target: str
    relationship: str  # SUPPLIES, CONSUMES, PRODUCES, SHIPPED_IN, DELIVERED_TO
    quantity: Optional[float] = None
    uom: Optional[str] = None

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "quantity": self.quantity,
            "uom": self.uom,
        }


@dataclass
class TraceabilityGraph:
    root_id: str
    direction: str  # UPSTREAM, DOWNSTREAM, BIDIRECTIONAL
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode):
        if node.id not in self.nodes:
            self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)

    def to_dict(self):
        return {
            "root_id": self.root_id,
            "direction": self.direction,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }
