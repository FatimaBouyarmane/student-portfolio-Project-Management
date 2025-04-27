from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    github_username = StringField('GitHub Username')
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered. Please use a different one.')


class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Post Comment')


class StyleForm(FlaskForm):
    primary_color = StringField('Primary Color', validators=[DataRequired()])
    secondary_color = StringField('Secondary Color', validators=[DataRequired()])
    background_color = StringField('Background Color', validators=[DataRequired()])
    font_family = SelectField('Font Family', 
                            choices=[
                                ("'Roboto', sans-serif", 'Roboto'),
                                ("'Open Sans', sans-serif", 'Open Sans'),
                                ("'Montserrat', sans-serif", 'Montserrat'),
                                ("'Lato', sans-serif", 'Lato'),
                                ("'Source Sans Pro', sans-serif", 'Source Sans Pro'),
                                ("'Raleway', sans-serif", 'Raleway'),
                                ("'Ubuntu', sans-serif", 'Ubuntu')
                            ],
                            validators=[DataRequired()])
    background_image = FileField('Background Image')
    submit = SubmitField('Save Style')


class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    technologies = StringField('Technologies (comma separated)', validators=[Length(max=200)])
    repo_url = StringField('Repository URL', validators=[Length(max=255)])
    live_url = StringField('Live Demo URL', validators=[Length(max=255)])
    project_image = FileField('Project Image')
    project_color = StringField('Project Color', default="#0d6efd")
    submit = SubmitField('Save Project')
