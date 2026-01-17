"""Initialize sample database for testing."""

import sqlite3
from pathlib import Path
import sys

def create_database(db_path: str = "test_database.db") -> None:
    """
    Create sample SQLite database with test data.
    
    Args:
        db_path: Path to database file
    """
    # Remove existing database if it exists
    db_file = Path(db_path)
    if db_file.exists():
        print(f"Removing existing database: {db_path}")
        db_file.unlink()
    
    # Create database and tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            signup_date TEXT NOT NULL,
            name TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # Create orders table
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    # Insert sample customers
    customers = [
        ("alice@example.com", "2024-01-15", "Alice Smith", "active"),
        ("bob@example.com", "2024-02-20", "Bob Jones", "active"),
        ("charlie@example.com", "2024-03-10", "Charlie Brown", "inactive"),
        ("diana@example.com", "2024-01-25", "Diana Prince", "active"),
    ]
    
    cursor.executemany("""
        INSERT INTO customers (email, signup_date, name, status)
        VALUES (?, ?, ?, ?)
    """, customers)
    
    # Insert sample orders
    orders = [
        (1, "2024-01-20", 99.99, "completed"),
        (1, "2024-02-15", 149.50, "completed"),
        (2, "2024-02-25", 79.99, "pending"),
        (2, "2024-03-05", 199.99, "completed"),
        (4, "2024-02-01", 299.99, "completed"),
        (4, "2024-02-20", 49.99, "completed"),
        (4, "2024-03-15", 129.99, "pending"),
    ]
    
    cursor.executemany("""
        INSERT INTO orders (customer_id, order_date, total_amount, status)
        VALUES (?, ?, ?, ?)
    """, orders)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"Database created successfully: {db_path}")
    print(f"  - customers table: {len(customers)} records")
    print(f"  - orders table: {len(orders)} records")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize sample database")
    parser.add_argument("--db-path", default="test_database.db", help="Database file path")
    
    args = parser.parse_args()
    
    try:
        create_database(args.db_path)
        print("\nDatabase initialization complete!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
