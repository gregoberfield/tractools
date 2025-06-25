#!/usr/bin/env python3
"""
Database setup script for TRACTools.
Creates the database and instance directory with proper permissions.
"""

import os
import sys
from pathlib import Path

def setup_database():
    """Set up the database and directories."""
    print("TRACTools Database Setup")
    print("=======================")
    
    # Create instance directory
    instance_dir = Path('instance')
    instance_dir.mkdir(mode=0o755, exist_ok=True)
    print(f"✅ Created instance directory: {instance_dir.absolute()}")
    
    # Check permissions
    if not os.access(instance_dir, os.W_OK):
        print(f"❌ Instance directory is not writable: {instance_dir.absolute()}")
        print("Run: sudo chown $USER:$USER instance && chmod 755 instance")
        return False
    
    # Test database creation
    db_path = instance_dir / 'tractools.db'
    try:
        # Try to create and write to the database file
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test_table (id INTEGER)")
        conn.execute("DROP TABLE test_table")
        conn.close()
        print(f"✅ Database path is writable: {db_path}")
        
        # Remove test database
        if db_path.exists():
            db_path.unlink()
            
    except Exception as e:
        print(f"❌ Cannot create database at {db_path}: {e}")
        return False
    
    print("\n✅ Database setup successful!")
    print("\nNext steps:")
    print("1. Run: flask db init")
    print("2. Run: flask db migrate -m 'Initial migration'")
    print("3. Run: flask db upgrade")
    print("4. Or run: flask init-db  # For initial setup without migrations")
    
    return True

if __name__ == '__main__':
    try:
        success = setup_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)