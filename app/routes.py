from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import User, BlogPost, Comment, PersonalityOfTheWeek, PotwComment, Event, BusLocation
from app.forms import (AssignBusForm, RegistrationForm, LoginForm, BlogPostForm, CommentForm, 
                      PotwForm, PotwCommentForm, EventForm, BusLocationForm)
import os
import secrets
from PIL import Image
from datetime import datetime

# Create blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__, url_prefix='/auth')
blog = Blueprint('blog', __name__, url_prefix='/blog')
editor = Blueprint('editor', __name__, url_prefix='/editor')

# Helper functions
# Helper functions
def save_image(form_image, folder='uploads'):
    """Save an uploaded image with a unique filename"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    picture_fn = random_hex + f_ext
    folder_path = os.path.join('app', 'static', folder)
    picture_path = os.path.join(folder_path, picture_fn)
    
    # Ensure directory exists
    os.makedirs(folder_path, exist_ok=True)
    
    # Resize image
    output_size = (800, 600)
    i = Image.open(form_image)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

# Main routes
@main.route('/')
def landing():
    return render_template('index.html')

@main.route('/home')
def home():
    events = Event.query.order_by(Event.event_date.desc()).limit(3).all()
    potw = PersonalityOfTheWeek.query.filter_by(is_active=True).first()
    latest_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
    return render_template('home.html', events=events, potw=potw, posts=latest_posts)

@main.route('/map')
def map():
    buses = BusLocation.query.all()
    return render_template('map.html', buses=buses)

@main.route('/potw')
def potw():
    personality = PersonalityOfTheWeek.query.filter_by(is_active=True).first_or_404()
    form = PotwCommentForm()
    comments = PotwComment.query.filter_by(potw_id=personality.id).order_by(PotwComment.date_posted.desc()).all()
    return render_template('potw.html', personality=personality, form=form, comments=comments)

@main.route('/personality-of-the-week/comment', methods=['POST'])
def potw_comment():
    personality = PersonalityOfTheWeek.query.filter_by(is_active=True).first_or_404()
    form = PotwCommentForm()
    if form.validate_on_submit():
        comment = PotwComment(
            author_name=form.author_name.data,
            content=form.content.data,
            potw_id=personality.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
    return redirect(url_for('main.potw'))

@main.route('/gallery')
def gallery():
    # You'd need to implement a gallery model or use existing content
    return render_template('gallery.html')

@main.route('/sports')
def sports():
    # You'd need to implement sports-related models or use existing content
    return render_template('sports.html')

# Auth routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', form=form, page='login')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    register_form = RegistrationForm()
    if register_form.validate_on_submit():
        user = User(username=register_form.username.data, email=register_form.email.data, role='student')
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('login.html', form=register_form, page='register')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# Blog routes
@blog.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).paginate(page=page, per_page=6)
    return render_template('blog.html', posts=posts)

@blog.route('/<int:post_id>')
def post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = CommentForm()
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.date_posted.desc()).all()
    return render_template('blog_post.html', post=post, form=form, comments=comments)

@blog.route('/<int:post_id>/comment', methods=['POST'])
def comment(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            post_id=post.id
        )
        if current_user.is_authenticated:
            comment.user_id = current_user.id
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
    return redirect(url_for('blog.post', post_id=post.id))

# Editor routes (protected)
@editor.route('/')
@login_required
def dashboard():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    events = Event.query.order_by(Event.event_date.desc()).all()
    personalities = PersonalityOfTheWeek.query.order_by(PersonalityOfTheWeek.created_at.desc()).all()
    return render_template('editor.html', posts=posts, events=events, personalities=personalities)

@editor.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    form = BlogPostForm()
    if form.validate_on_submit():
        image_file = 'default_blog.jpg'
        if form.image.data:
            image_file = save_image(form.image.data, 'blog_pics')
        
        post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            excerpt=form.excerpt.data,
            category=form.category.data,
            image_file=image_file,
            read_time=form.read_time.data,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('editor.dashboard'))
    return render_template('create_post.html', form=form, title='New Post')

@editor.route('/potw/new', methods=['GET', 'POST'])
@login_required
def new_potw():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    form = PotwForm()
    if form.validate_on_submit():
        # Set all active personalities to inactive
        if form.is_active.data:
            PersonalityOfTheWeek.query.filter_by(is_active=True).update({'is_active': False})
            
        image_file = save_image(form.image.data, 'potw_pics')
        
        personality = PersonalityOfTheWeek(
            name=form.name.data,
            title=form.title.data,
            bio=form.bio.data,
            school=form.school.data,
            year=form.year.data,
            high_school=form.high_school.data,
            quote=form.quote.data,
            image_file=image_file,
            is_active=True
        )
        db.session.add(personality)
        db.session.commit()
        flash('New Personality of the Week has been created!', 'success')
        return redirect(url_for('editor.dashboard'))
    return render_template('create_potw.html', form=form, title='New Personality')

@editor.route('/event/new', methods=['GET', 'POST'])
@login_required
def new_event():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    form = EventForm()
    if form.validate_on_submit():
        image_file = None
        if form.image.data:
            image_file = save_image(form.image.data, 'event_pics')
        
        event = Event(
            title=form.title.data,
            description=form.description.data,
            event_date=form.event_date.data,
            location=form.location.data,
            image_file=image_file
        )
        db.session.add(event)
        db.session.commit()
        flash('New event has been created!', 'success')
        return redirect(url_for('editor.dashboard'))
    return render_template('create_event.html', form=form, title='New Event')

# api route for bus tracking
@main.route('/api/buses')
def get_buses():
    buses = BusLocation.query.all()
    return jsonify([{
        'id': bus.bus_id,
        'route': bus.route,
        'position': [bus.longitude, bus.latitude],
        'lastUpdate': bus.last_update.strftime('%H:%M:%S'),
        'status': bus.status,
        'driver': User.query.get(bus.driver_id).username if bus.driver_id else None
    } for bus in buses])

@editor.route('/bus/update', methods=['GET', 'POST'])
@login_required
def update_bus():
    if current_user.role != 'admin':
        abort(403)
    form = BusLocationForm()
    if form.validate_on_submit():
        bus = BusLocation.query.filter_by(bus_id=form.bus_id.data).first()
        if bus:
            bus.route = form.route.data
            bus.latitude = float(form.latitude.data)
            bus.longitude = float(form.longitude.data)
            bus.last_update = datetime.utcnow()
        else:
            bus = BusLocation(
                bus_id=form.bus_id.data,
                route=form.route.data,
                latitude=float(form.latitude.data),
                longitude=float(form.longitude.data)
            )
            db.session.add(bus)
        db.session.commit()
        flash('Bus location updated!', 'success')
        return redirect(url_for('editor.dashboard'))
    return render_template('update_bus.html', form=form)

# Add this to the editor routes in routes.py

@editor.route('/assign_bus', methods=['GET', 'POST'])
@login_required
def assign_bus():
    if current_user.role != 'admin':
        abort(403)
    
    form = AssignBusForm()
    
    # Get all users with driver role for the dropdown
    form.driver.choices = [(u.id, u.username) for u in User.query.filter_by(role='driver').all()]
    
    if form.validate_on_submit():
        # Check if bus already exists
        bus = BusLocation.query.filter_by(bus_id=form.bus_id.data).first()
        
        if bus:
            # Update existing bus
            bus.route = form.route.data
            bus.driver_id = form.driver.data
        else:
            # Create new bus
            bus = BusLocation(
                bus_id=form.bus_id.data,
                route=form.route.data,
                driver_id=form.driver.data,
                latitude=6.67233,  # Default KNUST coordinates
                longitude=-1.56927,
                status='inactive'
            )
            db.session.add(bus)
        
        db.session.commit()
        flash(f'Bus {form.bus_id.data} has been assigned to driver successfully!', 'success')
        return redirect(url_for('editor.dashboard'))
    
    # Get all current bus assignments
    bus_assignments = BusLocation.query.all()
    
    return render_template('assign_bus.html', form=form, assignments=bus_assignments)