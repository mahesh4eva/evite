from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_name = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    image_path = db.Column(db.String(200))
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    theme = db.Column(db.String(100))

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invitation_id = db.Column(db.Integer, db.ForeignKey('invitation.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    rsvp = db.Column(db.Boolean, nullable=True)
    rsvp_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Guest {self.name}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from flask_mail import Message
from flask import render_template, url_for
import logging

def send_invitation_email(invitation, guest):
    try:
        # Replace non-breaking spaces with regular spaces for event_name and email
        event_name = invitation.event_name.replace('\xa0', ' ')
        guest_email = guest.email.replace('\xa0', ' ')

        # Ensure that strings are UTF-8 encoded (in case there are other non-ASCII characters)
        event_name_utf8 = event_name.encode('utf-8').decode('utf-8')
        guest_email_utf8 = guest_email.encode('utf-8').decode('utf-8')

        # Create the email message with UTF-8 encoded strings
        msg = Message(f"You're invited to {event_name_utf8}!",
                      recipients=[guest_email_utf8])
        
        # Generate RSVP link
        rsvp_link = url_for('rsvp', token=guest.id, _external=True)

        # Render the email template (Flask-Mail uses UTF-8 by default for email bodies)
        msg.html = render_template('email_template.html', 
                                   invitation=invitation, 
                                   guest=guest, 
                                   rsvp_link=rsvp_link)
        
        # Send the email
        mail.send(msg)
        return True
    except Exception as e:
        # Log the error with the proper guest email
        logging.error(f"Failed to send email to {guest_email_utf8}: {str(e)}")
        return False



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    invitations = Invitation.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', invitations=invitations)

# Make sure this is at the top of your file, after other imports
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

@app.route('/create_invitation', methods=['GET', 'POST'])
@login_required
def create_invitation():
    if request.method == 'POST':
        event_name = request.form['event_name']
        try:
            event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('create_invitation'))

        description = request.form['description']
        location = request.form['location']
        theme = request.form['theme']
        image = request.files.get('image')

        # Form validation
        if not event_name or not event_date or not location:
            flash('Event name, date, and location are required.', 'error')
            return redirect(url_for('create_invitation'))

        # Handle image upload
        try:
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
            else:
                image_path = None
        except Exception as e:
            flash('Error uploading the image. Please try again.', 'error')
            return redirect(url_for('create_invitation'))

        # Create new invitation
        invitation = Invitation(user_id=current_user.id, event_name=event_name, event_date=event_date, 
                                image_path=image_path, description=description, location=location, theme=theme)
        db.session.add(invitation)
        db.session.commit()

        # Process guest list
        guest_list = request.form.get('guest_list', '').strip()
        guests = re.split(r'[\n,]', guest_list)
        
        for guest in guests:
            name_email = guest.split(',')
            if len(name_email) == 2:
                name = name_email[0].strip()
                email = name_email[1].strip()
                if re.match(r'[^@]+@[^@]+\.[^@]+', email):  # Basic email validation
                    guest_obj = Guest(invitation_id=invitation.id, name=name, email=email)
                    db.session.add(guest_obj)
                    send_invitation_email(invitation, guest_obj)
        
        db.session.commit()  # Commit once after processing all guests
        
        flash('Invitation created and emails sent successfully!')
        return redirect(url_for('dashboard'))

    return render_template('create_invitation.html')


@app.route('/edit_invitation/<int:invitation_id>', methods=['GET', 'POST'])
@login_required
def edit_invitation(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to edit this invitation.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        invitation.event_name = request.form['event_name']
        invitation.event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%d')
        invitation.description = request.form['description']
        invitation.location = request.form['location']
        invitation.theme = request.form['theme']

        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            invitation.image_path = os.path.join('uploads', filename)

        db.session.commit()
        flash('Invitation updated successfully!')
        return redirect(url_for('preview_invitation', invitation_id=invitation.id))

    return render_template('edit_invitation.html', invitation=invitation)

@app.route('/delete_invitation/<int:invitation_id>', methods=['POST'])
@login_required
def delete_invitation(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to delete this invitation.')
        return redirect(url_for('dashboard'))

    db.session.delete(invitation)
    db.session.commit()
    flash('Invitation deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/preview_invitation/<int:invitation_id>')
@login_required
def preview_invitation(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to view this invitation.')
        return redirect(url_for('dashboard'))
    return render_template('preview_invitation.html', invitation=invitation)

@app.route('/send_invitations/<int:invitation_id>')
@login_required
def send_invitations(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to send invitations for this event.')
        return redirect(url_for('dashboard'))

    guests = Guest.query.filter_by(invitation_id=invitation_id).all()
    
    for guest in guests:
        msg = Message(f"Invitation to {invitation.event_name}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[guest.email])
        msg.html = render_template('email_template.html', invitation=invitation, guest=guest)
        mail.send(msg)
    
    flash('Invitations sent successfully!')
    return redirect(url_for('dashboard'))

@app.route('/rsvp_status/<int:invitation_id>')
@login_required
def rsvp_status(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to view RSVP status for this event.')
        return redirect(url_for('dashboard'))

    guests = Guest.query.filter_by(invitation_id=invitation_id).all()
    return render_template('rsvp_status.html', invitation=invitation, guests=guests)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.')
            return redirect(url_for('signup'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.')
            return redirect(url_for('signup'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'filename': os.path.join('uploads', filename)}), 200

@app.route('/manage_guests/<int:invitation_id>', methods=['GET', 'POST'])
@login_required
def manage_guests(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to manage guests for this invitation.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        guest = Guest(invitation_id=invitation_id, name=name, email=email)
        db.session.add(guest)
        db.session.commit()
        flash('Guest added successfully!')

    guests = Guest.query.filter_by(invitation_id=invitation_id).all()
    print(f"Fetched {len(guests)} guests for invitation {invitation_id}")  # Debug output
    for guest in guests:
        print(f"Guest: {guest.name}, {guest.email}")  # Debug output

    return render_template('manage_guests.html', invitation=invitation, guests=guests)

@app.route('/view_rsvps/<int:invitation_id>')
@login_required
def view_rsvps(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to view RSVPs for this invitation.')
        return redirect(url_for('dashboard'))

    guests = Guest.query.filter_by(invitation_id=invitation_id).all()
    return render_template('view_rsvps.html', invitation=invitation, guests=guests)

@app.route('/remove_guest/<int:guest_id>', methods=['POST'])
@login_required
def remove_guest(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    invitation = Invitation.query.get(guest.invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to remove this guest.')
        return redirect(url_for('dashboard'))

    db.session.delete(guest)
    db.session.commit()
    flash('Guest removed successfully!')
    return redirect(url_for('manage_guests', invitation_id=invitation.id))

from datetime import datetime

@app.route('/rsvp/<token>', methods=['GET', 'POST'])
def rsvp(token):
    guest = Guest.query.filter_by(id=token).first_or_404()
    invitation = Invitation.query.get(guest.invitation_id)
    
    if request.method == 'POST':
        response = request.form.get('response')
        if response in ['accept', 'decline']:
            guest.rsvp = (response == 'accept')
            guest.rsvp_date = datetime.utcnow()
            db.session.commit()
            flash('Thank you for your response!', 'success')
            return redirect(url_for('rsvp', token=token))
    
    return render_template('rsvp.html', guest=guest, invitation=invitation)

from flask import url_for, flash, redirect
from flask_login import login_required, current_user

@app.route('/send_reminders/<int:invitation_id>')
@login_required
def send_reminders(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.user_id != current_user.id:
        flash('You do not have permission to send reminders for this invitation.', 'error')
        return redirect(url_for('dashboard'))

    guests_without_response = Guest.query.filter_by(invitation_id=invitation_id, rsvp=None).all()
    
    for guest in guests_without_response:
        send_reminder_email(invitation, guest)

    flash(f'Reminder emails sent to {len(guests_without_response)} guests.', 'success')
    return redirect(url_for('view_rsvps', invitation_id=invitation_id))

def send_reminder_email(invitation, guest):
    msg = Message(f"Reminder: RSVP for {invitation.event_name}",
                  recipients=[guest.email])
    
    rsvp_link = url_for('rsvp', token=guest.id, _external=True)
    
    msg.html = render_template('reminder_email_template.html', 
                               invitation=invitation, 
                               guest=guest, 
                               rsvp_link=rsvp_link)
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send reminder email to {guest.email}: {str(e)}")
        return False

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
