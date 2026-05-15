"""
Configuración del observador.
Coordenadas de Montevideo, Uruguay.
"""

# Ubicación del observador
LOCATION = {
    "name": "Montevideo, Uruguay",
    "latitude": -34.9011,    # grados (negativo = sur)
    "longitude": -56.1645,   # grados (negativo = oeste)
    "elevation_m": 43,       # metros sobre nivel del mar
    "timezone": "America/Montevideo",
}

# Configuración de observación
OBSERVATION = {
    "min_altitude_deg": 10,  # Altitud mínima para considerar visible
                              # (objetos bajo 10° tienen mucha atmósfera)
}
