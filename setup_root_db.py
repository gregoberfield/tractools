#!/usr/bin/env python3
"""
Create database in root directory for TRACTools.
"""

import os
import sqlite3
from pathlib import Path

def create_root_database():
    """Create the SQLite database file in root directory."""
    print("Creating TRACTools Database in Root Directory")
    print("============================================")
    
    # Create database file in root directory
    db_path = Path('tractools.db')
    
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
    create_root_database()