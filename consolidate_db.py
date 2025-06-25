#!/usr/bin/env python3
"""
Database consolidation script for TRACTools.
Migrates data from old database file(s) to the new unified tractools.db
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

def find_existing_databases():
    """Find existing database files."""
    possible_names = ['weather_data.db', 'tractools.db']
    found_dbs = []
    
    # Check current directory
    for name in possible_names:
        if os.path.exists(name):
            found_dbs.append(name)
    
    # Check instance directory
    if os.path.exists('instance'):
        for name in possible_names:
            instance_path = os.path.join('instance', name)
            if os.path.exists(instance_path):
                found_dbs.append(instance_path)
    
    return found_dbs

def backup_database(db_path):
    """Create a backup of the database."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def consolidate_databases():
    """Consolidate existing databases into the new structure."""
    print("TRACTools Database Consolidation")
    print("===============================")
    
    # Find existing databases
    existing_dbs = find_existing_databases()
    
    if not existing_dbs:
        print("No existing databases found. New database will be created automatically.")
        return
    
    print(f"Found existing databases: {existing_dbs}")
    
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    target_db = os.path.join('instance', 'tractools.db')
    
    if os.path.exists(target_db):
        print(f"Target database {target_db} already exists.")
        response = input("Overwrite? (y/n): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return
        backup_database(target_db)
    
    # Find the most recent database with data
    source_db = None
    max_size = 0
    
    for db_path in existing_dbs:
        if db_path != target_db:
            size = os.path.getsize(db_path)
            if size > max_size:
                max_size = size
                source_db = db_path
    
    if source_db:
        print(f"Using {source_db} as source database (largest: {max_size} bytes)")
        
        # Create backup of source
        backup_database(source_db)
        
        # Copy to target location
        shutil.copy2(source_db, target_db)
        print(f"✅ Copied database to {target_db}")
        
        # Verify the copy worked
        try:
            conn = sqlite3.connect(target_db)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            print(f"✅ Verified database copy. Found tables: {[t[0] for t in tables]}")
            
        except Exception as e:
            print(f"❌ Error verifying database: {e}")
            return
        
        # Clean up old database files (after confirmation)
        print(f"\nOld database files found:")
        for db_path in existing_dbs:
            if db_path != target_db:
                print(f"  - {db_path}")
        
        cleanup = input("\nRemove old database files? (y/n): ").lower().strip()
        if cleanup in ['y', 'yes']:
            for db_path in existing_dbs:
                if db_path != target_db:
                    os.remove(db_path)
                    print(f"✅ Removed {db_path}")
    
    print(f"\n✅ Database consolidation complete!")
    print(f"Database location: {target_db}")
    print("\nNext steps:")
    print("1. Run: flask db init")
    print("2. Run: flask db stamp head  # Mark current schema as migrated")
    print("3. For future changes: flask db migrate -m 'description'")

if __name__ == '__main__':
    try:
        consolidate_databases()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)