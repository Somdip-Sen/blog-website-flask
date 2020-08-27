import os
import random
from PIL import Image
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from project import app
from project.connection import User
# FileAllowed help us to restrict the type of file that is acceptable.
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class RegistrationForm(FlaskForm):
    # flask default validation check
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    picture = FileField("Upload your profile picture", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Sign Up')

    # custom validation check
    def validate_username(self, username):
        user = User.query.filter_by(name=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('This email address is already registered. Please login with this email.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log in')


def save_pic(pic_data, type_):
    filename, extension = os.path.splitext(pic_data.filename)
    rename = str(hex(random.getrandbits(16))) + extension
    # generate a random hex code [random.getrandbits(16) -> return an binary with a specified number of bits.
    # hex() -> convert it to hexadecimal ]
    pic_path = os.path.join(app.root_path, 'static/img/profile_pics', rename)
    if type_ == 'modify':  # not for registration
        if current_user.image_file != 'default_pic.png':
            # delete previous saved file
            os.remove(os.path.join(app.root_path, 'static/img/profile_pics', current_user.image_file))
    # resize the uploaded file into css 125*125 size
    resized_img = Image.open(pic_data)
    resized_img.thumbnail((125, 125))
    # save the new file
    resized_img.save(pic_path)
    return rename  # to store the name in the database


class EditAccountForm(FlaskForm):
    # flask default validation check
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField("Update your profile picture", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    # custom validation check
    def validate_username(self, username):
        if username.data != current_user.name:
            user = User.query.filter_by(name=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose another name.')

    def validate_email(self, email):
        if email.data != current_user.email:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError('This email address is already taken. Please choose another email.')


class Postsubmitform(FlaskForm):
    title = StringField('Post Heading', validators=[DataRequired(), Length(min=5, max=30)])
    tagline = StringField('Post Sub-title/Tagline', validators=[DataRequired(), Length(min=5, max=20)])
    content = TextAreaField('Content', validators=[DataRequired()])
    picture = FileField("Upload post heading picture", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Post')


class Postupdateform(FlaskForm):
    title = StringField('Post Heading', validators=[DataRequired(), Length(min=5, max=30)])
    tagline = StringField('Post Sub-title/Tagline', validators=[DataRequired(), Length(min=5, max=20)])
    content = TextAreaField('Content', validators=[DataRequired()])
    picture = FileField("Update post heading picture", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')


class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send link')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is None:
            raise ValidationError('This email address doesn\'t exist with any account.')


class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset')
