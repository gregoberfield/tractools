#!/usr/bin/env python3
"""
Create the database file for TRACTools production deployment.
This script creates the database file without initializing Flask-Migrate.
"""

import os
import sqlite3
from pathlib import Path

def create_database():
    """Create the SQLite database file."""
    print("Creating TRACTools Database File")
    print("===============================")
    
    # Create instance directory
    instance_dir = Path('instance')
    instance_dir.mkdir(mode=0o775, exist_ok=True)
    print(f"✅ Instance directory ready: {instance_dir.absolute()}")
    
    # Create database file
    db_path = instance_dir / 'tractools.db'
    
    try:
        # Create empty database file
        conn = sqlite3.connect(str(db_path))
        conn.close()
        
        # Set proper permissions for web server
        os.chmod(str(db_path), 0o664)
        
        print(f"✅ Database file created: {db_path.absolute()}")
        print(f"✅ Database permissions set to 664")
        
        # Verify the file is accessible
        if os.access(str(db_path), os.R_OK | os.W_OK):
            print("✅ Database file is readable and writable")
        else:
            print("❌ Database file permission issue")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

if __name__ == '__main__':
    create_database()