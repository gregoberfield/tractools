#!/usr/bin/env python3
"""
Debug script to check database path and permissions.
"""

import os
from pathlib import Path
from app import create_app

def debug_database():
    """Debug database path and permissions."""
    print("TRACTools Database Debug")
    print("=======================")
    
    app = create_app()
    
    with app.app_context():
        # Get the actual database URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"Database URI: {db_uri}")
        
        # Extract the actual file path
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri[10:]  # Remove 'sqlite:///'
            db_path = Path(db_path)
            
            print(f"Database file path: {db_path}")
            print(f"Absolute path: {db_path.absolute()}")
            
            # Check if it's relative or absolute
            if not db_path.is_absolute():
                # It's relative, so it's relative to the current working directory
                print(f"Current working directory: {Path.cwd()}")
                full_path = Path.cwd() / db_path
                print(f"Full resolved path: {full_path}")
            else:
                full_path = db_path
            
            # Check parent directory
            parent_dir = full_path.parent
            print(f"Parent directory: {parent_dir}")
            print(f"Parent exists: {parent_dir.exists()}")
            if parent_dir.exists():
                print(f"Parent permissions: {oct(parent_dir.stat().st_mode)[-3:]}")
                print(f"Parent owner: {parent_dir.owner()}:{parent_dir.group()}" if hasattr(parent_dir, 'owner') else "Cannot determine owner")
                print(f"Parent writable: {os.access(parent_dir, os.W_OK)}")
            
            # Check database file
            print(f"Database file exists: {full_path.exists()}")
            if full_path.exists():
                print(f"Database permissions: {oct(full_path.stat().st_mode)[-3:]}")
                print(f"Database owner: {full_path.owner()}:{full_path.group()}" if hasattr(full_path, 'owner') else "Cannot determine owner")
                print(f"Database readable: {os.access(full_path, os.R_OK)}")
                print(f"Database writable: {os.access(full_path, os.W_OK)}")
            
            # Test creating the file
            try:
                print("\nTesting database creation...")
                parent_dir.mkdir(parents=True, exist_ok=True)
                test_file = full_path.with_suffix('.test')
                test_file.touch()
                test_file.unlink()
                print("✅ Can create files in the directory")
            except Exception as e:
                print(f"❌ Cannot create files: {e}")
            
            # Check Flask instance path
            print(f"\nFlask instance path: {app.instance_path}")
            print(f"Instance path exists: {Path(app.instance_path).exists()}")
            print(f"Instance path writable: {os.access(app.instance_path, os.W_OK)}")

if __name__ == '__main__':
    debug_database()