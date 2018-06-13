from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_babel import _
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Company
from app.auth.email import send_password_reset_email
import logging


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.admin:
            return redirect(url_for('admin.index'))
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        if user.admin:
            return redirect(url_for('admin.index'))
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))



@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.admin and not current_user.superuser:
        flash(_('You have no permission to register an user. Please contact your company\'s administrator.'))
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if current_user.superuser:
        del form.company
    if current_user.admin:
        form.company.choices = [(c.id, c.name) for c in Company.query.order_by('name')]
    if form.validate_on_submit():
        logging.info("Validating worked!")
        superuser = form.superuser.data
        user = User(username=form.username.data, email=form.email.data)
        if superuser == 'True':
            user.superuser = True
        if current_user.admin:
            user.company_id = form.company.data
        else:
            user.company_id = current_user.company_id
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you have registered a new user!'))
        if current_user.admin:
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/register.html', title=_('Register'), form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        if current_user.admin:
            return redirect(url_for('admin.index'))
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
