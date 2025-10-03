from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_caching import Cache
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
cache = Cache()

def create_app(config_name=None):
    app = Flask(__name__)
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from .config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register template filters
    from .template_filters import register_filters
    register_filters(app)
    
    # Add global template context for timezone
    @app.context_processor
    def inject_timezone_utils():
        from .timezone_utils import format_local_datetime, now_local
        return {
            'format_local_datetime': format_local_datetime,
            'now_local': now_local
        }
    
    # Register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    from .admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from .public import bp as public_bp
    app.register_blueprint(public_bp)

    from .api import bp as api_bp
    app.register_blueprint(api_bp)

    # Main route
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # Dashboard favicon route
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory, make_response
        response = make_response(send_from_directory(app.static_folder, 'favicon.ico'))
        response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 1 day
        response.headers['Content-Type'] = 'image/x-icon'
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('403.html'), 403
    
    @app.errorhandler(413)
    def request_entity_too_large_error(error):
        from flask import flash, redirect, request, jsonify
        max_size = app.config.get('MAX_CONTENT_LENGTH', 10485760) // (1024 * 1024)
        
        # Check if it's an AJAX request
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'error': f'El archivo es demasiado grande. Tamaño máximo permitido: {max_size}MB'
            }), 413
        
        flash(f'El archivo es demasiado grande. Tamaño máximo permitido: {max_size}MB', 'error')
        return redirect(request.referrer or '/')
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app