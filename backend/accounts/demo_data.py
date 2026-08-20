"""Datos fijos que usan `sembrar_demo` y `limpiar_demo`.

Viven en un módulo compartido y no en cada comando para que los dos
identifiquen exactamente los mismos registros: `sembrar_demo` los crea,
`limpiar_demo` los borra (o revierte) por el mismo criterio.

Dos tipos de identidad:

- **Desechables** (`ALUMNOS_DEMO`, `ASESORES_DEMO`): números de
  cuenta/trabajador con prefijo `DEMO` para que sean reconocibles a
  simple vista en el admin. `limpiar_demo` las borra por completo.
- **Fijas** (`EMAIL_*_DEMO_LOGIN`): correos `@unam.dev` con contraseña
  conocida (`PASSWORD_DEMO`) para que quien haga la demo inicie sesión
  de verdad e interactúe en vivo. `limpiar_demo` nunca borra estos
  `User` — solo revierte lo que la demo en vivo haya podido generar
  sobre ellos.
"""

import datetime

PASSWORD_DEMO = "Test.2026"

EMAIL_ALUMNO_DEMO_LOGIN = "alumno@unam.dev"
EMAIL_ACADEMICO_DEMO_LOGIN = "academico@unam.dev"
EMAIL_SAE_DEMO_LOGIN = "sae@unam.dev"

NUMERO_CUENTA_ALUMNO_FIJO = "DEMOFIJO1"
NUMERO_TRABAJADOR_ACADEMICO_FIJO = "DEMOFIJO2"
CARRERA_CLAVE_ALUMNO_FIJO = 101  # Actuaría

# (clave, generación) de las carreras usadas por ALUMNOS_DEMO, ya sembradas
# por la migración 0002_seed_areas_carreras de `carreras`.
ALUMNOS_DEMO = [
    {
        "numero_cuenta": "DEMO0001", "email": "ana.demo@atenea.demo",
        "nombre": "Ana", "ap1": "García", "ap2": "López",
        "carrera_clave": 101, "generacion": 2023,  # Actuaría
    },
    {
        "numero_cuenta": "DEMO0002", "email": "beto.demo@atenea.demo",
        "nombre": "Beto", "ap1": "Hernández", "ap2": "Cruz",
        "carrera_clave": 106, "generacion": 2022,  # Física
    },
    {
        "numero_cuenta": "DEMO0003", "email": "carla.demo@atenea.demo",
        "nombre": "Carla", "ap1": "Martínez", "ap2": "Ruiz",
        "carrera_clave": 201, "generacion": 2024,  # Biología
    },
]

# Dos asesores activos (con registro, disponibilidad y materia) y uno
# pendiente de aprobación (para mostrar la pantalla de asesor pendiente).
ASESORES_DEMO = [
    {
        "numero_trabajador": "DEMOTRAB1", "email": "diego.demo@atenea.demo",
        "nombre": "Diego", "ap1": "Sánchez", "ap2": "Torres", "area": "Matemáticas",
        "activo": True, "pendiente": False,
        "disponibilidades": [
            {"dia_semana": 0, "hora_inicio": datetime.time(10, 0), "formato": "virtual",
             "liga_virtual": "https://meet.atenea.demo/diego-lunes"},
            {"dia_semana": 2, "hora_inicio": datetime.time(10, 0), "formato": "virtual",
             "liga_virtual": "https://meet.atenea.demo/diego-miercoles"},
        ],
    },
    {
        "numero_trabajador": "DEMOTRAB2", "email": "elena.demo@atenea.demo",
        "nombre": "Elena", "ap1": "Ramírez", "ap2": "Flores", "area": "Física",
        "activo": True, "pendiente": False,
        "disponibilidades": [
            {"dia_semana": 1, "hora_inicio": datetime.time(12, 0), "formato": "presencial",
             "ubicacion": "Salón 105, Edificio Principal"},
            {"dia_semana": 3, "hora_inicio": datetime.time(12, 0), "formato": "presencial",
             "ubicacion": "Salón 105, Edificio Principal"},
        ],
    },
    {
        "numero_trabajador": "DEMOTRAB3", "email": "fernando.demo@atenea.demo",
        "nombre": "Fernando", "ap1": "Vargas", "ap2": "Ortiz", "area": "Biología",
        "activo": False, "pendiente": True,
        "disponibilidades": [],
    },
]

# 6 asesorías, dos por alumno demo: una pareja (realizada asistida / cancelada
# o no asistida) por cada quien, distribuidas en las disponibilidades de
# arriba. `disponibilidad` es el índice dentro de la lista de
# `disponibilidades` del asesor referido.
ASESORIAS_DEMO = [
    {
        "alumno": "DEMO0001", "asesor": "DEMOTRAB1", "disponibilidad": 0, "semanas_atras": 1,
        "estado": "realizada", "asistio": True,
        "notas": "Repasamos límites y continuidad; el alumno domina el tema.",
    },
    {
        "alumno": "DEMO0001", "asesor": "DEMOTRAB1", "disponibilidad": 1, "semanas_atras": 2,
        "estado": "cancelada", "motivo_cancelacion": "El alumno avisó que no podía asistir.",
    },
    {
        "alumno": "DEMO0002", "asesor": "DEMOTRAB2", "disponibilidad": 0, "semanas_atras": 1,
        "estado": "realizada", "asistio": True,
    },
    {
        "alumno": "DEMO0002", "asesor": "DEMOTRAB2", "disponibilidad": 1, "semanas_atras": 3,
        "estado": "realizada", "asistio": False,
    },
    {
        "alumno": "DEMO0003", "asesor": "DEMOTRAB2", "disponibilidad": 0, "semanas_atras": 2,
        "estado": "realizada", "asistio": False,
    },
    {
        "alumno": "DEMO0003", "asesor": "DEMOTRAB2", "disponibilidad": 1, "semanas_atras": 4,
        "estado": "cancelada", "motivo_cancelacion": "El asesor tuvo una emergencia.",
    },
]
