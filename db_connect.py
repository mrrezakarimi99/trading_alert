#!/usr/bin/env python3
"""
Database Connection Tool for Trading Bot
========================================

Tool to connect to and query the trading bot's SQLite database locally or remotely.
"""

import sqlite3
import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd


class DatabaseConnector:
    """Utility for connecting to the trading bot database."""
    
    def __init__(self, db_path: str):
        """Initialize database connector."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row  # Enable column access by name
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
    
    def get_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a table."""
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[1],
                'type': row[2],
                'not_null': bool(row[3]),
                'default': row[4],
                'primary_key': bool(row[5])
            })
        return columns
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame."""
        try:
            df = pd.read_sql_query(query, self.connection)
            return df
        except Exception as e:
            print(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        tables = self.get_tables()
        
        for table in tables:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        return stats
    
    def get_recent_data(self, table: str, limit: int = 10) -> pd.DataFrame:
        """Get recent data from a table."""
        query = f"""
        SELECT * FROM {table} 
        ORDER BY 
            CASE 
                WHEN datetime(timestamp) IS NOT NULL THEN datetime(timestamp)
                WHEN datetime(created_at) IS NOT NULL THEN datetime(created_at)
                ELSE datetime('now')
            END DESC 
        LIMIT {limit}
        """
        return self.execute_query(query)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Connect to Trading Bot Database")
    parser.add_argument("--db-path", "-d", 
                       default="data/database/trading.db",
                       help="Path to SQLite database file")
    parser.add_argument("--query", "-q", 
                       help="SQL query to execute")
    parser.add_argument("--table", "-t", 
                       help="Show recent data from specific table")
    parser.add_argument("--stats", "-s", 
                       action="store_true",
                       help="Show database statistics")
    parser.add_argument("--schema", 
                       help="Show schema for specific table")
    parser.add_argument("--list-tables", "-l", 
                       action="store_true",
                       help="List all tables")
    
    args = parser.parse_args()
    
    try:
        with DatabaseConnector(args.db_path) as db:
            if args.list_tables:
                print("📊 Available tables:")
                tables = db.get_tables()
                for table in tables:
                    print(f"  • {table}")
            
            elif args.schema:
                print(f"📋 Schema for table '{args.schema}':")
                schema = db.get_table_schema(args.schema)
                for col in schema:
                    pk = " (PRIMARY KEY)" if col['primary_key'] else ""
                    nn = " NOT NULL" if col['not_null'] else ""
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"  • {col['name']}: {col['type']}{pk}{nn}{default}")
            
            elif args.stats:
                print("📈 Database statistics:")
                stats = db.get_stats()
                for table, count in stats.items():
                    print(f"  • {table}: {count:,} records")
            
            elif args.table:
                print(f"📊 Recent data from '{args.table}':")
                df = db.get_recent_data(args.table)
                if not df.empty:
                    print(df.to_string(index=False))
                else:
                    print("  No data found")
            
            elif args.query:
                print("🔍 Query results:")
                df = db.execute_query(args.query)
                if not df.empty:
                    print(df.to_string(index=False))
                else:
                    print("  No results")
            
            else:
                # Default: show overview
                print("🗄️  Trading Bot Database Overview")
                print("=" * 40)
                
                # Show tables
                tables = db.get_tables()
                print(f"\n📊 Tables ({len(tables)}):")
                for table in tables:
                    print(f"  • {table}")
                
                # Show stats
                print("\n📈 Record counts:")
                stats = db.get_stats()
                for table, count in stats.items():
                    print(f"  • {table}: {count:,} records")
                
                print("\n💡 Usage examples:")
                print("  python db_connect.py --stats")
                print("  python db_connect.py --table price_data")
                print("  python db_connect.py --query 'SELECT * FROM trades LIMIT 5'")
                print("  python db_connect.py --schema trading_signals")
    
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\n💡 Make sure the database file exists and the path is correct.")
        print("   If using Docker, ensure volumes are mounted correctly.")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()