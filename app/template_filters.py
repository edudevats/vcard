from datetime import datetime
from .timezone_utils import utc_to_local, format_local_datetime

def register_filters(app):
    """Registra filtros personalizados para templates"""
    
    @app.template_filter('local_datetime')
    def local_datetime_filter(dt, format_str='%d/%m/%Y %H:%M'):
        """Convierte datetime UTC a zona local y lo formatea"""
        if dt is None:
            return ''
        return format_local_datetime(dt, format_str)
    
    @app.template_filter('local_date')
    def local_date_filter(dt):
        """Convierte datetime UTC a fecha local"""
        if dt is None:
            return ''
        return format_local_datetime(dt, '%d/%m/%Y')
    
    @app.template_filter('local_time')
    def local_time_filter(dt):
        """Convierte datetime UTC a hora local"""
        if dt is None:
            return ''
        return format_local_datetime(dt, '%H:%M')
    
    @app.template_filter('local_full')
    def local_full_filter(dt):
        """Convierte datetime UTC a fecha y hora local completa"""
        if dt is None:
            return ''
        return format_local_datetime(dt, '%d de %B de %Y a las %H:%M')
    
    @app.template_filter('relative_time')
    def relative_time_filter(dt):
        """Muestra tiempo relativo (hace 2 horas, ayer, etc.)"""
        if dt is None:
            return ''
        
        from .timezone_utils import now_local
        local_dt = utc_to_local(dt)
        now = now_local()
        
        diff = now - local_dt
        
        if diff.days > 0:
            if diff.days == 1:
                return "ayer"
            elif diff.days < 7:
                return f"hace {diff.days} días"
            else:
                return format_local_datetime(dt, '%d/%m/%Y')
        
        hours = diff.seconds // 3600
        if hours > 0:
            return f"hace {hours} hora{'s' if hours != 1 else ''}"
        
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"hace {minutes} minuto{'s' if minutes != 1 else ''}"
        
        return "ahora mismo"