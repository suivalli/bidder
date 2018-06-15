from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))


class NewClientForm(FlaskForm):
    name = StringField(_l('Client\'s name'), validators=[DataRequired()])
    representative_name = StringField(_l('Name of representative'), validators=[DataRequired()])
    phone = StringField(_l('Phone'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class NewQuoteForm(FlaskForm):
    object_name = StringField(_l('Object\'s name'), validators=[DataRequired()])


class ClientSearchForm(FlaskForm):
    autocomp = StringField(_l('Client\'s name'), id='client_autocomplete')


class ItemForm(FlaskForm):
    name = StringField(_l('Item name'), validators=[DataRequired()])
    description = TextAreaField(_l('Description'))
    unit = StringField(_l('Unit'))
    price_per_unit = StringField(_l('Price per unit'))
    is_category = BooleanField(_l('Is this a category?'), validators=[DataRequired()], id='is_category')
