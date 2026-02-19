#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓ
# ============================================
CARPETA_SORTIDA = "public"
FITXER_ESTACIONS = "estacions_actives.json"

def crear_carpeta_public():
    """Crea la carpeta public si no existeix"""
    if not os.path.exists(CARPETA_SORTIDA):
        os.makedirs(CARPETA_SORTIDA)
        print(f"📁 Carpeta '{CARPETA_SORTIDA}' creada")

def carregar_estacions():
    """Carrega la llista d'estacions actives"""
    try:
        with open(FITXER_ESTACIONS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ No es troba el fitxer {FITXER_ESTACIONS}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error llegint {FITXER_ESTACIONS}")
        return []

def processar_vent(resum_dia):
    """
    PUNT 1: Posar graus a Direcció del Vent
    Exemple: "N 15 km/h" → "N 15°"
    """
    # Buscar camps de vent al resum
    camps_vent = ['DIRECCIO_VENT', 'VENT_DIRECCIO', 'DIR_VENT']
    direccio = ''
    for camp in camps_vent:
        if camp in resum_dia and resum_dia[camp]:
            direccio = resum_dia[camp]
            break
    
    # Buscar velocitat
    camps_velocitat = ['VELOCITAT_VENT', 'VENT_VELOCITAT', 'VEL_VENT']
    velocitat = ''
    for camp in camps_velocitat:
        if camp in resum_dia and resum_dia[camp]:
            velocitat = resum_dia[camp]
            # Netejar unitats
            velocitat = velocitat.replace('km/h', '').replace('Km/h', '').strip()
            break
    
    if direccio and velocitat:
        return f"{direccio} {velocitat}°"
    return "N/A"

def processar_ratxa_maxima(resum_dia):
    """
    PUNT 2: Eliminar ºC del final de Ratxa màxima del vent
    """
    ratxa = resum_dia.get('RATXA_VENT_MAX', '')
    if ratxa and ratxa.endswith('ºC'):
        ratxa = ratxa[:-2]  # Treure els últims 2 caràcters
    return ratxa

def processar_pressio(resum_dia):
    """
    PUNT 3: Eliminar ºC del final de Pressió atmosfèrica
    """
    pressio = resum_dia.get('PRESSIO_ATMOSFERICA', '')
    if pressio and pressio.endswith('ºC'):
        pressio = pressio[:-2]
    return pressio

def generar_html_estacio(dades, resum_dia, index_estacio, total_estacions):
    """
    Genera l'HTML per a una estació amb TOTES les millores:
    - PUNT 1: Graus a vent
    - PUNT 2: Netejar ratxa
    - PUNT 3: Netejar pressió
    - PUNT 5: Responsive design
    - PUNT 7: Lletra verda període
    - PUNT 8: Alerta pluja
    - PUNT 9: Nou missatge capçalera
    """
    
    # Processar dades
    id_estacio = dades.get('ID_ESTAC', '')
    nom_estacio = dades.get('NOM_ESTACIO', '')
    data = dades.get('DATA_UTC', '')
    hora = dades.get('HORA_CONSULTA_UTC', '')
    periode = dades.get('PERIODE_UTC', '')
    
    # Dades del període
    tm_periode = dades.get('VAR_TM_grausC', 'N/A')
    ppt_periode = dades.get('VAR_PPT_mm', '0.0')
    
    # PUNT 1: Vent amb graus
    vent_mostrar = processar_vent(resum_dia)
    
    # PUNT 2: Ratxa màxima neta
    ratxa_max = processar_ratxa_maxima(resum_dia)
    
    # PUNT 3: Pressió neta
    pressio = processar_pressio(resum_dia)
    
    # PUNT 8: Detectar possibles errors de pluja
    ppt_dia = resum_dia.get('PRECIPITACIO_ACUM_DIA', '0.0 mm')
    try:
        ppt_dia_valor = float(ppt_dia.replace(' mm', '').replace('mm', '').strip())
        ppt_periode_valor = float(ppt_periode)
        
        if ppt_periode_valor == 0.0 and ppt_dia_valor > 0:
            print(f"⚠️ Alerta {id_estacio}: PPT període 0.0 però dia {ppt_dia}")
    except:
        pass
    
    # PUNT 7: Textos del període (lletra verda)
    periode_text_tm = f"Temperatura mitjana del període"
    periode_text_ppt = f"Precipitació del període"
    
    # ============================================
    # GENERAR HTML
    # ============================================
    html = f"""<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
    <title>Estació {id_estacio} - {nom_estacio}</title>
    <style>
        /* PUNT 5: RESPONSIVE DESIGN */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a237e, #0a2d5e);
            color: white;
            min-height: 100vh;
            padding: 15px;
            display: flex;
            flex-direction: column;
        }}
        
        /* PUNT 9: NOU MISSATGE CAPÇALERA */
        .header-info {{
            background: rgba(0, 188, 212, 0.15);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: clamp(0.7rem, 2vw, 0.9rem);
            text-align: center;
            margin-bottom: 15px;
            border-left: 4px solid #00bcd4;
            border-right: 4px solid #00bcd4;
            backdrop-filter: blur(5px);
        }}
        
        .header-info i {{
            color: #ff9800;
            font-style: normal;
        }}
        
        h1 {{
            font-size: clamp(1.2rem, 4vw, 1.8rem);
            margin-bottom: 5px;
            word-break: break-word;
        }}
        
        .subtitle {{
            font-size: clamp(0.7rem, 2vw, 0.9rem);
            color: #b0e0e6;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0, 188, 212, 0.3);
        }}
        
        /* TARGETA DEL PERÍODE ACTUAL */
        .periode-card {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid rgba(0, 188, 212, 0.3);
        }}
        
        .periode-title {{
            font-size: clamp(0.8rem, 2.5vw, 1rem);
            color: #00bcd4;
            margin-bottom: 15px;
            font-weight: bold;
        }}
        
        .periode-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        
        @media (max-width: 480px) {{
            .periode-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .dada-principal {{
            font-size: clamp(1.5rem, 5vw, 2.2rem);
            font-weight: bold;
            line-height: 1.2;
        }}
        
        /* PUNT 7: LETRA PETITA CURSIVA VERDA */
        .periode-info {{
            font-size: clamp(0.6rem, 1.8vw, 0.75rem);
            font-style: italic;
            color: #4caf50;
            margin-top: 3px;
        }}
        
        /* GRAELLA DE TARGETES */
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin: 15px 0;
        }}
        
        .targeta {{
            background: rgba(255, 255, 255, 0.1);
            padding: 12px;
            border-radius: 10px;
            border-left: 4px solid #00bcd4;
            backdrop-filter: blur(5px);
        }}
        
        .targeta h3 {{
            font-size: clamp(0.8rem, 2.2vw, 0.95rem);
            margin: 0 0 8px 0;
            color: #b0e0e6;
            border-bottom: 1px solid rgba(0, 188, 212, 0.2);
            padding-bottom: 3px;
        }}
        
        .targeta .valor {{
            font-size: clamp(1rem, 3vw, 1.3rem);
            font-weight: bold;
        }}
        
        .targeta .detall {{
            font-size: clamp(0.65rem, 1.8vw, 0.8rem);
            color: #ccc;
        }}
        
        /* RESUM DEL DIA */
        .resum-card {{
            background: rgba(0, 0, 0, 0.4);
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
            border: 1px solid rgba(255, 152, 0, 0.3);
        }}
        
        .resum-title {{
            font-size: clamp(0.9rem, 2.5vw, 1.1rem);
            color: #ff9800;
            margin-bottom: 15px;
            font-weight: bold;
        }}
        
        .resum-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }}
        
        .resum-item {{
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 6px;
        }}
        
        .resum-label {{
            font-size: clamp(0.65rem, 1.8vw, 0.75rem);
            color: #aaa;
        }}
        
        .resum-value {{
            font-size: clamp(0.9rem, 2.5vw, 1.1rem);
            font-weight: bold;
            color: #ff9800;
        }}
        
        /* FOOTER */
        .footer {{
            margin-top: 20px;
            text-align: center;
            font-size: clamp(0.6rem, 1.8vw, 0.7rem);
            color: #aaa;
            padding-top: 10px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        .footer a {{
            color: #80e27e;
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        /* PROGRÉS D'ESTACIONS (PETIT) */
        .progress {{
            position: fixed;
            bottom: 5px;
            right: 5px;
            background: rgba(0,0,0,0.5);
            color: #aaa;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.6rem;
            z-index: 100;
        }}
    </style>
</head>
<body>
    <!-- PUNT 9: NOU MISSATGE -->
    <div class="header-info">
        <i>📍</i> Per a finestra estàtica anar a "Estacions" i escollir la desitjada
    </div>
    
    <h1>🏔️ {nom_estacio}</h1>
    <div class="subtitle">
        ID: {id_estacio} | {data} {hora} TU
    </div>
    
    <!-- TARGETA DEL PERÍODE ACTUAL -->
    <div class="periode-card">
        <div class="periode-title">📊 Dades del període {periode}</div>
        <div class="periode-grid">
            <!-- Temperatura mitjana període -->
            <div>
                <div class="dada-principal">{tm_periode}°C</div>
                <div class="periode-info">{periode_text_tm}</div>
            </div>
            
            <!-- Precipitació període -->
            <div>
                <div class="dada-principal">{ppt_periode} mm</div>
                <div class="periode-info">{periode_text_ppt}</div>
            </div>
        </div>
    </div>
    
    <!-- GRAELLA DE TOTES LES DADES -->
    <div class="grid-container">
        <!-- Temperatures -->
        <div class="targeta">
            <h3>🌡️ Temperatures</h3>
            <div class="valor">{dades.get('VAR_TX_grausC', 'N/A')}°C</div>
            <div class="detall">Màxima període</div>
            <div class="valor" style="margin-top:5px;">{dades.get('VAR_TN_grausC', 'N/A')}°C</div>
            <div class="detall">Mínima període</div>
        </div>
        
        <!-- Humitat -->
        <div class="targeta">
            <h3>💧 Humitat</h3>
            <div class="valor">{dades.get('VAR_HRM_perc', 'N/A')}%</div>
            <div class="detall">Mitjana període</div>
        </div>
        
        <!-- Vent (PUNT 1) -->
        <div class="targeta">
            <h3>🌬️ Vent</h3>
            <div class="valor">{vent_mostrar}</div>
            <div class="detall">Direcció i velocitat</div>
            <div class="valor" style="margin-top:5px;">{ratxa_max}</div>
            <div class="detall">Ratxa màxima</div>
        </div>
        
        <!-- Pressió (PUNT 3) -->
        <div class="targeta">
            <h3>📈 Pressió</h3>
            <div class="valor">{pressio}</div>
            <div class="detall">Atmosfèrica</div>
        </div>
        
        <!-- Neu -->
        <div class="targeta">
            <h3>❄️ Neu</h3>
            <div class="valor">{dades.get('VAR_GN_cm', 'N/A')} cm</div>
            <div class="detall">Gruix actual</div>
        </div>
        
        <!-- Radiació -->
        <div class="targeta">
            <h3>☀️ Radiació</h3>
            <div class="valor">{dades.get('VAR_RS_W_m_2', '0')} W/m²</div>
            <div class="detall">Mitjana període</div>
        </div>
    </div>
    
    <!-- RESUM DEL DIA -->
    <div class="resum-card">
        <div class="resum-title">📅 Resum del dia {resum_dia.get('DATA_DIA', '')}</div>
        <div class="resum-grid">
            <div class="resum-item">
                <div class="resum-label">Temperatura mitjana</div>
                <div class="resum-value">{resum_dia.get('TEMPERATURA_MITJANA_DIA', 'N/A')}</div>
            </div>
            <div class="resum-item">
                <div class="resum-label">Temperatura màxima</div>
                <div class="resum-value">{resum_dia.get('TEMPERATURA_MAXIMA_DIA', 'N/A')}</div>
            </div>
            <div class="resum-item">
                <div class="resum-label">Temperatura mínima</div>
                <div class="resum-value">{resum_dia.get('TEMPERATURA_MINIMA_DIA', 'N/A')}</div>
            </div>
            <div class="resum-item">
                <div class="resum-label">Humitat mitjana</div>
                <div class="resum-value">{resum_dia.get('HUMITAT_MITJANA_DIA', 'N/A')}</div>
            </div>
            <div class="resum-item">
                <div class="resum-label">Precipitació acumulada</div>
                <div class="resum-value">{resum_dia.get('PRECIPITACIO_ACUM_DIA', '0.0 mm')}</div>
            </div>
            <div class="resum-item">
                <div class="resum-label">Gruix màxim neu</div>
                <div class="resum-value">{resum_dia.get('GRUIX_NEU_MAX', 'N/A')}</div>
            </div>
        </div>
    </div>
    
    <!-- Font de dades -->
    <div class="footer">
        Dades: <a href="{dades.get('URL_FONT', '#')}" target="_blank">Meteo.cat</a> • 
        Estació {index_estacio+1}/{total_estacions}
    </div>
    
    <!-- Petit comptador de progrés -->
    <div class="progress">
        {index_estacio+1}/{total_estacions}
    </div>
</body>
</html>"""
    
    return html

def generar_banner_html(estacions_actives, dades_completes):
    """
    Genera el fitxer banner.html amb la llista d'estacions
    """
    html = """<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estacions Actives - Meteo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1a237e, #0a2d5e);
            color: white;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #00bcd4;
        }
        .estacions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .estacio-card {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #ff9800;
        }
        .estacio-card h3 {
            margin: 0 0 10px 0;
            color: #ff9800;
        }
        .estacio-card a {
            color: #00bcd4;
            text-decoration: none;
            display: block;
            margin-top: 10px;
            word-break: break-all;
        }
        .estacio-card a:hover {
            text-decoration: underline;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #aaa;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <h1>🏔️ Estacions Meteorològiques Actives</h1>
    <div class="estacions-grid">
"""
    
    for estacio in estacions_actives:
        id_est = estacio.get('id', '')
        nom = estacio.get('nom', '')
        html += f"""
        <div class="estacio-card">
            <h3>{id_est}</h3>
            <p>{nom}</p>
            <a href="public/index_{id_est}.html" target="_blank">📊 index_{id_est}.html</a>
        </div>
"""
    
    html += """
    </div>
    <div class="footer">
        Total estacions: {} • Actualitzat: {}
    </div>
</body>
</html>
""".format(len(estacions_actives), datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    return html

def main():
    print("🚀 Iniciant generador de banners meteorològics...")
    
    # Crear carpeta de sortida
    crear_carpeta_public()
    
    # Carregar estacions actives
    estacions_actives = carregar_estacions()
    if not estacions_actives:
        print("❌ No hi ha estacions per processar")
        return
    
    print(f"📊 {len(estacions_actives)} estacions carregades")
    
    # Simular dades per cada estació (en producció, aquí es connectaria amb l'scraper)
    # Aquesta part s'ha de substituir per la crida real a les dades
    dades_completes = []
    
    for i, estacio in enumerate(estacions_actives):
        print(f"🔄 Processant {estacio.get('id', '')} ({i+1}/{len(estacions_actives)})...")
        
        # AQUÍ ANIRIA LA CRIDA A L'SCRAPER PER OBTENIR DADES REALS
        # Per ara, generem dades de prova
        dades_periode = {
            'ID_ESTAC': estacio.get('id', ''),
            'NOM_ESTACIO': estacio.get('nom', ''),
            'DATA_UTC': datetime.now().strftime("%Y-%m-%d"),
            'HORA_CONSULTA_UTC': datetime.now().strftime("%H:%M"),
            'PERIODE_UTC': f"{(datetime.now().hour-1):02d}:30 - {datetime.now().hour:02d}:00",
            'VAR_TM_grausC': f"{((i*0.5) % 10 - 5):.1f}",
            'VAR_TX_grausC': f"{((i*0.5) % 10 - 4):.1f}",
            'VAR_TN_grausC': f"{((i*0.5) % 10 - 6):.1f}",
            'VAR_HRM_perc': f"{50 + (i % 30)}",
            'VAR_PPT_mm': "0.0" if i % 3 == 0 else "0.2",
            'VAR_GN_cm': f"{80 + (i % 30)}",
            'VAR_RS_W_m_2': f"{i % 200}",
            'URL_FONT': f"https://www.meteo.cat/observacions/xema/dades?codi={estacio.get('id', '')}"
        }
        
        resum_dia = {
            'DATA_DIA': datetime.now().strftime("%Y-%m-%d"),
            'TEMPERATURA_MITJANA_DIA': f"{((i*0.5) % 10 - 3):.1f} °C",
            'TEMPERATURA_MAXIMA_DIA': f"{((i*0.5) % 10 - 2):.1f} °C {i%12:02d}:{i%60:02d} TU",
            'TEMPERATURA_MINIMA_DIA': f"{((i*0.5) % 10 - 7):.1f} °C {(i+5)%24:02d}:{i%60:02d} TU",
            'HUMITAT_MITJANA_DIA': f"{55 + (i % 35)}%",
            'PRECIPITACIO_ACUM_DIA': f"{i % 5}.{(i*3)%10} mm",
            'GRUIX_NEU_MAX': f"{85 + (i % 25)} cm",
            'RATXA_VENT_MAX': f"{(i*5) % 50}.{i%10} km/h" if i % 4 != 0 else f"{(i*5) % 50}.{i%10} km/h ºC",
            'RADIACIO_GLOBAL': f"{i % 20}.{i%10} MJ/m2",
            'PRESSIO_ATMOSFERICA': f"101{5 + (i%5)}.{i%10} hPa" if i % 3 != 0 else f"101{5 + (i%5)}.{i%10} hPa ºC",
            'DIRECCIO_VENT': ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][i % 8],
            'VELOCITAT_VENT': f"{(i*2) % 25}.{i%10}"
        }
        
        dades_completes.append({
            'periode': dades_periode,
            'resum': resum_dia
        })
        
        # Generar HTML individual
        html_estacio = generar_html_estacio(
            dades_periode, 
            resum_dia,
            i,
            len(estacions_actives)
        )
        
        # Guardar fitxer
        nom_fitxer = f"index_{estacio.get('id', '')}.html"
        cami_fitxer = os.path.join(CARPETA_SORTIDA, nom_fitxer)
        
        with open(cami_fitxer, 'w', encoding='utf-8') as f:
            f.write(html_estacio)
        
        print(f"✅ {nom_fitxer} generat")
    
    # Generar banner.html
    print("\n📄 Generant banner.html...")
    banner_html = generar_banner_html(estacions_actives, dades_completes)
    
    with open('banner.html', 'w', encoding='utf-8') as f:
        f.write(banner_html)
    
    print("✅ banner.html generat")
    print(f"\n🎯 Procés completat! {len(estacions_actives)} estacions processades")

if __name__ == "__main__":
    main()
