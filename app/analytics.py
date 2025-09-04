from flask import request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
from .models import Card, CardView, User
from . import db, cache
import json
from collections import defaultdict


class AnalyticsService:
    """Service for handling analytics and metrics"""
    
    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_card_analytics(card_id, days=30):
        """Get comprehensive analytics for a specific card"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Basic metrics
        total_views = CardView.query.filter_by(card_id=card_id).count()
        period_views = CardView.query.filter(
            CardView.card_id == card_id,
            CardView.viewed_at >= start_date
        ).count()
        
        # Daily views for chart
        daily_views = db.session.query(
            func.date(CardView.viewed_at).label('date'),
            func.count(CardView.id).label('views')
        ).filter(
            CardView.card_id == card_id,
            CardView.viewed_at >= start_date
        ).group_by(func.date(CardView.viewed_at)).all()
        
        # Device analytics
        device_stats = db.session.query(
            CardView.device_type,
            func.count(CardView.id).label('count')
        ).filter(
            CardView.card_id == card_id,
            CardView.viewed_at >= start_date
        ).group_by(CardView.device_type).all()
        
        # Browser analytics
        browser_stats = db.session.query(
            CardView.browser,
            func.count(CardView.id).label('count')
        ).filter(
            CardView.card_id == card_id,
            CardView.viewed_at >= start_date
        ).group_by(CardView.browser).all()
        
        # Location analytics (if available)
        location_stats = db.session.query(
            CardView.country,
            func.count(CardView.id).label('count')
        ).filter(
            CardView.card_id == card_id,
            CardView.viewed_at >= start_date,
            CardView.country.isnot(None)
        ).group_by(CardView.country).order_by(desc('count')).limit(10).all()
        
        # Peak hours
        hourly_stats = db.session.query(
            func.extract('hour', CardView.viewed_at).label('hour'),
            func.count(CardView.id).label('count')
        ).filter(
            CardView.card_id == card_id,
            CardView.viewed_at >= start_date
        ).group_by('hour').all()
        
        return {
            'total_views': total_views,
            'period_views': period_views,
            'daily_views': [{'date': str(d.date), 'views': d.views} for d in daily_views],
            'device_stats': [{'device': d.device_type or 'Unknown', 'count': d.count} for d in device_stats],
            'browser_stats': [{'browser': b.browser or 'Unknown', 'count': b.count} for b in browser_stats],
            'location_stats': [{'country': l.country or 'Unknown', 'count': l.count} for l in location_stats],
            'hourly_stats': [{'hour': int(h.hour), 'count': h.count} for h in hourly_stats],
        }
    
    @staticmethod
    @cache.memoize(timeout=600)  # Cache for 10 minutes
    def get_user_analytics(user_id, days=30):
        """Get analytics for all user's cards"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user's cards
        cards = Card.query.filter_by(owner_id=user_id).all()
        card_ids = [c.id for c in cards]
        
        if not card_ids:
            return {
                'total_views': 0,
                'period_views': 0,
                'cards_analytics': [],
                'top_performing_card': None
            }
        
        # Total views across all cards
        total_views = CardView.query.filter(CardView.card_id.in_(card_ids)).count()
        period_views = CardView.query.filter(
            CardView.card_id.in_(card_ids),
            CardView.viewed_at >= start_date
        ).count()
        
        # Individual card performance
        cards_performance = db.session.query(
            Card.id,
            Card.name,
            Card.slug,
            func.count(CardView.id).label('views')
        ).join(CardView, Card.id == CardView.card_id)\
         .filter(Card.owner_id == user_id)\
         .group_by(Card.id, Card.name, Card.slug)\
         .order_by(desc('views')).all()
        
        cards_analytics = []
        for cp in cards_performance:
            card_data = AnalyticsService.get_card_analytics(cp.id, days)
            cards_analytics.append({
                'card_id': cp.id,
                'card_name': cp.name,
                'card_slug': cp.slug,
                'views': cp.views,
                'analytics': card_data
            })
        
        top_card = cards_performance[0] if cards_performance else None
        
        return {
            'total_views': total_views,
            'period_views': period_views,
            'cards_analytics': cards_analytics,
            'top_performing_card': {
                'id': top_card.id,
                'name': top_card.name,
                'views': top_card.views
            } if top_card else None
        }
    
    @staticmethod
    @cache.memoize(timeout=300)
    def get_global_analytics(days=30):
        """Get platform-wide analytics (admin only)"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Platform stats
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_cards = Card.query.count()
        public_cards = Card.query.filter_by(is_public=True).count()
        total_views = CardView.query.count()
        
        # Growth metrics
        new_users = User.query.filter(User.created_at >= start_date).count()
        new_cards = Card.query.filter(Card.created_at >= start_date).count()
        period_views = CardView.query.filter(CardView.viewed_at >= start_date).count()
        
        # Top cards
        top_cards = db.session.query(
            Card.name,
            Card.slug,
            func.count(CardView.id).label('views')
        ).join(CardView, Card.id == CardView.card_id)\
         .group_by(Card.id, Card.name, Card.slug)\
         .order_by(desc('views')).limit(10).all()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_cards': total_cards,
            'public_cards': public_cards,
            'total_views': total_views,
            'new_users': new_users,
            'new_cards': new_cards,
            'period_views': period_views,
            'top_cards': [{'name': c.name, 'slug': c.slug, 'views': c.views} for c in top_cards]
        }
    
    @staticmethod
    def track_card_view(card, request):
        """Enhanced view tracking with device and location info"""
        user_agent = request.user_agent
        user_agent_string = str(user_agent)
        
        # Enhanced device detection
        device_type = AnalyticsService._detect_device_type(user_agent, user_agent_string)
        
        # Get IP for geolocation (you'd implement actual geolocation service)
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
        
        view = CardView(
            card_id=card.id,
            ip_address=ip_address,
            user_agent=str(user_agent),
            device_type=device_type,
            browser=user_agent.browser,
            platform=user_agent.platform,
            viewed_at=datetime.utcnow()
        )
        
        # You could add geolocation lookup here
        # view.country = get_country_from_ip(ip_address)
        # view.city = get_city_from_ip(ip_address)
        
        db.session.add(view)
        return view
    
    @staticmethod
    def _detect_device_type(user_agent, user_agent_string):
        """Enhanced device type detection"""
        user_agent_lower = user_agent_string.lower()
        
        # Mobile devices detection
        mobile_indicators = [
            'mobile', 'android', 'iphone', 'ipod', 'blackberry', 
            'windows phone', 'opera mini', 'opera mobi', 'palm',
            'webos', 'kindle', 'silk', 'fennec', 'maemo', 'mot',
            'samsung', 'lg', 'nokia', 'sony', 'htc'
        ]
        
        # Tablet detection
        tablet_indicators = [
            'ipad', 'tablet', 'kindle fire', 'nexus 7', 'nexus 9', 
            'nexus 10', 'galaxy tab', 'xoom', 'sch-i800', 'playbook',
            'tablet pc', 'kfapwi', 'kfarwi', 'kfaswi', 'kffowi', 'kfgiwi',
            'kfmewi', 'kfot', 'kfsaw', 'kfsowi', 'kfthwi', 'kftt'
        ]
        
        # Check for tablets first (more specific)
        for indicator in tablet_indicators:
            if indicator in user_agent_lower:
                return 'tablet'
        
        # Check for mobile devices
        for indicator in mobile_indicators:
            if indicator in user_agent_lower:
                return 'mobile'
        
        # Check platform-specific indicators
        if user_agent.platform:
            platform = user_agent.platform.lower()
            if platform in ['android', 'iphone']:
                return 'mobile'
            elif platform == 'ipad':
                return 'tablet'
        
        # Additional mobile detection based on screen size hints
        if any(x in user_agent_lower for x in ['mobi', 'mini', 'mobile']):
            return 'mobile'
        
        # Default to desktop
        return 'desktop'
    
    @staticmethod
    @cache.memoize(timeout=300)
    def get_device_analytics(card_id=None, days=30):
        """Get detailed device analytics with mobile vs desktop breakdown"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = db.session.query(
            CardView.device_type,
            func.count(CardView.id).label('count'),
            func.count(func.distinct(CardView.ip_address)).label('unique_count')
        )
        
        if card_id:
            query = query.filter(CardView.card_id == card_id)
        
        device_stats = query.filter(
            CardView.viewed_at >= start_date
        ).group_by(CardView.device_type).all()
        
        # Calculate percentages and organize data
        total_views = sum(stat.count for stat in device_stats)
        device_breakdown = []
        
        for stat in device_stats:
            device_type = stat.device_type or 'Unknown'
            percentage = (stat.count / total_views * 100) if total_views > 0 else 0
            
            device_breakdown.append({
                'device_type': device_type,
                'count': stat.count,
                'unique_count': stat.unique_count,
                'percentage': round(percentage, 1)
            })
        
        # Sort by count (descending)
        device_breakdown.sort(key=lambda x: x['count'], reverse=True)
        
        # Calculate mobile vs desktop summary
        mobile_count = sum(d['count'] for d in device_breakdown if d['device_type'] in ['mobile', 'tablet'])
        desktop_count = sum(d['count'] for d in device_breakdown if d['device_type'] == 'desktop')
        other_count = sum(d['count'] for d in device_breakdown if d['device_type'] not in ['mobile', 'tablet', 'desktop'])
        
        mobile_percentage = (mobile_count / total_views * 100) if total_views > 0 else 0
        desktop_percentage = (desktop_count / total_views * 100) if total_views > 0 else 0
        
        return {
            'device_breakdown': device_breakdown,
            'total_views': total_views,
            'mobile_vs_desktop': {
                'mobile': {
                    'count': mobile_count,
                    'percentage': round(mobile_percentage, 1)
                },
                'desktop': {
                    'count': desktop_count,
                    'percentage': round(desktop_percentage, 1)
                },
                'other': {
                    'count': other_count,
                    'percentage': round((other_count / total_views * 100) if total_views > 0 else 0, 1)
                }
            }
        }
    
    @staticmethod
    @cache.memoize(timeout=600)
    def get_hourly_device_pattern(card_id=None, days=7):
        """Get device usage patterns by hour of day"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = db.session.query(
            func.extract('hour', CardView.viewed_at).label('hour'),
            CardView.device_type,
            func.count(CardView.id).label('count')
        )
        
        if card_id:
            query = query.filter(CardView.card_id == card_id)
        
        hourly_device_stats = query.filter(
            CardView.viewed_at >= start_date
        ).group_by('hour', CardView.device_type).all()
        
        # Organize data by hour
        hourly_pattern = {}
        for hour in range(24):
            hourly_pattern[hour] = {'mobile': 0, 'desktop': 0, 'tablet': 0, 'total': 0}
        
        for stat in hourly_device_stats:
            hour = int(stat.hour)
            device = stat.device_type or 'desktop'
            count = stat.count
            
            if device in ['mobile', 'desktop', 'tablet']:
                hourly_pattern[hour][device] = count
            hourly_pattern[hour]['total'] += count
        
        return hourly_pattern
    
    @staticmethod
    def clear_cache():
        """Clear analytics cache"""
        cache.clear()


def get_analytics_summary(card_id, days=7):
    """Get quick analytics summary for dashboard"""
    analytics = AnalyticsService.get_card_analytics(card_id, days)
    
    # Calculate growth rate
    prev_period_start = datetime.utcnow() - timedelta(days=days*2)
    prev_period_end = datetime.utcnow() - timedelta(days=days)
    
    prev_views = CardView.query.filter(
        CardView.card_id == card_id,
        CardView.viewed_at >= prev_period_start,
        CardView.viewed_at < prev_period_end
    ).count()
    
    growth_rate = 0
    if prev_views > 0:
        growth_rate = ((analytics['period_views'] - prev_views) / prev_views) * 100
    
    return {
        'current_views': analytics['period_views'],
        'total_views': analytics['total_views'],
        'growth_rate': round(growth_rate, 1),
        'top_device': analytics['device_stats'][0] if analytics['device_stats'] else {'device': 'Unknown', 'count': 0},
        'top_country': analytics['location_stats'][0] if analytics['location_stats'] else {'country': 'Unknown', 'count': 0}
    }