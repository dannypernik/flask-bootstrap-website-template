from flask import Flask, render_template, flash, redirect, url_for, request, send_from_directory
from app import app, db
from app.forms import InquiryForm, EmailForm, SignupForm, LoginForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_inquiry_email

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_viewed = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = InquiryForm()
    if form.validate_on_submit():
        user = User(first_name=form.first_name.data, email=form.email.data)
        subject = form.subject.data
        message = form.message.data
        db.session.add(user)
        db.session.commit()
        send_inquiry_email(user, subject, message)
        flash("Thank you for your message. We will be in touch!")
        print(app.config['ADMINS'])
        return redirect(url_for('index', _anchor='home'))
    return render_template('index.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        username = form.first_name.data.lower() + "." + form.last_name.data.lower()
        username_id = 1
        username_check = User.query.filter_by(username=username).first()
        while username_check is not None:
            username_next = ''.join((str(username), str(username_id)))
            username_check = User.query.filter_by(username=username_next).first()
            if username_check is None:
                username = username_next
            username_id += 1
        user = User(first_name=form.first_name.data, last_name=form.last_name.data, \
        email=form.email.data, username=username)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("You are now registered. We're glad you're here!")
        return redirect(url_for('index'))
    return render_template('signup.html', title='Sign up', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already signed in')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('profile.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        username = User.query.filter_by(username=form.username.data).first()
        if username.id is not current_user.id and not None:
            flash("The username " + form.username.data + " is already taken")
            flash(username.id)
            form.username.data = current_user.username
            current_user.about_me = form.about_me.data
            db.session.commit()
            return render_template('edit_profile.html', title='Edit Profile', form=form)
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
