"""Automatic ontology remapping using Claude API."""

import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from owlready2 import get_ontology
from anthropic import Anthropic
import structlog

from .validator import TripleValidator
from ..monitoring.diff_engine import SchemaDiff

logger = structlog.get_logger()


class OntologyRemapper:
    """
    Automatically remap ontology when database schema changes.
    
    Uses Claude API to analyze schema changes and generate updated
    ontology mappings.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.3,
        ontology_path: str = "ontologies/business_domain.owl",
        auto_approve: bool = False,
        validation_enabled: bool = True
    ):
        """
        Initialize ontology remapper.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
            temperature: LLM temperature
            ontology_path: Path to ontology file
            auto_approve: Whether to auto-approve changes
            validation_enabled: Whether to validate triples before applying
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.ontology_path = Path(ontology_path)
        self.auto_approve = auto_approve
        self.validation_enabled = validation_enabled
        self.validator = TripleValidator()
        self.approval_callback: Optional[Callable[[str, List[SchemaDiff]], bool]] = None
        
        logger.info(
            "Ontology remapper initialized",
            model=model,
            auto_approve=auto_approve
        )
    
    def set_approval_callback(self, callback: Callable[[str, List[SchemaDiff]], bool]) -> None:
        """Set callback for manual approval."""
        self.approval_callback = callback
    
    async def remap_ontology(
        self,
        diffs: List[SchemaDiff],
        current_ontology: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Remap ontology based on schema changes.
        
        Args:
            diffs: List of schema differences
            current_ontology: Current ontology object (optional)
            
        Returns:
            Dictionary with remapping results
        """
        logger.info("Starting ontology remapping", diff_count=len(diffs))
        
        # Extract current ontology mappings
        current_mappings = self._extract_current_mappings(current_ontology)
        
        # Generate LLM prompt
        prompt = self._generate_prompt(diffs, current_mappings)
        
        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract triples from response
            triples_text = self._extract_triples_from_response(response)
            
            if not triples_text:
                logger.error("No triples found in Claude response")
                return {
                    "success": False,
                    "error": "No triples found in response"
                }
            
            # Validate triples
            if self.validation_enabled:
                is_valid, error, _ = self.validator.validate_triples(triples_text)
                
                if not is_valid:
                    logger.error("Invalid triples generated", error=error)
                    return {
                        "success": False,
                        "error": error,
                        "triples": triples_text
                    }
                
                # Validate mappings match expected changes
                for diff in diffs:
                    valid, error = self.validator.validate_mapping_update(
                        triples_text,
                        diff.diff_type.value,
                        diff.table_name,
                        diff.column_name
                    )
                    if not valid:
                        logger.warning("Mapping validation warning", error=error)
            
            # Request approval if needed
            if not self.auto_approve and self.approval_callback:
                approved = self.approval_callback(triples_text, diffs)
                if not approved:
                    logger.info("Remapping not approved by user")
                    return {
                        "success": False,
                        "error": "Not approved by user",
                        "triples": triples_text
                    }
            
            # Apply updates to ontology
            result = await self._apply_ontology_updates(triples_text, diffs)
            
            logger.info("Ontology remapping completed", success=result["success"])
            return result
            
        except Exception as e:
            logger.error("Remapping failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_current_mappings(
        self,
        ontology: Optional[Any]
    ) -> Dict[str, Any]:
        """Extract current ontology mappings."""
        mappings = {
            "classes": {},
            "properties": {}
        }
        
        if not ontology:
            # Load ontology if not provided
            if self.ontology_path.exists():
                ontology = get_ontology(f"file://{self.ontology_path.absolute()}").load()
            else:
                logger.warning("Ontology file not found", path=str(self.ontology_path))
                return mappings
        
        # Extract class to table mappings
        for cls in ontology.classes():
            if hasattr(cls, "mapsToTable"):
                mappings["classes"][cls.name] = str(cls.mapsToTable)
        
        # Extract property to column mappings
        for prop in ontology.properties():
            if hasattr(prop, "mapsToColumn"):
                mappings["properties"][prop.name] = str(prop.mapsToColumn)
        
        return mappings
    
    def _generate_prompt(
        self,
        diffs: List[SchemaDiff],
        current_mappings: Dict[str, Any]
    ) -> str:
        """Generate LLM prompt for remapping."""
        
        # Format diffs
        diff_summary = []
        for diff in diffs:
            diff_summary.append({
                "type": diff.diff_type.value,
                "table": diff.table_name,
                "column": diff.column_name,
                "old_value": str(diff.old_value) if diff.old_value else None,
                "new_value": str(diff.new_value) if diff.new_value else None
            })
        
        prompt = f"""You are an ontology expert. The database schema has changed, and the ontology mappings need to be updated.

SCHEMA CHANGES:
{json.dumps(diff_summary, indent=2)}

CURRENT ONTOLOGY MAPPINGS:
{json.dumps(current_mappings, indent=2)}

INSTRUCTIONS:
1. Analyze the schema changes and current mappings
2. Generate RDF triples in Turtle format to update the ontology
3. Use predicates like :mapsToTable and :mapsToColumn
4. Handle renames by updating existing mappings
5. Handle additions by creating new mappings
6. Handle deletions by removing mappings (if needed)

OUTPUT FORMAT:
Generate ONLY valid Turtle RDF triples. No explanations, just the triples.
Example format:
:OrderClass :mapsToTable "orders" .
:OrderClass :hasProperty :customerId .
:customerId :mapsToColumn "customer_id" .

Generate the updated ontology triples:"""
        
        return prompt
    
    def _extract_triples_from_response(self, response: Any) -> str:
        """Extract Turtle triples from Claude API response."""
        import re

        # Extract text from response
        content = response.content

        if isinstance(content, list):
            text = ""
            for block in content:
                if hasattr(block, "text"):
                    text += block.text
                elif isinstance(block, dict) and "text" in block:
                    text += block["text"]
        elif isinstance(content, str):
            text = content
        else:
            text = str(content)

        # Strip markdown code blocks (```turtle, ```rdf, ``` etc.)
        # Pattern matches ```language\n...content...\n```
        code_block_pattern = r'```(?:turtle|rdf|ttl|n3)?\s*\n?(.*?)\n?```'
        matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)

        if matches:
            # Return the content from code blocks (joined if multiple)
            extracted = '\n'.join(matches)
            logger.debug("Extracted triples from markdown code blocks", length=len(extracted))
            text = extracted.strip()
        else:
            text = text.strip()

        # Add default prefix if triples use ":" prefix without declaration
        if text and ':' in text and not '@prefix' in text.lower() and not 'prefix :' in text.lower():
            # Add a default prefix for the ontology namespace
            default_prefix = '@prefix : <http://example.org/ontology#> .\n\n'
            text = default_prefix + text
            logger.debug("Added default prefix to triples")

        return text
    
    async def _apply_ontology_updates(
        self,
        triples: str,
        diffs: List[SchemaDiff]
    ) -> Dict[str, Any]:
        """Apply updates to ontology file."""
        try:
            # Read current ontology file
            if not self.ontology_path.exists():
                logger.error("Ontology file not found", path=str(self.ontology_path))
                return {
                    "success": False,
                    "error": "Ontology file not found"
                }
            
            # In production, use proper RDF manipulation
            # For now, append triples to ontology file
            # This is simplified - production should merge properly
            
            with open(self.ontology_path, "r") as f:
                current_content = f.read()
            
            # Append new triples
            # In production, properly merge with existing ontology
            updated_content = current_content + "\n\n# Auto-generated updates\n" + triples
            
            # Backup original file
            backup_path = self.ontology_path.with_suffix(".owl.backup")
            with open(backup_path, "w") as f:
                f.write(current_content)
            
            # Write updated ontology
            with open(self.ontology_path, "w") as f:
                f.write(updated_content)
            
            logger.info("Ontology updates applied", path=str(self.ontology_path))
            
            return {
                "success": True,
                "triples": triples,
                "backup_path": str(backup_path),
                "ontology_path": str(self.ontology_path)
            }
            
        except Exception as e:
            logger.error("Failed to apply ontology updates", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
