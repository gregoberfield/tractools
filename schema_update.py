#!/usr/bin/env python3
"""
Schema update script for TRACTools database.
Use this to manually add new tables without affecting existing data.
"""

import os
import sys
from app import create_app
from tools.weather.models import db

def update_schema():
    """Update database schema by adding new tables."""
    app = create_app()
    
    with app.app_context():
        print("Current database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
        
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"Existing tables: {existing_tables}")
        
        # Create any new tables that don't exist
        # This will only create tables that are missing, not modify existing ones
        db.create_all()
        
        # Check tables after update
        inspector = db.inspect(db.engine)
        updated_tables = inspector.get_table_names()
        
        print(f"Tables after update: {updated_tables}")
        
        new_tables = set(updated_tables) - set(existing_tables)
        if new_tables:
            print(f"Added new tables: {new_tables}")
        else:
            print("No new tables added.")

if __name__ == '__main__':
    print("TRACTools Schema Update Script")
    print("==============================")
    
    # Backup reminder
    print("\n⚠️  IMPORTANT: Make sure you have a backup of your database before proceeding!")
    print("   This script will add new tables but won't modify existing data.")
    
    response = input("\nDo you want to proceed? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        try:
            update_schema()
            print("\n✅ Schema update completed successfully!")
        except Exception as e:
            print(f"\n❌ Error updating schema: {e}")
            sys.exit(1)
    else:
        print("Schema update cancelled.")
        sys.exit(0)