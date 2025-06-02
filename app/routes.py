from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, abort, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import (User, BlogPost, Comment, PersonalityOfTheWeek, 
                        PotwComment, Event, BusLocation, HomeBanner, GalleryPhoto, GalleryCategory, FohContestant, FohVote)
from app.forms import (AssignBusForm, RegistrationForm, LoginForm, BlogPostForm, CommentForm, 
                      PotwForm, PotwCommentForm, EventForm, BusLocationForm, HomeBannerForm, GalleryCategoryForm, 
                      GalleryPhotoForm, FohContestantForm, VoteForm)
import os
import secrets
from PIL import Image
from datetime import datetime
from app.utils.s3_helper import upload_file_to_s3

# Create blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__, url_prefix='/auth')
blog = Blueprint('blog', __name__, url_prefix='/blog')
editor = Blueprint('editor', __name__, url_prefix='/editor')

# Helper functions
def save_image(form_image, folder='uploads'):
    """
    Save an uploaded image with a unique filename
    Uses S3 if configured, otherwise saves locally
    """
    if current_app.config.get('USE_S3', False):
        # Use S3 for file storage
        file_url = upload_file_to_s3(form_image, folder=folder)
        if file_url:
            # Return the full URL for S3 images
            return file_url
        else:
            # Fallback to local storage if S3 upload fails
            print("S3 upload failed, falling back to local storage")
            return save_image_locally(form_image, folder)
    else:
        # Use local storage
        return save_image_locally(form_image, folder)

# In your main routes file - update the save_image_locally function:

def save_image_locally(form_image, folder='uploads'):
    """Save an uploaded image with a unique filename to the local filesystem"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    picture_fn = random_hex + f_ext
    folder_path = os.path.join('app', 'static', folder)
    picture_path = os.path.join(folder_path, picture_fn)
    
    # Ensure directory exists
    os.makedirs(folder_path, exist_ok=True)
    
    # Resize image with better quality settings
    output_size = (1200, 900)  # Increased resolution
    i = Image.open(form_image)
    
    # Use LANCZOS resampling for better quality
    i.thumbnail(output_size, Image.Resampling.LANCZOS)
    
    # Save with high quality
    if i.format == 'JPEG' or f_ext.lower() in ['.jpg', '.jpeg']:
        i.save(picture_path, 'JPEG', quality=95, optimize=True)
    elif i.format == 'PNG' or f_ext.lower() == '.png':
        i.save(picture_path, 'PNG', optimize=True)
    else:
        # Default to JPEG with high quality
        i.save(picture_path, 'JPEG', quality=95, optimize=True)
    
    return picture_fn


# Main routes
@main.route('/')
def landing():
    return render_template('index.html')


@main.route('/home')
def home():
    events = Event.query.order_by(Event.event_date.desc()).limit(3).all()
    potw = PersonalityOfTheWeek.query.filter_by(is_active=True).first()
    latest_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(4).all()
    
    # Get the active and ordered banners (max 3)
    banners = HomeBanner.query.filter_by(is_active=True).order_by(HomeBanner.order).limit(3).all()
    
    return render_template('home.html', events=events, potw=potw, posts=latest_posts, banners=banners)

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

# @main.route('/gallery')
# def gallery():
#     # You'd need to implement a gallery model or use existing content
#     return render_template('gallery.html')

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
    
    # Filter out posts with 'health' or 'event' category
    posts = BlogPost.query \
        .filter(BlogPost.category.notin_(['health', 'event'])) \
        .order_by(BlogPost.date_posted.desc()) \
        .paginate(page=page, per_page=9)
    
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
            # Add social media usernames
            twitter=form.twitter.data,
            facebook=form.facebook.data,
            instagram=form.instagram.data,
            linkedin=form.linkedin.data,
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



@editor.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    post = BlogPost.query.get_or_404(post_id)
    
    # Check if current user is the author or an admin
    if post.author != current_user and current_user.role != 'admin':
        abort(403)
    
    form = BlogPostForm()
    
    if form.validate_on_submit():
        # Update post data
        post.title = form.title.data
        post.content = form.content.data
        post.excerpt = form.excerpt.data
        post.category = form.category.data
        post.read_time = form.read_time.data
        
        # Update image if a new one is provided
        if form.image.data:
            # Delete old image if it's from S3
            if 'http' in post.image_file and post.image_file != 'default_blog.jpg':
                from app.utils.s3_helper import delete_file_from_s3
                delete_file_from_s3(post.image_file)
            
            # Save new image
            post.image_file = save_image(form.image.data, 'blog_pics')
        
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('editor.dashboard'))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.excerpt.data = post.excerpt
        form.category.data = post.category
        form.read_time.data = post.read_time
    
    return render_template('edit_post.html', form=form, post=post, title='Edit Post')

@editor.route('/potw/edit/<int:potw_id>', methods=['GET', 'POST'])
@login_required
def edit_potw(potw_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    personality = PersonalityOfTheWeek.query.get_or_404(potw_id)
    form = PotwForm()
    
    if form.validate_on_submit():
        # Set all active personalities to inactive if this one is marked as active
        if form.is_active.data and not personality.is_active:
            PersonalityOfTheWeek.query.filter_by(is_active=True).update({'is_active': False})
        
        # Update personality data
        personality.name = form.name.data
        personality.title = form.title.data
        personality.bio = form.bio.data
        personality.school = form.school.data
        personality.year = form.year.data
        personality.high_school = form.high_school.data
        personality.quote = form.quote.data
        # Update social media usernames
        personality.twitter = form.twitter.data
        personality.facebook = form.facebook.data
        personality.instagram = form.instagram.data
        personality.linkedin = form.linkedin.data
        personality.is_active = form.is_active.data
        
        # Update image if a new one is provided
        if form.image.data:
            # Delete old image if it's from S3
            if 'http' in personality.image_file:
                from app.utils.s3_helper import delete_file_from_s3
                delete_file_from_s3(personality.image_file)
            
            # Save new image
            personality.image_file = save_image(form.image.data, 'potw_pics')
        
        db.session.commit()
        flash('Personality has been updated!', 'success')
        return redirect(url_for('editor.dashboard'))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.name.data = personality.name
        form.title.data = personality.title
        form.bio.data = personality.bio
        form.school.data = personality.school
        form.year.data = personality.year
        form.high_school.data = personality.high_school
        form.quote.data = personality.quote
        # Populate social media fields
        form.twitter.data = personality.twitter
        form.facebook.data = personality.facebook
        form.instagram.data = personality.instagram
        form.linkedin.data = personality.linkedin
        form.is_active.data = personality.is_active
    
    return render_template('edit_potw.html', form=form, personality=personality, title='Edit Personality')
@editor.route('/event/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    event = Event.query.get_or_404(event_id)
    form = EventForm()
    
    if form.validate_on_submit():
        # Update event data
        event.title = form.title.data
        event.description = form.description.data
        event.event_date = form.event_date.data
        event.location = form.location.data
        
        # Update image if a new one is provided
        if form.image.data:
            # Delete old image if it's from S3
            if event.image_file and 'http' in event.image_file:
                from app.utils.s3_helper import delete_file_from_s3
                delete_file_from_s3(event.image_file)
            
            # Save new image
            event.image_file = save_image(form.image.data, 'event_pics')
        
        db.session.commit()
        flash('Event has been updated!', 'success')
        return redirect(url_for('editor.dashboard'))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.title.data = event.title
        form.description.data = event.description
        form.event_date.data = event.event_date
        form.location.data = event.location
    
    return render_template('edit_event.html', form=form, event=event, title='Edit Event')

@main.route('/event/<int:event_id>')
def event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event.html', event=event)


@editor.route('/post/delete/<int:post_id>', methods=['POST', 'DELETE'])
@login_required
def delete_post(post_id):
    # Check permissions
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    post = BlogPost.query.get_or_404(post_id)
    
    # Check if current user is the author or an admin
    if post.author != current_user and current_user.role != 'admin':
        abort(403)
    
    # Delete image from S3 if applicable
    if post.image_file and post.image_file != 'default_blog.jpg' and 'http' in post.image_file:
        from app.utils.s3_helper import delete_file_from_s3
        delete_file_from_s3(post.image_file)
    
    # Delete all comments associated with the post
    Comment.query.filter_by(post_id=post.id).delete()
    
    # Delete the post
    db.session.delete(post)
    db.session.commit()
    
    flash('Blog post has been deleted!', 'success')
    return redirect(url_for('editor.dashboard'))

@editor.route('/potw/delete/<int:potw_id>', methods=['POST', 'DELETE'])
@login_required
def delete_potw(potw_id):
    # Check permissions
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    personality = PersonalityOfTheWeek.query.get_or_404(potw_id)
    
    # Delete image from S3 if applicable
    if personality.image_file and 'http' in personality.image_file:
        from app.utils.s3_helper import delete_file_from_s3
        delete_file_from_s3(personality.image_file)
    
    # Delete all comments associated with the personality
    PotwComment.query.filter_by(potw_id=personality.id).delete()
    
    # Check if deleting the active personality
    is_active = personality.is_active
    
    # Delete the personality
    db.session.delete(personality)
    db.session.commit()
    
    # If the active personality was deleted, make another one active
    if is_active:
        # Find the most recent personality and make it active
        newest = PersonalityOfTheWeek.query.order_by(PersonalityOfTheWeek.created_at.desc()).first()
        if newest:
            newest.is_active = True
            db.session.commit()
            flash(f'Active personality deleted and {newest.name} was set as active.', 'info')
    
    flash('Personality has been deleted!', 'success')
    return redirect(url_for('editor.dashboard'))

@editor.route('/event/delete/<int:event_id>', methods=['POST', 'DELETE'])
@login_required
def delete_event(event_id):
    # Check permissions
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    event = Event.query.get_or_404(event_id)
    
    # Delete image from S3 if applicable
    if event.image_file and 'http' in event.image_file:
        from app.utils.s3_helper import delete_file_from_s3
        delete_file_from_s3(event.image_file)
    
    # Delete the event
    db.session.delete(event)
    db.session.commit()
    
    flash('Event has been deleted!', 'success')
    return redirect(url_for('editor.dashboard'))


# Add these routes to your editor blueprint section

@editor.route('/banners', methods=['GET'])
@login_required
def manage_banners():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    form = HomeBannerForm()
    banners = HomeBanner.query.order_by(HomeBanner.order).all()
    
    return render_template('manage_banners.html', form=form, banners=banners)

@editor.route('/banners/add', methods=['POST'])
@login_required
def add_banner():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    form = HomeBannerForm()
    
    if form.validate_on_submit():
        image_file = None
        if form.image.data:
            image_file = save_image(form.image.data, 'banners')
        
        # Get the highest order value to place this one at the end
        highest_order = db.session.query(db.func.max(HomeBanner.order)).scalar() or -1
        
        banner = HomeBanner(
            title=form.title.data,
            description=form.description.data,
            image_file=image_file,
            is_active=form.is_active.data,
            order=highest_order + 1
        )
        
        db.session.add(banner)
        db.session.commit()
        
        flash('Banner added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('editor.manage_banners'))

@editor.route('/banners/edit/<int:banner_id>', methods=['GET', 'POST'])
@login_required
def edit_banner(banner_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    banner = HomeBanner.query.get_or_404(banner_id)
    form = HomeBannerForm()
    
    if form.validate_on_submit():
        banner.title = form.title.data
        banner.description = form.description.data
        banner.is_active = form.is_active.data
        
        # Update image if a new one is provided
        if form.image.data:
            # Delete old image if it's from S3
            if banner.image_file and 'http' in banner.image_file:
                from app.utils.s3_helper import delete_file_from_s3
                delete_file_from_s3(banner.image_file)
            
            # Save new image
            banner.image_file = save_image(form.image.data, 'banners')
        
        db.session.commit()
        flash('Banner updated successfully!', 'success')
        return redirect(url_for('editor.manage_banners'))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.title.data = banner.title
        form.description.data = banner.description
        form.is_active.data = banner.is_active
    
    return render_template('edit_banner.html', form=form, banner=banner)

@editor.route('/banners/delete/<int:banner_id>', methods=['POST'])
@login_required
def delete_banner(banner_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    banner = HomeBanner.query.get_or_404(banner_id)
    
    # Delete image from S3 if applicable
    if banner.image_file and 'http' in banner.image_file:
        from app.utils.s3_helper import delete_file_from_s3
        delete_file_from_s3(banner.image_file)
    
    db.session.delete(banner)
    
    # Reorder remaining banners
    remaining_banners = HomeBanner.query.order_by(HomeBanner.order).all()
    for i, b in enumerate(remaining_banners):
        b.order = i
    
    db.session.commit()
    
    flash('Banner deleted successfully!', 'success')
    return redirect(url_for('editor.manage_banners'))

@editor.route('/banners/update-order', methods=['POST'])
@login_required
def update_banner_order():
    if current_user.role not in ['admin', 'editor']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.json
    banners_data = data.get('banners', [])
    
    for banner_data in banners_data:
        banner_id = banner_data.get('id')
        new_order = banner_data.get('order')
        
        banner = HomeBanner.query.get(banner_id)
        if banner:
            banner.order = new_order
    
    db.session.commit()
    
    return jsonify({'success': True})

@editor.route('/banners/toggle', methods=['POST'])
@login_required
def toggle_banner():
    if current_user.role not in ['admin', 'editor']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.json
    banner_id = data.get('banner_id')
    is_active = data.get('is_active')
    
    banner = HomeBanner.query.get(banner_id)
    if banner:
        banner.is_active = is_active
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Banner not found'}), 404



# Create a new blueprint for gallery
gallery = Blueprint('gallery', __name__, url_prefix='/gallery')

# Public gallery route
@gallery.route('/')
def index():
    photos = GalleryPhoto.query.filter_by(is_active=True).order_by(GalleryPhoto.order, GalleryPhoto.date_posted.desc()).all()
    categories = GalleryCategory.query.all()
    return render_template('gallery.html', photos=photos, categories=categories)

# Editor routes for gallery management
@editor.route('/gallery/manage')
@login_required
def manage_gallery():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    photos = GalleryPhoto.query.order_by(GalleryPhoto.order, GalleryPhoto.date_posted.desc()).all()
    categories = GalleryCategory.query.all()
    photo_form = GalleryPhotoForm()
    photo_form.category.choices = [(c.id, c.name) for c in categories]
    category_form = GalleryCategoryForm()
    
    return render_template('manage_gallery.html', 
                          photos=photos, 
                          categories=categories, 
                          photo_form=photo_form, 
                          category_form=category_form)

@editor.route('/gallery/add_category', methods=['POST'])
@login_required
def add_gallery_category():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    form = GalleryCategoryForm()
    if form.validate_on_submit():
        # Create slug from name
        slug = form.name.data.lower().replace(' ', '-')
        
        # Check if slug already exists
        existing = GalleryCategory.query.filter_by(slug=slug).first()
        if existing:
            flash('A category with this name already exists.', 'danger')
        else:
            category = GalleryCategory(name=form.name.data, slug=slug)
            db.session.add(category)
            db.session.commit()
            flash('New gallery category added!', 'success')
    
    return redirect(url_for('editor.manage_gallery'))

@editor.route('/gallery/upload', methods=['POST'])
@login_required
def upload_photo():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    categories = GalleryCategory.query.all()
    form = GalleryPhotoForm()
    form.category.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        if form.image.data:
            image_file = save_image(form.image.data, 'uploads/gallery')
            
            # Get the highest order value
            highest_order = db.session.query(db.func.max(GalleryPhoto.order)).scalar() or -1
            
            photo = GalleryPhoto(
                title=form.title.data,
                description=form.description.data,
                image_file=image_file,
                category_id=form.category.data,
                is_active=form.is_active.data,
                order=highest_order + 1
            )
            db.session.add(photo)
            db.session.commit()
            flash('Photo uploaded successfully!', 'success')
        else:
            flash('Please upload an image.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('editor.manage_gallery'))

@editor.route('/gallery/edit/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def edit_photo(photo_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    categories = GalleryCategory.query.all()
    
    form = GalleryPhotoForm()
    form.category.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        photo.title = form.title.data
        photo.description = form.description.data
        photo.category_id = form.category.data
        photo.is_active = form.is_active.data
        
        if form.image.data:
            # Delete old image if applicable
            if photo.image_file and 'http' in photo.image_file:
                from app.utils.s3_helper import delete_file_from_s3
                delete_file_from_s3(photo.image_file)
            
            # Save new image
            photo.image_file = save_image(form.image.data, 'uploads/gallery')
        
        db.session.commit()
        flash('Photo updated successfully!', 'success')
        return redirect(url_for('editor.manage_gallery'))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.title.data = photo.title
        form.description.data = photo.description
        form.category.data = photo.category_id
        form.is_active.data = photo.is_active
    
    return render_template('edit_photo.html', form=form, photo=photo)

@editor.route('/gallery/delete/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Delete image from S3 if applicable
    if photo.image_file and 'http' in photo.image_file:
        from app.utils.s3_helper import delete_file_from_s3
        delete_file_from_s3(photo.image_file)
    
    db.session.delete(photo)
    
    # Reorder remaining photos
    remaining_photos = GalleryPhoto.query.order_by(GalleryPhoto.order).all()
    for i, p in enumerate(remaining_photos):
        p.order = i
    
    db.session.commit()
    flash('Photo deleted successfully!', 'success')
    return redirect(url_for('editor.manage_gallery'))

@editor.route('/gallery/toggle/<int:photo_id>', methods=['POST'])
@login_required
def toggle_photo(photo_id):
    if current_user.role not in ['admin', 'editor']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    photo.is_active = not photo.is_active
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'is_active': photo.is_active,
        'message': f"Photo {'activated' if photo.is_active else 'deactivated'} successfully"
    })

@editor.route('/gallery/update_order', methods=['POST'])
@login_required
def update_photo_order():
    if current_user.role not in ['admin', 'editor']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.json
    photos_data = data.get('photos', [])
    
    for photo_data in photos_data:
        photo_id = photo_data.get('id')
        new_order = photo_data.get('order')
        
        photo = GalleryPhoto.query.get(photo_id)
        if photo:
            photo.order = new_order
    
    db.session.commit()
    
    return jsonify({'success': True})

# API route for likes
@gallery.route('/api/like/<int:photo_id>', methods=['POST'])
def like_photo(photo_id):
    photo = GalleryPhoto.query.get_or_404(photo_id)
    photo.likes += 1
    db.session.commit()
    return jsonify({'success': True, 'likes': photo.likes})


# Create a new blueprint for Face of HESA
foh = Blueprint('foh', __name__, url_prefix='/face-of-hesa')

# Global voting settings
class VotingSettings:
    is_voting_active = True
    vote_cost = 1.0  # Cost per vote in GHS

# Public routes for Face of HESA
@foh.route('/')
def index():
    contestants = FohContestant.query.filter_by(is_active=True).order_by(FohContestant.votes.desc()).all()
    voting_active = VotingSettings.is_voting_active
    vote_cost = VotingSettings.vote_cost
    return render_template('foh.html', contestants=contestants, voting_active=voting_active, vote_cost=vote_cost)

@foh.route('/vote/<int:contestant_id>', methods=['POST'])
def process_vote(contestant_id):
    if not VotingSettings.is_voting_active:
        flash('Voting is currently closed.', 'warning')
        return redirect(url_for('foh.index'))
    
    contestant = FohContestant.query.get_or_404(contestant_id)
    
    # Get votes from form data
    votes = int(request.form.get('votes', 1))
    email = request.form.get('email', '')
    
    # Calculate amount
    amount = votes * VotingSettings.vote_cost
    
    # Generate a unique reference
    reference = f"foh-{contestant_id}-{secrets.token_hex(6)}"
    
    # Store pending vote
    vote = FohVote(
        contestant_id=contestant_id,
        email=email,
        votes_count=votes,
        amount=amount,
        transaction_ref=reference,
        verified=False
    )
    db.session.add(vote)
    db.session.commit()
    
    # Redirect to payment gateway
    return redirect(url_for('foh.initiate_payment', reference=reference))

@foh.route('/payment/<reference>')
def initiate_payment(reference):
    vote = FohVote.query.filter_by(transaction_ref=reference).first_or_404()
    contestant = FohContestant.query.get_or_404(vote.contestant_id)
    
    # Calculate amount in kobo (multiply by 100) for Paystack
    amount_kobo = int(vote.amount * 100)
    
    # For demo purposes, we'll just show the payment page template
    # In production, you'd integrate with Paystack API to initialize transaction
    return render_template('payment.html', 
                          vote=vote, 
                          contestant=contestant, 
                          amount_kobo=amount_kobo,
                          reference=reference)

@foh.route('/verify/<reference>')
def verify_payment(reference):
    # In a real implementation, this would verify the payment with Paystack API
    # For demo purposes, we'll just mark the vote as verified
    
    vote = FohVote.query.filter_by(transaction_ref=reference).first_or_404()
    
    # Mark vote as verified
    vote.verified = True
    
    # Update contestant vote count
    contestant = FohContestant.query.get(vote.contestant_id)
    contestant.votes += vote.votes_count
    
    db.session.commit()
    
    flash(f'Thank you! Your {vote.votes_count} vote(s) for {contestant.name} has been recorded.', 'success')
    return redirect(url_for('foh.index'))

# Admin routes for Face of HESA management
@editor.route('/foh/manage')
@login_required
def manage_foh():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    contestants = FohContestant.query.order_by(FohContestant.created_at.desc()).all()
    form = FohContestantForm()
    
    return render_template('manage_foh.html', 
                          contestants=contestants, 
                          form=form, 
                          voting_active=VotingSettings.is_voting_active,
                          vote_cost=VotingSettings.vote_cost)

@editor.route('/foh/add', methods=['POST'])
@login_required
def add_contestant():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    form = FohContestantForm()
    
    if form.validate_on_submit():
        image_file = 'default_contestant.jpg'
        if form.image.data:
            image_file = save_image(form.image.data, 'foh_pics')
        
        contestant = FohContestant(
            name=form.name.data,
            description=form.description.data,
            image_file=image_file,
            is_active=form.is_active.data
        )
        
        db.session.add(contestant)
        db.session.commit()
        
        flash('Contestant added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('editor.manage_foh'))

@editor.route('/foh/edit/<int:contestant_id>', methods=['GET', 'POST'])
@login_required
def edit_contestant(contestant_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    contestant = FohContestant.query.get_or_404(contestant_id)
    form = FohContestantForm()
    
    if form.validate_on_submit():
        contestant.name = form.name.data
        contestant.description = form.description.data
        contestant.is_active = form.is_active.data
        
        if form.image.data:
            # Delete old image if applicable
            if contestant.image_file != 'default_contestant.jpg' and 'http' in contestant.image_file:
                from app.utils.s3_helper import delete_file_from_s3
                delete_file_from_s3(contestant.image_file)
            
            # Save new image
            contestant.image_file = save_image(form.image.data, 'foh_pics')
        
        db.session.commit()
        flash('Contestant updated successfully!', 'success')
        return redirect(url_for('editor.manage_foh'))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.name.data = contestant.name
        form.description.data = contestant.description
        form.is_active.data = contestant.is_active
    
    return render_template('edit_contestant.html', form=form, contestant=contestant)

@editor.route('/foh/delete/<int:contestant_id>', methods=['POST'])
@login_required
def delete_contestant(contestant_id):
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    contestant = FohContestant.query.get_or_404(contestant_id)
    
    # Delete image if applicable
    if contestant.image_file != 'default_contestant.jpg' and 'http' in contestant.image_file:
        from app.utils.s3_helper import delete_file_from_s3
        delete_file_from_s3(contestant.image_file)
    
    # Delete associated votes
    FohVote.query.filter_by(contestant_id=contestant.id).delete()
    
    # Delete the contestant
    db.session.delete(contestant)
    db.session.commit()
    
    flash('Contestant deleted successfully!', 'success')
    return redirect(url_for('editor.manage_foh'))

@editor.route('/foh/toggle_voting', methods=['POST'])
@login_required
def toggle_voting():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    # Toggle voting status
    VotingSettings.is_voting_active = not VotingSettings.is_voting_active
    
    status = "enabled" if VotingSettings.is_voting_active else "disabled"
    flash(f'Voting has been {status}!', 'success')
    
    return redirect(url_for('editor.manage_foh'))

@editor.route('/foh/update_vote_cost', methods=['POST'])
@login_required
def update_vote_cost():
    if current_user.role not in ['admin', 'editor']:
        abort(403)
    
    try:
        new_cost = float(request.form.get('vote_cost', 1.0))
        if new_cost <= 0:
            raise ValueError("Cost must be positive")
        
        VotingSettings.vote_cost = new_cost
        flash(f'Vote cost updated to GHS {new_cost:.2f}!', 'success')
    except ValueError:
        flash('Invalid vote cost. Please enter a positive number.', 'danger')
    
    return redirect(url_for('editor.manage_foh'))