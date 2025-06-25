#!/usr/bin/env python3
"""
Check the actual database path Flask is using.
"""

import os
from pathlib import Path
from config import Config

def check_paths():
    """Check database path resolution."""
    print("Database Path Check")
    print("==================")
    
    config = Config()
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Config SQLITE_DB_PATH: {config.SQLITE_DB_PATH}")
    print(f"Config SQLALCHEMY_DATABASE_URI: {config.SQLALCHEMY_DATABASE_URI}")
    
    # Extract path from URI
    uri = config.SQLALCHEMY_DATABASE_URI
    if uri.startswith('sqlite:///'):
        db_path = uri[10:]  # Remove 'sqlite:///'
        print(f"Extracted database path: {db_path}")
        print(f"Is absolute: {os.path.isabs(db_path)}")
        
        if not os.path.isabs(db_path):
            full_path = os.path.join(os.getcwd(), db_path)
            print(f"Full resolved path: {full_path}")
        else:
            full_path = db_path
            
        print(f"Database file exists: {os.path.exists(full_path)}")
        
        if os.path.exists(full_path):
            print(f"File permissions: {oct(os.stat(full_path).st_mode)[-3:]}")
            print(f"File readable: {os.access(full_path, os.R_OK)}")
            print(f"File writable: {os.access(full_path, os.W_OK)}")
        
        # Check parent directory
        parent_dir = os.path.dirname(full_path)
        print(f"Parent directory: {parent_dir}")
        print(f"Parent exists: {os.path.exists(parent_dir)}")
        if os.path.exists(parent_dir):
            print(f"Parent readable: {os.access(parent_dir, os.R_OK)}")
            print(f"Parent writable: {os.access(parent_dir, os.W_OK)}")

if __name__ == '__main__':
    check_paths()