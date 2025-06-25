#!/usr/bin/env python3
"""
User management script for TRACTools.
"""

import sys
import getpass
from app import create_app
from auth_models import User, db

def change_admin_password():
    """Change the admin password."""
    app = create_app()
    
    with app.app_context():
        print("TRACTools Admin Password Change")
        print("==============================")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print()
        
        # Get username
        username = input("Admin username [admin]: ").strip() or "admin"
        
        # Find the user
        user = User.get_admin_user(username)
        
        if not user:
            print(f"❌ Admin user '{username}' not found.")
            
            # Offer to create new admin
            create_new = input(f"Create new admin user '{username}'? (y/n): ").lower().strip()
            if create_new in ['y', 'yes']:
                user = User(username=username, is_admin=True)
                db.session.add(user)
            else:
                print("Operation cancelled.")
                return
        
        # Get new password
        while True:
            password1 = getpass.getpass("New password: ")
            password2 = getpass.getpass("Confirm password: ")
            
            if not password1:
                print("❌ Password cannot be empty.")
                continue
                
            if password1 != password2:
                print("❌ Passwords don't match. Please try again.")
                continue
                
            if len(password1) < 8:
                print("❌ Password must be at least 8 characters long.")
                continue
                
            break
        
        # Update password
        user.set_password(password1)
        db.session.commit()
        
        print(f"✅ Password updated successfully for user '{username}'")

def list_users():
    """List all admin users."""
    app = create_app()
    
    with app.app_context():
        users = User.query.filter_by(is_admin=True).all()
        
        print("TRACTools Admin Users")
        print("====================")
        
        if not users:
            print("No admin users found.")
            return
            
        for user in users:
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else "Never"
            print(f"Username: {user.username}")
            print(f"Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Last Login: {last_login}")
            print("-" * 40)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'change-password':
            change_admin_password()
        elif command == 'list':
            list_users()
        else:
            print("Unknown command. Use 'change-password' or 'list'")
    else:
        print("Usage:")
        print("  python manage_users.py change-password  # Change admin password")
        print("  python manage_users.py list            # List admin users")