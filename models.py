from datetime import datetime
from flask_login import UserMixin
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'consultant' or 'client'
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Consultant specific fields
    profession = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    bio = db.Column(db.Text)
    hourly_rate = db.Column(db.Float)
    is_available = db.Column(db.Boolean, default=True)
    
    # Verification fields
    is_verified = db.Column(db.Boolean, default=False)
    license_number = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    consultant_profile = db.relationship('ConsultantProfile', backref='user', uselist=False)
    appointments_as_client = db.relationship('Appointment', foreign_keys='Appointment.client_id', backref='client')
    appointments_as_consultant = db.relationship('Appointment', foreign_keys='Appointment.consultant_id', backref='consultant')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ConsultantProfile(db.Model):
    __tablename__ = 'consultant_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    qualifications = db.Column(db.Text)
    specialties = db.Column(db.String(200))
    languages = db.Column(db.String(200))

class AvailabilitySlot(db.Model):
    __tablename__ = 'availability_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    consultant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 (Monday-Sunday)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    
    # Relationship
    consultant = db.relationship('User', backref='availability_slots')
    
class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    consultant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.id}: {self.appointment_date} {self.start_time}>'