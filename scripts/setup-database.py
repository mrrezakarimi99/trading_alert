#!/usr/bin/env python3
"""
Database initialization script for the crypto trading system.
This script ensures the database and directories are properly set up.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import DatabaseService

def setup_directories():
    """Create necessary directories with proper permissions."""
    directories = [
        "data/csv",
        "data/database", 
        "logs"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
        
        # Set proper permissions (readable/writable by owner and group)
        try:
            os.chmod(dir_path, 0o755)
            print(f"✅ Set permissions for: {dir_path}")
        except Exception as e:
            print(f"⚠️  Could not set permissions for {dir_path}: {e}")

def test_database():
    """Test database initialization and basic operations."""
    try:
        print("🗄️  Testing database initialization...")
        
        # Initialize database service
        db_service = DatabaseService()
        
        # Test basic operations
        stats = db_service.get_database_stats()
        print(f"✅ Database initialized successfully")
        print(f"📊 Database statistics: {stats}")
        
        # Test write permissions by creating a test table
        db_path = str(db_service.db_path)
        if db_path != ":memory:":
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
                cursor.execute("DROP TABLE test_table")
                conn.commit()
            print("✅ Database write test successful")
        else:
            print("ℹ️  Using in-memory database (fallback mode)")
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🔧 Setting up crypto trading system database...")
    print("=" * 50)
    
    # Setup directories
    setup_directories()
    
    # Test database
    success = test_database()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Database setup completed successfully!")
        print("\n🚀 You can now start the trading system:")
        print("   - Docker: docker-compose up -d")
        print("   - Direct: python main.py")
    else:
        print("❌ Database setup failed!")
        print("\n🔍 Troubleshooting tips:")
        print("   1. Check file permissions in the data/ directory")
        print("   2. Ensure you have write access to the project directory")
        print("   3. Run with elevated permissions if necessary")
        sys.exit(1)

if __name__ == "__main__":
    main()