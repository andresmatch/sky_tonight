"""
comets.py - Cometas visibles desde la ubicación del observador.

Usa datos del Minor Planet Center (MPC).
"""

import math
from datetime import datetime
from pathlib import Path

import requests
from skyfield.api import load
from skyfield.data import mpc

from sky.observer import (
    get_ephemeris, get_observer, get_timescale,
    DATA_DIR,
)


COMETS_URL = 'https://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
COMETS_FILE = str(DATA_DIR / "CometEls.txt")


def download_comets_if_needed(force=False):
    """Descarga catálogo de cometas si no existe o está viejo."""
    path = Path(COMETS_FILE)
    DATA_DIR.mkdir(exist_ok=True)
    
    if path.exists() and not force:
        age_days = (datetime.now().timestamp() - path.stat().st_mtime) / 86400
        if age_days < 7:
            return True
    
    print(f"Descargando catálogo de cometas...")
    try:
        response = requests.get(COMETS_URL, timeout=30)
        response.raise_for_status()
        path.write_text(response.text)
        print(f"✅ Catálogo descargado: {len(response.text.splitlines())} cometas")
        return True
    except Exception as e:
        print(f"❌ Error descargando catálogo: {e}")
        return False


def load_comets():
    """Carga catálogo de cometas usando skyfield."""
    if not Path(COMETS_FILE).exists():
        if not download_comets_if_needed():
            return None
    
    with load.open(COMETS_FILE) as f:
        comets = mpc.load_comets_dataframe(f)
    
    comets = (comets.sort_values('reference')
              .groupby('designation', as_index=False).last()
              .set_index('designation', drop=False))
    
    return comets


def get_visible_comets(t, min_altitude=10, max_magnitude=12.0, max_comets=200):
    """
    Filtra cometas visibles según altitud y magnitud.
    
    Returns:
        Lista de dicts con info de cometas visibles, ordenada por brillo.
    """
    comets_df = load_comets()
    if comets_df is None or len(comets_df) == 0:
        return []
    
    eph = get_ephemeris()
    observer = get_observer()
    sun = eph['sun']
    earth = eph['earth']
    location = earth + observer
    
    visible = []
    
    for designation, comet_row in comets_df.head(max_comets).iterrows():
        try:
            comet = sun + mpc.comet_orbit(
                comet_row, ts=t.ts, GM_km3_s2=1.32712440018e11
            )
            
            astrometric = location.at(t).observe(comet)
            apparent = astrometric.apparent()
            alt, az, distance = apparent.altaz()
            
            if alt.degrees < min_altitude:
                continue
            
            r_au = distance.au
            mag_g = comet_row.get('magnitude_g', None)
            mag_k = comet_row.get('magnitude_k', None)
            
            if mag_g is not None and mag_k is not None:
                try:
                    mag_apparent = (
                        mag_g + 5 * math.log10(r_au) + 2.5 * mag_k * math.log10(r_au)
                    )
                except (ValueError, ZeroDivisionError):
                    mag_apparent = 20
            else:
                mag_apparent = 20
            
            if mag_apparent > max_magnitude:
                continue
            
            visible.append({
                'designation': designation,
                'altitude': alt.degrees,
                'azimuth': az.degrees,
                'distance_au': r_au,
                'magnitude': mag_apparent,
            })
            
        except Exception:
            continue
    
    visible.sort(key=lambda x: x['magnitude'])
    return visible
