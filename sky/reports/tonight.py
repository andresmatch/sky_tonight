"""
tonight.py - Reporte completo para la noche actual.

Incluye:
- Eventos solares
- Crepúsculos
- Luna detallada
- Planetas
- Cometas visibles
"""

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from sky.observer import (
    get_timescale, get_position, tz_local,
    LOCATION, OBSERVATION,
)
from sky.bodies import (
    get_planets, get_moon, get_sun,
    get_sun_events, get_twilight_events,
    get_moon_phase, get_moon_illumination, phase_name,
)
from sky.comets import get_visible_comets
from sky.utils import cardinal_direction, format_altitude


console = Console()


def print_header(now_local, sunrise, sunset):
    """Header completo."""
    header = (
        f"[bold cyan]🌌 SKY TONIGHT - {LOCATION['name']}[/bold cyan]\n\n"
        f"[white]📅 Fecha:[/white] {now_local.strftime('%A, %d de %B de %Y')}\n"
        f"[white]🕐 Hora local:[/white] {now_local.strftime('%H:%M:%S %Z')}\n"
        f"[yellow]☀️  Salida Sol:[/yellow] {sunrise.strftime('%H:%M') if sunrise else 'N/A'}\n"
        f"[orange3]🌅 Puesta Sol:[/orange3] {sunset.strftime('%H:%M') if sunset else 'N/A'}"
    )
    console.print(Panel(header, box=box.ROUNDED, border_style="cyan"))


def print_twilights(date_local):
    """Tabla de crepúsculos."""
    twilights = get_twilight_events(date_local)
    
    table = Table(
        title="🌅 CREPÚSCULOS",
        box=box.ROUNDED,
        border_style="orange3",
        header_style="bold orange3",
    )
    
    table.add_column("Evento", style="white", width=25)
    table.add_column("Hora", justify="right", width=10)
    
    rows = [
        ("🌃 Fin noche astronómica", twilights['astronomical_dawn']),
        ("🌆 Crepúsculo náutico", twilights['nautical_dawn']),
        ("🌇 Crepúsculo civil", twilights['civil_dawn']),
        ("☀️  Salida del Sol", twilights['sunrise']),
        ("🌅 Puesta del Sol", twilights['sunset']),
        ("🌆 Crepúsculo civil", twilights['civil_dusk']),
        ("🌃 Crepúsculo náutico", twilights['nautical_dusk']),
        ("🌌 Inicio noche astronómica", twilights['astronomical_dusk']),
    ]
    
    for label, dt in rows:
        if dt:
            table.add_row(label, dt.strftime("%H:%M"))
    
    console.print(table)
    console.print(
        "[dim]Noche astronómica = cielo totalmente oscuro (Sol < -18°)[/dim]"
    )


def print_moon_info(t):
    """Info detallada de la Luna."""
    moon = get_moon()
    phase = get_moon_phase(t)
    name = phase_name(phase)
    illumination = get_moon_illumination(phase)
    
    alt, az, dist_au = get_position(moon, t)
    visible = "✅ VISIBLE" if alt > OBSERVATION["min_altitude_deg"] else "❌ Bajo horizonte"
    
    info = (
        f"[bold yellow]🌙 LUNA[/bold yellow]\n\n"
        f"Fase: {name}\n"
        f"Iluminación: {illumination:.1f}%\n"
        f"Altitud: {alt:.1f}° {cardinal_direction(az)}\n"
        f"Distancia: {dist_au * 149597870.7:,.0f} km\n"
        f"Estado: {visible}"
    )
    console.print(Panel(info, box=box.ROUNDED, border_style="yellow"))


def print_planets_table(t):
    """Tabla detallada de planetas."""
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
    
    planets = get_planets()
    for name, body in planets.items():
        alt, az, dist_au = get_position(body, t)
        status, alt_str = format_altitude(alt, OBSERVATION["min_altitude_deg"])
        
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
    """Tabla de cometas visibles."""
    console.print("[dim]Procesando catálogo de cometas (puede tardar)...[/dim]")
    
    visible = get_visible_comets(
        t,
        min_altitude=OBSERVATION["min_altitude_deg"],
        max_magnitude=12.0,
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
    
    for comet in visible[:10]:
        mag_str = f"{comet['magnitude']:.1f}"
        if comet['magnitude'] < 6:
            mag_str = f"[green]{mag_str}[/green]"
        elif comet['magnitude'] < 10:
            mag_str = f"[yellow]{mag_str}[/yellow]"
        else:
            mag_str = f"[dim]{mag_str}[/dim]"
        
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


def run(skip_comets=False):
    """
    Genera reporte completo de esta noche.
    
    Args:
        skip_comets: Si True, omite cometas (más rápido)
    """
    ts = get_timescale()
    now_local = datetime.now(tz_local)
    t = ts.from_datetime(now_local)
    
    sunrise, sunset = get_sun_events(now_local)
    
    console.print()
    print_header(now_local, sunrise, sunset)
    console.print()
    print_twilights(now_local)
    console.print()
    print_moon_info(t)
    console.print()
    print_planets_table(t)
    console.print()
    
    if not skip_comets:
        print_comets_table(t)
        console.print()
    
    console.print(
        f"[dim]Altitud mínima para 'visible': {OBSERVATION['min_altitude_deg']}°[/dim]"
    )
    console.print()
