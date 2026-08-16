"""Vigencia de un académico según el directorio público de la Facultad de
Ciencias (contrato explorado en vivo el 2026-08-16, ver Task 13 del plan).

No existe un servicio dedicado con contrato propio: se usa el directorio
público de la Facultad, que indexa por NOMBRE, no por número de trabajador.
La URL base **no se versiona**: se lee de `settings.DIRECTORIO_FC_URL_BASE`
(variable de entorno `DIRECTORIO_FC_URL_BASE`, sin valor por default en
código ni en `.env.example`). Si no está configurada, esta función no
intenta ninguna petición y resuelve a `False` de inmediato — el servicio "no
disponible" nunca bloquea la solicitud del académico, solo la deja
pendiente.

Por decisión de Héctor (Task 13 Step 2), la validación automática es
deliberadamente estrecha: solo se concede cuando la búsqueda por nombre da
EXACTAMENTE un resultado, y ese resultado coincide, campo a campo y tras
limpiar acentos/mayúsculas/espacios, con el nombre esperado. Cualquier otro
caso -cero resultados, más de uno, un nombre que no calza, la URL sin
configurar, o un fallo del servicio- deja `activo=False`: el perfil queda
pendiente de que la SAE lo revise a mano. Nunca lanza una excepción hacia
quien la llama; es pesimista a propósito (ADR 0027 decisión 7).

"Activo" significa "imparte clases en el semestre vigente"
(`persona__grupos[].calendario__periodo == semestre_vigente()`), no la
vigencia del nombramiento -son preguntas distintas.
"""

import json
import re
import unicodedata
from urllib.parse import quote

import requests
from django.conf import settings

from academico.servicios import semestre_vigente

TIMEOUT_SEGUNDOS = 5


def _url_busqueda(nombre_completo: str) -> str:
    return f"{settings.DIRECTORIO_FC_URL_BASE}/gql/busquedadirectorio/{quote(nombre_completo, safe='')}"


def _url_detalle(persona_id: int) -> str:
    return f"{settings.DIRECTORIO_FC_URL_BASE}/directorio/{persona_id}"


def _limpiar(texto: str) -> str:
    """Normaliza para comparar: sin acentos, sin mayúsculas, un solo espacio."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_acentos).strip().casefold()


def _mismo_nombre(persona: dict, nombre_completo: str) -> bool:
    partes = [
        persona.get("persona__nombre") or "",
        persona.get("persona__apellido_1") or "",
        persona.get("persona__apellido_2") or "",
    ]
    nombre_directorio = _limpiar(" ".join(p for p in partes if p))
    return nombre_directorio == _limpiar(nombre_completo)


def _buscar_por_nombre(nombre_completo: str) -> list[dict]:
    respuesta = requests.get(_url_busqueda(nombre_completo), timeout=TIMEOUT_SEGUNDOS)
    respuesta.raise_for_status()
    return respuesta.json()["data"]["busca_directorio"]


def _extraer_arreglo_balanceado(texto: str, marcador: str) -> list | None:
    """Extrae `"marcador":[...]` embebido en el HTML del detalle.

    El JSON viaja embebido en un <script>, no como respuesta pura, y el
    arreglo puede contener objetos anidados con sus propios corchetes -una
    regex simple no basta-, así que se cuenta profundidad de corchetes hasta
    cerrar el que abrió el arreglo.
    """
    inicio = texto.find(f'"{marcador}":')
    if inicio == -1:
        return None
    inicio_arreglo = texto.index("[", inicio)
    profundidad = 0
    for i in range(inicio_arreglo, len(texto)):
        if texto[i] == "[":
            profundidad += 1
        elif texto[i] == "]":
            profundidad -= 1
            if profundidad == 0:
                return json.loads(texto[inicio_arreglo : i + 1])
    return None


def _imparte_en_el_semestre_vigente(persona_id: int) -> bool:
    respuesta = requests.get(_url_detalle(persona_id), timeout=TIMEOUT_SEGUNDOS)
    respuesta.raise_for_status()
    grupos = _extraer_arreglo_balanceado(respuesta.text, "persona__grupos")
    if not grupos:
        return False
    semestre = semestre_vigente()
    return any(str(grupo.get("calendario__periodo")) == semestre for grupo in grupos)


def validar_academico_activo(numero_trabajador: str, nombre_completo: str) -> bool:
    """¿Este académico imparte clases en el semestre vigente?

    `numero_trabajador` se recibe para trazabilidad/logging futuro, pero el
    directorio no lo usa como llave de búsqueda -no tiene ese campo-, así que
    la validación real depende de `nombre_completo`. Ver el docstring del
    módulo para el criterio de matching y el porqué del fallback pesimista.
    """
    if not settings.DIRECTORIO_FC_URL_BASE:
        return False
    try:
        resultados = _buscar_por_nombre(nombre_completo)
        if len(resultados) != 1:
            return False
        persona = resultados[0]["persona"]
        if not _mismo_nombre(persona, nombre_completo):
            return False
        return _imparte_en_el_semestre_vigente(persona["persona__id"])
    except Exception:
        return False
