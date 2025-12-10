from flask import Flask, render_template, request, jsonify
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import textwrap
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import re

app = Flask(__name__)

# --- CONFIGURACIÓN ---
DICCIONARIO_BRAILLE = {
    'a': [1], 'b': [1, 2], 'c': [1, 4], 'd': [1, 4, 5], 'e': [1, 5],
    'f': [1, 2, 4], 'g': [1, 2, 4, 5], 'h': [1, 2, 5], 'i': [2, 4], 'j': [2, 4, 5],
    'k': [1, 3], 'l': [1, 2, 3], 'm': [1, 3, 4], 'n': [1, 3, 4, 5], 'o': [1, 3, 5],
    'p': [1, 2, 3, 4], 'q': [1, 2, 3, 4, 5], 'r': [1, 2, 3, 5], 's': [2, 3, 4], 't': [2, 3, 4, 5],
    'u': [1, 3, 6], 'v': [1, 2, 3, 6], 'w': [2, 4, 5, 6], 'x': [1, 3, 4, 6], 'y': [1, 3, 4, 5, 6], 'z': [1, 3, 5, 6],
    'ñ': [1, 2, 4, 5, 6], '.': [3], ',': [2], ';': [2, 3], ':': [2, 5], 
    '-': [3, 6], '?': [2, 6], '!': [2, 3, 5], '"': [2, 3, 6],
    '(': [1, 2, 6], ')': [3, 4, 5], 
    '+': [2, 3, 5], '*': [3, 5], '/': [2, 5, 6], '=': [2, 3, 5, 6],
    ' ': [], 
    '»': [3, 4, 5], '[': [1, 2, 3, 5, 6], ']': [2, 3, 4, 5, 6],
    '#': [3, 4, 5, 6], '↑': [4, 6]
}
MAPA_NUMEROS = {'1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e', '6': 'f', '7': 'g', '8': 'h', '9': 'i', '0': 'j'}
PREFIJO_NUMERO = [3, 4, 5, 6] 
PREFIJO_MAYUSCULA = [4, 6]     

def obtener_puntos_braille(texto):
    resultado = []
    if not texto: return resultado
    texto = str(texto).replace('\r', '')
    for caracter in texto:
        if caracter == ' ':
            resultado.append({'label': ' ', 'puntos': [], 'tipo': 'espacio'})
        elif caracter.isdigit():
            resultado.append({'label': '#', 'puntos': PREFIJO_NUMERO, 'tipo': 'prefijo'})
            letra = MAPA_NUMEROS.get(caracter)
            puntos = DICCIONARIO_BRAILLE.get(letra, [])
            resultado.append({'label': caracter, 'puntos': puntos, 'tipo': 'numero'})
        else:
            char_p = caracter
            if caracter.isupper() and caracter not in ['↑', '#', '»', '[', ']']:
                resultado.append({'label': '↑', 'puntos': PREFIJO_MAYUSCULA, 'tipo': 'prefijo'})
                char_p = caracter.lower()
            puntos = DICCIONARIO_BRAILLE.get(char_p, [])
            label = caracter if puntos else ' '
            if caracter == '#': puntos = PREFIJO_NUMERO
            if caracter == '↑': puntos = PREFIJO_MAYUSCULA
            resultado.append({'label': label, 'puntos': puntos, 'tipo': 'letra'})
    return resultado

def procesar_imagen_a_braille(url):
    grid_final = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=4)
        img = Image.open(BytesIO(response.content))
        
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            alpha = img.convert('RGBA').split()[-1]
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.paste(img, mask=alpha)
            img = bg

        img = img.resize((80, 45))
        img = img.convert('L') 
        pixels = img.load()
        umbral = 128
        
        for r in range(15):
            for c in range(40):
                puntos_activos = []
                base_x, base_y = c * 2, r * 3
                try:
                    if pixels[base_x, base_y] < umbral: puntos_activos.append(1)
                    if pixels[base_x, base_y+1] < umbral: puntos_activos.append(2)
                    if pixels[base_x, base_y+2] < umbral: puntos_activos.append(3)
                    if pixels[base_x+1, base_y] < umbral: puntos_activos.append(4)
                    if pixels[base_x+1, base_y+1] < umbral: puntos_activos.append(5)
                    if pixels[base_x+1, base_y+2] < umbral: puntos_activos.append(6)
                except: pass
                grid_final.append({'label': '', 'puntos': puntos_activos, 'tipo': 'grafico'})
    except Exception as e: 
        return []
    return grid_final

def procesar_imagen_inline(url):
    lineas_imagen = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        img = Image.open(BytesIO(response.content))
        
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            alpha = img.convert('RGBA').split()[-1]
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.paste(img, mask=alpha)
            img = bg

        # --- LÓGICA DE REDIMENSIONAMIENTO ESTRICTA ---
        # Ancho fijo: 80 pixeles (40 celdas)
        # Alto máximo: 45 pixeles (15 celdas = 1 PAGINA EXACTA)
        
        aspect_ratio = img.height / img.width
        new_width = 80
        new_height = int(new_width * aspect_ratio)
        
        # Recortamos la altura si excede 45 pixeles (15 líneas)
        if new_height > 45: new_height = 45 
        
        img = img.resize((new_width, new_height))
        img = img.convert('L')
        pixels = img.load()
        
        rows_braille = new_height // 3
        umbral = 128 

        for r in range(rows_braille):
            linea_actual = []
            for c in range(40): 
                puntos_activos = []
                base_x, base_y = c * 2, r * 3
                try:
                    if base_x < new_width and base_y < new_height and pixels[base_x, base_y] < umbral: puntos_activos.append(1)
                    if base_x < new_width and base_y+1 < new_height and pixels[base_x, base_y+1] < umbral: puntos_activos.append(2)
                    if base_x < new_width and base_y+2 < new_height and pixels[base_x, base_y+2] < umbral: puntos_activos.append(3)
                    if base_x+1 < new_width and base_y < new_height and pixels[base_x+1, base_y] < umbral: puntos_activos.append(4)
                    if base_x+1 < new_width and base_y+1 < new_height and pixels[base_x+1, base_y+1] < umbral: puntos_activos.append(5)
                    if base_x+1 < new_width and base_y+2 < new_height and pixels[base_x+1, base_y+2] < umbral: puntos_activos.append(6)
                except: pass
                linea_actual.append({'label': '', 'puntos': puntos_activos, 'tipo': 'grafico-inline'})
            lineas_imagen.append({'braille': linea_actual, 'action': None})
            
    except Exception as e: return [] 
    return lineas_imagen

@app.route('/')
def index(): return render_template('index.html')

@app.route('/traducir', methods=['POST'])
def traducir():
    texto = request.json.get('texto', '')
    parrafos = texto.split('\n')
    lineas_finales = []
    for p in parrafos:
        if not p:
            lineas_finales.append([]) 
            continue
        lines_wrapped = textwrap.wrap(p, width=40)
        for l in lines_wrapped:
            lineas_finales.append(obtener_puntos_braille(l.ljust(40)))
    return jsonify({'lineas': lineas_finales})

@app.route('/buscar', methods=['POST'])
def buscar():
    consulta_raw = request.json.get('consulta', '')
    consulta_clean = consulta_raw.replace('↑', '').replace('#', '').strip()
    
    if consulta_clean.startswith('img:'):
        url = consulta_clean[4:].strip()
        data = procesar_imagen_a_braille(url)
        return jsonify([{'braille': data, 'is_image': True, 'action': None}]) if data else jsonify([])

    res_procesados = []
    try:
        url = "https://lite.duckduckgo.com/lite/"
        r = requests.post(url, data={'q': consulta_clean}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=6)
        soup = BeautifulSoup(r.text, 'html.parser')
        filas = soup.find_all('tr')
        for i in range(len(filas)):
            if len(res_procesados) >= 100: break
            link_tag = filas[i].find('a', class_='result-link')
            if link_tag:
                tit = link_tag.get_text().strip()
                href = link_tag.get('href')
                idx = len(res_procesados) + 1
                texto_linea = f"{idx}. {tit}".ljust(40)
                res_procesados.append({
                    'braille': obtener_puntos_braille(texto_linea),
                    'action': {'type': 'link', 'url': href}
                })
    except: pass

    count = len(res_procesados)
    if count == 0:
        res_procesados.append({'braille': obtener_puntos_braille("sin resultados.".ljust(40)), 'action': None})
    elif count < 100:
        faltan = 100 - count
        for i in range(faltan): res_procesados.append(res_procesados[i % count])

    return jsonify(res_procesados)

@app.route('/navegar', methods=['POST'])
def navegar():
    url = request.json.get('url', '')
    elementos = []
    seen_hashes = set()
    contador_links = 0
    LIMITE_LINKS = 10 
    ROWS_PER_PAGE = 15 
    
    try:
        head = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        r = requests.get(url, headers=head, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer', 'iframe', 'svg', 'noscript']): tag.decompose()
        ruido_css = ['.mw-jump-link', '.vector-menu', '.infobox', '#mw-navigation', '#footer', '.sidebar', '.cookie-banner', '.ad-container', '.social-share', '.mw-editsection']
        for sel in ruido_css:
            for t in soup.select(sel): t.decompose()

        target = soup.find('div', id='bodyContent')
        if not target: target = soup.find('article')
        if not target: target = soup.find('main')
        if not target: target = soup.find('div', class_='entry-content')
        if not target: target = soup.body

        tags = target.find_all(['h1', 'h2', 'h3', 'p', 'li', 'a', 'input', 'img'])
        
        for tag in tags:
            if tag.name == 'input' and tag.get('type') in ['text', 'search']:
                l = f"[ {tag.get('placeholder', 'Buscar')[:36]} ]".ljust(40)
                elementos.append({'braille': obtener_puntos_braille(l), 'action': {'type': 'input'}})
                continue

            if tag.name == 'img':
                src = tag.get('src')
                if src:
                    full_src = urljoin(url, src)
                    if any(x in src.lower() for x in ['.svg', 'logo', 'icon', 'pixel', 'sprite', '1x1']): continue
                    w = tag.get('width')
                    if w and w.isdigit() and int(w) < 50: continue

                    alt = tag.get('alt', 'imagen').strip()
                    if not alt: alt = "imagen"

                    # Procesamos imagen
                    lineas_img = procesar_imagen_inline(full_src)
                    
                    if lineas_img:
                        # --- LÓGICA DE PAGINACIÓN CORRECTA ---
                        
                        # 1. Insertamos el Texto (IMG: ...)
                        aviso = f"IMG: {alt[:35]}".ljust(40)
                        elementos.append({'braille': obtener_puntos_braille(aviso), 'action': None})
                        
                        # 2. Rellenamos con vacio hasta el final de la pagina actual
                        # Esto deja el texto "IMG:" al final de la hoja actual (o donde caiga)
                        # y fuerza a la imagen a saltar a la pagina nueva (índice 0)
                        while len(elementos) % ROWS_PER_PAGE != 0:
                            elementos.append({'braille': obtener_puntos_braille(" ".ljust(40)), 'action': None})

                        # 3. Insertamos la imagen (Ahora seguro está al inicio de pagina nueva)
                        elementos.extend(lineas_img)
                        
                        # Opcional: Si quieres que despues de la imagen tambien salte de pagina (imagen sola)
                        # descomenta el while de abajo. Por ahora solo dejamos un espacio.
                        elementos.append({'braille': obtener_puntos_braille(" ".ljust(40)), 'action': None})
                        
                continue

            txt = tag.get_text(" ", strip=True)
            if len(txt) < 5: continue 
            
            h = hash(txt)
            if h in seen_hashes: continue
            seen_hashes.add(h)

            es_link = False
            href_destino = "#"
            parent_link = tag.find_parent('a')
            if tag.name == 'a': es_link = True; href_destino = tag.get('href')
            elif parent_link: es_link = True; href_destino = parent_link.get('href')
            elif tag.find('a'):
                link_interno = tag.find('a')
                if len(link_interno.get_text(strip=True)) >= len(txt) * 0.8: es_link = True; href_destino = link_interno.get('href')

            if es_link and href_destino and not href_destino.startswith('#') and "javascript" not in href_destino:
                if contador_links < LIMITE_LINKS:
                    if not re.search(r'editar|edit|saltar|jump', txt, re.I):
                        l = f"» {txt[:37]}".ljust(40)
                        elementos.append({'braille': obtener_puntos_braille(l), 'action': {'type': 'link', 'url': urljoin(url, href_destino)}})
                        contador_links += 1
            else:
                if tag.name in ['p', 'h1', 'h2', 'h3', 'li']:
                    txt = re.sub(r'\[\d+\]', '', txt)
                    for line in textwrap.wrap(txt, width=40):
                        elementos.append({'braille': obtener_puntos_braille(line.ljust(40)), 'action': None})
                    if tag.name == 'p':
                        elementos.append({'braille': obtener_puntos_braille("".ljust(40)), 'action': None})

    except Exception as e:
        err = f"error: {str(e)[:30]}".ljust(40)
        elementos.append({'braille': obtener_puntos_braille(err), 'action': None})

    if not elementos:
        aviso = "contenido vacio.".ljust(40)
        elementos.append({'braille': obtener_puntos_braille(aviso), 'action': None})

    return jsonify(elementos)

if __name__ == '__main__':
    app.run(debug=True)