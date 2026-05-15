"""
comets.py - Manejo de cometas visibles desde la ubicación del observador.

Usa datos del Minor Planet Center (MPC).
"""

import os
from datetime import datetime
from pathlib import Path

import requests
from skyfield.api import load
from skyfield.data import mpc


COMETS_URL = 'https://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
COMETS_FILE = 'CometEls.txt'


def download_comets_if_needed(force=False):
    """
    Descarga catálogo de cometas si no existe o está viejo (>7 días).
    """
    path = Path(COMETS_FILE)
    
    if path.exists() and not force:
        # Verificar antigüedad
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
    """
    Carga catálogo de cometas usando skyfield.
    Retorna DataFrame con todos los cometas conocidos.
    """
    if not Path(COMETS_FILE).exists():
        if not download_comets_if_needed():
            return None
    
    with load.open(COMETS_FILE) as f:
        comets = mpc.load_comets_dataframe(f)
    
    # Filtrar duplicados (algunos cometas aparecen varias veces)
    comets = (comets.sort_values('reference')
              .groupby('designation', as_index=False).last()
              .set_index('designation', drop=False))
    
    return comets


def get_visible_comets(comets_df, eph, observer, t, min_altitude=10,
                       max_magnitude=10.0):
    """
    Filtra cometas visibles según:
    - Altitud sobre horizonte > min_altitude
    - Magnitud aparente < max_magnitude (más brillante)
    
    Retorna lista de dicts con info de cometas visibles.
    """
    if comets_df is None or len(comets_df) == 0:
        return []
    
    sun = eph['sun']
    earth = eph['earth']
    location = earth + observer
    
    visible = []
    
    # Solo evaluar los primeros 100 cometas (los más activos típicamente)
    # Optimización: hacer todos puede tardar mucho
    for designation, comet_row in comets_df.head(200).iterrows():
        try:
            # Construir órbita del cometa
            comet = sun + mpc.comet_orbit(comet_row, ts=t.ts, GM_km3_s2=1.32712440018e11)
            
            # Calcular posición aparente
            astrometric = location.at(t).observe(comet)
            apparent = astrometric.apparent()
            alt, az, distance = apparent.altaz()
            
            # Filtrar por altitud
            if alt.degrees < min_altitude:
                continue
            
            # Calcular magnitud aproximada
            # (los cometas no tienen magnitud bien definida, esto es estimación)
            r_au = distance.au  # distancia a Tierra
            
            # Magnitud absoluta del cometa (de los elementos orbitales)
            mag_g = comet_row.get('magnitude_g', None)
            mag_k = comet_row.get('magnitude_k', None)
            
            if mag_g is not None and mag_k is not None:
                # Magnitud aparente típica
                # m = g + 5*log10(r) + 2.5*k*log10(d)
                # Simplificación
                import math
                try:
                    mag_apparent = mag_g + 5 * math.log10(r_au) + 2.5 * mag_k * math.log10(r_au)
                except (ValueError, ZeroDivisionError):
                    mag_apparent = 20  # muy débil
            else:
                mag_apparent = 20  # sin datos = asumir débil
            
            # Filtrar por brillo
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
            # Algunos cometas pueden fallar en cálculo, skip
            continue
    
    # Ordenar por magnitud (más brillante primero)
    visible.sort(key=lambda x: x['magnitude'])
    
    return visible
