#!/usr/bin/env python3
"""
sky_tonight.py - Qué hay visible esta noche desde Montevideo

Calcula posiciones de planetas, Luna, Sol y cometas para una
sesión de observación.
"""

from datetime import datetime, timedelta
from skyfield.api import load, wgs84, N, S, E, W
from skyfield.almanac import find_discrete, sunrise_sunset
import pytz

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from config import LOCATION, OBSERVATION
from comets import download_comets_if_needed, load_comets, get_visible_comets


# ============================================================
# SETUP
# ============================================================

console = Console()

# Cargar timezone local
tz_local = pytz.timezone(LOCATION["timezone"])

# Cargar timescale de Skyfield
ts = load.timescale()

# Cargar ephemeris
console.print("[dim]Cargando ephemeris...[/dim]")
eph = load('de421.bsp')

# Definir observador (Montevideo)
observer = wgs84.latlon(
    latitude_degrees=LOCATION["latitude"],
    longitude_degrees=LOCATION["longitude"],
    elevation_m=LOCATION["elevation_m"],
)

# Cuerpos celestes
earth = eph['earth']
sun = eph['sun']
moon = eph['moon']
planets = {
    'Mercurio': eph['mercury'],
    'Venus':    eph['venus'],
    'Marte':    eph['mars'],
    'Júpiter':  eph['jupiter barycenter'],
    'Saturno':  eph['saturn barycenter'],
    'Urano':    eph['uranus barycenter'],
    'Neptuno':  eph['neptune barycenter'],
}


# ============================================================
# CÁLCULOS
# ============================================================

def get_now_local():
    return datetime.now(tz_local)


def get_position(body, t):
    location = earth + observer
    astrometric = location.at(t).observe(body)
    apparent = astrometric.apparent()
    alt, az, distance = apparent.altaz()
    return alt.degrees, az.degrees, distance.au


def get_sun_events(date_local):
    t0 = ts.from_datetime(date_local.replace(hour=0, minute=0))
    t1 = ts.from_datetime(date_local.replace(hour=23, minute=59))
    
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


def get_moon_phase(t):
    location = earth + observer
    sun_pos = location.at(t).observe(sun).apparent()
    moon_pos = location.at(t).observe(moon).apparent()
    
    sun_lon = sun_pos.ecliptic_latlon()[1].degrees
    moon_lon = moon_pos.ecliptic_latlon()[1].degrees
    
    phase = (moon_lon - sun_lon) % 360
    return phase


def phase_name(phase_deg):
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


def cardinal_direction(azimuth):
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO']
    idx = int((azimuth + 11.25) / 22.5) % 16
    return directions[idx]


# ============================================================
# OUTPUT
# ============================================================

def print_header(now_local, sunrise, sunset):
    header = f"""[bold cyan]🌌 SKY TONIGHT - {LOCATION['name']}[/bold cyan]

[white]📅 Fecha:[/white] {now_local.strftime('%A, %d de %B de %Y')}
[white]🕐 Hora local:[/white] {now_local.strftime('%H:%M:%S %Z')}
[yellow]☀️  Salida Sol:[/yellow] {sunrise.strftime('%H:%M') if sunrise else 'N/A'}
[orange3]🌅 Puesta Sol:[/orange3] {sunset.strftime('%H:%M') if sunset else 'N/A'}"""
    
    console.print(Panel(header, box=box.ROUNDED, border_style="cyan"))


def print_moon_info(t):
    phase = get_moon_phase(t)
    name = phase_name(phase)
    illumination = abs((phase % 360) - 180) / 180 * 100
    illumination = 100 - illumination if phase < 180 else illumination
    
    alt, az, dist_au = get_position(moon, t)
    visible = "✅ VISIBLE" if alt > OBSERVATION["min_altitude_deg"] else "❌ Bajo horizonte"
    
    info = f"""[bold yellow]🌙 LUNA[/bold yellow]

Fase: {name}
Iluminación: {illumination:.1f}%
Altitud: {alt:.1f}° {cardinal_direction(az)}
Distancia: {dist_au * 149597870.7:,.0f} km
Estado: {visible}"""
    
    console.print(Panel(info, box=box.ROUNDED, border_style="yellow"))


def print_planets_table(t):
    table = Table(
        title="🪐 PLANETAS",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
    )
    
    table.add_column("Planeta", style="white", width=12)
    table.add_column("Altitud", justify="right", width=10)
    table.add_column("Azimut", justify="right", width=10)
    table.add_column("Dirección", justify="center", width=10)
    table.add_column("Distancia (AU)", justify="right", width=15)
    table.add_column("Estado", justify="center", width=15)
    
    for name, body in planets.items():
        alt, az, dist_au = get_position(body, t)
        
        if alt > OBSERVATION["min_altitude_deg"]:
            status = "[green]✅ VISIBLE[/green]"
            alt_str = f"[green]{alt:.1f}°[/green]"
        elif alt > 0:
            status = "[yellow]⚠️ Bajo[/yellow]"
            alt_str = f"[yellow]{alt:.1f}°[/yellow]"
        else:
            status = "[red]❌ Horizonte[/red]"
            alt_str = f"[red]{alt:.1f}°[/red]"
        
        table.add_row(
            name,
            alt_str,
            f"{az:.1f}°",
            cardinal_direction(az),
            f"{dist_au:.3f}",
            status,
        )
    
    console.print(table)


def print_comets_table(t):
    """Imprime cometas visibles desde la ubicación."""
    console.print("[dim]Procesando catálogo de cometas...[/dim]")
    
    comets_df = load_comets()
    if comets_df is None:
        console.print("[yellow]⚠️  No se pudo cargar catálogo de cometas[/yellow]")
        return
    
    visible = get_visible_comets(
        comets_df, eph, observer, t,
        min_altitude=OBSERVATION["min_altitude_deg"],
        max_magnitude=12.0,  # Cometas hasta magnitud 12 (telescopios pequeños)
    )
    
    if not visible:
        console.print(Panel(
            "[yellow]No hay cometas visibles en este momento[/yellow]\n"
            "[dim]Criterio: altitud > 10°, magnitud < 12[/dim]",
            title="☄️ COMETAS",
            box=box.ROUNDED,
            border_style="magenta",
        ))
        return
    
    table = Table(
        title=f"☄️ COMETAS VISIBLES ({len(visible)})",
        box=box.ROUNDED,
        border_style="magenta",
        header_style="bold magenta",
    )
    
    table.add_column("Designación", style="white", width=20)
    table.add_column("Altitud", justify="right", width=10)
    table.add_column("Dirección", justify="center", width=10)
    table.add_column("Magnitud", justify="right", width=10)
    table.add_column("Dist. (AU)", justify="right", width=12)
    
    for comet in visible[:10]:  # Top 10 más brillantes
        mag_str = f"{comet['magnitude']:.1f}"
        if comet['magnitude'] < 6:
            mag_str = f"[green]{mag_str}[/green]"  # Visible a ojo
        elif comet['magnitude'] < 10:
            mag_str = f"[yellow]{mag_str}[/yellow]"  # Binoculares
        else:
            mag_str = f"[dim]{mag_str}[/dim]"  # Telescopio
        
        table.add_row(
            str(comet['designation'])[:20],
            f"{comet['altitude']:.1f}°",
            cardinal_direction(comet['azimuth']),
            mag_str,
            f"{comet['distance_au']:.3f}",
        )
    
    console.print(table)
    console.print(
        "[dim]Magnitudes: <6 ojo desnudo | 6-10 binoculares | >10 telescopio[/dim]"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    now_local = get_now_local()
    t = ts.from_datetime(now_local)
    
    sunrise, sunset = get_sun_events(now_local)
    
    console.print()
    print_header(now_local, sunrise, sunset)
    console.print()
    print_moon_info(t)
    console.print()
    print_planets_table(t)
    console.print()
    print_comets_table(t)
    console.print()
    
    console.print(
        f"[dim]Altitud mínima para 'visible': {OBSERVATION['min_altitude_deg']}°[/dim]"
    )
    console.print()


if __name__ == "__main__":
    main()
