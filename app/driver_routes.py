# Create a new file called driver_routes.py

from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models import BusLocation, User
from app.forms import BusLocationForm
from datetime import datetime

# Create blueprint
driver = Blueprint('driver', __name__, url_prefix='/driver')

@driver.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'driver':
        flash('Only drivers can access this page', 'danger')
        return redirect(url_for('main.home'))
    
    # Get buses assigned to the current driver
    buses = BusLocation.query.filter_by(driver_id=current_user.id).all()
    
    return render_template('driver/dashboard.html', buses=buses)

@driver.route('/start_tracking/<int:bus_id>', methods=['GET', 'POST'])
@login_required
def start_tracking(bus_id):
    if current_user.role != 'driver':
        flash('Only drivers can access this page', 'danger')
        return redirect(url_for('main.home'))
    
    bus = BusLocation.query.get_or_404(bus_id)
    
    # Check if the bus is assigned to this driver
    if bus.driver_id != current_user.id:
        flash('You are not assigned to this bus', 'danger')
        return redirect(url_for('driver.dashboard'))
    
    # Update bus status to active
    bus.status = 'active'
    db.session.commit()
    
    return render_template('driver/tracking.html', bus=bus)

@driver.route('/stop_tracking/<int:bus_id>')
@login_required
def stop_tracking(bus_id):
    if current_user.role != 'driver':
        flash('Only drivers can access this page', 'danger')
        return redirect(url_for('main.home'))
    
    bus = BusLocation.query.get_or_404(bus_id)
    
    # Check if the bus is assigned to this driver
    if bus.driver_id != current_user.id:
        flash('You are not assigned to this bus', 'danger')
        return redirect(url_for('driver.dashboard'))
    
    # Update bus status to inactive
    bus.status = 'inactive'
    db.session.commit()
    
    flash('Bus tracking stopped successfully', 'success')
    return redirect(url_for('driver.dashboard'))

@driver.route('/update_location/<int:bus_id>', methods=['POST'])
@login_required
def update_location(bus_id):
    if current_user.role != 'driver':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    bus = BusLocation.query.get_or_404(bus_id)
    
    # Check if the bus is assigned to this driver
    if bus.driver_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not assigned to this bus'}), 403
    
    data = request.json
    
    # Validate data
    if 'latitude' not in data or 'longitude' not in data:
        return jsonify({'success': False, 'error': 'Missing coordinates'}), 400
    
    try:
        bus.latitude = float(data['latitude'])
        bus.longitude = float(data['longitude'])
        bus.last_update = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500