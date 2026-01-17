"""Generate initial ontology from database schema."""

from pathlib import Path
import sys

def create_sample_ontology(output_path: str = "ontologies/business_domain.owl") -> None:
    """
    Create sample OWL ontology.
    
    Args:
        output_path: Path to output ontology file
    """
    ontology_dir = Path(output_path).parent
    ontology_dir.mkdir(parents=True, exist_ok=True)
    
    ontology_content = """<?xml version="1.0"?>
<rdf:RDF xmlns="http://example.org/ontology#"
     xml:base="http://example.org/ontology"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <owl:Ontology rdf:about="http://example.org/ontology"/>
    
    <!-- Classes -->
    <owl:Class rdf:about="#Customer">
        <rdfs:label>Customer</rdfs:label>
        <rdfs:comment>Represents a customer in the system</rdfs:comment>
    </owl:Class>
    
    <owl:Class rdf:about="#Order">
        <rdfs:label>Order</rdfs:label>
        <rdfs:comment>Represents an order placed by a customer</rdfs:comment>
    </owl:Class>
    
    <!-- Properties -->
    <owl:DatatypeProperty rdf:about="#customerId">
        <rdfs:domain rdf:resource="#Customer"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#integer"/>
        <rdfs:label>Customer ID</rdfs:label>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#email">
        <rdfs:domain rdf:resource="#Customer"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
        <rdfs:label>Email</rdfs:label>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#signupDate">
        <rdfs:domain rdf:resource="#Customer"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#date"/>
        <rdfs:label>Signup Date</rdfs:label>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#orderId">
        <rdfs:domain rdf:resource="#Order"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#integer"/>
        <rdfs:label>Order ID</rdfs:label>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#orderDate">
        <rdfs:domain rdf:resource="#Order"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#date"/>
        <rdfs:label>Order Date</rdfs:label>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#totalAmount">
        <rdfs:domain rdf:resource="#Order"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#decimal"/>
        <rdfs:label>Total Amount</rdfs:label>
    </owl:DatatypeProperty>
    
    <owl:ObjectProperty rdf:about="#hasOrder">
        <rdfs:domain rdf:resource="#Customer"/>
        <rdfs:range rdf:resource="#Order"/>
        <rdfs:label>Has Order</rdfs:label>
    </owl:ObjectProperty>
    
    <!-- Table Mappings -->
    <owl:Class rdf:about="#Customer">
        <mapsToTable>customers</mapsToTable>
    </owl:Class>
    
    <owl:Class rdf:about="#Order">
        <mapsToTable>orders</mapsToTable>
    </owl:Class>
    
    <!-- Column Mappings -->
    <owl:DatatypeProperty rdf:about="#customerId">
        <mapsToColumn>id</mapsToColumn>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#email">
        <mapsToColumn>email</mapsToColumn>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#signupDate">
        <mapsToColumn>signup_date</mapsToColumn>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#orderId">
        <mapsToColumn>id</mapsToColumn>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#orderDate">
        <mapsToColumn>order_date</mapsToColumn>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="#totalAmount">
        <mapsToColumn>total_amount</mapsToColumn>
    </owl:DatatypeProperty>
    
</rdf:RDF>
"""
    
    with open(output_path, "w") as f:
        f.write(ontology_content)
    
    print(f"Ontology created successfully: {output_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate initial ontology")
    parser.add_argument("--output", default="ontologies/business_domain.owl", help="Output ontology file path")
    
    args = parser.parse_args()
    
    try:
        create_sample_ontology(args.output)
        print("\nOntology generation complete!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
