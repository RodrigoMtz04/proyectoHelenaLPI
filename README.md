Proyecto 3 – Asistente Virtual por Voz (Helena)

Descripción

Este proyecto implementa un asistente virtual por voz en Python llamado "Helena". Escucha comandos por micrófono (o por texto en modo --text), ejecuta acciones (abrir páginas, buscar en Wikipedia, reproducir en YouTube, obtener precio de acciones, enviar WhatsApp, guardar recordatorios y notas, obtener clima) y responde con voz sintetizada usando pyttsx3.

Requisitos e instalación

1. Python 3.8+ (probado con 3.13)
2. En Windows puede ser necesario instalar ruedas para PyAudio si falla la instalación automática.

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Si `PyAudio` falla en Windows, instala la rueda adecuada desde https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio y luego ejecuta:

```bash
pip install path\to\PyAudio‑<versión>.whl
```

Uso

Ejecutar en modo normal (usa micrófono):

```bash
python main.py
```

Ejecutar en modo texto (ideal para desarrollo o si no hay micrófono):

```bash
python main.py --text
```

Ejecutar modo prueba (no requiere micrófono, ejecuta varias funciones de verificación):

```bash
python main.py --test
```

Comandos implementados (voz o texto)

- "abrir youtube" — abre YouTube
- "abrir navegador" — abre Google
- "qué día es hoy" — dice el día actual
- "qué hora es" — dice la hora actual
- "busca en wikipedia <tema>" — resumen en español desde Wikipedia
- "busca en internet <término>" — búsqueda en Google (abre navegador)
- "reproducir <término>" — reproduce en YouTube
- "broma" — cuenta un chiste
- "precio de las acciones de <empresa>" — consulta precios (Apple/Amazon/Google/Microsoft)
- "guardar recordatorio <texto>" — guarda un recordatorio persistente
- "listar recordatorios" — muestra recordatorios guardados
- "modo notas" — entra en modo notas de voz/texto (escribe o habla; decir "salir notas" para salir)
- "enviar whatsapp" — interacción para enviar mensaje por WhatsApp Web
- "clima [ciudad]" — obtiene el clima simple usando wttr.in
- "adiós" — cierra el asistente

Mejoras añadidas

- Manejo robusto de errores para reconocimiento de voz y llamadas de red
- Persistencia de recordatorios y notas en archivos en la carpeta del proyecto
- Modo texto y modo prueba para facilitar desarrollo sin micrófono

Archivos

- `main.py` — código del asistente
- `requirements.txt` — dependencias
- `recordatorios.json` — creado al agregar recordatorios
- `notas.txt` — creado al guardar notas

Limitaciones y recomendaciones

- El reconocimiento de voz usa el servicio de Google (requiere Internet)
- En Windows, pyttsx3 usa voces SAPI; si la voz sugerida no existe se usa la por defecto
- Para enviar WhatsApp se abre WhatsApp Web y requiere que el usuario esté logueado

Próximos pasos (opcional)

- Añadir traducción completa usando googletrans o una API
- Integrar un pequeño diálogo conversacional con un modelo local


