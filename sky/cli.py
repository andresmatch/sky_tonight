"""
cli.py - Interfaz de línea de comandos.
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog='sky',
        description='Calculadora de visibilidad celestial desde Montevideo, Uruguay',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m sky now              Estado actual rápido
  python -m sky tonight          Reporte completo para esta noche
  python -m sky tonight --no-comets   Sin búsqueda de cometas (más rápido)
""")
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando: now
    parser_now = subparsers.add_parser(
        'now',
        help='Estado actual del cielo (rápido, sin cometas)',
    )
    
    # Comando: tonight
    parser_tonight = subparsers.add_parser(
        'tonight',
        help='Reporte completo para esta noche',
    )
    parser_tonight.add_argument(
        '--no-comets',
        action='store_true',
        help='Omitir cometas (más rápido)',
    )
    
    args = parser.parse_args()
    
    if args.command == 'now':
        from sky.reports import now
        now.run()
    elif args.command == 'tonight':
        from sky.reports import tonight
        tonight.run(skip_comets=args.no_comets)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
