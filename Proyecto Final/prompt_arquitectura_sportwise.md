# Prompt: Diagrama de arquitectura del sistema Sportwise

## 1. Rol

Actuás como un **arquitecto de software senior y diseñador de infografías técnicas**, especializado en diagramas de arquitectura para documentación académica y profesional (estilo C4 / AWS / Azure). Tu prioridad es la **fidelidad técnica, la claridad visual y la legibilidad**.

## 2. Objetivo

Generá **una única imagen** con el **esquema completo de la arquitectura del sistema Sportwise**, basado exclusivamente en la descripción de este documento. Se insertará en la sección "Diseño – Arquitectura" de un informe de Proyecto Final de Ingeniería en Sistemas de Información (UTN FRRO), por lo que debe verse profesional, ordenada y fácil de leer al imprimirse.

## 3. Contexto del sistema

**Sportwise** es una plataforma **SaaS** para el ámbito deportivo que integra información **deportiva, nutricional y médica**. Sus usuarios son clubes, administradores, directores técnicos, preparadores físicos, nutricionistas, jugadores y deportistas (modelo de suscripción con planes Deportista, Profesional y Élite). Sus módulos principales: usuarios, torneos y fixture, instituciones, equipos, jugadores, deportistas, partidos, estadísticas y BI, nutrición, preparación física y administración.

La arquitectura es **cliente-servidor en capas**:

- Tres aplicaciones cliente (web, móvil, escritorio) se comunican con un **backend central** mediante una **API REST** (HTTP/HTTPS, JSON). La API es el único punto de entrada al sistema.
- El backend concentra la lógica de negocio, las reglas de seguridad y el acceso a datos, y es el **único intermediario** hacia la base de datos y hacia todos los servicios externos (IA, APIs de terceros, BI, pagos, correo, notificaciones push).
- **Ningún cliente accede directamente** a la base de datos ni a los servicios externos, para centralizar los controles de seguridad y no exponer credenciales.
- El sistema distingue procesamiento **transaccional (OLTP)** de **analítico (OLAP / BI)**, para que las consultas analíticas pesadas no degraden el rendimiento de la aplicación.

## 4. Componentes que deben aparecer

### 4.1 Capa de Presentación
| Componente | Tecnología | Detalle a mostrar |
|---|---|---|
| Aplicación Web | **React + Next.js** | Paneles de gestión, análisis y dashboards BI |
| Aplicación Móvil | **React Native** | Enfoque **offline-first**. Incluye dentro del bloque un sub-componente **"SQLite (almacenamiento local)"** |
| Aplicación de Escritorio | *(tecnología no definida: NO inventar una)* | Solo cliente de presentación |

### 4.2 Capa de Servicios
- **API REST** (HTTP/HTTPS · JSON), versionada.
- Responsabilidades (etiquetas pequeñas): recibir solicitudes · validar peticiones · autenticación y autorización (roles y permisos, MFA) · derivar a la lógica de negocio · punto de integración con servicios externos.

### 4.3 Backend principal (un contenedor que agrupa las capas internas)
- Rótulo: **"Backend · Node.js + TypeScript · Serverless"** (con ícono de nube; infraestructura administrada, sin servidores propios).
- Capas internas, en este orden vertical: **Servicios (API REST) → Negocio → Persistencia**.
  - **Negocio:** reglas y procesos propios de Sportwise, independientes de la interfaz y del almacenamiento.
  - **Persistencia:** abstrae consultar / insertar / modificar / eliminar sobre PostgreSQL.
- Dentro del backend, un pequeño módulo **"Generación de reportes PDF/JPG (renderizado en servidor)"**.

### 4.4 Capa de datos
- **PostgreSQL**: base de datos relacional central (soporta JSONB). Ícono de cilindro. Solo accede a ella la capa de Persistencia del backend.
- **Repositorio analítico / réplica de lectura**: dibujalo con **borde punteado** y la leyenda *"Evolución futura, según volumen"*. Recibe datos consolidados desde PostgreSQL y alimenta a BI.

### 4.5 Servicios externos al núcleo (agrupados bajo el rótulo "Componentes externos")
1. **Servicios de Inteligencia Artificial** — Python + FastAPI, **independientes** del backend, desplegados en infraestructura con **CPU, RAM y GPU**. Funciones (sub-etiquetas breves): *reconocimiento de alimentos por foto y estimación de porciones* · *análisis táctico y predicción de resultados*.
2. **Servicios de Business Intelligence (BI)** — tableros y visualizaciones (herramienta no definida: no nombrar ninguna).
3. **APIs externas de terceros** — datos deportivos u otros, consumidas solo desde el backend.
4. **Pasarela de pagos** — comunicación en dos vías: invocación síncrona para procesar la suscripción y **webhooks asíncronos** de vuelta al backend (confirmaciones, renovaciones, rechazos). No se almacenan datos de tarjetas: solo tokens.
5. **Servicio de correo transaccional** — recuperación de contraseña y avisos.
6. **Notificaciones push** — **FCM (Android)** y **APNs (iOS)**, entregadas a la app móvil.

### 4.5 bis Elementos transversales de seguridad (franja fina, no un componente más)
Una franja o conjunto de íconos discretos con: **HTTPS/TLS en todas las comunicaciones · Autenticación y autorización por roles (MFA) · Cifrado en tránsito y en reposo · Registro de eventos y trazabilidad · Backups cifrados (estrategia 3-2-1-1-0)**.

## 5. Flujos y conexiones (flechas)

Dibujá flechas **dirigidas y etiquetadas**:

| # | Origen → Destino | Etiqueta | Estilo |
|---|---|---|---|
| 1 | Web / Móvil / Escritorio ↔ API REST | `HTTPS · JSON` | Sólida, bidireccional |
| 2 | API REST → Negocio → Persistencia (dentro del backend) | — | Sólida, descendente |
| 3 | Persistencia ↔ PostgreSQL | `Consultas / escritura (OLTP)` | Sólida |
| 4 | Móvil (SQLite) ↔ API REST | `Sincronización diferida · endpoints idempotentes · control de versiones` | Línea de trazo corto, bidireccional |
| 5 | Backend ↔ Servicios de IA | `Comunicación entre servicios` | Sólida, con retorno de resultados |
| 6 | Backend ↔ Pasarela de pagos | `Invocación síncrona + webhooks` | Sólida (ida) + discontinua (webhooks de vuelta) |
| 7 | Backend → APIs externas | `Consumo de APIs de terceros` | Sólida |
| 8 | Backend → Correo transaccional | `Emails` | Sólida |
| 9 | Backend → Push (FCM / APNs) → App móvil | `Notificaciones push` | Sólida, termina en la app móvil |
| 10 | PostgreSQL → Repositorio analítico/réplica → BI | `Consultas controladas (OLAP)` | **Punteada** (parte futura) |
| 11 | Backend → BI | `Datos para análisis y visualización` | Sólida |

**Prohibido dibujar** flechas directas desde cualquier cliente hacia PostgreSQL, IA, APIs externas, BI, pasarela de pagos o correo. Incluí una nota pequeña: *"Los clientes nunca acceden directamente a la base de datos ni a servicios externos"*.

## 6. Organización visual (layout)

Composición **horizontal 16:9**, de izquierda a derecha, en bandas claramente delimitadas. Arriba, como guía, la cadena de capas:

`Presentación → Servicios → Negocio → Persistencia → Base de datos`

```
┌ Presentación ┐   ┌ Servicios ┐   ┌ Backend (Node.js/TS · Serverless) ┐   ┌ Datos ┐
│ Web (Next.js)│   │           │   │  Negocio → Persistencia            │   │ PostgreSQL │
│ Móvil + SQLite│→ │ API REST  │ → │  Reportes PDF/JPG                  │ → │ Réplica/OLAP (punteado) │
│ Escritorio   │   │           │   └──────────────┬─────────────────────┘   └────────────┘
└──────────────┘   └───────────┘                  │
                                                  ▼
              ┌ Componentes externos ──────────────────────────────────────┐
              │ IA (FastAPI · CPU/RAM/GPU) · BI · APIs externas · Pagos ·   │
              │ Correo · Push (FCM/APNs)                                     │
              └─────────────────────────────────────────────────────────────┘
        [ Franja inferior: HTTPS/TLS · Roles + MFA · Cifrado · Logs · Backups ]
```

- El **backend** y la **API REST** deben ocupar el centro y destacar visualmente.
- Los componentes externos van agrupados en una banda inferior o lateral, claramente separados del núcleo.
- Evitá cruces de flechas innecesarios; usá codos rectos (ortogonales).

## 7. Estilo visual

- Diagrama técnico **moderno, limpio, minimalista**; fondo **blanco o gris muy claro**.
- Bloques con **esquinas redondeadas**, bordes finos, sombra sutil.
- Un color por capa (tonos suaves):
  - Presentación: azul
  - Servicios / API REST: violeta
  - Backend (Negocio): verde
  - Persistencia y datos (PostgreSQL, réplica): naranja
  - Componentes externos: gris azulado / turquesa
  - Seguridad transversal: gris oscuro
- Íconos planos y simples (monitor, teléfono, escritorio, nube, cilindro de BD, cerebro/engranaje para IA, gráfico de barras para BI, tarjeta para pagos, sobre para correo, campana para push, candado para seguridad).
- Tipografía **sans-serif** legible; nombres en negrita y tecnologías en texto menor.
- **Título superior:** "Arquitectura del sistema Sportwise".
- **Leyenda** con: significado de colores, flecha sólida (comunicación síncrona), discontinua (asíncrona / webhooks / sincronización), punteada con borde (componente de evolución futura).

## 8. Requisitos de calidad

- **Fidelidad:** usá solo los componentes y tecnologías de este documento. **No inventes** caché, colas de mensajes, balanceadores, API Gateway, Docker, Kubernetes, Redis, nombres de proveedores (ni de pasarela, ni de BI, ni de correo) ni la tecnología de escritorio.
- **No dibujes** el modelo de datos (DER/tablas) ni flujos funcionales (casos de uso, QR): este diagrama es solo de arquitectura.
- Todo el texto en **español** (los nombres de tecnologías se mantienen: React, Next.js, React Native, Node.js, TypeScript, PostgreSQL, SQLite, Python, FastAPI, REST, FCM, APNs).
- Texto **sin errores ortográficos**, sin superposición de elementos.
- Resolución alta (mínimo 1920×1080 px; ideal 3840×2160), apta para impresión.

## 9. Prioridad si hay que simplificar

Si el modelo no puede incluir todo con texto legible, mantené **siempre** (prioridad alta): clientes, API REST, backend con capas, PostgreSQL, IA, BI, APIs externas, sincronización offline y la regla "los clientes no acceden directo". Simplificá o resumí en este orden: franja de seguridad → correo/push → pasarela de pagos → réplica analítica → sub-etiquetas. **Menos texto y más claridad** es preferible a texto ilegible.

## 10. Formato de salida

Entregá **solo la imagen**, sin texto explicativo adicional.

## 11. Verificación final (checklist interno)

- [ ] Web (React + Next.js), Móvil (React Native + SQLite) y Escritorio presentes.
- [ ] API REST como único punto de entrada.
- [ ] Backend rotulado Node.js + TypeScript + Serverless, con capas Negocio y Persistencia.
- [ ] PostgreSQL conectado solo con el backend; réplica/repositorio analítico punteado.
- [ ] IA (Python + FastAPI, CPU/RAM/GPU), BI, APIs externas, pasarela (síncrono + webhooks), correo y push (FCM/APNs) conectados solo al backend.
- [ ] Flecha de sincronización diferida de la app móvil.
- [ ] Ningún cliente conectado directo a BD ni a servicios externos.
- [ ] Título, leyenda y cadena de capas presentes; texto en español y legible.
