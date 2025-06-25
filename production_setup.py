#!/usr/bin/env python3
"""
Production setup script for TRACTools.
Handles database creation and initialization for production deployment.
"""

import os
import sys
import sqlite3
from pathlib import Path

def production_setup():
    """Set up TRACTools for production deployment."""
    print("TRACTools Production Setup")
    print("=========================")
    
    # Step 1: Create instance directory with proper permissions
    instance_dir = Path('instance')
    instance_dir.mkdir(mode=0o775, exist_ok=True)
    print(f"✅ Instance directory: {instance_dir.absolute()}")
    
    # Step 2: Create empty database file
    db_path = instance_dir / 'tractools.db'
    
    if not db_path.exists():
        try:
            # Create empty database file
            conn = sqlite3.connect(str(db_path))
            conn.close()
            
            # Set permissions for www-data group
            os.chmod(str(db_path), 0o664)
            
            print(f"✅ Database file created: {db_path.absolute()}")
        except Exception as e:
            print(f"❌ Failed to create database file: {e}")
            return False
    else:
        print(f"✅ Database file already exists: {db_path.absolute()}")
    
    # Step 3: Initialize Flask-Migrate
    print("\n📋 Next steps:")
    print("1. Run: flask db init")
    print("2. Run: flask db migrate -m 'Initial migration'") 
    print("3. Run: flask db upgrade")
    print("4. Run: flask init-db  # To create admin user")
    
    # Step 4: Set up proper ownership (if needed)
    print("\n🔧 If you get permission errors, run:")
    print(f"sudo chgrp www-data {instance_dir.absolute()}")
    print(f"sudo chgrp www-data {db_path.absolute()}")
    print(f"sudo chmod g+w {instance_dir.absolute()}")
    print(f"sudo chmod g+w {db_path.absolute()}")
    
    return True

if __name__ == '__main__':
    try:
        success = production_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)