"""
Authentication routes for Crypto Trading Bot
"""
import os
import jwt
import uuid
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint("auth", __name__, url_prefix="/auth")

# In-memory user database for simplicity
# In a production environment, use a proper database
users = {}

logger = logging.getLogger(__name__)

def token_required(f):
    """
    JWT token authentication decorator
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode token
            secret_key = current_app.config['SECRET_KEY']
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # Set current user in flask g object
            g.current_user = users.get(data['user_id'])
            
            if not g.current_user:
                return jsonify({'error': 'User not found'}), 401
        
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        for user in users.values():
            if user['username'] == data['username']:
                return jsonify({'error': 'Username already taken'}), 409
            if user['email'] == data['email']:
                return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'id': user_id,
            'username': data['username'],
            'email': data['email'],
            'password': generate_password_hash(data['password']),
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and issue JWT token
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Find user by username
        user = None
        for u in users.values():
            if u['username'] == data['username']:
                user = u
                break
        
        # Check user and password
        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Generate token
        secret_key = current_app.config['SECRET_KEY']
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, secret_key, algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['GET'])
@token_required
def profile():
    """
    Get user profile
    """
    try:
        user = g.current_user
        
        # Remove password from user data
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at']
        }
        
        return jsonify(user_data)
    
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/update', methods=['PUT'])
@token_required
def update_profile():
    """
    Update user profile
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user = g.current_user
        
        # Update allowed fields
        allowed_fields = ['email']
        for field in allowed_fields:
            if field in data:
                user[field] = data[field]
        
        # Update password if provided
        if 'password' in data and data['password']:
            user['password'] = generate_password_hash(data['password'])
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """
    Logout user
    
    Note: JWT tokens cannot be invalidated without a blacklist.
    In a real system, you would implement a token blacklist or use short-lived tokens.
    """
    return jsonify({'message': 'Logout successful'})
