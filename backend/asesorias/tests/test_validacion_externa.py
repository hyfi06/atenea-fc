import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from asesorias.validacion_externa import validar_academico_activo

NOMBRE = "Claudia Solís Said"
URL_DE_PRUEBA = "https://directorio-de-prueba.example"

RESPUESTA_UN_RESULTADO = {
    "data": {
        "busca_directorio": [
            {
                "persona": {
                    "persona__nombre": "Claudia",
                    "persona__apellido_1": "Solís",
                    "persona__apellido_2": "Said",
                    "persona__id": 54601,
                }
            }
        ]
    }
}

RESPUESTA_SIN_RESULTADOS = {"data": {"busca_directorio": []}}

RESPUESTA_DOS_RESULTADOS = {
    "data": {"busca_directorio": [{"persona": {"persona__id": 1}}, {"persona": {"persona__id": 2}}]}
}


def _html_con_grupos(grupos):
    return f'<script>var x = {{"queryData":{{"data":{{"resumen_persona":{{"persona__grupos":{json.dumps(grupos)}}}}}}}}}</script>'


@override_settings(DIRECTORIO_FC_URL_BASE=URL_DE_PRUEBA)
class ValidarAcademicoActivoTests(SimpleTestCase):
    """Todos estos tests corren con `DIRECTORIO_FC_URL_BASE` configurado por
    `override_settings` -en el entorno real, sin esa variable, la Task
    `test_sin_url_configurada_no_concede_vigencia` (fuera de esta clase)
    cubre el guard que evita cualquier llamada de red."""

    @patch("asesorias.validacion_externa.requests.get")
    def test_sin_resultados_no_concede_vigencia(self, mock_get):
        mock_get.return_value = Mock(json=lambda: RESPUESTA_SIN_RESULTADOS, raise_for_status=lambda: None)
        self.assertFalse(validar_academico_activo("70001", NOMBRE))

    @patch("asesorias.validacion_externa.requests.get")
    def test_mas_de_un_resultado_no_concede_vigencia(self, mock_get):
        mock_get.return_value = Mock(json=lambda: RESPUESTA_DOS_RESULTADOS, raise_for_status=lambda: None)
        self.assertFalse(validar_academico_activo("70001", NOMBRE))

    @patch("asesorias.validacion_externa.requests.get")
    def test_un_resultado_pero_nombre_distinto_no_concede_vigencia(self, mock_get):
        mock_get.return_value = Mock(json=lambda: RESPUESTA_UN_RESULTADO, raise_for_status=lambda: None)
        self.assertFalse(validar_academico_activo("70001", "Otra Persona Distinta"))

    @patch("asesorias.validacion_externa.semestre_vigente", return_value="20271")
    @patch("asesorias.validacion_externa.requests.get")
    def test_un_resultado_nombre_coincide_e_imparte_en_el_semestre_vigente(self, mock_get, mock_semestre):
        html = _html_con_grupos([{"calendario__periodo": 20271}])
        mock_get.side_effect = [
            Mock(json=lambda: RESPUESTA_UN_RESULTADO, raise_for_status=lambda: None),
            Mock(text=html, raise_for_status=lambda: None),
        ]
        self.assertTrue(validar_academico_activo("70001", NOMBRE))

    @patch("asesorias.validacion_externa.semestre_vigente", return_value="20271")
    @patch("asesorias.validacion_externa.requests.get")
    def test_un_resultado_nombre_coincide_pero_no_imparte_en_el_semestre_vigente(self, mock_get, mock_semestre):
        html = _html_con_grupos([{"calendario__periodo": 20262}])
        mock_get.side_effect = [
            Mock(json=lambda: RESPUESTA_UN_RESULTADO, raise_for_status=lambda: None),
            Mock(text=html, raise_for_status=lambda: None),
        ]
        self.assertFalse(validar_academico_activo("70001", NOMBRE))

    @patch("asesorias.validacion_externa.requests.get", side_effect=Exception("timeout"))
    def test_un_fallo_de_red_no_concede_vigencia(self, mock_get):
        self.assertFalse(validar_academico_activo("70001", NOMBRE))

    def test_url_de_prueba_efectivamente_se_usa(self):
        """La URL que forma la petición viene de settings, no de una
        constante hardcodeada -si esto se rompiera, todos los tests de
        arriba seguirían pasando pero por la razón equivocada."""
        with patch("asesorias.validacion_externa.requests.get") as mock_get:
            mock_get.return_value = Mock(json=lambda: RESPUESTA_SIN_RESULTADOS, raise_for_status=lambda: None)
            validar_academico_activo("70001", NOMBRE)
            url_llamada = mock_get.call_args[0][0]
            self.assertTrue(url_llamada.startswith(URL_DE_PRUEBA))


@override_settings(DIRECTORIO_FC_URL_BASE="")
class SinUrlConfiguradaTests(SimpleTestCase):
    def test_sin_url_configurada_no_concede_vigencia_y_no_llama_a_la_red(self):
        """La URL no se versiona (nunca hay default en código ni en
        .env.example): si el operador no la configuró, la solicitud queda
        pendiente de revisión de la SAE en vez de fallar o bloquear -y ni
        siquiera se intenta una petición de red."""
        with patch("asesorias.validacion_externa.requests.get") as mock_get:
            self.assertFalse(validar_academico_activo("70001", NOMBRE))
            mock_get.assert_not_called()
