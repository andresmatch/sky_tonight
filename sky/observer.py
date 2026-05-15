"""
observer.py - Configuración del observador y carga de ephemeris.

Centraliza:
- Ubicación geográfica
- Carga de timescale
- Carga de ephemeris JPL
- Acceso a cuerpos celestes
"""

from pathlib import Path

from skyfield.api import load, wgs84
import pytz


# ============================================================
# CONFIGURACIÓN
# ============================================================

LOCATION = {
    "name": "Montevideo, Uruguay",
    "latitude": -34.9011,
    "longitude": -56.1645,
    "elevation_m": 43,
    "timezone": "America/Montevideo",
}

OBSERVATION = {
    "min_altitude_deg": 10,
}

# Rutas de datos
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EPHEMERIS_FILE = str(DATA_DIR / "de421.bsp")


# ============================================================
# SETUP
# ============================================================

# Timezone local
tz_local = pytz.timezone(LOCATION["timezone"])

# Timescale (lazy load)
_ts = None
_eph = None


def get_timescale():
    """Retorna timescale (lazy loaded)."""
    global _ts
    if _ts is None:
        _ts = load.timescale()
    return _ts


def get_ephemeris():
    """Retorna ephemeris JPL (lazy loaded)."""
    global _eph
    if _eph is None:
        if not Path(EPHEMERIS_FILE).exists():
            raise FileNotFoundError(
                f"Ephemeris no encontrado: {EPHEMERIS_FILE}\n"
                f"Descargar de: https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp"
            )
        _eph = load(EPHEMERIS_FILE)
    return _eph


def get_observer():
    """Retorna objeto observador (Montevideo)."""
    return wgs84.latlon(
        latitude_degrees=LOCATION["latitude"],
        longitude_degrees=LOCATION["longitude"],
        elevation_m=LOCATION["elevation_m"],
    )


def get_position(body, t):
    """
    Calcula altitud, azimut y distancia de un cuerpo desde el observador.
    
    Args:
        body: objeto celeste de skyfield
        t: Time de skyfield
    
    Returns:
        (alt_deg, az_deg, dist_au)
    """
    eph = get_ephemeris()
    observer = get_observer()
    location = eph['earth'] + observer
    
    astrometric = location.at(t).observe(body)
    apparent = astrometric.apparent()
    alt, az, distance = apparent.altaz()
    
    return alt.degrees, az.degrees, distance.au
