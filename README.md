# Atenea System - SAE Facultad de Ciencias UNAM

System of SAE Facultad de Ciencias UNAM

## Desarrollo

Guía de entorno local en [`docs/development/getting-started.md`](docs/development/getting-started.md).

## Despliegue

Producción se despliega en el ecosistema externo `services/`; las imágenes se publican en
GHCR al hacer merge a `main`. Pasos operativos en
[`docs/development/despliegue-produccion.md`](docs/development/despliegue-produccion.md)
y la decisión de fondo en [ADR 0025](docs/decisions/0025-despliegue-produccion-ghcr.md).
El `docker-compose.prod.yml` de este repo es solo referencia de dev aislado.

## License

Atenea System of SAE Facultad de Ciencias UNAM

Copyright (C) 2021 Héctor Olvera Vital

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.
