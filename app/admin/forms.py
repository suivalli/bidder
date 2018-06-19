from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email
from flask_babel import _, lazy_gettext as _l
from app.models import Company


class CompanyRegistrationForm(FlaskForm):
    name = StringField(_l('Company name'), validators=[DataRequired()])
    vat_code = StringField(_l('VAT code'), validators=[DataRequired()])
    reg_code = StringField(_l('Registration code'), validators=[DataRequired()])

    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    url = StringField(_l('Company homepage URL'))
    phone = StringField(_l('Company phone'), validators=[DataRequired()])
    address = StringField(_l('Address'), validators=[DataRequired()])
    city = StringField(_l('City'), validators=[DataRequired()])
    parish = StringField(_l('Parish'), validators=[DataRequired()])
    county = StringField(_l('County'), validators=[DataRequired()])
    state = StringField(_l('State'), validators=[DataRequired()])
    zip = StringField(_l('Zip'), validators=[DataRequired()])

    submit = SubmitField(_l('Register company'))

    def validate_companyname(self, name):
        company = Company.query.filter_by(name=name.data).first()
        if company is not None:
            raise ValidationError(_('This company is already registgered!'))





