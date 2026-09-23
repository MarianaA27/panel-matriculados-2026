# Panel de Matriculados 2026

Tablero interactivo de Business Intelligence sobre la matricula academica del
periodo 2026: 29.014 estudiantes, 61 sedes, 72 programas y 4 facultades.
Construido en Python con Streamlit, Pandas y Plotly.

**Aplicacion en linea:** https://matriculados2026.streamlit.app

---

## Contenido del tablero

Once modulos analiticos mas conmutador de modo claro y oscuro:

| Modulo | Contenido |
|---|---|
| Inicio y dashboard | Indicadores clave, matricula por facultad y sexo, modalidad, programas mas demandados, estratos y concentracion por sede |
| Mapa interactivo de sedes | Cartografia con nodos proporcionales al volumen de matricula y panel de detalle por sede |
| Explorar sedes | Catalogo en tarjetas con buscador, orden y desglose de programas y estratos |
| Estadisticas interactivas | Ocho filtros cruzados y cuatro pestanas analiticas |
| Buscador inteligente | Busqueda simultanea en programas, sedes, colegios, territorios y facultades |
| Tabla de datos | Vista administrativa con paginacion, orden y filtro por texto libre |
| Comparador de sedes | Contraste de dos sedes con barras divergentes y radar de indicadores |
| Descubre los datos | Hallazgos generados automaticamente y curva de concentracion |
| Indicadores y alertas | Semaforo de gestion en tres niveles y mapa de riesgo de la oferta |
| Calidad de datos | Auditoria de completitud, duplicados y limpieza automatica |
| Exportar analisis | Descarga en CSV, Excel y reporte visual imprimible |

---

## Ejecucion local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # macOS o Linux
pip install -r requirements.txt
python app.py
```

El script levanta el servidor y abre el navegador en `http://localhost:8501`.
El archivo `matriculados_2026_limpio.csv` debe estar en la misma carpeta que
`app.py`. Si no lo encuentra, la aplicacion ofrece un cargador para subirlo.

---

## Despliegue en Streamlit Community Cloud

1. Sube esta carpeta a un repositorio de GitHub, sin incluir `.venv`.
2. Entra a `share.streamlit.io` e inicia sesion con GitHub.
3. Crea la aplicacion indicando el repositorio, la rama `main` y el archivo
   principal `app.py`.
4. Personaliza el subdominio y despliega.

El archivo `.streamlit/config.toml` de este repositorio ya esta preparado para
el servidor: no contiene la seccion `[server]`, que solo sirve en ejecucion local.

---

## Estructura del proyecto

```
.
├── app.py                         Aplicacion completa
├── requirements.txt               Dependencias
├── .gitignore                     Exclusiones de control de versiones
├── .streamlit/config.toml         Tema y configuracion de cliente
├── assets/sedes/                  Fotografias opcionales de las sedes
└── matriculados_2026_limpio.csv   Fuente de datos (agregala tu)
```

---

## Notas metodologicas

- **Georreferenciacion**: los campus principales tienen coordenadas reales.
  Las sedes de barrio y de region usan la coordenada de la institucion
  educativa o del municipio. El modulo de calidad de datos identifica cuales
  son aproximadas.
- **Mapa**: usa mosaicos publicos de Carto, sin token ni clave de servicio.
  Requiere conexion a internet unicamente para el fondo cartografico.
- **Completitud**: 26.608 registros estan completos en todos los campos clave.
  Los 2.406 restantes presentan al menos un vacio, principalmente en barrio,
  comuna y colegio de procedencia. El tablero los conserva y los reporta en
  lugar de eliminarlos silenciosamente.
- **Alcance**: el dataset corresponde a un unico periodo, por lo que el analisis
  es transversal y no permite lectura de tendencia entre anos.
