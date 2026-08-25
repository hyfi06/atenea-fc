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
