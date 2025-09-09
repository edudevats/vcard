from datetime import datetime, timedelta, timezone
import pytz

# Configurar zona horaria UTC-6 (México/CST)
MEXICO_TZ = pytz.timezone('America/Mexico_City')  # UTC-6

def utc_to_local(utc_dt):
    """Convierte datetime UTC a zona horaria local (UTC-6)"""
    if utc_dt is None:
        return None
    
    if utc_dt.tzinfo is None:
        # Si no tiene tzinfo, asumimos que es UTC
        utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
    
    return utc_dt.astimezone(MEXICO_TZ)

def local_to_utc(local_dt):
    """Convierte datetime local (UTC-6) a UTC para almacenar en BD"""
    if local_dt is None:
        return None
    
    if local_dt.tzinfo is None:
        # Si no tiene tzinfo, asumimos que es local
        local_dt = MEXICO_TZ.localize(local_dt)
    
    return local_dt.astimezone(pytz.UTC).replace(tzinfo=None)

def now_local():
    """Obtiene la fecha/hora actual en zona horaria local (UTC-6)"""
    return datetime.now(MEXICO_TZ)

def now_utc_for_db():
    """Obtiene la fecha/hora actual en UTC para almacenar en BD"""
    return datetime.utcnow()

def today_start_local():
    """Obtiene el inicio del día actual en zona horaria local"""
    local_now = now_local()
    return local_now.replace(hour=0, minute=0, second=0, microsecond=0)

def today_start_utc():
    """Obtiene el inicio del día actual en UTC para consultas de BD"""
    return local_to_utc(today_start_local())

def format_local_datetime(dt, format_str='%d/%m/%Y %H:%M'):
    """Formatea datetime para mostrar en zona horaria local"""
    if dt is None:
        return ''
    
    # Convertir a local si viene de BD (UTC)
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)

def get_date_range_utc(days=30):
    """Obtiene rango de fechas en UTC para consultas de analytics"""
    end_local = now_local().replace(hour=23, minute=59, second=59, microsecond=999999)
    start_local = end_local - timedelta(days=days-1)
    start_local = start_local.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return local_to_utc(start_local), local_to_utc(end_local)

def get_month_range_utc():
    """Obtiene el rango del mes actual en UTC"""
    local_now = now_local()
    start_of_month_local = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month_local = local_now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return local_to_utc(start_of_month_local), local_to_utc(end_of_month_local)

def get_today_range_utc():
    """Obtiene el rango del día actual en UTC"""
    local_now = now_local()
    start_of_day_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day_local = local_now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return local_to_utc(start_of_day_local), local_to_utc(end_of_day_local)

def convert_existing_data():
    """
    Función de utilidad para convertir datos existentes si es necesario.
    Los datos ya están en UTC, por lo que no necesitamos convertir nada.
    Esta función está aquí para documentar que los datos existentes se mantienen igual.
    """
    pass