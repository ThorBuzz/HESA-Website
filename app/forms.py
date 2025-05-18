from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import HiddenField, StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
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
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    excerpt = TextAreaField('Excerpt', validators=[DataRequired(), Length(max=200)])
    category = SelectField('Category', choices=[
        ('news', 'News'), 
        ('tutorial', 'Tutorial'), 
        ('review', 'Review'),
        ('event', 'Event'),
        ('health', 'Health Awareness')
        
    ], validators=[DataRequired()])
    image = FileField('Featured Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    read_time = StringField('Estimated Read Time (minutes)', validators=[DataRequired()])
    submit = SubmitField('Submit Post')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')

class PotwForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    title = StringField('Title/Position', validators=[DataRequired(), Length(max=200)])
    bio = TextAreaField('Biography', validators=[DataRequired()])
    school = StringField('School/Department', validators=[DataRequired(), Length(max=100)])
    year = StringField('Current Year', validators=[Length(max=20)])
    high_school = StringField('High School', validators=[Length(max=100)])
    quote = StringField('Personal Quote', validators=[Length(max=200)])
    image = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg']), DataRequired()])
    is_active = BooleanField('Set as Active Personality')
    submit = SubmitField('Submit')

class PotwCommentForm(FlaskForm):
    author_name = StringField('Your Name', validators=[DataRequired(), Length(max=50)])
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')

class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Event Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    event_date = DateField('Event Date', validators=[DataRequired()], format='%Y-%m-%d')
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Submit Event')

class BusLocationForm(FlaskForm):
    bus_id = StringField('Bus ID', validators=[DataRequired(), Length(max=20)])
    route = StringField('Route', validators=[DataRequired(), Length(max=100)])
    latitude = StringField('Latitude', validators=[DataRequired()])
    longitude = StringField('Longitude', validators=[DataRequired()])
    submit = SubmitField('Update Location')
    
class AssignBusForm(FlaskForm):
    bus_id = StringField('Bus ID', validators=[DataRequired(), Length(max=20)])
    route = StringField('Route', validators=[DataRequired(), Length(max=100)])
    driver = SelectField('Driver', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Assign Bus')
    

class HomeBannerForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Banner Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    is_active = BooleanField('Active', default=True)
    order = HiddenField('Order')

# Add to forms.py

class GalleryCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Add Category')

class GalleryPhotoForm(FlaskForm):
    title = StringField('Photo Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Upload Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg']), DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Upload Photo')