"""
bodies.py - Cuerpos celestes principales (Sol, Luna, Planetas).
"""

from skyfield.almanac import find_discrete, sunrise_sunset
from skyfield.almanac import dark_twilight_day, moon_phases

from sky.observer import (
    get_ephemeris, get_observer, get_timescale,
    get_position, tz_local,
)


# ============================================================
# DICCIONARIO DE PLANETAS
# ============================================================

def get_planets():
    """Retorna dict de planetas del sistema solar."""
    eph = get_ephemeris()
    return {
        'Mercurio': eph['mercury'],
        'Venus':    eph['venus'],
        'Marte':    eph['mars'],
        'Júpiter':  eph['jupiter barycenter'],
        'Saturno':  eph['saturn barycenter'],
        'Urano':    eph['uranus barycenter'],
        'Neptuno':  eph['neptune barycenter'],
    }


def get_sun():
    """Retorna objeto Sol."""
    return get_ephemeris()['sun']


def get_moon():
    """Retorna objeto Luna."""
    return get_ephemeris()['moon']


# ============================================================
# EVENTOS DEL SOL
# ============================================================

def get_sun_events(date_local):
    """
    Calcula salida y puesta del Sol para un día específico.
    
    Returns:
        (sunrise, sunset) como datetime en timezone local
    """
    ts = get_timescale()
    eph = get_ephemeris()
    observer = get_observer()
    
    t0 = ts.from_datetime(date_local.replace(hour=0, minute=0, second=0))
    t1 = ts.from_datetime(date_local.replace(hour=23, minute=59, second=59))
    
    f = sunrise_sunset(eph, observer)
    times, events = find_discrete(t0, t1, f)
    
    sunrise = None
    sunset = None
    for t, e in zip(times, events):
        dt_local = t.utc_datetime().astimezone(tz_local)
        if e == 1:
            sunrise = dt_local
        else:
            sunset = dt_local
    
    return sunrise, sunset


def get_twilight_events(date_local):
    """
    Calcula crepúsculos: civil, náutico, astronómico.
    
    Returns:
        dict con horas de cada transición
    """
    ts = get_timescale()
    eph = get_ephemeris()
    observer = get_observer()
    
    t0 = ts.from_datetime(date_local.replace(hour=0, minute=0, second=0))
    t1 = ts.from_datetime(date_local.replace(hour=23, minute=59, second=59))
    
    f = dark_twilight_day(eph, observer)
    times, events = find_discrete(t0, t1, f)
    
    # events: 0=noche, 1=astronómico, 2=náutico, 3=civil, 4=día
    twilights = {
        'astronomical_dawn': None,
        'nautical_dawn': None,
        'civil_dawn': None,
        'sunrise': None,
        'sunset': None,
        'civil_dusk': None,
        'nautical_dusk': None,
        'astronomical_dusk': None,
    }
    
    # Mapear transiciones
    prev_e = None
    for t, e in zip(times, events):
        dt = t.utc_datetime().astimezone(tz_local)
        
        if prev_e is None:
            prev_e = e
            continue
        
        # Mañana (transiciones ascendentes)
        if prev_e == 0 and e == 1:
            twilights['astronomical_dawn'] = dt
        elif prev_e == 1 and e == 2:
            twilights['nautical_dawn'] = dt
        elif prev_e == 2 and e == 3:
            twilights['civil_dawn'] = dt
        elif prev_e == 3 and e == 4:
            twilights['sunrise'] = dt
        # Tarde (transiciones descendentes)
        elif prev_e == 4 and e == 3:
            twilights['sunset'] = dt
        elif prev_e == 3 and e == 2:
            twilights['civil_dusk'] = dt
        elif prev_e == 2 and e == 1:
            twilights['nautical_dusk'] = dt
        elif prev_e == 1 and e == 0:
            twilights['astronomical_dusk'] = dt
        
        prev_e = e
    
    return twilights


# ============================================================
# LUNA
# ============================================================

def get_moon_phase(t):
    """
    Calcula fase de la Luna en grados (0-360).
    
    Returns:
        phase_deg (float): 0=nueva, 90=creciente, 180=llena, 270=menguante
    """
    eph = get_ephemeris()
    observer = get_observer()
    location = eph['earth'] + observer
    
    sun_pos = location.at(t).observe(eph['sun']).apparent()
    moon_pos = location.at(t).observe(eph['moon']).apparent()
    
    sun_lon = sun_pos.ecliptic_latlon()[1].degrees
    moon_lon = moon_pos.ecliptic_latlon()[1].degrees
    
    phase = (moon_lon - sun_lon) % 360
    return phase


def get_moon_illumination(phase_deg):
    """
    Calcula porcentaje de iluminación de la Luna.
    
    Args:
        phase_deg: ángulo de fase (0-360)
    
    Returns:
        porcentaje (0-100)
    """
    from math import cos, radians
    return (1 - cos(radians(phase_deg))) / 2 * 100


def phase_name(phase_deg):
    """Convierte grados de fase a nombre."""
    if phase_deg < 22.5 or phase_deg >= 337.5:
        return "Nueva 🌑"
    elif phase_deg < 67.5:
        return "Creciente 🌒"
    elif phase_deg < 112.5:
        return "Cuarto Creciente 🌓"
    elif phase_deg < 157.5:
        return "Gibosa Creciente 🌔"
    elif phase_deg < 202.5:
        return "Llena 🌕"
    elif phase_deg < 247.5:
        return "Gibosa Menguante 🌖"
    elif phase_deg < 292.5:
        return "Cuarto Menguante 🌗"
    else:
        return "Menguante 🌘"


def get_next_moon_phase(date_local, phase_target='new'):
    """
    Encuentra próxima fase específica de la Luna.
    
    Args:
        date_local: fecha desde la cual buscar
        phase_target: 'new', 'first_quarter', 'full', 'last_quarter'
    
    Returns:
        datetime de la próxima ocurrencia
    """
    from datetime import timedelta
    
    ts = get_timescale()
    eph = get_ephemeris()
    
    target_idx = {
        'new': 0,
        'first_quarter': 1,
        'full': 2,
        'last_quarter': 3,
    }[phase_target]
    
    t0 = ts.from_datetime(date_local)
    t1 = ts.from_datetime(date_local + timedelta(days=35))
    
    times, phases = find_discrete(t0, t1, moon_phases(eph))
    
    for t, p in zip(times, phases):
        if p == target_idx:
            return t.utc_datetime().astimezone(tz_local)
    
    return None
