from flask import request, g
from functools import wraps
import time
import logging

# Import database instance
try:
    from . import db
except ImportError:
    # Fallback for direct execution or testing
    db = None


def monitor_performance(f):
    """Decorator to monitor route performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        # Track database queries
        g.query_count = 0
        g.query_time = 0
        
        result = f(*args, **kwargs)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Log performance metrics
        if total_time > 1.0:  # Log slow requests (>1 second)
            logging.warning(f"Slow request: {request.path} took {total_time:.2f}s")
        
        return result
    return decorated_function


def optimize_db_queries():
    """Apply database optimization techniques"""
    # Enable query optimization
    db.engine.pool_pre_ping = True
    db.engine.pool_recycle = 3600  # Recycle connections every hour


class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def add_indexes():
        """Add database indexes for better performance"""
        try:
            # Add composite indexes for common queries
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_owner_public 
                ON card(owner_id, is_public);
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_view_date_card 
                ON card_view(viewed_at, card_id);
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_service_card_visible 
                ON service(card_id, is_visible, order_index);
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_product_card_visible 
                ON product(card_id, is_visible, order_index);
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_gallery_card_visible 
                ON gallery_item(card_id, is_visible, order_index);
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_gallery_featured 
                ON gallery_item(card_id, is_featured, is_visible);
            """)
            
            print("Database indexes created successfully")
            
        except Exception as e:
            print(f"Error creating indexes: {e}")
    
    @staticmethod
    def analyze_slow_queries():
        """Analyze and report slow queries"""
        import sqlite3
        # Use the global db instance if available
        if db is None:
            return
        
        try:
            # Get database file path
            db_path = db.engine.url.database
            
            # Enable query logging for analysis
            with sqlite3.connect(db_path) as conn:
                conn.execute('PRAGMA analysis_limit=1000')
                conn.execute('PRAGMA optimize')
                
                # Query to find tables that might benefit from indexing
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = cursor.fetchall()
                
                print("Tables analyzed for optimization:")
                for table in tables:
                    table_name = table[0]
                    cursor = conn.execute(f'ANALYZE {table_name}')
                    print(f"- {table_name}: Analyzed successfully")
                    
        except Exception as e:
            print(f"Error analyzing queries: {e}")
            logging.error(f"Query analysis failed: {e}")
    
    @staticmethod
    def optimize_images():
        """Optimize image storage and delivery"""
        import os
        from PIL import Image
        from flask import current_app
        
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
            
            if not os.path.exists(upload_folder):
                return
                
            optimized_count = 0
            
            for filename in os.listdir(upload_folder):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(upload_folder, filename)
                    
                    try:
                        with Image.open(filepath) as img:
                            # Convert to WebP if not already
                            if not filename.lower().endswith('.webp'):
                                webp_path = os.path.splitext(filepath)[0] + '.webp'
                                img.save(webp_path, 'WebP', quality=85, optimize=True)
                                optimized_count += 1
                                
                            # Optimize existing images
                            if img.size[0] > 1920 or img.size[1] > 1920:
                                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                                img.save(filepath, optimize=True, quality=85)
                                optimized_count += 1
                                
                    except Exception as e:
                        print(f"Error optimizing {filename}: {e}")
                        
            print(f"Optimized {optimized_count} images")
            
        except Exception as e:
            print(f"Image optimization failed: {e}")
            logging.error(f"Image optimization error: {e}")


class MemoryOptimizer:
    """Memory usage optimization"""
    
    @staticmethod
    def cleanup_sessions():
        """Clean up expired sessions"""
        from datetime import datetime, timedelta
        try:
            from . import db, cache
            from .models import User
        except ImportError:
            # Handle case where imports fail
            if db is None:
                return
            try:
                from app import cache
                from app.models import User
            except ImportError:
                return
        
        try:
            # Clear expired cache entries
            if hasattr(cache, 'clear'):
                # Clear old analytics cache (older than 1 hour)
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                # Clean up user login tracking
                expired_users = User.query.filter(
                    User.last_login < cutoff_time
                ).all()
                
                for user in expired_users:
                    cache.delete_many(f'user_session_{user.id}_*')
                    cache.delete_many(f'user_analytics_{user.id}_*')
                
                print(f"Cleaned up sessions for {len(expired_users)} inactive users")
                
        except Exception as e:
            print(f"Session cleanup failed: {e}")
            logging.error(f"Session cleanup error: {e}")
    
    @staticmethod
    def optimize_queries():
        """Apply query optimizations"""
        # Use the global db instance if available
        if db is None:
            return
        
        try:
            # Configure SQLAlchemy for better performance
            db.session.configure(
                # Enable query caching
                query_cls=db.Query,
                # Optimize connection pooling
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Enable SQLite optimizations
            if 'sqlite' in str(db.engine.url):
                db.session.execute('PRAGMA journal_mode=WAL')
                db.session.execute('PRAGMA synchronous=NORMAL')
                db.session.execute('PRAGMA cache_size=-64000')  # 64MB cache
                db.session.execute('PRAGMA temp_store=MEMORY')
                db.session.execute('PRAGMA mmap_size=268435456')  # 256MB mmap
                
            db.session.commit()
            print("Database query optimizations applied")
            
        except Exception as e:
            print(f"Query optimization failed: {e}")
            logging.error(f"Query optimization error: {e}")
            db.session.rollback()


def compress_response(response):
    """Compress HTTP responses"""
    import gzip
    from flask import request
    
    # Check if client accepts gzip
    if 'gzip' not in request.headers.get('Accept-Encoding', ''):
        return response
        
    # Only compress text responses
    if not response.content_type.startswith(('text/', 'application/json', 'application/javascript')):
        return response
        
    # Don't compress small responses
    if len(response.data) < 1000:
        return response
        
    try:
        response.data = gzip.compress(response.data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(response.data)
        response.headers['Vary'] = 'Accept-Encoding'
        
    except Exception as e:
        logging.error(f"Response compression failed: {e}")
        
    return response


# Performance monitoring middleware
class PerformanceMiddleware:
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
    
    def before_request(self):
        g.start_time = time.time()
        g.query_count = 0
    
    def after_request(self, response):
        total_time = time.time() - g.start_time
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{total_time:.3f}s"
        
        # Log slow requests
        if total_time > 2.0:
            logging.warning(f"Slow request: {request.path} - {total_time:.3f}s")
        
        return response


# Asset optimization
def optimize_static_assets():
    """Optimize CSS, JS, and image assets"""
    import os
    import gzip
    from flask import current_app
    
    try:
        static_folder = current_app.static_folder
        
        if not os.path.exists(static_folder):
            return
            
        optimized_files = 0
        
        # Walk through static files
        for root, dirs, files in os.walk(static_folder):
            for file in files:
                filepath = os.path.join(root, file)
                
                # Skip already compressed files
                if file.endswith('.gz'):
                    continue
                    
                # Compress CSS, JS, and other text files
                if file.endswith(('.css', '.js', '.html', '.svg', '.txt')):
                    try:
                        with open(filepath, 'rb') as f:
                            content = f.read()
                            
                        # Only compress if file is larger than 1KB
                        if len(content) > 1024:
                            compressed_path = filepath + '.gz'
                            with gzip.open(compressed_path, 'wb') as f:
                                f.write(content)
                            optimized_files += 1
                            
                    except Exception as e:
                        print(f"Error compressing {file}: {e}")
                        
        print(f"Pre-compressed {optimized_files} static assets")
        
    except Exception as e:
        print(f"Static asset optimization failed: {e}")
        logging.error(f"Asset optimization error: {e}")


# Cache warming utilities
def warm_cache_on_startup():
    """Warm up cache with frequently accessed data"""
    try:
        from .cache_utils import CacheManager
        from .models import Theme, Card
        from . import cache
    except ImportError:
        # Handle case where imports fail
        try:
            from app.cache_utils import CacheManager
            from app.models import Theme, Card
            from app import cache
        except ImportError:
            return
        
        # Warm popular cards cache
        CacheManager.warm_popular_cards()
        
        # Cache frequently used themes
        themes = Theme.query.filter_by(is_active=True).all()
        for theme in themes:
            cache.set(f'theme_{theme.id}', theme, timeout=3600)
            
        # Cache public cards count for dashboard
        public_cards_count = Card.query.filter_by(is_public=True).count()
        cache.set('public_cards_count', public_cards_count, timeout=1800)
        
        print(f"Cache warmed: {len(themes)} themes, popular cards, and stats")
        
    except Exception as e:
        print(f"Cache warming failed: {e}")
        logging.error(f"Cache warming error: {e}")


# Database connection pooling
def setup_connection_pooling(app):
    """Configure database connection pooling"""
    # Configure connection pool settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }