# 🌌 Sky Tonight

Calculadora de visibilidad celestial desde Montevideo, Uruguay.

## Funcionalidad

- ☀️ Horarios de salida y puesta del Sol
- 🌙 Fase de la Luna e iluminación
- 🪐 Posición de planetas visibles
- 📍 Coordenadas en altitud/azimut

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python sky_tonight.py
```

## Stack

- [Skyfield](https://rhodesmill.org/skyfield/) - Cálculos astronómicos
- [Astropy](https://www.astropy.org/) - Constantes y utilidades
- [Rich](https://github.com/Textualize/rich) - Output en terminal

## Licencia

MIT
