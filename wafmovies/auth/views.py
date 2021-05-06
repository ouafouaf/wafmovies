from flask import flash, redirect, render_template, url_for
from flask_wtf import FlaskForm 
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired
from flask_login import login_required, login_user, logout_user

from . import auth 
from ..models import User 

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for('home.homepage'))
        else: 
            flash('Invalid username or password.')
    return render_template('login.html', form=form, title='Login')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.homepage'))
