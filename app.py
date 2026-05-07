from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from datetime import datetime, time, timedelta
from sqlalchemy import or_
import os
import secrets
import threading

from config import Config
from database import db, login_manager
from models import User, ConsultantProfile, AvailabilitySlot, Appointment

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Store reset tokens
reset_tokens = {}

# ========== EMAIL FUNCTIONS ==========

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"Email sent successfully")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

def send_email(recipient, subject, body):
    msg = Message(
        subject=subject,
        recipients=[recipient],
        body=body,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    thr = threading.Thread(target=send_async_email, args=[app, msg])
    thr.start()

def send_password_reset_email(user):
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = user.email
    reset_link = url_for('reset_password', token=token, _external=True)
    
    email_body = f"""
Dear {user.full_name},

You requested to reset your password for ConsultantEase.

Click the link below to reset your password:

{reset_link}

This link will expire in 30 minutes.

If you did not request this, please ignore this email.

Best regards,
ConsultantEase Team
"""
    send_email(user.email, "Reset Your Password - ConsultantEase", email_body)

def send_booking_email(client, consultant, appointment_date, start_time, end_time):
    # Email to client
    client_body = f"""
Dear {client.full_name},

Your appointment has been successfully booked!

Appointment Details:
----------------------
Consultant: {consultant.full_name}
Profession: {consultant.profession}
Date: {appointment_date.strftime('%B %d, %Y')}
Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}

Thank you for using ConsultantEase!
"""
    
    # Email to consultant
    consultant_body = f"""
Dear {consultant.full_name},

A new appointment has been booked!

Appointment Details:
----------------------
Client: {client.full_name}
Client Email: {client.email}
Client Phone: {client.phone}
Date: {appointment_date.strftime('%B %d, %Y')}
Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}

Thank you for using ConsultantEase!
"""
    
    send_email(client.email, "Appointment Confirmation - ConsultantEase", client_body)
    send_email(consultant.email, "New Appointment Booked - ConsultantEase", consultant_body)

def send_cancellation_email(client, consultant, appointment_date, start_time, cancelled_by):
    client_body = f"""
Dear {client.full_name},

Your appointment has been cancelled.

Cancelled Appointment Details:
----------------------
Consultant: {consultant.full_name}
Date: {appointment_date.strftime('%B %d, %Y')}
Time: {start_time.strftime('%I:%M %p')}
Cancelled by: {cancelled_by}

You can book another appointment from your dashboard.

Thank you for using ConsultantEase!
"""
    
    consultant_body = f"""
Dear {consultant.full_name},

An appointment has been cancelled.

Cancelled Appointment Details:
----------------------
Client: {client.full_name}
Date: {appointment_date.strftime('%B %d, %Y')}
Time: {start_time.strftime('%I:%M %p')}
Cancelled by: {cancelled_by}

Thank you for using ConsultantEase!
"""
    
    send_email(client.email, "Appointment Cancelled - ConsultantEase", client_body)
    send_email(consultant.email, "Appointment Cancelled - ConsultantEase", consultant_body)

def verify_reset_token(token):
    email = reset_tokens.get(token)
    if email:
        del reset_tokens[token]
        return email
    return None

# ========== MAIN ROUTES ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        user_type = request.form.get('user_type')
        phone = request.form.get('phone')
        
        existing_user = User.query.filter(or_(User.username == username, User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            user_type=user_type,
            full_name=full_name,
            phone=phone
        )
        
        if user_type == 'consultant':
            user.profession = request.form.get('profession')
            user.experience = request.form.get('experience')
            user.bio = request.form.get('bio')
            user.hourly_rate = request.form.get('hourly_rate')
            user.license_number = request.form.get('license_number')
            user.is_verified = False
        
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            
            if user.username == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.user_type == 'consultant':
                return redirect(url_for('consultant_dashboard'))
            else:
                return redirect(url_for('client_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# ========== FORGOT PASSWORD ROUTES ==========

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                send_password_reset_email(user)
                flash('Password reset link has been sent to your email address.', 'success')
            except Exception as e:
                print(f"Email error: {e}")
                flash('Could not send email. Please try again later.', 'danger')
        else:
            flash('If an account exists with that email, you will receive a reset link.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset link. Please try again.', 'danger')
        return redirect(url_for('forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        user.set_password(new_password)
        db.session.commit()
        
        flash('Password reset successfully! Please login with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

# ========== ADMIN ROUTES ==========

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.username != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    pending_consultants = User.query.filter_by(user_type='consultant', is_verified=False).all()
    verified_consultants = User.query.filter_by(user_type='consultant', is_verified=True).all()
    
    return render_template('admin_dashboard.html', 
                         pending_consultants=pending_consultants,
                         verified_consultants=verified_consultants)

@app.route('/admin/verify/<int:consultant_id>')
@login_required
def verify_consultant(consultant_id):
    if current_user.username != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    consultant = User.query.get_or_404(consultant_id)
    consultant.is_verified = True
    consultant.verified_at = datetime.utcnow()
    consultant.verified_by = current_user.id
    
    db.session.commit()
    flash(f'Consultant {consultant.full_name} verified successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:consultant_id>')
@login_required
def reject_consultant(consultant_id):
    if current_user.username != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    consultant = User.query.get_or_404(consultant_id)
    db.session.delete(consultant)
    db.session.commit()
    
    flash(f'Consultant {consultant.full_name} rejected and removed!', 'warning')
    return redirect(url_for('admin_dashboard'))

# ========== CONSULTANT ROUTES ==========

@app.route('/consultant/dashboard')
@login_required
def consultant_dashboard():
    if current_user.user_type != 'consultant':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    appointments = Appointment.query.filter_by(consultant_id=current_user.id).order_by(Appointment.appointment_date).all()
    availability = AvailabilitySlot.query.filter_by(consultant_id=current_user.id).all()
    
    return render_template('consultant_dashboard.html', appointments=appointments, availability=availability)

@app.route('/consultant/availability/add', methods=['POST'])
@login_required
def add_availability():
    if current_user.user_type != 'consultant':
        return jsonify({'error': 'Unauthorized'}), 403
    
    day = int(request.form.get('day'))
    start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    
    slot = AvailabilitySlot(
        consultant_id=current_user.id,
        day_of_week=day,
        start_time=start_time,
        end_time=end_time
    )
    
    db.session.add(slot)
    db.session.commit()
    
    flash('Availability slot added successfully', 'success')
    return redirect(url_for('consultant_dashboard'))

@app.route('/consultant/availability/<int:slot_id>/delete')
@login_required
def delete_availability(slot_id):
    slot = AvailabilitySlot.query.get_or_404(slot_id)
    
    if slot.consultant_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(slot)
    db.session.commit()
    
    flash('Availability slot deleted successfully', 'success')
    return redirect(url_for('consultant_dashboard'))

# ========== CLIENT ROUTES ==========

@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.user_type != 'client':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    appointments = Appointment.query.filter_by(client_id=current_user.id).order_by(Appointment.appointment_date).all()
    
    consultants = User.query.filter_by(
        user_type='consultant', 
        is_available=True,
        is_verified=True
    ).order_by(User.is_verified.desc()).all()
    
    return render_template('client_dashboard.html', appointments=appointments, consultants=consultants)

# ========== CONSULTANT SEARCH & PROFILE ==========

@app.route('/consultants')
def list_consultants():
    profession = request.args.get('profession', '')
    
    query = User.query.filter_by(user_type='consultant', is_available=True, is_verified=True)
    
    if profession:
        query = query.filter(User.profession.ilike(f'%{profession}%'))
    
    consultants = query.order_by(User.is_verified.desc()).all()
    return render_template('consultants.html', consultants=consultants)

@app.route('/consultant/<int:consultant_id>')
def consultant_profile(consultant_id):
    consultant = User.query.get_or_404(consultant_id)
    
    if consultant.user_type != 'consultant':
        flash('Invalid consultant profile', 'danger')
        return redirect(url_for('index'))
    
    if not consultant.is_verified:
        flash('This consultant profile is not available yet.', 'warning')
        return redirect(url_for('list_consultants'))
    
    availability = AvailabilitySlot.query.filter_by(consultant_id=consultant_id, is_booked=False).all()
    
    return render_template('consultant_profile.html', consultant=consultant, availability=availability)

@app.route('/api/consultant/<int:consultant_id>/availability')
def get_consultant_availability(consultant_id):
    consultant = User.query.get_or_404(consultant_id)
    
    if not consultant.is_verified:
        return jsonify([])
    
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date parameter required'}), 400
    
    appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    day_of_week = appointment_date.weekday()
    
    slots = AvailabilitySlot.query.filter_by(
        consultant_id=consultant_id,
        day_of_week=day_of_week,
        is_booked=False
    ).all()
    
    existing_appointments = Appointment.query.filter_by(
        consultant_id=consultant_id,
        appointment_date=appointment_date,
        status='scheduled'
    ).all()
    
    booked_times = [(apt.start_time, apt.end_time) for apt in existing_appointments]
    
    available_slots = []
    for slot in slots:
        is_available = True
        for start, end in booked_times:
            if not (slot.end_time <= start or slot.start_time >= end):
                is_available = False
                break
        
        if is_available:
            available_slots.append({
                'id': slot.id,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M')
            })
    
    return jsonify(available_slots)

@app.route('/book/<int:consultant_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(consultant_id):
    if current_user.user_type != 'client':
        flash('Only clients can book appointments', 'danger')
        return redirect(url_for('index'))
    
    consultant = User.query.get_or_404(consultant_id)
    
    if not consultant.is_verified:
        flash('This consultant is not available for booking.', 'danger')
        return redirect(url_for('list_consultants'))
    
    if request.method == 'POST':
        appointment_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        notes = request.form.get('notes')
        
        existing = Appointment.query.filter_by(
            consultant_id=consultant_id,
            appointment_date=appointment_date,
            start_time=start_time,
            status='scheduled'
        ).first()
        
        if existing:
            flash('This time slot is no longer available', 'danger')
            return redirect(url_for('book_appointment', consultant_id=consultant_id))
        
        appointment = Appointment(
            client_id=current_user.id,
            consultant_id=consultant_id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            notes=notes
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Send email notifications
        try:
            send_booking_email(current_user, consultant, appointment_date, start_time, end_time)
            flash('Appointment booked successfully! Confirmation emails sent.', 'success')
        except Exception as e:
            print(f"Email error: {e}")
            flash('Appointment booked successfully! (Email notification failed)', 'warning')
        
        return redirect(url_for('client_dashboard'))
    
    return render_template('book_appointment.html', consultant=consultant)

@app.route('/appointment/<int:appointment_id>/cancel')
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if current_user.id not in [appointment.client_id, appointment.consultant_id]:
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    client = User.query.get(appointment.client_id)
    consultant = User.query.get(appointment.consultant_id)
    cancelled_by = current_user.full_name
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Send email notifications
    try:
        send_cancellation_email(client, consultant, appointment.appointment_date, appointment.start_time, cancelled_by)
        flash('Appointment cancelled successfully! Cancellation emails sent.', 'success')
    except Exception as e:
        print(f"Email error: {e}")
        flash('Appointment cancelled successfully! (Email notification failed)', 'warning')
    
    if current_user.user_type == 'consultant':
        return redirect(url_for('consultant_dashboard'))
    else:
        return redirect(url_for('client_dashboard'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    profession = request.args.get('profession', '')
    
    consultants = User.query.filter_by(user_type='consultant', is_available=True, is_verified=True)
    
    if query:
        consultants = consultants.filter(
            or_(
                User.full_name.ilike(f'%{query}%'),
                User.profession.ilike(f'%{query}%'),
                User.bio.ilike(f'%{query}%')
            )
        )
    
    if profession:
        consultants = consultants.filter(User.profession.ilike(f'%{profession}%'))
    
    consultants = consultants.all()
    
    return render_template('search_results.html', consultants=consultants, query=query)

# ========== ACCOUNT MANAGEMENT ROUTES ==========

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.email = request.form.get('email')
        
        if current_user.user_type == 'consultant':
            current_user.profession = request.form.get('profession')
            current_user.experience = request.form.get('experience')
            current_user.bio = request.form.get('bio')
            current_user.hourly_rate = request.form.get('hourly_rate')
            current_user.license_number = request.form.get('license_number')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
        if current_user.user_type == 'consultant':
            return redirect(url_for('consultant_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    
    return render_template('edit_profile.html')

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    user_id = current_user.id
    user_type = current_user.user_type
    
    if user_type == 'consultant':
        Appointment.query.filter_by(consultant_id=user_id).delete()
        AvailabilitySlot.query.filter_by(consultant_id=user_id).delete()
    else:
        Appointment.query.filter_by(client_id=user_id).delete()
    
    db.session.delete(current_user)
    db.session.commit()
    
    logout_user()
    flash('Your account has been deleted successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(old_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('logout'))
    
    return render_template('change_password.html')

# ========== DASHBOARD SETTINGS ROUTE ==========
@app.route('/dashboard-settings')
@login_required
def dashboard_settings():
    return render_template('dashboard_settings.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)