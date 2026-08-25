# Guía de usuario — Académico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar una guía de usuario pública, servida por la app en `/docs/`, con mockups de teléfono del flujo completo del académico (convertirse en asesor, materias, horario, asesorías), más el punto de entrada desde Home.

**Architecture:** Archivos HTML/CSS estáticos y autocontenidos bajo `frontend/public/docs/` — Vite copia `public/` sin procesar a `dist/`, y `frontend/nginx.conf` ya resuelve archivos reales antes del fallback de la SPA (`try_files $uri $uri/ /index.html;`), así que no hace falta build step ni cambio de infraestructura. Cada mockup de pantalla es un marco de iPhone en CSS puro con la paleta M3 oscura real de la app (`frontend/src/index.css`). `Home.tsx` gana un tile "Guía de uso" que navega con `<a href>` en vez de `useNavigate()`, porque `/docs/` es un árbol estático fuera del router de React.

**Tech Stack:** HTML/CSS puro (sin JS, sin build) para la guía; React + TypeScript + Vitest + Testing Library para el cambio en `Home.tsx`.

**Spec:** `docs/superpowers/specs/2026-08-25-guia-usuario-academico-design.md`

## Global Constraints

- Ningún archivo de la guía carga JS, CSS externo ni fuentes externas — todo inline, sin build step.
- Ningún archivo de la guía muestra rutas reales de la SPA (`/asesorias/...`, `/sae/...`, `/home`) en texto ni en `href` — los links entre páginas de la guía usan solo nombres de archivo de la propia guía (`academico/01-registro-asesor.html`, etc.). La única ruta real de la app permitida es `/` (landing), en el header.
- Paleta: tokens M3 oscuros exactos de `frontend/src/index.css` (ver bloque CSS completo en el Task 1). No se soporta tema claro — la app tampoco lo tiene.
- Tipografía: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
- Cada archivo `.html` de la guía es autocontenido: su propio `<style>` inline completo, sin depender de otro archivo ni de una hoja de estilos compartida. La duplicación entre archivos es intencional (ver spec, "Alternativas consideradas").
- Header de página (chrome propio de la guía, fuera de cualquier mockup de teléfono): logo de Atenea + texto "Atenea", envuelto en un único `<a href="/">`. Ningún ícono de menú aparte.
- Toda página de sección de académico lleva un link "← Volver" a `index.html` (su portada); `academico/index.html` lleva un link "← Volver" a `../index.html` (el portal).
- Ningún mockup de teléfono reproduce el header real de la app (Logo + MenuUsuario) — cada pantalla mockeada muestra solo su propio contenido, no la barra de navegación de Home.

## File Structure

```
frontend/public/docs/
  index.html                    # Task 2 — portal, hoy una sola tarjeta → academico/
  academico/
    index.html                  # Task 3 — portada de la guía de académico, 4 tarjetas
    01-registro-asesor.html     # Task 4 — convertirte en asesor (6 pasos)
    02-mis-materias.html        # Task 5 — tus materias (3 pasos)
    03-mi-horario.html          # Task 6 — tu horario (3 pasos + aviso)
    04-tus-asesorias.html       # Task 7 — atender asesorías (4 pasos)
docs/development/
  guia-de-usuario.md            # Task 1 — convenciones de mantenimiento
frontend/src/screens/
  Home.tsx                      # Task 8 — tile "Guía de uso"
  Home.test.tsx                 # Task 8 — tests del tile nuevo
```

Orden de tareas: Task 1 primero (define el kit de CSS que las Tasks 2–7 copian literal). Tasks 2–7 son independientes entre sí una vez hecho Task 1. Task 8 es independiente de todas — solo necesita que `/docs/` exista como concepto, no como archivo (el test no visita la URL real).

---

### Task 1: Documento de mantenimiento — kit de CSS y convenciones

**Files:**
- Create: `docs/development/guia-de-usuario.md`

**Interfaces:**
- Produces: el "kit de CSS" (bloque `<style>` completo) y el snippet del logo que las Tasks 2–7 copian literal dentro de cada archivo `.html`. Este task no depende de ningún otro.

- [ ] **Step 1: Escribir el documento**

Crea `docs/development/guia-de-usuario.md` con exactamente este contenido:

````markdown
# Mantener la guía de usuario

La guía de usuario de Atenea vive en `frontend/public/docs/` — Vite copia
`public/` sin procesar a `dist/`, y `frontend/nginx.conf` la sirve como
archivos estáticos reales antes del fallback de la SPA. Es pública (sin
login) y queda en `/docs/` (portal) y `/docs/<rol>/` (guía de cada rol).
Ver `docs/superpowers/specs/2026-08-25-guia-usuario-academico-design.md`
para el porqué de estas decisiones.

## Mapa de archivos

```
frontend/public/docs/
  index.html              # portal: una tarjeta por rol con guía
  academico/
    index.html            # portada de la guía de ese rol
    01-registro-asesor.html
    02-mis-materias.html
    03-mi-horario.html
    04-tus-asesorias.html
```

Convención de nombres de sección: `NN-nombre-seccion.html`, numeradas en el
orden en que un usuario las recorre.

## Regla de oro: nunca reveles rutas reales

La guía es pública. Ningún texto ni `href` debe mostrar una ruta real de la
SPA (`/asesorias/materias`, `/sae/asesorias`, `/home`, etc.). Las pantallas
se nombran solo por lo que el usuario ve en la UI ("Mis materias", "Mi
horario"). La única ruta real permitida en toda la guía es `/` (la landing,
en el header). Los links entre páginas de la guía usan únicamente rutas
relativas a otros archivos de la propia guía.

## Cada archivo es autocontenido

Ningún archivo de la guía importa CSS ni JS externo, ni depende de otro
archivo `.html`. Se duplica el kit de CSS completo (abajo) en cada archivo.
Es deuda aceptada a propósito: cualquiera que mantenga la guía —incluyendo
un subagente— abre un solo archivo y tiene todo lo que necesita para
entenderlo y editarlo, sin tener que rastrear una hoja de estilos
compartida.

## Kit de CSS (copiar/pegar dentro de `<style>` en cada archivo nuevo)

Paleta: tokens M3 oscuros exactos de `frontend/src/index.css` — si esa
paleta cambia, hay que actualizar el bloque `:root` de cada archivo de la
guía a mano, uno por uno.

```css
:root {
  --color-primary: #a6daf2;
  --color-on-primary: #0d4159;
  --color-primary-container: #136286;
  --color-on-primary-container: #d2edf9;
  --color-secondary: #bfd3d9;
  --color-on-secondary: #263a40;
  --color-secondary-container: #395760;
  --color-on-secondary-container: #dfe9ec;
  --color-tertiary: #e3b5c5;
  --color-on-tertiary: #4a1c2c;
  --color-tertiary-container: #6f2a43;
  --color-on-tertiary-container: #f1dae2;
  --color-error: #f0aea8;
  --color-on-error: #57150f;
  --color-error-container: #822017;
  --color-on-error-container: #f7d7d4;
  --color-background: #171a1c;
  --color-on-background: #e3e6e8;
  --color-surface-variant: #425157;
  --color-on-surface-variant: #c5cfd3;
  --color-outline: #8b9ea7;
  --color-outline-variant: #425157;
  --color-surface-container-low: #191d1f;
  --color-surface-container: #23292b;
  --color-surface-container-high: #2d3436;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: #0e1011;
  color: var(--color-on-background);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

a { color: inherit; }

.guia-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.guia-header .marca {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
}

.guia-header svg { width: 24px; height: 24px; }

.volver {
  display: inline-block;
  margin: 20px 24px 0;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

main.contenido {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 24px 64px;
}

h1.titulo-guia { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }

p.intro {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  max-width: 60ch;
  margin: 0 0 32px;
}

.tarjetas { display: grid; gap: 12px; }

.tarjeta {
  display: block;
  background: var(--color-surface-container);
  border-radius: 14px;
  padding: 16px 18px;
  text-decoration: none;
  color: var(--color-on-background);
}

.tarjeta h2 { font-size: 15px; margin: 0 0 4px; color: var(--color-primary); }
.tarjeta p { font-size: 13px; margin: 0; color: var(--color-on-surface-variant); }

.paso {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  padding: 32px 0;
  border-top: 1px solid var(--color-outline-variant);
  flex-wrap: wrap;
}

.paso:first-of-type { border-top: none; padding-top: 8px; }

.paso .nota { flex: 1 1 260px; min-width: 240px; }

.paso .numero {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 10px;
}

.paso h2 { font-size: 16px; margin: 0 0 8px; }
.paso p { font-size: 14px; line-height: 1.5; color: var(--color-on-surface-variant); margin: 0 0 8px; }

.telefono {
  flex: 0 0 auto;
  width: 300px;
  height: 649px;
  background: #05070a;
  border-radius: 42px;
  padding: 10px;
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.6);
}

.telefono .pantalla {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--color-background);
  border-radius: 32px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.telefono .isla {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 22px;
  background: #000;
  border-radius: 999px;
  z-index: 2;
}

.telefono .barra-estado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 22px 4px;
  font-size: 12px;
  font-weight: 600;
}

.telefono .app {
  flex: 1;
  padding: 10px 16px 16px;
  overflow: hidden;
  font-size: 13px;
}

.app h3 { font-size: 15px; font-weight: 600; margin: 4px 0 10px; }
.app .subtitulo { font-size: 11px; color: var(--color-on-surface-variant); margin: -6px 0 10px; }

.tiles-app { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }
.tile-app {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  border-radius: 14px;
  padding: 12px 6px;
  text-align: center;
  font-size: 10px;
  font-weight: 600;
}
.tile-app.terciario { background: var(--color-tertiary-container); color: var(--color-on-tertiary-container); }
.tile-app.secundario { background: var(--color-secondary-container); color: var(--color-on-secondary-container); }

.boton-app {
  display: inline-block;
  border-radius: 999px;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}
.boton-app.primario { background: var(--color-primary); color: var(--color-on-primary); }
.boton-app.secundario { background: transparent; border: 1px solid var(--color-outline); color: var(--color-primary); }
.boton-app.peligro { background: var(--color-error); color: var(--color-on-error); }
.boton-app.bloque { display: block; width: 100%; }

.banner-app {
  background: var(--color-secondary-container);
  color: var(--color-on-secondary-container);
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 11px;
}

.card-app { background: var(--color-surface-container); border-radius: 12px; padding: 10px; margin-bottom: 8px; }
.card-app.bajo { background: var(--color-surface-container-low); }

.fila-app {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-outline-variant);
  font-size: 12px;
}

.chip-app { border-radius: 999px; padding: 2px 8px; font-size: 10px; }
.chip-app.activo { background: var(--color-primary-container); color: var(--color-on-primary-container); }
.chip-app.inactivo { background: var(--color-surface-variant); color: var(--color-on-surface-variant); }

.tabs-app { display: flex; gap: 6px; margin: 8px 0 10px; }
.tab-app { font-size: 11px; padding: 5px 10px; border-radius: 999px; color: var(--color-on-surface-variant); }
.tab-app.activa { background: var(--color-primary-container); color: var(--color-on-primary-container); font-weight: 600; }

.campo-app label { display: block; font-size: 10px; color: var(--color-on-surface-variant); margin-bottom: 4px; }
.campo-app select, .campo-app textarea {
  width: 100%;
  background: transparent;
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  color: var(--color-on-background);
  font-size: 12px;
  padding: 6px 8px;
  font-family: inherit;
}

.overlay-app { position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: flex-end; }
.hoja-app { background: var(--color-surface-container-high); width: 100%; border-radius: 18px 18px 0 0; padding: 14px 16px 18px; font-size: 12px; }
.hoja-app h4 { margin: 0 0 10px; font-size: 13px; }
```

## Header de página (logo → landing)

Va al inicio del `<body>` de cada archivo, fuera de cualquier `.telefono`:

```html
<header class="guia-header">
  <a class="marca" href="/">
    <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Atenea">
      <circle cx="32" cy="32" r="27"></circle>
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32"></path>
      <path d="M20 32 L18 43 L24 46 L26 35"></path>
      <path d="M44 32 L46 43 L40 46 L38 35"></path>
      <path d="M32 22 L32 44"></path>
      <path d="M22 14 Q32 3 42 14"></path>
    </svg>
    <span>Atenea</span>
  </a>
</header>
```

Es el mismo trazo SVG que `frontend/src/components/Logo.tsx` — si ese
componente cambia, actualizar este snippet a mano en cada archivo de la
guía.

## Barra de estado de un mockup de teléfono

Va al inicio de cada `.pantalla`, antes del contenido (`.app`):

```html
<div class="isla"></div>
<div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
```

## Cómo agregar un paso/pantalla a una sección existente

Cada paso es un bloque `.paso` con dos hijos: la nota (a la izquierda o
arriba) y el teléfono (a la derecha o abajo, según el ancho disponible):

```html
<section class="paso">
  <div class="telefono">
    <div class="pantalla">
      <div class="isla"></div>
      <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
      <div class="app">
        <!-- contenido de la pantalla mockeada, con las clases *-app del kit -->
      </div>
    </div>
  </div>
  <div class="nota">
    <span class="numero">N</span>
    <h2>Título corto del paso</h2>
    <p>Qué ve el usuario y qué debe tocar.</p>
  </div>
</section>
```

## Cómo agregar una sección nueva o un rol nuevo

- Sección nueva dentro de un rol existente: crear
  `frontend/public/docs/<rol>/NN-nombre.html` con el header, el kit de CSS
  completo, un link "← Volver" a `index.html`, y sus pasos. Agregar su
  tarjeta a `frontend/public/docs/<rol>/index.html`.
- Rol nuevo: crear `frontend/public/docs/<rol>/index.html` (portada, mismo
  patrón que `academico/index.html`) y agregar su tarjeta a
  `frontend/public/docs/index.html` (el portal). El link desde `Home.tsx`
  sigue apuntando a `/docs/` sin cambios — el portal es el punto de entrada
  estable.
````

- [ ] **Step 2: Verificar que el archivo se creó**

Run: `test -f docs/development/guia-de-usuario.md && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add docs/development/guia-de-usuario.md
git commit -m "[docs] agregar convenciones de mantenimiento de la guía de usuario

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

### Task 2: Portal de la guía — `frontend/public/docs/index.html`

**Files:**
- Create: `frontend/public/docs/index.html`

**Interfaces:**
- Consumes: el kit de CSS y el snippet de header del Task 1 (copiados literal, no importados).
- Produces: el link `academico/index.html` que consume el Task 3.

- [ ] **Step 1: Crear el archivo**

Crea `frontend/public/docs/index.html` con exactamente este contenido:

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guía de uso — Atenea</title>
<style>
:root {
  --color-primary: #a6daf2;
  --color-on-primary: #0d4159;
  --color-primary-container: #136286;
  --color-on-primary-container: #d2edf9;
  --color-secondary: #bfd3d9;
  --color-on-secondary: #263a40;
  --color-secondary-container: #395760;
  --color-on-secondary-container: #dfe9ec;
  --color-tertiary: #e3b5c5;
  --color-on-tertiary: #4a1c2c;
  --color-tertiary-container: #6f2a43;
  --color-on-tertiary-container: #f1dae2;
  --color-error: #f0aea8;
  --color-on-error: #57150f;
  --color-error-container: #822017;
  --color-on-error-container: #f7d7d4;
  --color-background: #171a1c;
  --color-on-background: #e3e6e8;
  --color-surface-variant: #425157;
  --color-on-surface-variant: #c5cfd3;
  --color-outline: #8b9ea7;
  --color-outline-variant: #425157;
  --color-surface-container-low: #191d1f;
  --color-surface-container: #23292b;
  --color-surface-container-high: #2d3436;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0e1011;
  color: var(--color-on-background);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
a { color: inherit; }
.guia-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.guia-header .marca {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
}
.guia-header svg { width: 24px; height: 24px; }
main.contenido {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 24px 64px;
}
h1.titulo-guia { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
p.intro {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  max-width: 60ch;
  margin: 0 0 32px;
}
.tarjetas { display: grid; gap: 12px; }
.tarjeta {
  display: block;
  background: var(--color-surface-container);
  border-radius: 14px;
  padding: 16px 18px;
  text-decoration: none;
  color: var(--color-on-background);
}
.tarjeta h2 { font-size: 15px; margin: 0 0 4px; color: var(--color-primary); }
.tarjeta p { font-size: 13px; margin: 0; color: var(--color-on-surface-variant); }
</style>
</head>
<body>
<header class="guia-header">
  <a class="marca" href="/">
    <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Atenea">
      <circle cx="32" cy="32" r="27"></circle>
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32"></path>
      <path d="M20 32 L18 43 L24 46 L26 35"></path>
      <path d="M44 32 L46 43 L40 46 L38 35"></path>
      <path d="M32 22 L32 44"></path>
      <path d="M22 14 Q32 3 42 14"></path>
    </svg>
    <span>Atenea</span>
  </a>
</header>
<main class="contenido">
  <h1 class="titulo-guia">Guía de uso</h1>
  <p class="intro">Guías paso a paso para usar los servicios de la SAE en Atenea, con ejemplos de pantalla.</p>
  <div class="tarjetas">
    <a class="tarjeta" href="academico/index.html">
      <h2>Académico</h2>
      <p>Regístrate como asesor, gestiona tus materias, tu horario y tus asesorías.</p>
    </a>
  </div>
</main>
</body>
</html>
```

- [ ] **Step 2: Verificar en el navegador**

Run: `pnpm --prefix frontend dev &` (o si ya está corriendo, omite esto) y
abre `http://localhost:5173/docs/` — o, sin levantar el servidor:

Run: `python3 -m http.server 8123 --directory frontend/public &`
Abre `http://localhost:8123/docs/` con un navegador o:
Run: `curl -s http://localhost:8123/docs/ | grep -c 'Guía de uso'`
Expected: `1`

Luego detén el servidor: `kill %1` (o el job correspondiente).

- [ ] **Step 3: Verificar que no hay rutas reales de la SPA**

Run: `grep -E "/asesorias|/sae|/home" frontend/public/docs/index.html || echo "sin rutas reales"`
Expected: `sin rutas reales`

- [ ] **Step 4: Commit**

```bash
git add frontend/public/docs/index.html
git commit -m "[frontend] agregar portal de la guía de usuario

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

### Task 3: Portada de la guía de académico — `frontend/public/docs/academico/index.html`

**Files:**
- Create: `frontend/public/docs/academico/index.html`

**Interfaces:**
- Consumes: nada de otro task (el link `../index.html` no depende de que el Task 2 ya exista para poder escribir este archivo, solo para que el link funcione en el navegador).
- Produces: los links `01-registro-asesor.html`, `02-mis-materias.html`, `03-mi-horario.html`, `04-tus-asesorias.html` que consumen los Tasks 4–7.

- [ ] **Step 1: Crear el archivo**

Crea `frontend/public/docs/academico/index.html` con exactamente este contenido:

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guía de académico — Atenea</title>
<style>
:root {
  --color-primary: #a6daf2;
  --color-on-primary: #0d4159;
  --color-primary-container: #136286;
  --color-on-primary-container: #d2edf9;
  --color-secondary: #bfd3d9;
  --color-on-secondary: #263a40;
  --color-secondary-container: #395760;
  --color-on-secondary-container: #dfe9ec;
  --color-tertiary: #e3b5c5;
  --color-on-tertiary: #4a1c2c;
  --color-tertiary-container: #6f2a43;
  --color-on-tertiary-container: #f1dae2;
  --color-error: #f0aea8;
  --color-on-error: #57150f;
  --color-error-container: #822017;
  --color-on-error-container: #f7d7d4;
  --color-background: #171a1c;
  --color-on-background: #e3e6e8;
  --color-surface-variant: #425157;
  --color-on-surface-variant: #c5cfd3;
  --color-outline: #8b9ea7;
  --color-outline-variant: #425157;
  --color-surface-container-low: #191d1f;
  --color-surface-container: #23292b;
  --color-surface-container-high: #2d3436;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0e1011;
  color: var(--color-on-background);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
a { color: inherit; }
.guia-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.guia-header .marca {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
}
.guia-header svg { width: 24px; height: 24px; }
.volver {
  display: inline-block;
  margin: 20px 24px 0;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
main.contenido {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 24px 64px;
}
h1.titulo-guia { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
p.intro {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  max-width: 60ch;
  margin: 0 0 32px;
}
.tarjetas { display: grid; gap: 12px; }
.tarjeta {
  display: block;
  background: var(--color-surface-container);
  border-radius: 14px;
  padding: 16px 18px;
  text-decoration: none;
  color: var(--color-on-background);
}
.tarjeta h2 { font-size: 15px; margin: 0 0 4px; color: var(--color-primary); }
.tarjeta p { font-size: 13px; margin: 0; color: var(--color-on-surface-variant); }
</style>
</head>
<body>
<header class="guia-header">
  <a class="marca" href="/">
    <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Atenea">
      <circle cx="32" cy="32" r="27"></circle>
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32"></path>
      <path d="M20 32 L18 43 L24 46 L26 35"></path>
      <path d="M44 32 L46 43 L40 46 L38 35"></path>
      <path d="M32 22 L32 44"></path>
      <path d="M22 14 Q32 3 42 14"></path>
    </svg>
    <span>Atenea</span>
  </a>
</header>
<a class="volver" href="../index.html">← Volver</a>
<main class="contenido">
  <h1 class="titulo-guia">Guía de académico</h1>
  <p class="intro">Cómo ofrecer asesorías en Atenea: de convertirte en asesor a atender tus sesiones.</p>
  <div class="tarjetas">
    <a class="tarjeta" href="01-registro-asesor.html">
      <h2>1. Convertirte en asesor</h2>
      <p>Solicita tu perfil de asesor y registra tu semestre.</p>
    </a>
    <a class="tarjeta" href="02-mis-materias.html">
      <h2>2. Tus materias</h2>
      <p>Agrega o quita las materias que impartes este semestre.</p>
    </a>
    <a class="tarjeta" href="03-mi-horario.html">
      <h2>3. Tu horario</h2>
      <p>Define cuándo y cómo —virtual o presencial— das asesorías.</p>
    </a>
    <a class="tarjeta" href="04-tus-asesorias.html">
      <h2>4. Atender asesorías</h2>
      <p>Revisa tus próximas sesiones, marca asistencia y agrega notas.</p>
    </a>
  </div>
</main>
</body>
</html>
```

- [ ] **Step 2: Verificar el contenido**

Run: `grep -c '<a class="tarjeta"' frontend/public/docs/academico/index.html`
Expected: `4`

- [ ] **Step 3: Verificar que no hay rutas reales de la SPA**

Run: `grep -E "/asesorias|/sae|/home" frontend/public/docs/academico/index.html || echo "sin rutas reales"`
Expected: `sin rutas reales`

- [ ] **Step 4: Commit**

```bash
git add frontend/public/docs/academico/index.html
git commit -m "[frontend] agregar portada de la guía de académico

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

### Task 4: Sección 1 — Convertirte en asesor — `frontend/public/docs/academico/01-registro-asesor.html`

**Files:**
- Create: `frontend/public/docs/academico/01-registro-asesor.html`

**Interfaces:**
- Consumes: nada (autocontenido). El link "← Volver" apunta a `index.html`, que produce el Task 3.

Pantallas reales que ilustra este archivo (para referencia del ejecutor,
no aparecen como texto en la guía): `frontend/src/screens/Home.tsx`,
`frontend/src/features/asesorias/screens/Asesorias.tsx`,
`frontend/src/features/asesorias/screens/SolicitudAsesor.tsx`,
`frontend/src/features/asesorias/components/AsesorPendiente.tsx`,
`frontend/src/features/asesorias/components/SinRegistroAsesor.tsx`.

- [ ] **Step 1: Crear el archivo**

Crea `frontend/public/docs/academico/01-registro-asesor.html` con exactamente este contenido:

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Convertirte en asesor — Guía de académico — Atenea</title>
<style>
:root {
  --color-primary: #a6daf2;
  --color-on-primary: #0d4159;
  --color-primary-container: #136286;
  --color-on-primary-container: #d2edf9;
  --color-secondary: #bfd3d9;
  --color-on-secondary: #263a40;
  --color-secondary-container: #395760;
  --color-on-secondary-container: #dfe9ec;
  --color-tertiary: #e3b5c5;
  --color-on-tertiary: #4a1c2c;
  --color-tertiary-container: #6f2a43;
  --color-on-tertiary-container: #f1dae2;
  --color-error: #f0aea8;
  --color-on-error: #57150f;
  --color-error-container: #822017;
  --color-on-error-container: #f7d7d4;
  --color-background: #171a1c;
  --color-on-background: #e3e6e8;
  --color-surface-variant: #425157;
  --color-on-surface-variant: #c5cfd3;
  --color-outline: #8b9ea7;
  --color-outline-variant: #425157;
  --color-surface-container-low: #191d1f;
  --color-surface-container: #23292b;
  --color-surface-container-high: #2d3436;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0e1011;
  color: var(--color-on-background);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
a { color: inherit; }
.guia-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.guia-header .marca {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
}
.guia-header svg { width: 24px; height: 24px; }
.volver {
  display: inline-block;
  margin: 20px 24px 0;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
main.contenido {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 24px 64px;
}
h1.titulo-guia { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
p.intro {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  max-width: 60ch;
  margin: 0 0 32px;
}
.paso {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  padding: 32px 0;
  border-top: 1px solid var(--color-outline-variant);
  flex-wrap: wrap;
}
.paso:first-of-type { border-top: none; padding-top: 8px; }
.paso .nota { flex: 1 1 260px; min-width: 240px; }
.paso .numero {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 10px;
}
.paso h2 { font-size: 16px; margin: 0 0 8px; }
.paso p { font-size: 14px; line-height: 1.5; color: var(--color-on-surface-variant); margin: 0 0 8px; }
.telefono {
  flex: 0 0 auto;
  width: 300px;
  height: 649px;
  background: #05070a;
  border-radius: 42px;
  padding: 10px;
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.6);
}
.telefono .pantalla {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--color-background);
  border-radius: 32px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.telefono .isla {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 22px;
  background: #000;
  border-radius: 999px;
  z-index: 2;
}
.telefono .barra-estado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 22px 4px;
  font-size: 12px;
  font-weight: 600;
}
.telefono .app {
  flex: 1;
  padding: 10px 16px 16px;
  overflow: hidden;
  font-size: 13px;
}
.app h3 { font-size: 15px; font-weight: 600; margin: 4px 0 10px; }
.app .subtitulo { font-size: 11px; color: var(--color-on-surface-variant); margin: -6px 0 10px; }
.tiles-app { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }
.tile-app {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  border-radius: 14px;
  padding: 12px 6px;
  text-align: center;
  font-size: 10px;
  font-weight: 600;
}
.boton-app {
  display: inline-block;
  border-radius: 999px;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  border: none;
  font-family: inherit;
}
.boton-app.primario { background: var(--color-primary); color: var(--color-on-primary); }
.boton-app.bloque { display: block; width: 100%; }
.banner-app {
  background: var(--color-secondary-container);
  color: var(--color-on-secondary-container);
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 11px;
}
.tabs-app { display: flex; gap: 6px; margin: 8px 0 10px; }
.tab-app { font-size: 11px; padding: 5px 10px; border-radius: 999px; color: var(--color-on-surface-variant); }
.tab-app.activa { background: var(--color-primary-container); color: var(--color-on-primary-container); font-weight: 600; }
.campo-app label { display: block; font-size: 10px; color: var(--color-on-surface-variant); margin-bottom: 4px; }
.campo-app select {
  width: 100%;
  background: transparent;
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  color: var(--color-on-background);
  font-size: 12px;
  padding: 6px 8px;
  font-family: inherit;
}
</style>
</head>
<body>
<header class="guia-header">
  <a class="marca" href="/">
    <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Atenea">
      <circle cx="32" cy="32" r="27"></circle>
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32"></path>
      <path d="M20 32 L18 43 L24 46 L26 35"></path>
      <path d="M44 32 L46 43 L40 46 L38 35"></path>
      <path d="M32 22 L32 44"></path>
      <path d="M22 14 Q32 3 42 14"></path>
    </svg>
    <span>Atenea</span>
  </a>
</header>
<a class="volver" href="index.html">← Volver</a>
<main class="contenido">
  <h1 class="titulo-guia">1. Convertirte en asesor</h1>
  <p class="intro">Antes de dar asesorías necesitas un perfil de asesor aprobado por la SAE y un registro para el semestre en curso. Estos son los pasos.</p>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Atenea</h3>
          <p class="subtitulo">Hola</p>
          <div class="tiles-app">
            <div class="tile-app">Asesorías</div>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">1</span>
      <h2>Entra a Asesorías</h2>
      <p>Desde el inicio, toca el tile <strong>Asesorías</strong>.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Asesorías</h3>
          <div class="tabs-app">
            <span class="tab-app activa">Próximas</span>
            <span class="tab-app">Historial</span>
          </div>
          <button class="boton-app primario bloque" style="margin-bottom:10px;">Registrarme como asesor</button>
          <p style="font-size:11px;color:var(--color-on-surface-variant);">No tienes asesorías próximas.</p>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">2</span>
      <h2>Regístrate como asesor</h2>
      <p>Como todavía no tienes perfil de asesor, verás este botón en la parte superior. Tócalo.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Registrarme como asesor</h3>
          <p style="font-size:11px;color:var(--color-on-surface-variant);margin-bottom:10px;">Elige el área en la que darás asesorías. La SAE confirmará que tu nombramiento esté vigente antes de publicar tu disponibilidad.</p>
          <div class="campo-app" style="margin-bottom:14px;">
            <label>Área</label>
            <select><option>Elige un área</option></select>
          </div>
          <button class="boton-app primario">Solicitar</button>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">3</span>
      <h2>Elige tu área</h2>
      <p>Selecciona el área en la que darás asesorías y confirma.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Solicitud enviada</h3>
          <p style="font-size:12px;color:var(--color-on-surface-variant);margin-bottom:14px;">Tu perfil de asesor quedó pendiente de que la SAE confirme que tu nombramiento está vigente. En cuanto quede aprobado podrás cargar tus materias y tu horario.</p>
          <button class="boton-app primario">Ir a Asesorías</button>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">4</span>
      <h2>Solicitud enviada</h2>
      <p>Ya no hay nada más que hacer de tu parte — solo esperar a que la SAE revise tu nombramiento.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Asesorías</h3>
          <div class="banner-app">Tu perfil de asesor está pendiente de revisión de la SAE.</div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">5</span>
      <h2>Espera la revisión de la SAE</h2>
      <p>Mientras la SAE confirma tu nombramiento verás este aviso. Todavía no puedes cargar materias ni horario.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Mis materias</h3>
          <p style="font-size:12px;color:var(--color-on-surface-variant);margin-bottom:14px;">Aún no tienes un registro de asesor para este semestre.</p>
          <button class="boton-app primario">Registrar semestre 2026-2</button>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">6</span>
      <h2>Registra tu semestre</h2>
      <p>Una vez aprobado tu perfil, registra el semestre para empezar a cargar materias y horario. Este botón solo aparece mientras la SAE tenga abierta la ventana de registro del semestre.</p>
    </div>
  </section>
</main>
</body>
</html>
```

- [ ] **Step 2: Verificar que hay 6 pasos**

Run: `grep -c '<section class="paso">' frontend/public/docs/academico/01-registro-asesor.html`
Expected: `6`

- [ ] **Step 3: Verificar que no hay rutas reales de la SPA**

Run: `grep -E "/asesorias|/sae|/home" frontend/public/docs/academico/01-registro-asesor.html || echo "sin rutas reales"`
Expected: `sin rutas reales`

- [ ] **Step 4: Commit**

```bash
git add frontend/public/docs/academico/01-registro-asesor.html
git commit -m "[frontend] agregar sección 1 de la guía de académico: convertirte en asesor

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

### Task 5: Sección 2 — Tus materias — `frontend/public/docs/academico/02-mis-materias.html`

**Files:**
- Create: `frontend/public/docs/academico/02-mis-materias.html`

**Interfaces:**
- Consumes: nada (autocontenido). El link "← Volver" apunta a `index.html`, que produce el Task 3.

Pantalla real que ilustra este archivo (para referencia del ejecutor, no
aparece como texto en la guía):
`frontend/src/features/asesorias/screens/MisMaterias.tsx`,
`frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx`,
`frontend/src/features/asesorias/components/DialogoQuitarMateria.tsx`.

- [ ] **Step 1: Crear el archivo**

Crea `frontend/public/docs/academico/02-mis-materias.html` con exactamente este contenido:

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tus materias — Guía de académico — Atenea</title>
<style>
:root {
  --color-primary: #a6daf2;
  --color-on-primary: #0d4159;
  --color-primary-container: #136286;
  --color-on-primary-container: #d2edf9;
  --color-secondary: #bfd3d9;
  --color-on-secondary: #263a40;
  --color-secondary-container: #395760;
  --color-on-secondary-container: #dfe9ec;
  --color-tertiary: #e3b5c5;
  --color-on-tertiary: #4a1c2c;
  --color-tertiary-container: #6f2a43;
  --color-on-tertiary-container: #f1dae2;
  --color-error: #f0aea8;
  --color-on-error: #57150f;
  --color-error-container: #822017;
  --color-on-error-container: #f7d7d4;
  --color-background: #171a1c;
  --color-on-background: #e3e6e8;
  --color-surface-variant: #425157;
  --color-on-surface-variant: #c5cfd3;
  --color-outline: #8b9ea7;
  --color-outline-variant: #425157;
  --color-surface-container-low: #191d1f;
  --color-surface-container: #23292b;
  --color-surface-container-high: #2d3436;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0e1011;
  color: var(--color-on-background);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
a { color: inherit; }
.guia-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.guia-header .marca {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
}
.guia-header svg { width: 24px; height: 24px; }
.volver {
  display: inline-block;
  margin: 20px 24px 0;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
main.contenido {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 24px 64px;
}
h1.titulo-guia { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
p.intro {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  max-width: 60ch;
  margin: 0 0 32px;
}
.paso {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  padding: 32px 0;
  border-top: 1px solid var(--color-outline-variant);
  flex-wrap: wrap;
}
.paso:first-of-type { border-top: none; padding-top: 8px; }
.paso .nota { flex: 1 1 260px; min-width: 240px; }
.paso .numero {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 10px;
}
.paso h2 { font-size: 16px; margin: 0 0 8px; }
.paso p { font-size: 14px; line-height: 1.5; color: var(--color-on-surface-variant); margin: 0 0 8px; }
.telefono {
  flex: 0 0 auto;
  width: 300px;
  height: 649px;
  background: #05070a;
  border-radius: 42px;
  padding: 10px;
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.6);
}
.telefono .pantalla {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--color-background);
  border-radius: 32px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.telefono .isla {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 22px;
  background: #000;
  border-radius: 999px;
  z-index: 2;
}
.telefono .barra-estado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 22px 4px;
  font-size: 12px;
  font-weight: 600;
}
.telefono .app {
  flex: 1;
  padding: 10px 16px 16px;
  overflow: hidden;
  font-size: 13px;
}
.app h3 { font-size: 15px; font-weight: 600; margin: 4px 0 10px; }
.app .subtitulo { font-size: 11px; color: var(--color-on-surface-variant); margin: -6px 0 10px; }
.boton-app {
  display: inline-block;
  border-radius: 999px;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  border: none;
  font-family: inherit;
}
.boton-app.primario { background: var(--color-primary); color: var(--color-on-primary); }
.boton-app.secundario { background: transparent; border: 1px solid var(--color-outline); color: var(--color-primary); }
.boton-app.peligro { background: var(--color-error); color: var(--color-on-error); }
.boton-app.bloque { display: block; width: 100%; }
.fila-app {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-outline-variant);
  font-size: 12px;
}
.campo-app label { display: block; font-size: 10px; color: var(--color-on-surface-variant); margin-bottom: 4px; }
.campo-app select {
  width: 100%;
  background: transparent;
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  color: var(--color-on-background);
  font-size: 12px;
  padding: 6px 8px;
  font-family: inherit;
}
.overlay-app { position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: flex-end; }
.hoja-app { background: var(--color-surface-container-high); width: 100%; border-radius: 18px 18px 0 0; padding: 14px 16px 18px; font-size: 12px; }
.hoja-app h4 { margin: 0 0 10px; font-size: 13px; }
</style>
</head>
<body>
<header class="guia-header">
  <a class="marca" href="/">
    <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Atenea">
      <circle cx="32" cy="32" r="27"></circle>
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32"></path>
      <path d="M20 32 L18 43 L24 46 L26 35"></path>
      <path d="M44 32 L46 43 L40 46 L38 35"></path>
      <path d="M32 22 L32 44"></path>
      <path d="M22 14 Q32 3 42 14"></path>
    </svg>
    <span>Atenea</span>
  </a>
</header>
<a class="volver" href="index.html">← Volver</a>
<main class="contenido">
  <h1 class="titulo-guia">2. Tus materias</h1>
  <p class="intro">Las materias que registres aquí son las que verán los alumnos al agendar una asesoría contigo.</p>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Mis materias</h3>
          <p class="subtitulo">Semestre 2026-2</p>
          <button class="boton-app secundario" style="margin-bottom:10px;">+ Agregar</button>
          <div class="fila-app"><span>Cálculo III</span><span>🗑</span></div>
          <div class="fila-app"><span>Álgebra Lineal</span><span>🗑</span></div>
          <div class="fila-app"><span>Probabilidad I</span><span>🗑</span></div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">1</span>
      <h2>Revisa tus materias</h2>
      <p>La lista muestra las materias que ya impartes este semestre. Toca <strong>+ Agregar</strong> para sumar una más.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Mis materias</h3>
          <p class="subtitulo">Semestre 2026-2</p>
          <div class="fila-app"><span>Cálculo III</span><span>🗑</span></div>
          <div class="overlay-app">
            <div class="hoja-app">
              <h4>Agregar materia</h4>
              <div class="campo-app" style="margin-bottom:12px;">
                <label>Materia</label>
                <select><option>Elige una materia</option></select>
              </div>
              <button class="boton-app primario bloque">Agregar</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">2</span>
      <h2>Agrega una materia</h2>
      <p>Elige la materia de la lista y confirma. Aparecerá de inmediato en tu lista.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Mis materias</h3>
          <p class="subtitulo">Semestre 2026-2</p>
          <div class="fila-app"><span>Cálculo III</span><span>🗑</span></div>
          <div class="overlay-app">
            <div class="hoja-app">
              <h4>¿Quitar Cálculo III?</h4>
              <p style="color:var(--color-on-surface-variant);margin:0 0 12px;">Ya no aparecerá como una materia que impartes este semestre.</p>
              <div style="display:flex;gap:8px;">
                <button class="boton-app secundario" style="flex:1;">Cancelar</button>
                <button class="boton-app peligro" style="flex:1;">Quitar</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">3</span>
      <h2>Quita una materia</h2>
      <p>Toca el ícono de basura junto a una materia y confirma para quitarla del semestre.</p>
    </div>
  </section>
</main>
</body>
</html>
```

- [ ] **Step 2: Verificar que hay 3 pasos**

Run: `grep -c '<section class="paso">' frontend/public/docs/academico/02-mis-materias.html`
Expected: `3`

- [ ] **Step 3: Verificar que no hay rutas reales de la SPA**

Run: `grep -E "/asesorias|/sae|/home" frontend/public/docs/academico/02-mis-materias.html || echo "sin rutas reales"`
Expected: `sin rutas reales`

- [ ] **Step 4: Commit**

```bash
git add frontend/public/docs/academico/02-mis-materias.html
git commit -m "[frontend] agregar sección 2 de la guía de académico: tus materias

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

### Task 6: Sección 3 — Tu horario — `frontend/public/docs/academico/03-mi-horario.html`

**Files:**
- Create: `frontend/public/docs/academico/03-mi-horario.html`

**Interfaces:**
- Consumes: nada (autocontenido). El link "← Volver" apunta a `index.html`, que produce el Task 3.

Pantalla real que ilustra este archivo (para referencia del ejecutor, no
aparece como texto en la guía):
`frontend/src/features/asesorias/screens/MiHorario.tsx`,
`frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx`,
`frontend/src/features/asesorias/components/DialogoBloqueActivo.tsx`,
`frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.tsx`.

- [ ] **Step 1: Crear el archivo**

Crea `frontend/public/docs/academico/03-mi-horario.html` con exactamente este contenido:

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tu horario — Guía de académico — Atenea</title>
<style>
:root {
  --color-primary: #a6daf2;
  --color-on-primary: #0d4159;
  --color-primary-container: #136286;
  --color-on-primary-container: #d2edf9;
  --color-secondary: #bfd3d9;
  --color-on-secondary: #263a40;
  --color-secondary-container: #395760;
  --color-on-secondary-container: #dfe9ec;
  --color-tertiary: #e3b5c5;
  --color-on-tertiary: #4a1c2c;
  --color-tertiary-container: #6f2a43;
  --color-on-tertiary-container: #f1dae2;
  --color-error: #f0aea8;
  --color-on-error: #57150f;
  --color-error-container: #822017;
  --color-on-error-container: #f7d7d4;
  --color-background: #171a1c;
  --color-on-background: #e3e6e8;
  --color-surface-variant: #425157;
  --color-on-surface-variant: #c5cfd3;
  --color-outline: #8b9ea7;
  --color-outline-variant: #425157;
  --color-surface-container-low: #191d1f;
  --color-surface-container: #23292b;
  --color-surface-container-high: #2d3436;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0e1011;
  color: var(--color-on-background);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
a { color: inherit; }
.guia-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.guia-header .marca {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
}
.guia-header svg { width: 24px; height: 24px; }
.volver {
  display: inline-block;
  margin: 20px 24px 0;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
main.contenido {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 24px 64px;
}
h1.titulo-guia { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
p.intro {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  max-width: 60ch;
  margin: 0 0 32px;
}
.paso {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  padding: 32px 0;
  border-top: 1px solid var(--color-outline-variant);
  flex-wrap: wrap;
}
.paso:first-of-type { border-top: none; padding-top: 8px; }
.paso .nota { flex: 1 1 260px; min-width: 240px; }
.paso .numero {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 10px;
}
.paso h2 { font-size: 16px; margin: 0 0 8px; }
.paso p { font-size: 14px; line-height: 1.5; color: var(--color-on-surface-variant); margin: 0 0 8px; }
.telefono {
  flex: 0 0 auto;
  width: 300px;
  height: 649px;
  background: #05070a;
  border-radius: 42px;
  padding: 10px;
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.6);
}
.telefono .pantalla {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--color-background);
  border-radius: 32px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.telefono .isla {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 22px;
  background: #000;
  border-radius: 999px;
  z-index: 2;
}
.telefono .barra-estado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 22px 4px;
  font-size: 12px;
  font-weight: 600;
}
.telefono .app {
  flex: 1;
  padding: 10px 16px 16px;
  overflow: hidden;
  font-size: 13px;
}
.app h3 { font-size: 15px; font-weight: 600; margin: 4px 0 10px; }
.app .subtitulo { font-size: 11px; color: var(--color-on-surface-variant); margin: -6px 0 10px; }
.boton-app {
  display: inline-block;
  border-radius: 999px;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  border: none;
  font-family: inherit;
}
.boton-app.secundario { background: transparent; border: 1px solid var(--color-outline); color: var(--color-primary); }
.boton-app.peligro { background: var(--color-error); color: var(--color-on-error); }
.boton-app.bloque { display: block; width: 100%; }
.fila-app {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-outline-variant);
  font-size: 12px;
}
.chip-app { border-radius: 999px; padding: 2px 8px; font-size: 10px; }
.chip-app.activo { background: var(--color-primary-container); color: var(--color-on-primary-container); }
.chip-app.inactivo { background: var(--color-surface-variant); color: var(--color-on-surface-variant); }
.tabs-app { display: flex; gap: 6px; margin: 8px 0 10px; }
.tab-app { font-size: 11px; padding: 5px 10px; border-radius: 999px; color: var(--color-on-surface-variant); }
.tab-app.activa { background: var(--color-primary-container); color: var(--color-on-primary-container); font-weight: 600; }
.campo-app label { display: block; font-size: 10px; color: var(--color-on-surface-variant); margin-bottom: 4px; }
.campo-app select, .campo-app input {
  width: 100%;
  background: transparent;
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  color: var(--color-on-background);
  font-size: 12px;
  padding: 6px 8px;
  font-family: inherit;
}
.overlay-app { position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: flex-end; }
.hoja-app { background: var(--color-surface-container-high); width: 100%; border-radius: 18px 18px 0 0; padding: 14px 16px 18px; font-size: 12px; }
.hoja-app h4 { margin: 0 0 10px; font-size: 13px; }
</style>
</head>
<body>
<header class="guia-header">
  <a class="marca" href="/">
    <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Atenea">
      <circle cx="32" cy="32" r="27"></circle>
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32"></path>
      <path d="M20 32 L18 43 L24 46 L26 35"></path>
      <path d="M44 32 L46 43 L40 46 L38 35"></path>
      <path d="M32 22 L32 44"></path>
      <path d="M22 14 Q32 3 42 14"></path>
    </svg>
    <span>Atenea</span>
  </a>
</header>
<a class="volver" href="index.html">← Volver</a>
<main class="contenido">
  <h1 class="titulo-guia">3. Tu horario</h1>
  <p class="intro">Aquí defines en qué días y horas puedes atender asesorías, y si son virtuales o presenciales. Los alumnos solo pueden agendar en los bloques que actives.</p>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Mi horario</h3>
          <p class="subtitulo">Toca una celda para activarla o editarla.</p>
          <div class="tabs-app">
            <span class="tab-app activa">Lun</span>
            <span class="tab-app">Mar</span>
            <span class="tab-app">Mié</span>
            <span class="tab-app">Jue</span>
            <span class="tab-app">Vie</span>
            <span class="tab-app">Sáb</span>
          </div>
          <div class="fila-app"><span>10:00 · Virtual</span><span class="chip-app activo">Activo</span></div>
          <div class="fila-app"><span>11:00</span><span class="chip-app inactivo">Inactivo</span></div>
          <div class="fila-app"><span>12:00 · Presencial</span><span class="chip-app activo">Activo</span></div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">1</span>
      <h2>Revisa tu semana</h2>
      <p>Cambia de día con las pestañas de arriba. Cada fila es una hora: verde/activo significa que un alumno puede agendar ahí.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Mi horario</h3>
          <div class="fila-app"><span>11:00</span><span class="chip-app inactivo">Inactivo</span></div>
          <div class="overlay-app">
            <div class="hoja-app">
              <h4>Nuevo horario — Lunes 11:00</h4>
              <div class="campo-app" style="margin-bottom:10px;">
                <label>Formato</label>
                <select><option>Virtual</option><option>Presencial</option></select>
              </div>
              <div class="campo-app" style="margin-bottom:12px;">
                <label>Liga de la sesión</label>
                <input type="text" placeholder="https://…">
              </div>
              <button class="boton-app secundario bloque" style="background:var(--color-primary);color:var(--color-on-primary);border:none;">Guardar</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">2</span>
      <h2>Crea un bloque nuevo</h2>
      <p>Toca una celda vacía. Elige si es virtual (con liga) o presencial (con ubicación) y guarda.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Mi horario</h3>
          <div class="fila-app"><span>10:00 · Virtual</span><span class="chip-app activo">Activo</span></div>
          <div class="overlay-app">
            <div class="hoja-app">
              <h4>Lunes 10:00 · Virtual</h4>
              <p style="color:var(--color-on-surface-variant);margin:0 0 12px;">Este bloque está activo. Puedes desactivarlo o eliminarlo.</p>
              <div style="display:flex;flex-direction:column;gap:8px;">
                <button class="boton-app secundario bloque">Desactivar</button>
                <button class="boton-app peligro bloque">Eliminar</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">3</span>
      <h2>Edita o quita un bloque activo</h2>
      <p>Toca una celda activa para desactivarla (deja de recibir citas nuevas) o eliminarla por completo.</p>
    </div>
  </section>

  <section class="paso">
    <div class="nota" style="flex:1 1 100%;">
      <span class="numero">4</span>
      <h2>Si el bloque ya tiene sesiones agendadas</h2>
      <p>La app te preguntará si quieres desactivarlo solo para citas nuevas, o si además quieres cancelar las sesiones que ya tenían alumnos agendados en ese horario. Cancelar sí avisa al alumno — elige con cuidado.</p>
    </div>
  </section>
</main>
</body>
</html>
```

- [ ] **Step 2: Verificar que hay 4 pasos**

Run: `grep -c '<section class="paso">' frontend/public/docs/academico/03-mi-horario.html`
Expected: `4`

- [ ] **Step 3: Verificar que no hay rutas reales de la SPA**

Run: `grep -E "/asesorias|/sae|/home" frontend/public/docs/academico/03-mi-horario.html || echo "sin rutas reales"`
Expected: `sin rutas reales`

- [ ] **Step 4: Commit**

```bash
git add frontend/public/docs/academico/03-mi-horario.html
git commit -m "[frontend] agregar sección 3 de la guía de académico: tu horario

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

### Task 7: Sección 4 — Atender asesorías — `frontend/public/docs/academico/04-tus-asesorias.html`

**Files:**
- Create: `frontend/public/docs/academico/04-tus-asesorias.html`

**Interfaces:**
- Consumes: nada (autocontenido). El link "← Volver" apunta a `index.html`, que produce el Task 3.

Pantalla real que ilustra este archivo (para referencia del ejecutor, no
aparece como texto en la guía):
`frontend/src/features/asesorias/screens/Asesorias.tsx`,
`frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`,
`frontend/src/features/asesorias/components/DialogoCancelar.tsx`.

- [ ] **Step 1: Crear el archivo**

Crea `frontend/public/docs/academico/04-tus-asesorias.html` con exactamente este contenido:

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atender asesorías — Guía de académico — Atenea</title>
<style>
:root {
  --color-primary: #a6daf2;
  --color-on-primary: #0d4159;
  --color-primary-container: #136286;
  --color-on-primary-container: #d2edf9;
  --color-secondary: #bfd3d9;
  --color-on-secondary: #263a40;
  --color-secondary-container: #395760;
  --color-on-secondary-container: #dfe9ec;
  --color-tertiary: #e3b5c5;
  --color-on-tertiary: #4a1c2c;
  --color-tertiary-container: #6f2a43;
  --color-on-tertiary-container: #f1dae2;
  --color-error: #f0aea8;
  --color-on-error: #57150f;
  --color-error-container: #822017;
  --color-on-error-container: #f7d7d4;
  --color-background: #171a1c;
  --color-on-background: #e3e6e8;
  --color-surface-variant: #425157;
  --color-on-surface-variant: #c5cfd3;
  --color-outline: #8b9ea7;
  --color-outline-variant: #425157;
  --color-surface-container-low: #191d1f;
  --color-surface-container: #23292b;
  --color-surface-container-high: #2d3436;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0e1011;
  color: var(--color-on-background);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
a { color: inherit; }
.guia-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.guia-header .marca {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
}
.guia-header svg { width: 24px; height: 24px; }
.volver {
  display: inline-block;
  margin: 20px 24px 0;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
main.contenido {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 24px 64px;
}
h1.titulo-guia { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
p.intro {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  max-width: 60ch;
  margin: 0 0 32px;
}
.paso {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  padding: 32px 0;
  border-top: 1px solid var(--color-outline-variant);
  flex-wrap: wrap;
}
.paso:first-of-type { border-top: none; padding-top: 8px; }
.paso .nota { flex: 1 1 260px; min-width: 240px; }
.paso .numero {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 10px;
}
.paso h2 { font-size: 16px; margin: 0 0 8px; }
.paso p { font-size: 14px; line-height: 1.5; color: var(--color-on-surface-variant); margin: 0 0 8px; }
.telefono {
  flex: 0 0 auto;
  width: 300px;
  height: 649px;
  background: #05070a;
  border-radius: 42px;
  padding: 10px;
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.6);
}
.telefono .pantalla {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--color-background);
  border-radius: 32px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.telefono .isla {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 22px;
  background: #000;
  border-radius: 999px;
  z-index: 2;
}
.telefono .barra-estado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 22px 4px;
  font-size: 12px;
  font-weight: 600;
}
.telefono .app {
  flex: 1;
  padding: 10px 16px 16px;
  overflow: hidden;
  font-size: 13px;
}
.app h3 { font-size: 15px; font-weight: 600; margin: 4px 0 10px; }
.boton-app {
  display: inline-block;
  border-radius: 999px;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  border: none;
  font-family: inherit;
}
.boton-app.primario { background: var(--color-primary); color: var(--color-on-primary); }
.boton-app.secundario { background: transparent; border: 1px solid var(--color-outline); color: var(--color-primary); }
.boton-app.peligro { background: var(--color-error); color: var(--color-on-error); }
.boton-app.bloque { display: block; width: 100%; }
.card-app { background: var(--color-surface-container); border-radius: 12px; padding: 10px; margin-bottom: 8px; }
.card-app.bajo { background: var(--color-surface-container-low); }
.fila-app {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-outline-variant);
  font-size: 12px;
}
.chip-app { border-radius: 999px; padding: 2px 8px; font-size: 10px; }
.chip-app.activo { background: var(--color-primary-container); color: var(--color-on-primary-container); }
.tabs-app { display: flex; gap: 6px; margin: 8px 0 10px; }
.tab-app { font-size: 11px; padding: 5px 10px; border-radius: 999px; color: var(--color-on-surface-variant); }
.tab-app.activa { background: var(--color-primary-container); color: var(--color-on-primary-container); font-weight: 600; }
.campo-app label { display: block; font-size: 10px; color: var(--color-on-surface-variant); margin-bottom: 4px; }
.campo-app textarea {
  width: 100%;
  background: transparent;
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  color: var(--color-on-background);
  font-size: 12px;
  padding: 6px 8px;
  font-family: inherit;
  resize: none;
}
.overlay-app { position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: flex-end; }
.hoja-app { background: var(--color-surface-container-high); width: 100%; border-radius: 18px 18px 0 0; padding: 14px 16px 18px; font-size: 12px; }
.hoja-app h4 { margin: 0 0 10px; font-size: 13px; }
</style>
</head>
<body>
<header class="guia-header">
  <a class="marca" href="/">
    <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Atenea">
      <circle cx="32" cy="32" r="27"></circle>
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32"></path>
      <path d="M20 32 L18 43 L24 46 L26 35"></path>
      <path d="M44 32 L46 43 L40 46 L38 35"></path>
      <path d="M32 22 L32 44"></path>
      <path d="M22 14 Q32 3 42 14"></path>
    </svg>
    <span>Atenea</span>
  </a>
</header>
<a class="volver" href="index.html">← Volver</a>
<main class="contenido">
  <h1 class="titulo-guia">4. Atender asesorías</h1>
  <p class="intro">Cuando un alumno agenda contigo, la sesión aparece en tu lista de asesorías. Aquí ves cómo revisarla, marcar asistencia, dejar notas y cancelar si hace falta.</p>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Asesorías</h3>
          <div class="tabs-app">
            <span class="tab-app activa">Próximas</span>
            <span class="tab-app">Historial</span>
          </div>
          <div class="card-app">
            <div style="display:flex;justify-content:space-between;"><strong>Cálculo III</strong><span class="chip-app activo">Agendada</span></div>
            <p style="margin:6px 0 0;color:var(--color-on-surface-variant);">Ana Torres · Lunes 10:00</p>
          </div>
          <div class="card-app">
            <div style="display:flex;justify-content:space-between;"><strong>Álgebra Lineal</strong><span class="chip-app activo">Agendada</span></div>
            <p style="margin:6px 0 0;color:var(--color-on-surface-variant);">Luis Peña · Miércoles 12:00</p>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">1</span>
      <h2>Revisa tus asesorías</h2>
      <p>"Próximas" muestra lo que sigue; "Historial" muestra sesiones pasadas por semestre. Toca una tarjeta para ver el detalle.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Cálculo III</h3>
          <div class="card-app bajo">
            <div class="fila-app" style="border:none;padding:2px 0;"><span>Alumno</span><span>Ana Torres</span></div>
            <div class="fila-app" style="border:none;padding:2px 0;"><span>Carrera</span><span>Actuaría</span></div>
            <div class="fila-app" style="border:none;padding:2px 0;"><span>Fecha</span><span>Lunes 15 sep</span></div>
            <div class="fila-app" style="border:none;padding:2px 0;"><span>Hora</span><span>10:00</span></div>
            <div class="fila-app" style="border:none;padding:2px 0;"><span>Formato</span><span>Virtual</span></div>
          </div>
          <p style="margin:10px 0 6px;">¿El alumno asistió a esta sesión?</p>
          <div style="display:flex;gap:8px;">
            <button class="boton-app primario" style="flex:1;">Asistió</button>
            <button class="boton-app secundario" style="flex:1;">No asistió</button>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">2</span>
      <h2>Marca la asistencia</h2>
      <p>Pasada la hora de la sesión, marca si el alumno asistió o no. Esto habilita el historial y, si asistió, la nota de sesión.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Cálculo III</h3>
          <p style="color:var(--color-on-surface-variant);">Asistió a la sesión.</p>
          <div class="campo-app" style="margin:10px 0;">
            <label>Nota de la sesión</label>
            <textarea rows="3" placeholder="Notas de la sesión…"></textarea>
          </div>
          <button class="boton-app primario">Guardar notas</button>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">3</span>
      <h2>Deja una nota</h2>
      <p>Anota lo que viste en la sesión — te sirve como recordatorio la próxima vez que atiendas al mismo alumno.</p>
    </div>
  </section>

  <section class="paso">
    <div class="telefono">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="barra-estado"><span>9:41</span><span>●●● 📶 🔋</span></div>
        <div class="app">
          <h3>Cálculo III</h3>
          <button class="boton-app peligro">Cancelar asesoría</button>
          <div class="overlay-app">
            <div class="hoja-app">
              <h4>Cancelar asesoría</h4>
              <div class="campo-app" style="margin-bottom:12px;">
                <label>Motivo</label>
                <textarea rows="2" placeholder="Cuéntale al alumno por qué…"></textarea>
              </div>
              <div style="display:flex;gap:8px;">
                <button class="boton-app secundario" style="flex:1;">Cerrar</button>
                <button class="boton-app peligro" style="flex:1;">Confirmar</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="nota">
      <span class="numero">4</span>
      <h2>Cancela si hace falta</h2>
      <p>Explica el motivo — el alumno lo verá. Cancelar libera el bloque para que otro alumno pueda agendar.</p>
    </div>
  </section>
</main>
</body>
</html>
```

- [ ] **Step 2: Verificar que hay 4 pasos**

Run: `grep -c '<section class="paso">' frontend/public/docs/academico/04-tus-asesorias.html`
Expected: `4`

- [ ] **Step 3: Verificar que no hay rutas reales de la SPA**

Run: `grep -E "/asesorias|/sae|/home" frontend/public/docs/academico/04-tus-asesorias.html || echo "sin rutas reales"`
Expected: `sin rutas reales`

- [ ] **Step 4: Commit**

```bash
git add frontend/public/docs/academico/04-tus-asesorias.html
git commit -m "[frontend] agregar sección 4 de la guía de académico: atender asesorías

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

### Task 8: Tarjeta "Guía de uso" en Home

**Files:**
- Modify: `frontend/src/screens/Home.tsx` (reemplazo completo, ver Step 3)
- Modify: `frontend/src/screens/Home.test.tsx:73-77` (test de leyenda vacía)

**Interfaces:**
- Consumes: nada de los tasks anteriores — este task no depende de que
  `frontend/public/docs/` exista físicamente, porque el test no navega a esa
  URL real, solo comprueba el atributo `href` del link.
- Produces: nada que otro task consuma.

Este task cambia el comportamiento de un caso ya cubierto por un test
existente: hoy, si ningún rol aplica, `Home` muestra el texto "Aún no
contamos con servicios para ti." y ningún tile. Como el tile "Guía de uso"
va a estar siempre visible, ese mensaje deja de poder aparecer nunca — hay
que quitar la rama de código que lo pinta (queda muerta) y reemplazar el
test que la cubre.

- [ ] **Step 1: Actualizar el test que cubre el caso "sin roles"**

En `frontend/src/screens/Home.test.tsx`, reemplaza este bloque (líneas
73–77 tal como está hoy):

```tsx
  it('muestra una leyenda cuando ningún servicio aplica', () => {
    montar()
    expect(screen.getByText('Aún no contamos con servicios para ti.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Asesorías' })).not.toBeInTheDocument()
  })
```

por esto:

```tsx
  it('sin roles, solo se ve la Guía de uso', () => {
    montar()
    expect(screen.getByRole('link', { name: 'Guía de uso' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Asesorías' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Asesorías · SAE' })).not.toBeInTheDocument()
  })

  it('la Guía de uso es un link a /docs/, visible para cualquier rol', () => {
    montar({ alumno: true })
    const link = screen.getByRole('link', { name: 'Guía de uso' })
    expect(link).toHaveAttribute('href', '/docs/')
  })
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `pnpm --prefix frontend vitest run src/screens/Home.test.tsx`
Expected: FAIL — los dos tests nuevos no encuentran ningún link con nombre
accesible "Guía de uso" (el tile todavía no existe en `Home.tsx`).

- [ ] **Step 3: Reemplazar `frontend/src/screens/Home.tsx`**

Reemplaza el archivo completo por exactamente este contenido:

```tsx
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { MenuUsuario } from '../components/MenuUsuario'
import { IconTutorias } from '../components/icons/ServiceIcons'
import { useEsAcademico, useEsAlumno, useEsMiembroSAE } from '../auth/rol'

interface Tile {
  id: string
  etiqueta: string
  ruta: string
  visible: boolean
  /** Navegación de página completa (fuera del router de la SPA) en vez de
   *  `navigate()`. La usa "Guía de uso": vive en `frontend/public/docs/`,
   *  un árbol estático fuera de React Router — `navigate()` la mandaría a
   *  `NoEncontrado`. */
  externo?: boolean
  containerClassName: string
}

/**
 * Los tiles son los servicios que existen de verdad y que este usuario puede
 * usar, no un catálogo aspiracional (ADR 0027 decisión 9). Se arman en el
 * cliente a partir de `roles`: todavía no hay un endpoint de catálogo de
 * servicios de la SAE (deuda 0019).
 *
 * Excepción: "Guía de uso" no es un servicio ni depende de rol — es
 * documentación pública (`frontend/public/docs/`), por eso su tile siempre
 * está visible y navega con un `<a>` normal en vez de `useNavigate()`.
 */
export function Home() {
  const navigate = useNavigate()
  const esAlumno = useEsAlumno()
  const esAcademico = useEsAcademico()
  const esMiembroSAE = useEsMiembroSAE()

  const tiles: Tile[] = [
    {
      id: 'asesorias',
      etiqueta: 'Asesorías',
      ruta: '/asesorias',
      visible: esAlumno || esAcademico,
      containerClassName: 'bg-primary-container text-on-primary-container',
    },
    {
      id: 'sae-asesorias',
      etiqueta: 'Asesorías · SAE',
      ruta: '/sae/asesorias',
      visible: esMiembroSAE,
      containerClassName: 'bg-secondary-container text-on-secondary-container',
    },
    {
      id: 'guia',
      etiqueta: 'Guía de uso',
      ruta: '/docs/',
      visible: true,
      externo: true,
      containerClassName: 'bg-tertiary-container text-on-tertiary-container',
    },
  ].filter((tile) => tile.visible)

  return (
    <main className="min-h-svh px-4 pb-8">
      <header className="flex items-center gap-2 py-4">
        <Logo className="h-7 w-7 text-primary" />
        <span className="text-base font-semibold">Atenea</span>
        <span className="flex-1" />
        <MenuUsuario />
      </header>

      <p className="pb-4 text-sm text-on-surface-variant">Hola</p>

      <div className="grid grid-cols-3 gap-3">
        {tiles.map((tile, indice) =>
          tile.externo ? (
            <a
              key={tile.id}
              href={tile.ruta}
              style={{ animationDelay: `${indice * 30}ms` }}
              className={`entrada-lista presionable foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl p-3 text-center ${tile.containerClassName}`}
            >
              <IconTutorias className="h-6 w-6" />
              <span className="text-xs font-semibold leading-tight">{tile.etiqueta}</span>
            </a>
          ) : (
            <button
              key={tile.id}
              type="button"
              onClick={() => navigate(tile.ruta)}
              style={{ animationDelay: `${indice * 30}ms` }}
              className={`entrada-lista presionable foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl p-3 text-center ${tile.containerClassName}`}
            >
              <IconTutorias className="h-6 w-6" />
              <span className="text-xs font-semibold leading-tight">{tile.etiqueta}</span>
            </button>
          ),
        )}
      </div>
    </main>
  )
}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `pnpm --prefix frontend vitest run src/screens/Home.test.tsx`
Expected: PASS — los 7 tests del archivo (5 preexistentes + 2 nuevos) en verde.

- [ ] **Step 5: Lint y typecheck**

Run: `pnpm --prefix frontend lint && pnpm --prefix frontend build`
Expected: ambos sin errores (el `build` corre `tsc` antes de Vite, así que
también valida el tipo `Tile` y el `.filter`).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/screens/Home.tsx frontend/src/screens/Home.test.tsx
git commit -m "[feat][frontend] agregar tarjeta Guía de uso en Home

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Self-Review

**Cobertura del spec:**
- Ubicación servida en `frontend/public/docs/`, sin build/JS → Tasks 2–7.
- Portal (`/docs/`) como punto de entrada estable → Task 2.
- Portada de académico con 4 secciones → Task 3.
- Las 4 secciones del flujo mapeado en el spec → Tasks 4–7 (registro/pendiente/semestre, materias, horario con aviso de sesiones, asesorías con asistencia/notas/cancelar).
- Sistema visual (paleta M3 oscura, marco de iPhone, tipografía de sistema) → kit de CSS en Task 1, reutilizado literal en Tasks 2–7.
- Sin URLs reales en la guía → verificación explícita (`grep`) en cada task de HTML.
- Header logo→landing, sin ícono de hamburguesa aparte → snippet fijo en Task 1, presente en Tasks 2–7.
- Documento de mantenimiento en `docs/development/` → Task 1.
- Tarjeta en Home, visible para todos, `<a>` externo, color terciario → Task 8.
- Ningún requisito del spec quedó sin task.

**Placeholders:** ninguno — todo código HTML/CSS/TSX está completo y literal en cada task, sin “similar a Task N” ni TODOs.

**Consistencia de tipos/nombres:** el campo `externo?: boolean` de `Tile` (Task 8) es el único nombre nuevo introducido en código de aplicación; se usa igual en la definición del tile y en la condición de render. Los nombres de archivo (`01-registro-asesor.html`, etc.) son consistentes entre el árbol de `File Structure`, los links de Task 3, y el `href` de cada `<a class="volver">`.

---

## Execution Handoff

Plan completo, guardado en `docs/superpowers/plans/2026-08-25-guia-usuario-academico.md`.
