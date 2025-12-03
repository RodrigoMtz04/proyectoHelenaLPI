import sys
import os
import json
import datetime
import webbrowser
import requests

import pyttsx3
import speech_recognition as sr
import pywhatkit
import yfinance as yf
import pyjokes
import wikipedia

# Vozes sugeridas (tokens de Windows). Si no existen, pyttsx3 usará la voz por defecto.
ID_ES_MX = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ES-MX_SABINA_11.0'
ID_ES_ES = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ES-ES_HELENA_11.0'
ID_EN_US = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0'

# Inicializar motor de voz una vez
engine = pyttsx3.init()


def _configurar_voz(engine_obj):
    """Configura la voz del engine al español, usando una instalada o los tokens de respaldo."""
    try:
        voices = engine_obj.getProperty('voices')
        voz_es = None
        for v in voices:
            vid = (v.id or '').lower()
            vname = (getattr(v, 'name', '') or '').lower()
            if 'es-' in vid or 'spanish' in vname or 'espa' in vname:
                voz_es = v
                break
        if voz_es:
            engine_obj.setProperty('voice', voz_es.id)
        else:
            # Fallback a tokens específicos de Windows si existen
            try:
                engine_obj.setProperty('voice', ID_ES_ES)
            except Exception:
                try:
                    engine_obj.setProperty('voice', ID_ES_MX)
                except Exception:
                    pass
    except Exception as e:
        print('Error al seleccionar voz:', e)


# Seleccionar voz
_configurar_voz(engine)

# Ajustes de velocidad y volumen
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

# Archivos para persistencia
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDATORIOS_FILE = os.path.join(BASE_DIR, 'recordatorios.json')
NOTAS_FILE = os.path.join(BASE_DIR, 'notas.txt')


def _recrear_engine():
    """Recrea el engine de pyttsx3 en caso de bloqueo, manteniendo configuración básica."""
    global engine
    try:
        engine = pyttsx3.init()
        _configurar_voz(engine)
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        print('[DEBUG] Engine de voz recreado correctamente')
    except Exception as e:
        print('[DEBUG] Error al recrear engine de voz:', e)


# Helper: hablar
def hablar(mensaje):
    print('[Helena]:', mensaje)
    try:
        # Crear un engine nuevo por llamada usando el driver SAPI5 de Windows
        local_engine = pyttsx3.init(driverName='sapi5')
        # Configurar voz español
        _configurar_voz(local_engine)
        local_engine.setProperty('rate', 150)
        local_engine.setProperty('volume', 1.0)
        # Pronunciar
        local_engine.say(mensaje)
        local_engine.runAndWait()
        # Liberar recursos
        try:
            local_engine.stop()
        except Exception:
            pass
        del local_engine
    except Exception as e:
        print('Error al sintetizar voz:', e)
        # No relanzamos para no cortar el flujo

# Helper: mostrar (imprime y opcionalmente habla)
def mostrar(mensaje, speak=True):
    # Mensaje siempre se imprime en terminal; si speak=True, también se pronuncia.
    try:
        print(mensaje)
    except Exception:
        pass
    if speak:
        try:
            hablar(mensaje)
        except Exception:
            pass

# Helper: escuchar (con fallback a entrada por texto)
def escuchar(text_mode=False, timeout=None, phrase_time_limit=None):
    """Devuelve el comando del usuario.

    - Si text_mode=True: siempre pide entrada por teclado, sin usar micrófono.
    - Si text_mode=False: usa el micrófono y reconocimiento de voz.
    """
    if text_mode:
        try:
            # En modo texto NO usamos el micrófono nunca.
            mostrar('Por favor, escribe tu comando:', speak=False)
            # Si quieres que también hable la invitación a escribir, cambia speak a True.
            return input('Escribe tu comando: ').strip()
        except Exception:
            return None

    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.pause_threshold = 0.8
            hablar('Estoy escuchando...')
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        try:
            pedido = r.recognize_google(audio, language='es-ES')
            # Mostrar en terminal y decir la transcripción reconocida
            hablar(f'Reconocido: {pedido}')
            return pedido
        except sr.UnknownValueError:
            hablar('Lo siento, no pude entenderte. ¿Puedes repetirlo?')
            return None
        except sr.RequestError:
            hablar('Lo siento, no hay servicio de reconocimiento ahora mismo.')
            return None
        except Exception as e:
            # Mensaje de error interno (se registra en consola, el usuario recibe voz)
            print('Error interno en reconocimiento:', e)
            hablar('Ups, ha ocurrido un error al procesar el audio.')
            return None
    except Exception as e:
        # No se pudo acceder al micrófono: informar y sugerir modo texto
        print('No hay micrófono disponible o permiso denegado:', e)
        mostrar('No puedo acceder al micrófono. Usa el modo texto escribiendo --text al ejecutar.', speak=True)
        return None

# Funciones de utilidad

def pedir_dia():
    dia = datetime.date.today()
    dia_semana = dia.weekday()
    calendario = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    hablar(f'Hoy es {calendario.get(dia_semana, "día desconocido")}')


def pedir_hora():
    ahora = datetime.datetime.now()
    hablar(f'En este momento son las {ahora.hour} horas con {ahora.minute} minutos')


def saludo_inicial():
    ahora = datetime.datetime.now()
    if ahora.hour < 6 or ahora.hour > 20:
        momento = 'Buenas noches'
    elif 6 <= ahora.hour < 13:
        momento = 'Buen día'
    else:
        momento = 'Buenas tardes'
    hablar(f'{momento}, soy Helena, tu asistente personal. Por favor, dime en qué te puedo ayudar')

# Wikipedia

def buscar_wikipedia(query):
    try:
        wikipedia.set_lang('es')
        resumen = wikipedia.summary(query, sentences=2)
        hablar('Según Wikipedia:')
        hablar(resumen)
    except wikipedia.exceptions.DisambiguationError as e:
        hablar('La búsqueda es ambigua. ¿Podrías ser más específico?')
    except Exception as e:
        print('Error Wikipedia:', e)
        hablar('No pude encontrar información en Wikipedia para eso.')

# Buscar en internet

def buscar_internet(query):
    try:
        pywhatkit.search(query)
        hablar('Esto es lo que encontré en internet.')
    except Exception as e:
        print('Error búsqueda internet:', e)
        hablar('No pude realizar la búsqueda en internet.')

# Reproducir en YouTube

def reproducir_youtube(query):
    try:
        pywhatkit.playonyt(query)
        hablar(f'Reproduciendo {query} en YouTube')
    except Exception as e:
        print('Error reproducir YouTube:', e)
        hablar('No pude reproducir eso en YouTube.')

# Abrir YouTube o navegador

def abrir_youtube():
    try:
        webbrowser.open('https://www.youtube.com')
        hablar('Abriendo YouTube')
    except Exception as e:
        print('Error abrir YouTube:', e)
        hablar('No pude abrir YouTube.')


def abrir_navegador():
    try:
        webbrowser.open('https://www.google.com')
        hablar('Abriendo navegador')
    except Exception as e:
        print('Error abrir navegador:', e)
        hablar('No pude abrir el navegador.')

# Broma

def contar_broma():
    try:
        b = pyjokes.get_joke('es')
        hablar(b)
    except Exception as e:
        print('Error pyjokes:', e)
        hablar('Lo siento, no tengo chistes ahora mismo.')

# Precio de acciones

def precio_acciones(nombre):
    cartera = {'apple': 'AAPL', 'amazon': 'AMZN', 'google': 'GOOGL', 'microsoft': 'MSFT'}
    try:
        clave = nombre.lower().strip()
        simbolo = cartera.get(clave)
        if not simbolo:
            hablar('No conozco esa acción en mi cartera. Prueba con Apple, Amazon, Google o Microsoft.')
            return
        ticker = yf.Ticker(simbolo)
        info = ticker.info
        precio = info.get('regularMarketPrice') or info.get('previousClose')
        if precio:
            hablar(f'El precio actual de {nombre} ({simbolo}) es {precio} dólares')
        else:
            hablar('No pude obtener el precio de la acción ahora mismo.')
    except Exception as e:
        print('Error yfinance:', e)
        hablar('No pude obtener el precio de las acciones debido a un error.')

# Recordatorios (persistentes)

def cargar_recordatorios():
    try:
        if os.path.exists(RECORDATORIOS_FILE):
            with open(RECORDATORIOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print('Error cargar recordatorios:', e)
    return []


def guardar_recordatorios(recordatorios):
    try:
        with open(RECORDATORIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(recordatorios, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('Error guardar recordatorios:', e)


def agregar_recordatorio(texto):
    recordatorios = cargar_recordatorios()
    item = {'texto': texto, 'fecha': datetime.datetime.now().isoformat()}
    recordatorios.append(item)
    guardar_recordatorios(recordatorios)
    hablar('Recordatorio guardado.')


def listar_recordatorios():
    recordatorios = cargar_recordatorios()
    if not recordatorios:
        hablar('No tienes recordatorios guardados.')
        return
    hablar(f'Tienes {len(recordatorios)} recordatorios:')
    for r in recordatorios:
        fecha = r.get('fecha', '')
        texto = r.get('texto', '')
        hablar(f'El {fecha}: {texto}')

# Notas de voz (guardar en archivo)

def modo_notas(text_mode=False):
    hablar('Entrando en modo notas. Di o escribe lo que quieras guardar. Di "salir notas" para terminar.')
    while True:
        pedido = escuchar(text_mode=text_mode)
        if not pedido:
            continue
        if 'salir notas' in pedido.lower():
            hablar('Saliendo del modo notas.')
            break
        try:
            with open(NOTAS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.datetime.now().isoformat()}] {pedido}\n")
            hablar('Nota guardada.')
        except Exception as e:
            print('Error guardar nota:', e)
            hablar('No pude guardar la nota.')

# Clima sencillo usando wttr.in (no requiere API key)

def obtener_clima(ciudad=''):
    try:
        lugar = ciudad.strip() or 'Mexicali'
        session = requests.Session()
        # Intentar wttr.in con hasta 3 reintentos y backoff
        url = f'https://wttr.in/{requests.utils.requote_uri(lugar)}?format=3'
        last_exc = None
        for attempt in range(3):
            try:
                timeout = 5 + attempt * 5
                resp = session.get(url, timeout=timeout)
                if resp.status_code == 200 and resp.text:
                    hablar(f'Clima en {resp.text}')
                    return
                last_exc = Exception(f'Código HTTP {resp.status_code}')
            except requests.RequestException as e:
                last_exc = e
                # Pequeña espera antes del siguiente intento
                try:
                    import time
                    time.sleep(1 + attempt)
                except Exception:
                    pass
        # Si wttr.in falló, intentar con Open-Meteo (geocoding + current_weather)
        hablar('No pude obtener respuesta de wttr.in, voy a intentar con un servicio alternativo.')
        try:
            geo_url = f'https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.requote_uri(lugar)}&count=1'
            g = session.get(geo_url, timeout=8)
            if g.status_code != 200:
                raise Exception('Error en geocoding')
            data = g.json()
            results = data.get('results')
            if not results:
                hablar(f'No encontré la ubicación {lugar} en la base de datos de geocoding.')
                return
            first = results[0]
            lat = first.get('latitude')
            lon = first.get('longitude')
            name = first.get('name') or lugar
            # Obtener clima actual
            weather_url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto'
            w = session.get(weather_url, timeout=8)
            if w.status_code != 200:
                raise Exception('Error al consultar Open-Meteo')
            wdata = w.json()
            current = wdata.get('current_weather')
            if not current:
                hablar('No pude obtener el clima actual del servicio alternativo.')
                return
            temp = current.get('temperature')
            wind = current.get('windspeed')
            direction = current.get('winddirection')
            hablar(f'Actualmente en {name} la temperatura es de {temp}°C, con viento de {wind} km/h.')
            return
        except Exception as e:
            print('Error alternativa Open-Meteo:', e)
            hablar('Lo siento, no pude obtener el clima debido a un problema de red o del servicio.')
            return
    except Exception as e:
        print('Error obtener clima:', e)
        hablar('No pude obtener el clima debido a un error inesperado.')
        return

# Enviar WhatsApp (usar pywhatkit). Nota: funciona abriendo WhatsApp Web.

def enviar_whatsapp(numero, mensaje):
    try:
        # pywhatkit.sendwhatmsg_instantly necesita que WhatsApp Web se pueda abrir y el usuario esté logueado
        pywhatkit.sendwhatmsg_instantly(numero, mensaje)
        hablar('Mensaje de WhatsApp enviado (o se abrió WhatsApp Web para que lo confirmes).')
    except Exception as e:
        print('Error enviar WhatsApp:', e)
        hablar('No pude enviar el mensaje por WhatsApp.')

# Bucle principal de interacción

def pedir_cosas(text_mode=False):
    """Bucle principal de comandos.

    No hace saludo inicial, para que el main pueda controlar mejor el arranque
    (y la frase de prueba) en ambos modos.
    """
    comenzar = True
    while comenzar:
        pedido = escuchar(text_mode=text_mode)
        if not pedido:
            continue
        pedido = pedido.lower()

        try:
            if 'abrir youtube' in pedido:
                abrir_youtube()
                continue
            elif 'abrir navegador' in pedido or 'abrir chrome' in pedido or 'abrir navegador' in pedido:
                abrir_navegador()
                continue
            elif 'qué día es hoy' in pedido or 'que día es hoy' in pedido:
                pedir_dia()
                continue
            elif 'qué hora es' in pedido or 'que hora es' in pedido:
                pedir_hora()
                continue
            elif 'busca en wikipedia' in pedido:
                buscar = pedido.replace('busca en wikipedia', '').strip()
                if buscar:
                    buscar_wikipedia(buscar)
                else:
                    hablar('¿Qué quieres que busque en Wikipedia?')
                continue
            elif 'busca en internet' in pedido or 'buscar en internet' in pedido:
                buscar = pedido.replace('busca en internet', '').replace('buscar en internet', '').strip()
                if buscar:
                    buscar_internet(buscar)
                else:
                    hablar('¿Qué quieres que busque en internet?')
                continue
            elif pedido.startswith('reproducir'):
                # reproducir <algo>
                buscar = pedido.replace('reproducir', '').strip()
                if buscar:
                    reproducir_youtube(buscar)
                else:
                    hablar('¿Qué quieres que reproduzca en YouTube?')
                continue
            elif 'broma' in pedido:
                contar_broma()
                continue
            elif 'precio de las acciones' in pedido or 'precio de la acción' in pedido:
                # Extraer nombre después de "de"
                partes = pedido.split('de')
                if len(partes) > 1:
                    nombre = partes[-1].strip()
                    precio_acciones(nombre)
                else:
                    hablar('¿De qué acción quieres el precio?')
                continue
            elif 'adiós' in pedido or 'adios' in pedido or 'salir' in pedido:
                hablar('Me voy a descansar, cualquier cosa me avisas. Hasta luego.')
                break
            elif 'guardar recordatorio' in pedido or 'añadir recordatorio' in pedido or 'agregar recordatorio' in pedido:
                # Ejemplo: "guardar recordatorio comprar leche mañana"
                texto = pedido.replace('guardar recordatorio', '').replace('añadir recordatorio', '').replace('agregar recordatorio', '').strip()
                if texto:
                    agregar_recordatorio(texto)
                else:
                    hablar('¿Qué quieres que recorde?')
                continue
            elif 'listar recordatorios' in pedido or 'mostrar recordatorios' in pedido:
                listar_recordatorios()
                continue
            elif 'modo notas' in pedido or 'notas' in pedido:
                modo_notas(text_mode=text_mode)
                continue
            elif 'enviar whatsapp' in pedido:
                # Formato esperado: "enviar whatsapp +521123456789 mensaje hola"
                hablar('Dime el número (con código de país)')
                numero = escuchar(text_mode=text_mode)
                if not numero:
                    continue
                hablar('Dime el mensaje')
                mensaje = escuchar(text_mode=text_mode)
                if not mensaje:
                    continue
                enviar_whatsapp(numero, mensaje)
                continue
            elif 'clima' in pedido:
                # "clima madrid" o solo "clima"
                partes = pedido.split()
                if len(partes) > 1:
                    ciudad = ' '.join(partes[1:])
                else:
                    ciudad = ''
                obtener_clima(ciudad)
                continue
            elif 'traduce' in pedido or 'traducir' in pedido:
                # Comando simple: "traduce hola a ingles" o "traducir hola a ingles"
                hablar('Función de traducción no implementada completamente en offline.')
                continue
            else:
                # Si no reconoce el comando, ofrecer búsqueda web
                hablar('No entendí el comando exacto. ¿Quieres que busque eso en internet?')
                respuesta = escuchar(text_mode=text_mode)
                if respuesta and respuesta.lower() in ['si', 'sí', 's']:
                    buscar_internet(pedido)
                else:
                    hablar('De acuerdo.')
                continue
        except Exception as e:
            print('Error general en el procesamiento del pedido:', e)
            hablar('Lo siento, ha ocurrido un error al ejecutar esa acción. ¿Puedes intentarlo de nuevo?')


# Modo de prueba para validar funciones sin micrófono
def modo_prueba():
    # Sustituir temporalmente 'hablar' por una versión que solo imprime para evitar bloqueos de audio
    hablar_original = globals().get('hablar')
    def hablar_solo_print(msg):
        print('[Helena - PRUEBA]:', msg)
    globals()['hablar'] = hablar_solo_print

    log_path = os.path.join(BASE_DIR, 'test_log.txt')
    def log(msg):
        timestamp = datetime.datetime.now().isoformat()
        entry = f"[{timestamp}] {msg}\n"
        try:
            with open(log_path, 'a', encoding='utf-8') as lf:
                lf.write(entry)
        except Exception:
            pass
        # Mostrar y pronunciar el mensaje (si hablar fue sustituida, hablar_solo_print imprimirá)
        hablar(entry.strip())

    log('Modo prueba activado. Ejecutando comandos de verificación...')
    try:
        log('-> pedir_hora')
        pedir_hora()
        log('-> pedir_dia')
        pedir_dia()
        log('-> contar_broma')
        contar_broma()
        log('-> buscar_wikipedia')
        buscar_wikipedia('Python (lenguaje de programación)')
        log('-> agregar_recordatorio')
        agregar_recordatorio('Probar recordatorio desde modo prueba')
        log('-> listar_recordatorios')
        listar_recordatorios()
        log('-> obtener_clima')
        obtener_clima('Mexicali')
        log('Prueba finalizada correctamente.')
    except Exception as e:
        log(f'Error durante modo_prueba: {e}')
    finally:
        # Restaurar 'hablar'
        if hablar_original:
            globals()['hablar'] = hablar_original


if __name__ == '__main__':
    text_mode = '--text' in sys.argv
    test_mode = '--test' in sys.argv

    # Saludo inicial solo una vez, controlado desde aquí
    saludo_inicial()

    if test_mode:
        modo_prueba()
    else:
        pedir_cosas(text_mode=text_mode)
