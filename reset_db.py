from app import app
from database import db
from models import User

print("Creating new database with updated schema...")

with app.app_context():
    # Drop all tables and recreate
    db.drop_all()
    db.create_all()
    print("✅ Database tables created successfully with all new columns!")
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@consultease.com',
        user_type='client',
        full_name='Administrator',
        phone='0000000000'
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin user created successfully!")
    print("   Username: admin")
    print("   Password: admin123")

print("\nDatabase reset complete!")