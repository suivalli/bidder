from flask import render_template, redirect, url_for, flash, request, current_app
from flask_babel import _
from app import db
from app.admin import bp
from app.admin.forms import CompanyRegistrationForm
from app.models import Company
from flask_login import login_required
import logging


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    companies = Company.query.paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('admin.index', page=companies.next_num) \
        if companies.has_next else None
    prev_url = url_for('admin.index', page=companies.prev_num) \
        if companies.has_prev else None
    return render_template('admin/index.html', title=_('Admin home'),
                           companies=companies.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register_company():
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        company = Company(
            name=form.name.data,
            vat_code=form.vat_code.data,
            reg_code=form.reg_code.data,
            email=form.email.data,
            url=form.url.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            parish=form.parish.data,
            county=form.county.data,
            state=form.state.data,
            zip=form.zip.data
        )
        db.session.add(company)
        db.session.commit()
        flash(_('Congratulations, you have registered a company!'))
        return redirect(url_for('admin.index'))
    return render_template('admin/register_company.html', title=_('Register'),
                           form=form)


@bp.route('/company/<name>')
@login_required
def company(name):
    company = Company.query.filter_by(name=name).first()
    if company is None:
        flash(_('Company %(name)s not found.', name=name))
        return redirect(url_for('admin.index'))
    return render_template('admin/company.html', title=_('Company'), company=company)
