"""
utils.py - Utilidades comunes.
"""


def cardinal_direction(azimuth):
    """Convierte azimut (grados) a dirección cardinal."""
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO']
    idx = int((azimuth + 11.25) / 22.5) % 16
    return directions[idx]


def format_altitude(alt_deg, min_altitude=10):
    """
    Formatea altitud con color según visibilidad.
    
    Returns:
        (status_str, alt_str) - texto con tags rich
    """
    if alt_deg > min_altitude:
        return (
            "[green]✅ VISIBLE[/green]",
            f"[green]{alt_deg:.1f}°[/green]",
        )
    elif alt_deg > 0:
        return (
            "[yellow]⚠️ Bajo[/yellow]",
            f"[yellow]{alt_deg:.1f}°[/yellow]",
        )
    else:
        return (
            "[red]❌ Horizonte[/red]",
            f"[red]{alt_deg:.1f}°[/red]",
        )
