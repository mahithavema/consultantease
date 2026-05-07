from app import app
from database import db
from models import User, ConsultantProfile, AvailabilitySlot, Appointment

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Create sample data (optional)
        create_sample_data()

def create_sample_data():
    # Check if data already exists
    if User.query.first() is None:
        print("Creating sample data...")
        
        # Create sample consultant
        consultant = User(
            username="dr_smith",
            email="smith@example.com",
            user_type="consultant",
            full_name="Dr. John Smith",
            phone="+1234567890",
            profession="Psychologist",
            experience=10,
            bio="Experienced psychologist specializing in cognitive behavioral therapy",
            hourly_rate=150.0,
            license_number="LIC12345",
            is_verified=True
        )
        consultant.set_password("password123")
        
        # Create sample client
        client = User(
            username="jane_doe",
            email="jane@example.com",
            user_type="client",
            full_name="Jane Doe",
            phone="+0987654321"
        )
        client.set_password("password123")
        
        db.session.add(consultant)
        db.session.add(client)
        db.session.commit()
        print("Sample data created successfully!")
        print("Consultant login: dr_smith / password123")
        print("Client login: jane_doe / password123")

if __name__ == "__main__":
    init_database()