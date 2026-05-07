from app import app
from database import db
from models import User

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
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
    else:
        print("⚠️ Admin user already exists!")