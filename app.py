import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
babel = Babel(app)
csrf = CSRFProtect(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class SubscriberForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Save')

def get_locale():
    return request.accept_languages.best_match(['en', 'es'])

babel.init_app(app, locale_selector=get_locale)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        try:
            valid = validate_email(email)
            email = valid.email
            
            existing_subscriber = Subscriber.query.filter_by(email=email).first()
            if existing_subscriber:
                return jsonify({"success": False, "message": "email_already_subscribed"}), 400
            
            new_subscriber = Subscriber(email=email)
            db.session.add(new_subscriber)
            db.session.commit()
            return jsonify({"success": True, "message": "subscription_successful"}), 200
        except EmailNotValidError:
            return jsonify({"success": False, "message": "invalid_email"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": "subscription_error"}), 500
    else:
        return jsonify({"success": False, "message": "email_required"}), 400

@app.route('/change_language', methods=['POST'])
def change_language():
    lang = request.form.get('lang', 'en')
    if lang in ['en', 'es']:
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "message": "Invalid language"}), 400

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    logger.info('Admin login route accessed')
    init_db()  # Ensure admin user is created
    form = AdminLoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        logger.debug(f"Login attempt for username: {username}")
        
        admin = Admin.query.filter_by(username=username).first()
        logger.debug(f"Retrieved admin: {admin}")
        
        if admin:
            logger.debug(f"Admin from database: {admin.__dict__}")
            logger.debug(f"Provided password: {password}")
            logger.debug(f"Stored hashed password: {admin.password}")
            password_check = check_password_hash(admin.password, password)
            logger.debug(f"Password check result: {password_check}")
            if password_check:
                logger.debug("Password check successful")
                session['admin_id'] = admin.id
                return redirect(url_for('admin_dashboard'))
            else:
                logger.debug("Password check failed")
        else:
            logger.debug("Admin not found")
        
        flash('Invalid username or password', 'error')
    return render_template('admin_login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    subscribers = Subscriber.query.all()
    return render_template('admin_dashboard.html', subscribers=subscribers)

@app.route('/admin/edit_subscriber/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subscriber(id):
    subscriber = Subscriber.query.get_or_404(id)
    form = SubscriberForm(obj=subscriber)
    if form.validate_on_submit():
        try:
            subscriber.email = form.email.data
            db.session.commit()
            flash('Subscriber updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the subscriber.', 'error')
    return render_template('edit_subscriber.html', form=form, subscriber=subscriber)

@app.route('/admin/delete_subscriber/<int:id>', methods=['POST'])
@login_required
def delete_subscriber(id):
    subscriber = Subscriber.query.get_or_404(id)
    try:
        db.session.delete(subscriber)
        db.session.commit()
        flash('Subscriber deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the subscriber.', 'error')
    return redirect(url_for('admin_dashboard'))

def init_db():
    with app.app_context():
        try:
            # Test database connection
            result = db.session.execute(db.text('SELECT 1'))
            logger.info(f'Database connection test result: {result.scalar()}')
            
            db.create_all()
            
            admin = Admin.query.filter_by(username="admin").first()
            if not admin:
                logger.info("Creating admin user")
                hashed_password = generate_password_hash("admin123")
                logger.debug(f"Generated hash for admin password: {hashed_password}")
                new_admin = Admin(username="admin", password=hashed_password)
                db.session.add(new_admin)
                db.session.commit()
                logger.info(f'Admin user created with username: {new_admin.username}')
            else:
                logger.info("Admin user already exists")
            
            verify_admin_credentials()
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")

def verify_admin_credentials():
    admin = Admin.query.filter_by(username='admin').first()
    if admin and check_password_hash(admin.password, 'admin123'):
        logger.info('Manual credential check: Success')
    else:
        logger.info('Manual credential check: Failed')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
