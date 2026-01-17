"""Triple validation for ontology updates."""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
import structlog

logger = structlog.get_logger()


class TripleValidator:
    """Validator for RDF triples and ontology updates."""
    
    def __init__(self):
        """Initialize the triple validator."""
        logger.info("Triple validator initialized")
    
    def validate_triples(
        self,
        triples: str,
        format: str = "turtle"
    ) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
        """
        Validate RDF triples.
        
        Args:
            triples: RDF triples in Turtle or other format
            format: RDF format (turtle, xml, json-ld, etc.)
            
        Returns:
            Tuple of (is_valid, error_message, parsed_triples)
        """
        try:
            # Parse triples
            graph = Graph()
            graph.parse(data=triples, format=format)
            
            # Extract triples
            parsed_triples = []
            for s, p, o in graph:
                parsed_triples.append({
                    "subject": str(s),
                    "predicate": str(p),
                    "object": str(o)
                })
            
            logger.info("Triples validated", count=len(parsed_triples))
            return True, None, parsed_triples
            
        except Exception as e:
            error_msg = f"Invalid triples: {str(e)}"
            logger.error("Triple validation failed", error=str(e))
            return False, error_msg, []
    
    def validate_mapping_update(
        self,
        triples: str,
        diff_type: str,
        table_name: str,
        column_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that triple updates match expected schema changes.
        
        Args:
            triples: Proposed RDF triples
            diff_type: Type of schema change
            table_name: Name of affected table
            column_name: Name of affected column (if applicable)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error, parsed = self.validate_triples(triples)
        
        if not is_valid:
            return False, error
        
        # Check that triples relate to the expected changes
        # This is a simplified validation - production would have more checks
        
        # Look for :mapsToTable or :mapsToColumn predicates
        has_table_mapping = any(
            ":mapsToTable" in t["predicate"] or "mapsToTable" in t["predicate"]
            for t in parsed
        )
        
        has_column_mapping = any(
            ":mapsToColumn" in t["predicate"] or "mapsToColumn" in t["predicate"]
            for t in parsed
        )
        
        # Basic validation based on diff type
        if "COLUMN" in diff_type and not has_column_mapping:
            return False, "Expected column mapping not found in triples"
        
        if "TABLE" in diff_type and not has_table_mapping:
            return False, "Expected table mapping not found in triples"
        
        logger.info("Mapping update validated", diff_type=diff_type)
        return True, None
    
    def extract_mappings(
        self,
        triples: str,
        format: str = "turtle"
    ) -> Dict[str, Any]:
        """
        Extract table and column mappings from triples.
        
        Args:
            triples: RDF triples
            format: RDF format
            
        Returns:
            Dictionary with extracted mappings
        """
        is_valid, error, parsed = self.validate_triples(triples, format)
        
        if not is_valid:
            logger.warning("Cannot extract mappings from invalid triples", error=error)
            return {}
        
        mappings = {
            "table_mappings": {},
            "column_mappings": {}
        }
        
        for triple in parsed:
            subject = triple["subject"]
            predicate = triple["predicate"]
            obj = triple["object"]
            
            if ":mapsToTable" in predicate or "mapsToTable" in predicate:
                # Extract class name from subject
                class_name = subject.split("#")[-1].split("/")[-1]
                table_name = obj.strip('"').strip("'")
                mappings["table_mappings"][class_name] = table_name
            
            if ":mapsToColumn" in predicate or "mapsToColumn" in predicate:
                # Extract property name from subject
                prop_name = subject.split("#")[-1].split("/")[-1]
                column_name = obj.strip('"').strip("'")
                mappings["column_mappings"][prop_name] = column_name
        
        logger.info("Mappings extracted", mappings_count=len(mappings["table_mappings"]) + len(mappings["column_mappings"]))
        return mappings
