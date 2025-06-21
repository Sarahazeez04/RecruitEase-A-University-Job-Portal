import os
from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '12345'

# Directory to store profile images
UPLOAD_FOLDER = 'static/profile_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    degree = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    cgpa = db.Column(db.String(10), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    skills = db.Column(db.Text, nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)  # Store image filename

class AdminProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    designation = db.Column(db.String(50), nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)  # Profile picture


class JobPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(50), nullable=True)
    qualifications = db.Column(db.Text, nullable=False)
    posted_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)
    applicant_name = db.Column(db.String(100), nullable=False)
    applicant_email = db.Column(db.String(100), nullable=False)
    resume_filename = db.Column(db.String(255), nullable=False)  # Store the resume file name

    job = db.relationship('JobPost', backref=db.backref('applications', lazy=True))

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'student':
                existing_profile = StudentProfile.query.filter_by(user_id=user.id).first()
                if existing_profile:
                    return redirect(url_for('studenthome'))
                return redirect(url_for('student_profile'))

            if user.role == 'admin':
                existing_profile = AdminProfile.query.filter_by(user_id=user.id).first()
                if existing_profile:
                    return redirect(url_for('adminhome'))
                return redirect(url_for('admin_profile'))
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))  # Hash the password

        new_user = User(role=role, name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        if role == 'student':
            session['user_id'] = new_user.id
            session['role'] = new_user.role
            return redirect(url_for('student_profile'))
        
        if role == 'admin':
            session['user_id'] = new_user.id
            session['role'] = new_user.role
            return redirect(url_for('admin_profile'))
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/student_profile', methods=['GET', 'POST'])
def student_profile():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    existing_profile = StudentProfile.query.filter_by(user_id=session['user_id']).first()

    if request.method == 'POST':
        profile_image = request.files.get('profile_image')
        image_filename = existing_profile.profile_image if existing_profile else None

        # Save the new image if uploaded
        if profile_image and profile_image.filename:
            filename = secure_filename(profile_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image.save(image_path)
            image_filename = filename  # Store in the database

        if existing_profile:
            # Update profile
            existing_profile.name = request.form.get('full_name')
            existing_profile.phone = request.form.get('phone')
            existing_profile.dob = request.form.get('dob')
            existing_profile.gender = request.form.get('gender')
            existing_profile.degree = request.form.get('degree')
            existing_profile.branch = request.form.get('branch')
            existing_profile.cgpa = request.form.get('cgpa')
            existing_profile.graduation_year = request.form.get('graduation_year')
            existing_profile.skills = request.form.get('skills')
            existing_profile.profile_image = image_filename
        else:
            # Create new profile
            profile = StudentProfile(
                user_id=session['user_id'],
                name=request.form.get('full_name'),
                phone=request.form.get('phone'),
                dob=request.form.get('dob'),
                gender=request.form.get('gender'),
                degree=request.form.get('degree'),
                branch=request.form.get('branch'),
                cgpa=request.form.get('cgpa'),
                graduation_year=request.form.get('graduation_year'),
                skills=request.form.get('skills'),
                profile_image=image_filename
            )
            db.session.add(profile)

        db.session.commit()
        return redirect(url_for('studenthome'))

    return render_template('student_profile.html', profile=existing_profile)

@app.route('/admin_profile', methods=['GET', 'POST'])
def admin_profile():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    existing_profile = AdminProfile.query.filter_by(user_id=session['user_id']).first()

    if request.method == 'POST':
        profile_image = request.files.get('profile_image')
        image_filename = existing_profile.profile_image if existing_profile else None

        # Save the new image if uploaded
        if profile_image and profile_image.filename:
            filename = secure_filename(profile_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image.save(image_path)
            image_filename = filename  # Store in the database

        if existing_profile:
            # Update profile
            existing_profile.name = request.form.get('name')
            existing_profile.email = request.form.get('email')
            existing_profile.phone = request.form.get('phone')
            existing_profile.designation = request.form.get('designation')
            existing_profile.profile_image = image_filename
        else:
            # Create new profile
            profile = AdminProfile(
                user_id=session['user_id'],
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                designation=request.form.get('designation'),
                profile_image=image_filename
            )
            db.session.add(profile)

        db.session.commit()
        return redirect(url_for('adminhome'))

    return render_template('admin_profile.html', profile=existing_profile)

@app.route('/studenthome')
def studenthome():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    student_profile = StudentProfile.query.filter_by(user_id=session['user_id']).first()
    return render_template('studenthome.html', profile=student_profile)

@app.route('/adminhome')
def adminhome():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    admin_profile = AdminProfile.query.filter_by(user_id=session['user_id']).first()
    return render_template('adminhome.html', profile=admin_profile)

@app.route('/view_profile')
def view_profile():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    student_profile = StudentProfile.query.filter_by(user_id=session['user_id']).first()
    return render_template('view_profile.html', profile=student_profile)

@app.route('/admin_view_profile')
def admin_view_profile():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    admin_profile = AdminProfile.query.filter_by(user_id=session['user_id']).first()
    return render_template('viewadminprofile.html', profile=admin_profile)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        company_name = request.form.get('company_name')
        job_title = request.form.get('job_title')
        job_description = request.form.get('job_description')
        location = request.form.get('location')
        salary = request.form.get('salary')
        qualifications = request.form.get('qualifications')

        new_job = JobPost(
            admin_id=session['user_id'],
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
            location=location,
            salary=salary,
            qualifications=qualifications
        )

        db.session.add(new_job)
        db.session.commit()

        return redirect(url_for('adminhome'))

    return render_template('post_job.html')

@app.route('/jobstatus', methods=['GET', 'POST'])
def jobstatus():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        application_id = request.form.get('application_id')
        status = request.form.get('status')

        application = JobApplication.query.get(application_id)
        if application:
            application.status = status
            db.session.commit()
            flash(f"Application {status.capitalize()} successfully!", "success")

    # Fetch all jobs posted by the admin
    jobs = JobPost.query.filter_by(admin_id=session['user_id']).all()

    # Fetch applications for each job
    job_applications = {}
    for job in jobs:
        applications = JobApplication.query.filter_by(job_id=job.id).all()
        job_applications[job.id] = applications

    return render_template('jobstatus.html', jobs=jobs, job_applications=job_applications)

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash("You have been logged out successfully!", "info")
    return redirect(url_for('login'))  # Redirect to login page

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    