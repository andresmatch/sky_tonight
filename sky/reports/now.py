"""
now.py - Estado actual del cielo (snapshot rápido).

Para consultar en cualquier momento sin esperar cálculos pesados.
NO incluye cometas (lento).
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
    get_moon_phase, get_moon_illumination, phase_name,
)
from sky.utils import cardinal_direction, format_altitude


console = Console()


def print_compact_header(now_local):
    """Header compacto."""
    header = (
        f"[bold cyan]🌌 SKY NOW - {LOCATION['name']}[/bold cyan]\n"
        f"[white]🕐 {now_local.strftime('%A, %d %B %Y - %H:%M:%S %Z')}[/white]"
    )
    console.print(Panel(header, box=box.ROUNDED, border_style="cyan"))


def print_sun_status(t):
    """Estado del Sol."""
    sun = get_sun()
    alt, az, _ = get_position(sun, t)
    
    if alt > 0:
        emoji = "☀️"
        status = "[yellow]DÍA[/yellow]"
    elif alt > -6:
        emoji = "🌅"
        status = "[orange3]Crepúsculo civil[/orange3]"
    elif alt > -12:
        emoji = "🌆"
        status = "[blue]Crepúsculo náutico[/blue]"
    elif alt > -18:
        emoji = "🌃"
        status = "[purple]Crepúsculo astronómico[/purple]"
    else:
        emoji = "🌌"
        status = "[bright_blue]NOCHE CERRADA[/bright_blue]"
    
    info = (
        f"{emoji} [bold]SOL[/bold]\n"
        f"Estado: {status}\n"
        f"Altitud: {alt:.1f}° {cardinal_direction(az)}"
    )
    console.print(Panel(info, box=box.ROUNDED, border_style="yellow"))


def print_moon_status(t):
    """Estado de la Luna."""
    moon = get_moon()
    phase = get_moon_phase(t)
    name = phase_name(phase)
    illumination = get_moon_illumination(phase)
    
    alt, az, dist_au = get_position(moon, t)
    visible = "[green]✅ VISIBLE[/green]" if alt > 10 else "[red]❌ Bajo horizonte[/red]"
    
    info = (
        f"🌙 [bold]LUNA[/bold]\n"
        f"Fase: {name}\n"
        f"Iluminación: {illumination:.1f}%\n"
        f"Altitud: {alt:.1f}° {cardinal_direction(az)}\n"
        f"Estado: {visible}"
    )
    console.print(Panel(info, box=box.ROUNDED, border_style="yellow"))


def print_planets_compact(t):
    """Tabla compacta de planetas."""
    table = Table(
        title="🪐 PLANETAS AHORA",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
        show_header=True,
    )
    
    table.add_column("Planeta", style="white", width=10)
    table.add_column("Alt", justify="right", width=8)
    table.add_column("Az", justify="right", width=8)
    table.add_column("Dir", justify="center", width=6)
    table.add_column("Estado", justify="center", width=14)
    
    # Solo mostrar planetas con datos relevantes
    planets = get_planets()
    visible_count = 0
    
    for name, body in planets.items():
        alt, az, _ = get_position(body, t)
        status, alt_str = format_altitude(alt, OBSERVATION["min_altitude_deg"])
        
        if alt > OBSERVATION["min_altitude_deg"]:
            visible_count += 1
        
        table.add_row(
            name,
            alt_str,
            f"{az:.0f}°",
            cardinal_direction(az),
            status,
        )
    
    console.print(table)
    
    if visible_count == 0:
        console.print(
            "[yellow]⚠️  Ningún planeta visible en este momento[/yellow]"
        )
    else:
        console.print(
            f"[green]✅ {visible_count} planeta(s) visible(s) sobre {OBSERVATION['min_altitude_deg']}° horizonte[/green]"
        )


def run():
    """Genera reporte de estado actual."""
    ts = get_timescale()
    now_local = datetime.now(tz_local)
    t = ts.from_datetime(now_local)
    
    console.print()
    print_compact_header(now_local)
    console.print()
    print_sun_status(t)
    console.print()
    print_moon_status(t)
    console.print()
    print_planets_compact(t)
    console.print()
