# 🌌 Sky Tonight

Calculadora de visibilidad celestial desde Montevideo, Uruguay.

## Funcionalidad

- ☀️ Eventos solares (salida/puesta + crepúsculos)
- 🌙 Fase de la Luna e iluminación
- 🪐 Posiciones de planetas
- ☄️ Cometas visibles (catálogo MPC)
- 📍 Coordenadas altitud/azimut

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Descargar ephemeris JPL (primera vez):
wget -P data/ https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp
```

## Uso

### Estado actual rápido
```bash
python -m sky now
```

### Reporte completo esta noche
```bash
python -m sky tonight              # Con cometas (lento)
python -m sky tonight --no-comets  # Sin cometas (rápido)
```

## Stack

- [Skyfield](https://rhodesmill.org/skyfield/) - Cálculos astronómicos
- [Astropy](https://www.astropy.org/) - Constantes y utilidades
- [Rich](https://github.com/Textualize/rich) - Output en terminal

## Arquitectura
sky/
├── init.py
├── main.py
├── cli.py              # CLI con argparse
├── observer.py         # Configuración y carga de ephemeris
├── bodies.py           # Sol, Luna, Planetas
├── comets.py           # Cometas
├── utils.py            # Helpers
└── reports/
├── now.py          # Estado actual
└── tonight.py      # Reporte completo de noche
## Próximas funcionalidades

- `sky week` - Eventos próximos 7 días
- `sky month` - Eventos próximos 30 días  
- `sky year` - Fenómenos relevantes 12 meses
- Lluvias de meteoros
- Conjunciones planetarias
- Oposiciones
- Eclipses

## Licencia

MIT
