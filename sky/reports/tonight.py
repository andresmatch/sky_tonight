"""
tonight.py - Reporte completo para la noche actual.

Incluye:
- Eventos solares + crepúsculos (mañana + anochecer)
- Luna detallada (snapshot actual)
- Planetas snapshot ahora
- 🆕 Análisis "mejor observación esta noche" (ventana oscura)
- Cometas visibles
"""

from datetime import datetime, timedelta

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
    analyze_night_visibility,
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
    """Tabla de crepúsculos organizada cronológicamente."""
    twilights = get_twilight_events(date_local)

    table = Table(
        title="🌅 CREPÚSCULOS HOY",
        box=box.ROUNDED,
        border_style="orange3",
        header_style="bold orange3",
    )

    table.add_column("Evento", style="white", width=30)
    table.add_column("Hora", justify="right", width=10)

    # Mañana (amanecer)
    rows_morning = [
        ("🌌 Fin noche astronómica", twilights.get('astronomical_dawn')),
        ("🌃 Crepúsculo náutico (fin)", twilights.get('nautical_dawn')),
        ("🌆 Crepúsculo civil (fin)", twilights.get('civil_dawn')),
        ("☀️  Salida del Sol", twilights.get('sunrise')),
    ]
    # Atardecer
    rows_evening = [
        ("🌅 Puesta del Sol", twilights.get('sunset')),
        ("🌆 Crepúsculo civil (inicio)", twilights.get('civil_dusk')),
        ("🌃 Crepúsculo náutico (inicio)", twilights.get('nautical_dusk')),
        ("🌌 Inicio noche astronómica", twilights.get('astronomical_dusk')),
    ]

    for label, dt in rows_morning + rows_evening:
        if dt:
            table.add_row(label, dt.strftime("%H:%M"))

    console.print(table)
    console.print(
        "[dim]Noche astronómica = cielo totalmente oscuro (Sol < -18°)[/dim]"
    )


def print_moon_info(t):
    """Info detallada de la Luna (snapshot actual)."""
    moon = get_moon()
    phase = get_moon_phase(t)
    name = phase_name(phase)
    illumination = get_moon_illumination(phase)

    alt, az, dist_au = get_position(moon, t)
    visible = "✅ VISIBLE" if alt > OBSERVATION["min_altitude_deg"] else "❌ Bajo horizonte"

    info = (
        f"[bold yellow]🌙 LUNA (ahora)[/bold yellow]\n\n"
        f"Fase: {name}\n"
        f"Iluminación: {illumination:.1f}%\n"
        f"Altitud: {alt:.1f}° {cardinal_direction(az)}\n"
        f"Distancia: {dist_au * 149597870.7:,.0f} km\n"
        f"Estado: {visible}"
    )
    console.print(Panel(info, box=box.ROUNDED, border_style="yellow"))


def print_planets_table(t):
    """Tabla detallada de planetas (snapshot actual)."""
    table = Table(
        title="🪐 PLANETAS (ahora)",
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


def print_night_analysis(date_local):
    """
    🆕 Análisis de mejor visibilidad durante la ventana oscura completa.

    Para cada planeta + Luna, calcula durante la noche astronómica:
    - Si supera el horizonte
    - Mejor altitud alcanzada y cuándo
    - Hora de salida y puesta sobre el horizonte
    """
    ts = get_timescale()
    twilights = get_twilight_events(date_local)
    tomorrow_local = date_local + timedelta(days=1)
    twilights_tomorrow = get_twilight_events(tomorrow_local)

    # Ventana oscura: fin crep. astronómico hoy → fin noche astro mañana
    night_start = twilights.get('astronomical_dusk')
    night_end = twilights_tomorrow.get('astronomical_dawn')

    if night_start is None or night_end is None:
        console.print(
            "[yellow]⚠️  No se pudo determinar la ventana oscura. "
            "Análisis nocturno omitido.[/yellow]\n"
        )
        return

    duration_h = (night_end - night_start).total_seconds() / 3600

    console.print(
        f"[bold cyan]🌃 VENTANA OSCURA:[/bold cyan] "
        f"{night_start.strftime('%H:%M')} → "
        f"{night_end.strftime('%H:%M (%a)')}  "
        f"[dim]({duration_h:.1f}h de cielo astronómico)[/dim]"
    )

    t_start = ts.from_datetime(night_start)
    t_end = ts.from_datetime(night_end)

    table = Table(
        title="🔭 MEJOR OBSERVACIÓN ESTA NOCHE",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green",
    )
    table.add_column("Cuerpo",    style="white", width=12)
    table.add_column("Estado",    justify="center", width=14)
    table.add_column("Sale",      justify="center", width=8)
    table.add_column("Mejor",     justify="center", width=8)
    table.add_column("Max alt",   justify="right", width=10)
    table.add_column("Az",        justify="right", width=8)
    table.add_column("Pone",      justify="center", width=8)

    def _fmt(dt):
        return dt.strftime("%H:%M") if dt else "—"

    def _state(max_alt, visible):
        if not visible:
            return "[red]🔻 no visible[/red]"
        if max_alt >= 50:
            return "[bold green]✨ alto[/bold green]"
        if max_alt >= 25:
            return "[green]📐 medio[/green]"
        if max_alt >= 10:
            return "[yellow]🌄 bajo[/yellow]"
        return "[red]🌅 muy bajo[/red]"

    # Luna primero
    moon = get_moon()
    vis = analyze_night_visibility(moon, t_start, t_end, step_minutes=15)
    table.add_row(
        "🌙 Luna",
        _state(vis['max_alt'], vis['visible']),
        _fmt(vis['rise_time']),
        _fmt(vis['max_alt_time']) if vis['visible'] else "—",
        f"{vis['max_alt']:+.1f}°" if vis['visible'] else "—",
        f"{vis['max_az']:.0f}°" if vis['visible'] else "—",
        _fmt(vis['set_time']),
    )

    # Planetas
    planets = get_planets()
    for name, body in planets.items():
        vis = analyze_night_visibility(body, t_start, t_end, step_minutes=15)
        table.add_row(
            name,
            _state(vis['max_alt'], vis['visible']),
            _fmt(vis['rise_time']),
            _fmt(vis['max_alt_time']) if vis['visible'] else "—",
            f"{vis['max_alt']:+.1f}°" if vis['visible'] else "—",
            f"{vis['max_az']:.0f}°" if vis['visible'] else "—",
            _fmt(vis['set_time']),
        )

    console.print(table)
    console.print(
        "[dim]Análisis con barrido cada 15 min durante toda la noche astronómica.[/dim]"
    )


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
    print_night_analysis(now_local)
    console.print()

    if not skip_comets:
        print_comets_table(t)
        console.print()

    console.print(
        f"[dim]Altitud mínima para 'visible': {OBSERVATION['min_altitude_deg']}°[/dim]"
    )
    console.print()
