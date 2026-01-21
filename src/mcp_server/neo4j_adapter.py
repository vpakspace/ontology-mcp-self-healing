"""Neo4j adapter for MCP Server - translates semantic queries to Cypher."""

from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase
import structlog

logger = structlog.get_logger()


class Neo4jAdapter:
    """
    Adapter for Neo4j graph database.

    Translates ontology-based queries to Cypher queries.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "testpassword"
    ):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Neo4j adapter initialized", uri=uri)

    def close(self):
        """Close the driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(
        self,
        label: str,
        query: str,
        column_mappings: Dict[str, str],
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a semantic query against Neo4j.

        Args:
            label: Node label (e.g., 'Customer', 'Order')
            query: Natural language or structured query
            column_mappings: Map of property names to return
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Query result dictionary
        """
        try:
            # Build Cypher query
            cypher = self._build_cypher_query(label, query, column_mappings, limit, offset)

            with self.driver.session() as session:
                result = session.run(cypher)
                records = [dict(record) for record in result]

                # Flatten nested 'n' properties if present
                data = []
                for record in records:
                    if 'n' in record and hasattr(record['n'], '_properties'):
                        data.append(dict(record['n']._properties))
                    elif 'n' in record and isinstance(record['n'], dict):
                        data.append(record['n'])
                    else:
                        data.append(record)

                logger.info("Neo4j query executed", label=label, row_count=len(data))

                return {
                    "success": True,
                    "data": data,
                    "count": len(data),
                    "cypher": cypher
                }

        except Exception as e:
            logger.error("Neo4j query failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "cypher": cypher if 'cypher' in locals() else None
            }

    def _build_cypher_query(
        self,
        label: str,
        query: str,
        column_mappings: Dict[str, str],
        limit: int,
        offset: int
    ) -> str:
        """Build Cypher query from semantic query."""
        # Map ontology properties to Neo4j properties
        properties = list(column_mappings.values()) if column_mappings else ['id', 'email', 'name']

        # Build RETURN clause
        return_props = ", ".join([f"n.{prop} as {prop}" for prop in properties])

        # Base query
        cypher = f"MATCH (n:{label})"

        # Add WHERE clause for filters
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ["where", "filter", "find", "status"]):
            # Simple keyword extraction
            if "active" in query_lower:
                cypher += " WHERE n.status = 'active'"
            elif "inactive" in query_lower:
                cypher += " WHERE n.status = 'inactive'"
            elif "completed" in query_lower:
                cypher += " WHERE n.status = 'completed'"
            elif "pending" in query_lower:
                cypher += " WHERE n.status = 'pending'"

        cypher += f" RETURN {return_props}"
        cypher += f" SKIP {offset} LIMIT {limit}"

        return cypher

    def execute_graph_query(
        self,
        query_type: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute graph-specific queries (relationships, paths, etc.)

        Args:
            query_type: Type of graph query
            params: Query parameters

        Returns:
            Query result dictionary
        """
        params = params or {}

        try:
            with self.driver.session() as session:
                if query_type == "customer_orders":
                    # Get customer with their orders
                    customer_id = params.get("customer_id")
                    cypher = """
                        MATCH (c:Customer {id: $customer_id})-[:PLACED]->(o:Order)
                        RETURN c.name as customer_name, c.email as customer_email,
                               collect({id: o.id, date: o.order_date, amount: o.total_amount, status: o.status}) as orders
                    """
                    result = session.run(cypher, customer_id=customer_id)

                elif query_type == "top_customers":
                    # Get customers with most orders
                    limit = params.get("limit", 5)
                    cypher = """
                        MATCH (c:Customer)-[:PLACED]->(o:Order)
                        RETURN c.name as customer, c.email as email,
                               count(o) as order_count, sum(o.total_amount) as total_spent
                        ORDER BY total_spent DESC
                        LIMIT $limit
                    """
                    result = session.run(cypher, limit=limit)

                elif query_type == "revenue_summary":
                    # Get total revenue
                    cypher = """
                        MATCH (o:Order)
                        RETURN count(o) as total_orders,
                               sum(o.total_amount) as total_revenue,
                               avg(o.total_amount) as avg_order_value
                    """
                    result = session.run(cypher)

                else:
                    return {"success": False, "error": f"Unknown query type: {query_type}"}

                data = [dict(record) for record in result]

                return {
                    "success": True,
                    "data": data,
                    "count": len(data),
                    "query_type": query_type
                }

        except Exception as e:
            logger.error("Graph query failed", query_type=query_type, error=str(e))
            return {"success": False, "error": str(e)}
