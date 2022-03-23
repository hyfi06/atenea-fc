# Atenea FC

## Run

## Development

```bash
export COMPOSE_FILE=local.yml
docker-compose build
docker-compose up

docker rm -f ID
docker-compose run --rm --service-ports django

docker-compose run --rm django COMMAND
```

## License

Copyright (C) 2021-2022 Héctor Olvera Vital

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.
