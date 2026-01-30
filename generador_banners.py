#!/usr/bin/env python3
"""
GENERADOR DE BANNERS METEOCAT
=============================
Genera:
1. index.html        - Banner principal amb rotació (120s)
2. banner.html       - Detall complet amb acordió desplegable
3. index_[ID].html   - Banner fix per a cada estació

Estructura de dades basada en les variables del PDF i organització en columnes.
"""

import json
import pandas as pd
from pathlib import Path
import re
from datetime import datetime
import shutil

# ============================================================================
# CONFIGURACIÓ
# ============================================================================
class Config:
    # Rutes d'entrada - RUTA ABSOLUTA AL TEU CAS
    DATA_DIR = Path(r"C:\Users\joant\Documents\OBS-Scripts\overlay-plus\src\dades")
    
    METADATA_FILE = DATA_DIR / "Totes_les_dades_de_les_estacions.xlsx"
    PERIODE_JSON = DATA_DIR / "resum_periode_meteocat.json"
    DIARI_JSON = DATA_DIR / "resum_diari_meteocat.json"
    
    # Ruta de sortida
    OUTPUT_DIR = Path("public")    
    # Configuració de rotació
    ROTATION_SECONDS = 120  # Canvi cada 2 minuts
    
    # Variables per a index.html (part inferior) - només 3 variables diàries
    VARIABLES_DIARI_INDEX = [
        "TEMPERATURA_MITJANA_DIA",
        "TEMPERATURA_MAXIMA_DIA", 
        "PRECIPITACIO_ACUM_DIA"
    ]
    
    # Organització de columnes (segons especificació)
    COLUMNES_ESTRUCTURA = {
        "basiques": [
            ("VAR_TM_grausC", "Temp. Mitjana:"),
            ("VAR_TX_grausC", "Temp. Màxima:"),
            ("VAR_TN_grausC", "Temp. Mínima:"),
            ("VAR_HRM_perc", "Humitat Relativa:")
        ],
        "precip_vent": [
            ("VAR_PPT_mm", "Precipitació:"),
            ("VAR_VVM_10_m_km_h", "Vent Mitjà:"),
            ("VAR_DVM_10_m_graus", "Direcció Vent:"),
            ("VAR_VVX_10_m_km_h", "Ràfega Màxima:")
        ],
        "altres": [
            ("VAR_PM_hPa", "Pressió:"),
            ("VAR_RS_W_m_2", "Irradiància:"),
            ("VAR_GN_cm", "Gruix de neu:")
        ],
        "addicionals": [
            ("VAR_Periode_TU", "Període:"),
            ("altitud", "Altitud:"),
            ("hora_actualitzacio", "Hora actualització:")
        ]
    }
    
    # Variables diàries completes per a banner.html
    VARIABLES_DIARI_COMPLETES = [
        ("TEMPERATURA_MITJANA_DIA", "Temperatura mitjana"),
        ("TEMPERATURA_MAXIMA_DIA", "Temperatura màxima"),
        ("TEMPERATURA_MINIMA_DIA", "Temperatura mínima"),
        ("HUMITAT_MITJANA_DIA", "Humitat relativa"),
        ("PRECIPITACIO_ACUM_DIA", "Precipitació acumulada"),
        ("GRUIX_NEU_MAX", "Gruix de neu màxim"),
        ("RATXA_VENT_MAX", "Ratxa màxima del vent"),
        ("PRESSIO_ATMOSFERICA", "Pressió atmosfèrica"),
        ("RADIACIO_GLOBAL", "Irradiació solar global")
    ]

# ============================================================================
# FUNCIONS DE LECTURA DE DADES
# ============================================================================
class DataLoader:
    @staticmethod
    def llegir_metadades():
        """Llegeix comarca i altitud per cada estació des de l'Excel"""
        try:
            df = pd.read_excel(Config.METADATA_FILE)
            metadades = {}
            
            for _, row in df.iterrows():
                # Assegurar que llegim des de la fila correcta
                if pd.isna(row.get('ID', None)):
                    continue
                    
                estacio_id = str(row['ID']).strip()
                comarca = str(row['Comarca']).strip() if 'Comarca' in row and pd.notna(row['Comarca']) else "Desconeguda"
                altitud = str(row['Altitud (m)']).strip() if 'Altitud (m)' in row and pd.notna(row['Altitud (m)']) else "N/D"
                
                metadades[estacio_id] = {
                    'comarca': comarca,
                    'altitud': altitud
                }
            
            print(f"✅ Metadades: {len(metadades)} estacions llegides")
            return metadades
            
        except Exception as e:
            print(f"❌ Error llegint metadades: {e}")
            return {}

    @staticmethod
    def llegir_dades_periode():
        """Llegeix les dades periòdiques del JSON"""
        try:
            with open(Config.PERIODE_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            periode_per_estacio = {}
            
            if 'dades_periode' in data:
                for p in data['dades_periode']:
                    if 'ID_ESTAC' in p:
                        estacio_id = str(p['ID_ESTAC']).strip()
                        
                        # Filtrar només les variables que necessitem
                        dades_filtrades = {}
                        for col_grup in Config.COLUMNES_ESTRUCTURA.values():
                            for var, _ in col_grup:
                                if var in p and p[var] not in ['', None]:
                                    dades_filtrades[var] = p[var]
                        
                        # Afegir metadades bàsiques
                        dades_filtrades['NOM_ESTACIO'] = p.get('NOM_ESTACIO', estacio_id)
                        dades_filtrades['DATA_UTC'] = p.get('DATA_UTC', '')
                        dades_filtrades['DATA_EXTRACCIO'] = p.get('DATA_EXTRACCIO', '')
                        dades_filtrades['PERIODE_UTC'] = p.get('PERIODE_UTC', '')
                        
                        periode_per_estacio[estacio_id] = dades_filtrades
            
            print(f"✅ Dades període: {len(periode_per_estacio)} estacions amb dades")
            return periode_per_estacio
            
        except Exception as e:
            print(f"❌ Error llegint dades període: {e}")
            return {}

    @staticmethod
    def llegir_dades_diari():
        """Llegeix les dades diàries del JSON"""
        try:
            with open(Config.DIARI_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            diari_per_estacio = {}
            
            if 'estacions' in data:
                for d in data['estacions']:
                    if 'ID_ESTAC' in d:
                        estacio_id = str(d['ID_ESTAC']).strip()
                        
                        # Agafar totes les variables diàries
                        dades_diari = {}
                        for var, _ in Config.VARIABLES_DIARI_COMPLETES:
                            if var in d and d[var] not in ['', None]:
                                dades_diari[var] = d[var]
                        
                        # Afegir metadades
                        dades_diari['NOM_ESTACIO'] = d.get('NOM_ESTACIO', estacio_id)
                        dades_diari['DATA_DIA'] = d.get('DATA_DIA', '')
                        
                        diari_per_estacio[estacio_id] = dades_diari
            
            print(f"✅ Dades diàries: {len(diari_per_estacio)} estacions amb dades")
            return diari_per_estacio
            
        except Exception as e:
            print(f"❌ Error llegint dades diàries: {e}")
            return {}

# ============================================================================
# GENERADOR HTML
# ============================================================================
class HTMLGenerator:
    @staticmethod
    def netejar_id(id_str):
        """Netega ID per a ús en noms de fitxer"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(id_str))
    
    @staticmethod
    def formatar_data(data_str):
        """Formata la data per mostrar"""
        try:
            if ' ' in data_str:
                data_part = data_str.split(' ')[0]
            else:
                data_part = data_str
                
            # Convertir de YYYY-MM-DD a DD/MM/YYYY
            parts = data_part.split('-')
            if len(parts) == 3:
                return f"{parts[2]}/{parts[1]}/{parts[0]}"
            return data_str
        except:
            return data_str
    
    @staticmethod
    def generar_head(titol="Banner Meteo.cat"):
        """Genera la secció head dels HTMLs"""
        return f"""<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titol}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* ==== ESTIL ORIGINAL PRESERVAT 100% ==== */
        body {{
            margin: 0;
            padding: 20px;
            background-color: #007BFF;
            min-height: 100vh;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        
        .meteo-overlay {{
            background: rgba(10, 25, 49, 0.95);
            border-radius: 15px;
            padding: 25px;
            color: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            max-width: 1400px;
            margin: 0 auto;
            cursor: pointer;
        }}
        
        .overlay-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid #3949ab;
        }}
        
        .station-info {{
            flex: 1;
        }}
        
        .station-name {{
            font-size: 24px;
            color: #4fc3f7;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .location-details {{
            font-size: 14px;
            color: #bbdefb;
        }}
        
        .location-label {{
            color: #7986cb;
            margin-right: 5px;
        }}
        
        .header-right {{
            text-align: right;
            flex: 1;
        }}
        
        .dual-clock-digital {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            background: transparent !important;
            padding: 0;
            border: none !important;
            min-width: 180px;
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            align-items: flex-end;
        }}
        
        .clock-row-digital {{
            display: flex;
            justify-content: flex-end;
            align-items: baseline;
            gap: 20px;
            width: 100%;
        }}
        
        .clock-time-digital {{
            color: white !important;
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 2px;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
            min-width: 85px;
            text-align: right;
        }}
        
        .clock-label-digital {{
            color: white !important;
            font-size: 16px;
            font-weight: 600;
            min-width: 35px;
            text-align: left;
        }}
        
        .header-center {{
            text-align: center;
            flex: 2;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }}
        
        .station-controls {{
            display: flex;
            align-items: center;
            gap: 15px;
            justify-content: center;
        }}
        
        .station-selector select {{
            background: linear-gradient(145deg, #1a237e, #283593) !important;
            color: #bbdefb !important;
            border: 2px solid #3949ab !important;
            border-radius: 8px;
            padding: 10px 15px;
            font-size: 14px;
            font-weight: 600;
            min-width: 300px;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            appearance: none;
            -webkit-appearance: none;
            -moz-appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23bbdefb'%3e%3cpath d='M7 10l5 5 5-5z'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right 15px center;
            background-size: 16px;
            padding-right: 40px;
        }}
        
        .station-selector select:hover {{
            border-color: #4fc3f7 !important;
            background: linear-gradient(145deg, #283593, #1a237e) !important;
        }}
        
        .station-selector select:focus {{
            outline: none;
            border-color: #2ecc71 !important;
            box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.2);
        }}
        
        .station-selector select option {{
            background: white !important;
            color: black !important;
            font-weight: 500;
            padding: 12px 15px;
            font-size: 14px;
        }}
        
        .station-selector select option:hover {{
            background: #f0f0f0 !important;
            color: #1a237e !important;
        }}
        
        .station-selector select option:checked {{
            background: #e3f2fd !important;
            color: #1a237e !important;
            font-weight: 600;
        }}
        
        .station-selector label {{
            color: #bbdefb;
            font-size: 16px;
            font-weight: bold;
            margin-right: 12px;
        }}
        
        .station-icon {{
            margin-left: 15px;
        }}
        
        .station-icon a {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(145deg, #1a237e, #283593);
            border: 2px solid #3949ab;
            border-radius: 8px;
            color: #bbdefb;
            padding: 10px 15px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .station-icon a:hover {{
            background: linear-gradient(145deg, #283593, #1a237e);
            border-color: #4fc3f7;
            color: #4fc3f7;
            transform: translateY(-2px);
            box-shadow: 0 0 15px rgba(79, 195, 247, 0.5);
        }}
        
        .icon-text {{
            display: inline;
        }}
        
        .rotation-status-container {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
        }}
        
        .rotation-status {{
            font-size: 13px;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(46, 204, 113, 0.15);
            color: #2ecc71;
            border: 1px solid #2ecc71;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        
        .rotation-status.paused {{
            background: rgba(231, 76, 60, 0.15);
            color: #e74c3c;
            border-color: #e74c3c;
        }}
        
        .overlay-content {{
            margin: 30px 0;
        }}
        
        .columns-4-container {{
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
        }}
        
        .column {{
            flex: 1;
            min-width: 200px;
        }}
        
        .col-basics {{
            padding-left: 15px;
        }}
        
        .col-precip-wind {{
            padding-left: 15px;
        }}
        
        .col-other {{
            padding-left: 15px;
        }}
        
        .col-additional {{
            padding-left: 15px;
        }}
        
        .data-column {{
            margin-bottom: 25px;
        }}
        
        .column-title {{
            color: #bbdefb;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #3949ab;
        }}
        
        .data-item {{
            background: linear-gradient(145deg, #1a237e, #283593);
            border-radius: 10px;
            padding: 12px 15px;
            margin-bottom: 12px;
            border: 2px solid #3949ab;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
            box-shadow: -5px 0 15px rgba(255, 123, 0, 0.4), 0 4px 8px rgba(0, 0, 0, 0.2);
            border-left: 4px solid #ff7b00;
        }}
        
        .data-item:hover {{
            transform: translateY(-3px);
            box-shadow: -8px 0 20px rgba(255, 123, 0, 0.6), 0 6px 12px rgba(0, 0, 0, 0.3);
            border-left-color: #ff9d4d;
        }}
        
        .data-label {{
            color: #bbdefb;
            font-weight: bold;
            font-size: 15px;
        }}
        
        .data-value {{
            color: #ffcc80;
            font-weight: bold;
            font-size: 17px;
            text-align: right;
        }}
        
        @media (max-width: 1200px) {{
            .columns-4-container {{
                flex-direction: column;
            }}
            .column {{
                min-width: 100%;
                margin-bottom: 20px;
            }}
            
            .header-center {{
                order: 3;
                width: 100%;
                margin-top: 15px;
            }}
            
            .station-controls {{
                flex-direction: column;
            }}
            
            .dual-clock-digital {{
                min-width: 160px;
            }}
            
            .clock-time-digital {{
                font-size: 20px;
                letter-spacing: 1px;
            }}
            
            .clock-label-digital {{
                font-size: 14px;
            }}
        }}
        
        /* ESTILS ESPECÍFICS PER A BANNER.HTML (llista completa) */
        .llista-estacions {{
            margin-top: 20px;
        }}
        
        .estacio-resum {{
            background: linear-gradient(145deg, #1a237e, #283593);
            border-radius: 10px;
            padding: 15px 20px;
            margin-bottom: 10px;
            border-left: 4px solid #4fc3f7;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
        }}
        
        .estacio-resum:hover {{
            border-left-color: #ff7b00;
            transform: translateX(5px);
        }}
        
        .estacio-detall {{
            background: rgba(26, 35, 126, 0.5);
            border-radius: 0 0 10px 10px;
            padding: 20px;
            display: none;
            margin-top: -10px;
            margin-bottom: 15px;
            animation: fadeIn 0.3s ease;
        }}
        
        .detall-obert {{
            display: block;
        }}
        
        .estacio-dades-diari {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #3949ab;
        }}
        
        .btn-estacio-fixa {{
            display: inline-block;
            background: linear-gradient(145deg, #ff7b00, #e56b00);
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 15px;
            transition: all 0.3s ease;
        }}
        
        .btn-estacio-fixa:hover {{
            background: linear-gradient(145deg, #ff9d4d, #ff7b00);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 123, 0, 0.4);
        }}
        
        /* Amagar la secció de resum diari a index.html */
        .day-summary {{
            display: none !important;
        }}
        
        .overlay-footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #3949ab;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
            color: #9fa8da;
        }}
        
        .footer-left, .footer-center, .footer-right {{
            flex: 1;
        }}
        
        .footer-center {{
            text-align: center;
        }}
        
        .footer-right {{
            text-align: right;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
        }}
        
        .email-icon {{
            color: #4fc3f7;
            font-size: 18px;
            vertical-align: middle;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        /* Per a mòbils */
        @media (max-width: 768px) {{
            .icon-text {{
                display: none;
            }}
            
            .station-icon a {{
                padding: 10px;
                width: 42px;
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
"""

    @staticmethod
    def generar_footer():
        """Genera el footer dels HTMLs"""
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
    <div class="overlay-footer">
        <div class="footer-left">
            <span>ℹ️ Dades extretes automàticament de Meteo.cat</span>
        </div>
        <div class="footer-center">
            <span>🔄 Rotació automàtica cada {Config.ROTATION_SECONDS}s</span>
        </div>
        <div class="footer-right">
            <span>🕐 Actualització: {hora} TU</span>
            <i class="fas fa-envelope email-icon"></i>
        </div>
    </div>
    
</body>
</html>
"""

    @staticmethod
    def generar_columnes_dades(periode_data, metadades, estacio_id, nom_estacio):
        """Genera les 4 columnes de dades per a una estació"""
        html = '<div class="columns-4-container">\n'
        
        # Columna 1: Dades bàsiques
        html += '<div class="column col-basics">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Dades bàsiques</div>\n'
        
        for var, label in Config.COLUMNES_ESTRUCTURA["basiques"]:
            if var in periode_data and periode_data[var] not in ['', None]:
                html += f'''
                <div class="data-item">
                    <div class="data-label">{label}</div>
                    <div class="data-value">{periode_data[var]}</div>
                </div>'''
        
        html += '</div>\n</div>\n'
        
        # Columna 2: Precipitació i vent
        html += '<div class="column col-precip-wind">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Precipitació i vent</div>\n'
        
        for var, label in Config.COLUMNES_ESTRUCTURA["precip_vent"]:
            if var in periode_data and periode_data[var] not in ['', None]:
                html += f'''
                <div class="data-item">
                    <div class="data-label">{label}</div>
                    <div class="data-value">{periode_data[var]}</div>
                </div>'''
        
        html += '</div>\n</div>\n'
        
        # Columna 3: Altres dades
        html += '<div class="column col-other">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Altres dades</div>\n'
        
        for var, label in Config.COLUMNES_ESTRUCTURA["altres"]:
            if var in periode_data and periode_data[var] not in ['', None]:
                html += f'''
                <div class="data-item">
                    <div class="data-label">{label}</div>
                    <div class="data-value">{periode_data[var]}</div>
                </div>'''
        
        html += '</div>\n</div>\n'
        
        # Columna 4: Dades addicionals (ocupa més espai)
        html += '<div class="column col-additional">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Dades addicionals</div>\n'
        
        # Període
        if 'PERIODE_UTC' in periode_data and periode_data['PERIODE_UTC']:
            periode_value = periode_data['PERIODE_UTC']
            if 'DATA_UTC' in periode_data and periode_data['DATA_UTC']:
                data_formated = HTMLGenerator.formatar_data(periode_data['DATA_UTC'])
                periode_value = f"Data: {data_formated} / {periode_value}"
            
            html += f'''
            <div class="data-item">
                <div class="data-label">Període:</div>
                <div class="data-value">{periode_value}</div>
            </div>'''
        
        # Altitud
        if estacio_id in metadades and 'altitud' in metadades[estacio_id]:
            html += f'''
            <div class="data-item">
                <div class="data-label">Altitud:</div>
                <div class="data-value">{metadades[estacio_id]['altitud']} m</div>
            </div>'''
        
        # Hora actualització
        if 'DATA_EXTRACCIO' in periode_data and periode_data['DATA_EXTRACCIO']:
            hora_actual = periode_data['DATA_EXTRACCIO'].split(' ')[1] if ' ' in periode_data['DATA_EXTRACCIO'] else periode_data['DATA_EXTRACCIO']
            html += f'''
            <div class="data-item">
                <div class="data-label">Hora actualització:</div>
                <div class="data-value">{hora_actual} TU</div>
            </div>'''
        
        html += '</div>\n</div>\n'
        html += '</div>\n'  # Tanca columns-4-container
        
        return html

# ============================================================================
# FUNCIONS PRINCIPALS DE GENERACIÓ
# ============================================================================
def generar_index_principal(metadades, periode_data, diari_data):
    """Genera index.html amb rotació automàtica"""
    print("🔄 Generant index.html (banner principal amb rotació)...")
    
    # Identificar estacions amb dades vàlides
    estacions_valides = []
    for estacio_id in metadades.keys():
        if estacio_id in periode_data:
            estacions_valides.append(estacio_id)
    
    if not estacions_valides:
        print("⚠️  No hi ha estacions amb dades vàlides per a index.html")
        return
    
    # Crear contingut HTML
    html = HTMLGenerator.generar_head("Banner Principal - Rotació Automàtica")
    
    # Header amb controls
    html += '''
    <div class="meteo-overlay">
        <div class="overlay-header">
            <div class="station-info">
                <div class="station-name" id="nom-estacio-actual">🏔️ BANNER PRINCIPAL</div>
                <div class="location-details" id="detalls-estacio-actual">Rotació automàtica cada ''' + str(Config.ROTATION_SECONDS) + '''s</div>
            </div>
            
            <div class="header-center">
                <div class="station-controls">
                    <div class="station-selector">
                        <label for="selectorEstacions">Estació actual:</label>
                        <select id="selectorEstacions">
    '''
    
    # Opcions del dropdown
    for estacio_id in estacions_valides:
        nom = periode_data[estacio_id].get('NOM_ESTACIO', estacio_id)
        html += f'<option value="{estacio_id}">{nom}</option>\n'
    
    html += '''
                        </select>
                    </div>
                    <div class="station-icon">
                        <a href="banner.html" title="Veure totes les estacions">
                            <i class="fas fa-list"></i>
                            <span class="icon-text">Detall</span>
                        </a>
                    </div>
                </div>
                <div class="rotation-status-container">
                    <div class="rotation-status" id="estat-rotacio">
                        <i class="fas fa-sync-alt"></i>
                        Rotació ACTIVA (''' + str(Config.ROTATION_SECONDS) + '''s)
                    </div>
                </div>
            </div>
            
            <div class="header-right">
                <div class="dual-clock-digital">
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-local">--:--</div>
                        <div class="clock-label-digital">LT</div>
                    </div>
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-utc">--:--</div>
                        <div class="clock-label-digital">TU</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="overlay-content">
            <!-- Contingut que es canviarà amb la rotació -->
            <div id="contingut-estacio-actual">
                <p>Carregant dades de les estacions...</p>
            </div>
        </div>
    '''
    
    # JavaScript per a la rotació
    html += '''
    <script>
        // Dades de totes les estacions (carregades una vegada)
        const estacions = ''' + json.dumps(estacions_valides) + ''';
        const periodeData = ''' + json.dumps(periode_data) + ''';
        const diariData = ''' + json.dumps(diari_data) + ''';
        const metadades = ''' + json.dumps(metadades) + ''';
        
        let indexActual = 0;
        let intervalRotacio = null;
        const tempsRotacio = ''' + str(Config.ROTATION_SECONDS * 1000) + ''';
        
        function mostrarEstacio(estacioId) {
            const contingutDiv = document.getElementById('contingut-estacio-actual');
            const nomDiv = document.getElementById('nom-estacio-actual');
            const detallsDiv = document.getElementById('detalls-estacio-actual');
            const selector = document.getElementById('selectorEstacions');
            
            if (periodeData[estacioId] && metadades[estacioId]) {
                const periode = periodeData[estacioId];
                const meta = metadades[estacioId];
                
                // Actualitzar nom i detalls
                nomDiv.textContent = periode.NOM_ESTACIO || estacioId;
                detallsDiv.innerHTML = `Comarca: ${meta.comarca} | Altitud: ${meta.altitud} m`;
                
                // Actualitzar selector
                selector.value = estacioId;
                
                // Generar les 4 columnes de dades
                let html = '';
                
                // Columna 1: Dades bàsiques
                html += '<div class="columns-4-container">';
                html += '<div class="column col-basics"><div class="data-column"><div class="column-title">Dades bàsiques</div>';
                
                // Dades bàsiques
                const basiques = ''' + json.dumps(Config.COLUMNES_ESTRUCTURA["basiques"]) + ''';
                basiques.forEach(([var, label]) => {
                    if (periode[var] && periode[var] !== '') {
                        html += `<div class="data-item"><div class="data-label">${label}</div><div class="data-value">${periode[var]}</div></div>`;
                    }
                });
                
                html += '</div></div>';
                
                // Columna 2: Precipitació i vent
                html += '<div class="column col-precip-wind"><div class="data-column"><div class="column-title">Precipitació i vent</div>';
                
                const precipVent = ''' + json.dumps(Config.COLUMNES_ESTRUCTURA["precip_vent"]) + ''';
                precipVent.forEach(([var, label]) => {
                    if (periode[var] && periode[var] !== '') {
                        html += `<div class="data-item"><div class="data-label">${label}</div><div class="data-value">${periode[var]}</div></div>`;
                    }
                });
                
                html += '</div></div>';
                
                // Columna 3: Altres dades
                html += '<div class="column col-other"><div class="data-column"><div class="column-title">Altres dades</div>';
                
                const altres = ''' + json.dumps(Config.COLUMNES_ESTRUCTURA["altres"]) + ''';
                altres.forEach(([var, label]) => {
                    if (periode[var] && periode[var] !== '') {
                        html += `<div class="data-item"><div class="data-label">${label}</div><div class="data-value">${periode[var]}</div></div>`;
                    }
                });
                
                html += '</div></div>';
                
                // Columna 4: Dades addicionals
                html += '<div class="column col-additional"><div class="data-column"><div class="column-title">Dades addicionals</div>';
                
                // Període
                if (periode.PERIODE_UTC) {
                    let periodeValue = periode.PERIODE_UTC;
                    if (periode.DATA_UTC) {
                        const dataParts = periode.DATA_UTC.split('-');
                        if (dataParts.length === 3) {
                            periodeValue = `Data: ${dataParts[2]}/${dataParts[1]}/${dataParts[0]} / ${periodeValue}`;
                        }
                    }
                    html += `<div class="data-item"><div class="data-label">Període:</div><div class="data-value">${periodeValue}</div></div>`;
                }
                
                // Altitud
                if (meta.altitud) {
                    html += `<div class="data-item"><div class="data-label">Altitud:</div><div class="data-value">${meta.altitud} m</div></div>`;
                }
                
                // Hora actualització
                if (periode.DATA_EXTRACCIO) {
                    const horaActual = periode.DATA_EXTRACCIO.split(' ')[1] || periode.DATA_EXTRACCIO;
                    html += `<div class="data-item"><div class="data-label">Hora actualització:</div><div class="data-value">${horaActual} TU</div></div>`;
                }
                
                html += '</div></div></div>';
                
                // Dades diàries (només les 3 especials)
                if (diariData[estacioId]) {
                    const diari = diariData[estacioId];
                    html += '<div style="margin-top: 30px; padding: 20px; background: rgba(26, 35, 126, 0.7); border-radius: 10px; border: 2px solid #5c6bc0;">';
                    html += '<div class="column-title" style="text-align: center; margin-bottom: 15px;">📅 Dades Diàries (Avui)</div>';
                    html += '<div class="day-data-container">';
                    
                    const varsDiariIndex = ''' + json.dumps(Config.VARIABLES_DIARI_INDEX) + ''';
                    varsDiariIndex.forEach(varDiari => {
                        if (diari[varDiari]) {
                            const label = varDiari.replace(/_/g, ' ');
                            html += `<div class="day-data-item"><span class="day-data-label">${label}</span><span class="day-data-value">${diari[varDiari]}</span></div>`;
                        }
                    });
                    
                    html += '</div></div>';
                }
                
                contingutDiv.innerHTML = html;
            }
        }
        
        function iniciarRotacio() {
            // Aturar interval anterior si existeix
            if (intervalRotacio) {
                clearInterval(intervalRotacio);
            }
            
            // Mostrar primera estació
            if (estacions.length > 0) {
                mostrarEstacio(estacions[0]);
                indexActual = 0;
                
                // Actualitzar estat
                document.getElementById('estat-rotacio').innerHTML = '<i class="fas fa-sync-alt"></i> Rotació ACTIVA (''' + str(Config.ROTATION_SECONDS) + '''s)';
                document.getElementById('estat-rotacio').className = 'rotation-status';
                
                // Configurar interval
                intervalRotacio = setInterval(() => {
                    indexActual = (indexActual + 1) % estacions.length;
                    mostrarEstacio(estacions[indexActual]);
                }, tempsRotacio);
            }
        }
        
        function pausarRotacio() {
            if (intervalRotacio) {
                clearInterval(intervalRotacio);
                intervalRotacio = null;
                document.getElementById('estat-rotacio').innerHTML = '<i class="fas fa-pause"></i> Rotació PAUSADA';
                document.getElementById('estat-rotacio').className = 'rotation-status paused';
            }
        }
        
        function reprendreRotacio() {
            if (!intervalRotacio) {
                iniciarRotacio();
            }
        }
        
        // Configurar events
        document.addEventListener('DOMContentLoaded', function() {
            iniciarRotacio();
            
            // Actualitzar rellotges
            function actualitzarRellotges() {
                const ara = new Date();
                
                // Hora local
                const horaLocal = ara.toLocaleTimeString('ca-ES', { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: false 
                });
                document.getElementById('hora-local').textContent = horaLocal;
                
                // Hora UTC
                const horaUTC = ara.toUTCString().split(' ')[4];
                document.getElementById('hora-utc').textContent = horaUTC;
            }
            
            actualitzarRellotges();
            setInterval(actualitzarRellotges, 1000);
            
            // Event per al selector
            document.getElementById('selectorEstacions').addEventListener('change', function(e) {
                pausarRotacio();
                mostrarEstacio(e.target.value);
                
                // Trobar l'índex de l'estació seleccionada
                const index = estacions.indexOf(e.target.value);
                if (index !== -1) {
                    indexActual = index;
                }
            });
            
            // Events per pausar/reprendre amb clic
            const overlay = document.querySelector('.meteo-overlay');
            overlay.addEventListener('click', function(e) {
                if (e.target.closest('.station-selector') || e.target.closest('.station-icon')) {
                    return; // No fer res per als controls
                }
                
                if (intervalRotacio) {
                    pausarRotacio();
                } else {
                    reprendreRotacio();
                }
            });
        });
    </script>
    '''
    
    html += HTMLGenerator.generar_footer()
    
    # Guardar fitxer
    output_path = Config.OUTPUT_DIR / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ index.html generat: {output_path}")
    return output_path

def generar_banner_html(metadades, periode_data, diari_data):
    """Genera banner.html amb totes les estacions en acordió desplegable"""
    print("🔄 Generant banner.html (detall complet)...")
    
    # Identificar estacions amb dades
    estacions_amb_dades = []
    for estacio_id in metadades.keys():
        if estacio_id in periode_data:
            estacions_amb_dades.append(estacio_id)
    
    if not estacions_amb_dades:
        print("⚠️  No hi ha estacions amb dades per a banner.html")
        return
    
    # Crear contingut HTML
    html = HTMLGenerator.generar_head("Detall complet de totes les estacions")
    
    # Header
    html += '''
    <div class="meteo-overlay">
        <div class="overlay-header">
            <div class="station-info">
                <div class="station-name">📋 Llistat complet d'estacions</div>
                <div class="location-details">Fes clic a qualsevol estació per veure totes les seves dades</div>
            </div>
            
            <div class="header-center">
                <div class="station-controls">
                    <div class="station-selector">
                        <label for="filterComarca">Filtrar per comarca:</label>
                        <select id="filterComarca">
                            <option value="">Totes les comarques</option>
    '''
    
    # Llistar totes les comarques úniques
    comarques = sorted(set([m['comarca'] for m in metadades.values() if m['comarca'] != 'Desconeguda']))
    for comarca in comarques:
        html += f'<option value="{comarca}">{comarca}</option>\n'
    
    html += '''
                        </select>
                    </div>
                    <div class="station-icon">
                        <a href="index.html" title="Tornar al banner principal">
                            <i class="fas fa-home"></i>
                            <span class="icon-text">Principal</span>
                        </a>
                    </div>
                </div>
                <div class="rotation-status-container">
                    <div class="rotation-status">
                        <i class="fas fa-list"></i>
                        ''' + str(len(estacions_amb_dades)) + ''' estacions amb dades
                    </div>
                </div>
            </div>
            
            <div class="header-right">
                <div class="dual-clock-digital">
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-local">--:--</div>
                        <div class="clock-label-digital">LT</div>
                    </div>
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-utc">--:--</div>
                        <div class="clock-label-digital">TU</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="llista-estacions" id="containerLlistaEstacions">
    '''
    
    # Generar llistat d'estacions (serà omplert per JavaScript)
    html += '''
            <!-- El JavaScript omplirà aquí les estacions -->
            <div style="text-align: center; padding: 40px; color: #bbdefb;">
                <i class="fas fa-spinner fa-spin fa-2x"></i>
                <p style="margin-top: 20px;">Carregant dades de les estacions...</p>
            </div>
        </div>
    '''
    
    # JavaScript per carregar i mostrar les dades
    html += f'''
    <script>
        // Dades per a banner.html
        const estacionsBanner = {json.dumps(estacions_amb_dades)};
        const periodeData = {json.dumps(periode_data)};
        const diariData = {json.dumps(diari_data)};
        const metadades = {json.dumps(metadades)};
        
        // Estructura de columnes
        const columnesEstructura = {json.dumps(Config.COLUMNES_ESTRUCTURA)};
        const variablesDiariCompletes = {json.dumps(Config.VARIABLES_DIARI_COMPLETES)};
        
        function generarHTMLColumna(columnaClau, columnaDades, periode, estacioId) {{
            let html = `<div class="column"><div class="data-column"><div class="column-title">${{columnaDades.titol}}</div>`;
            
            columnaDades.variables.forEach(([var, label]) => {{
                if (periode[var] && periode[var] !== '') {{
                    html += `<div class="data-item"><div class="data-label">${{label}}</div><div class="data-value">${{periode[var]}}</div></div>`;
                }}
            }});
            
            // Afegir dades especials per a columna addicional
            if (columnaClau === 'addicionals') {{
                // Altitud
                if (metadades[estacioId] && metadades[estacioId].altitud) {{
                    html += `<div class="data-item"><div class="data-label">Altitud:</div><div class="data-value">${{metadades[estacioId].altitud}} m</div></div>`;
                }}
                
                // Hora actualització
                if (periode.DATA_EXTRACCIO) {{
                    const horaActual = periode.DATA_EXTRACCIO.split(' ')[1] || periode.DATA_EXTRACCIO;
                    html += `<div class="data-item"><div class="data-label">Hora actualització:</div><div class="data-value">${{horaActual}} TU</div></div>`;
                }}
            }}
            
            html += '</div></div>';
            return html;
        }}
        
        function crearElementEstacio(estacioId) {{
            const periode = periodeData[estacioId];
            const diari = diariData[estacioId] || {{}};
            const meta = metadades[estacioId] || {{comarca: 'Desconeguda', altitud: 'N/D'}};
            const idNet = estacioId.replace(/[^a-zA-Z0-9]/g, '_');
            
            // Crear estructura d'estació
            let html = `
            <div class="estacio-resum" onclick="toggleDetall('${{estacioId}}')" data-comarca="${{meta.comarca}}">
                <div>
                    <strong>${{periode.NOM_ESTACIO || estacioId}}</strong>
                    <div style="font-size: 14px; color: #bbdefb; margin-top: 5px;">
                        Comarca: ${{meta.comarca}} | Altitud: ${{meta.altitud}} m
                    </div>
                </div>
                <i class="fas fa-chevron-down" id="icon-${{estacioId}}"></i>
            </div>
            <div class="estacio-detall" id="detall-${{estacioId}}">
                <div style="margin-bottom: 20px;">
                    <div class="columns-4-container">`;
            
            // Afegir les 4 columnes de dades del període
            const columnesInfo = {{
                basiques: {{ titol: "Dades bàsiques", variables: columnesEstructura.basiques }},
                precip_vent: {{ titol: "Precipitació i vent", variables: columnesEstructura.precip_vent }},
                altres: {{ titol: "Altres dades", variables: columnesEstructura.altres }},
                addicionals: {{ titol: "Dades addicionals", variables: columnesEstructura.addicionals }}
            }};
            
            for (const [clau, info] of Object.entries(columnesInfo)) {{
                html += generarHTMLColumna(clau, info, periode, estacioId);
            }}
            
            html += `</div></div>`;
            
            // Afegir dades diàries completes si n'hi ha
            const dadesDiariPresent = variablesDiariCompletes.some(([var, _]) => diari[var]);
            if (dadesDiariPresent) {{
                html += `
                <div class="estacio-dades-diari">
                    <div class="column-title">📅 Dades Diàries Completes (Avui)</div>
                    <div class="columns-4-container">`;
                
                // Dividir les variables diàries en 4 columnes aproximadament iguals
                const varsPerColumna = Math.ceil(variablesDiariCompletes.length / 4);
                for (let i = 0; i < 4; i++) {{
                    const startIdx = i * varsPerColumna;
                    const endIdx = startIdx + varsPerColumna;
                    const varsColumna = variablesDiariCompletes.slice(startIdx, endIdx);
                    
                    if (varsColumna.length > 0) {{
                        html += `<div class="column"><div class="data-column">`;
                        varsColumna.forEach(([var, label]) => {{
                            if (diari[var]) {{
                                html += `<div class="data-item"><div class="data-label">${{label}}:</div><div class="data-value">${{diari[var]}}</div></div>`;
                            }}
                        }});
                        html += '</div></div>';
                    }}
                }}
                
                html += `</div></div>`;
            }}
            
            // Afegir enllaç al banner fix
            html += `
                <div style="text-align: center; margin-top: 20px;">
                    <a href="index_${{idNet}}.html" class="btn-estacio-fixa">
                        <i class="fas fa-external-link-alt"></i> Veure banner fix d'aquesta estació
                    </a>
                </div>
            </div>`;
            
            return html;
        }}
        
        function carregarLlistatEstacions() {{
            const container = document.getElementById('containerLlistaEstacions');
            container.innerHTML = '';
            
            estacionsBanner.forEach(estacioId => {{
                container.innerHTML += crearElementEstacio(estacioId);
            }});
        }}
        
        function toggleDetall(estacioId) {{
            const detall = document.getElementById('detall-' + estacioId);
            const icon = document.getElementById('icon-' + estacioId);
            
            if (detall.classList.contains('detall-obert')) {{
                detall.classList.remove('detall-obert');
                icon.className = 'fas fa-chevron-down';
            }} else {{
                // Tancar altres oberts
                document.querySelectorAll('.estacio-detall.detall-obert').forEach(el => {{
                    el.classList.remove('detall-obert');
                }});
                document.querySelectorAll('.estacio-resum i').forEach(el => {{
                    el.className = 'fas fa-chevron-down';
                }});
                
                // Obrir aquest
                detall.classList.add('detall-obert');
                icon.className = 'fas fa-chevron-up';
                
                // Desplaçar-se suavement a l'estació
                detall.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}
        }}
        
        function filtrarPerComarca() {{
            const comarcaSeleccionada = document.getElementById('filterComarca').value;
            const elementsEstacio = document.querySelectorAll('.estacio-resum');
            
            elementsEstacio.forEach(element => {{
                const comarca = element.getAttribute('data-comarca');
                const estacioDetall = element.nextElementSibling;
                
                if (!comarcaSeleccionada || comarca === comarcaSeleccionada) {{
                    element.style.display = 'flex';
                    estacioDetall.style.display = element.nextElementSibling.style.display;
                }} else {{
                    element.style.display = 'none';
                    estacioDetall.style.display = 'none';
                }}
            }});
        }}
        
        // Inicialització
        document.addEventListener('DOMContentLoaded', function() {{
            // Carregar rellotges
            function actualitzarRellotges() {{
                const ara = new Date();
                const horaLocal = ara.toLocaleTimeString('ca-ES', {{ 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: false 
                }});
                document.getElementById('hora-local').textContent = horaLocal;
                
                const horaUTC = ara.toUTCString().split(' ')[4];
                document.getElementById('hora-utc').textContent = horaUTC;
            }}
            
            actualitzarRellotges();
            setInterval(actualitzarRellotges, 1000);
            
            // Carregar dades
            setTimeout(() => {{
                carregarLlistatEstacions();
                
                // Configurar filtre
                document.getElementById('filterComarca').addEventListener('change', filtrarPerComarca);
            }}, 100);
        }});
    </script>
    '''
    
    html += HTMLGenerator.generar_footer()
    
    # Guardar fitxer
    output_path = Config.OUTPUT_DIR / "banner.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ banner.html generat: {output_path}")
    return output_path

def generar_banners_individuals(metadades, periode_data, diari_data):
    """Genera un index_[ID].html per a cada estació"""
    print("🔄 Generant banners individuals per a cada estació...")
    
    banners_generats = []
    
    for estacio_id, meta in metadades.items():
        if estacio_id not in periode_data:
            continue  # Saltar estacions sense dades
        
        periode = periode_data[estacio_id]
        diari = diari_data.get(estacio_id, {})
        
        # Netejar ID per al nom de fitxer
        id_net = HTMLGenerator.netejar_id(estacio_id)
        nom_estacio = periode.get('NOM_ESTACIO', estacio_id)
        
        # Generar HTML
        html = HTMLGenerator.generar_head(f"Banner Fix - {nom_estacio}")
        
        html += f'''
    <div class="meteo-overlay">
        <div class="overlay-header">
            <div class="station-info">
                <div class="station-name">🏔️ {nom_estacio}</div>
                <div class="location-details">
                    <span class="location-label">Comarca:</span> {meta.get('comarca', 'Desconeguda')} | 
                    <span class="location-label">Altitud:</span> {meta.get('altitud', 'N/D')} m | 
                    <span class="location-label">ID:</span> {estacio_id}
                </div>
            </div>
            
            <div class="header-center">
                <div class="station-controls">
                    <div class="station-selector">
                        <label for="navEstacions">Navegar a:</label>
                        <select id="navEstacions" onchange="window.location.href=this.value">
                            <option value="">-- Selecciona una estació --</option>
        '''
        
        # Afegir opcions per a totes les estacions
        for altre_id, altre_meta in metadades.items():
            if altre_id in periode_data:
                nom_altre = periode_data[altre_id].get('NOM_ESTACIO', altre_id)
                id_net_altre = HTMLGenerator.netejar_id(altre_id)
                selected = 'selected' if altre_id == estacio_id else ''
                html += f'<option value="index_{id_net_altre}.html" {selected}>{nom_altre}</option>\n'
        
        html += '''
                        </select>
                    </div>
                    <div class="station-icon">
                        <a href="banner.html" title="Veure totes les estacions">
                            <i class="fas fa-list"></i>
                            <span class="icon-text">Totes</span>
                        </a>
                    </div>
                    <div class="station-icon">
                        <a href="index.html" title="Tornar al banner principal">
                            <i class="fas fa-home"></i>
                            <span class="icon-text">Principal</span>
                        </a>
                    </div>
                </div>
                <div class="rotation-status-container">
                    <div class="rotation-status">
                        <i class="fas fa-map-pin"></i>
                        BANNER FIX
                    </div>
                </div>
            </div>
            
            <div class="header-right">
                <div class="dual-clock-digital">
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-local">--:--</div>
                        <div class="clock-label-digital">LT</div>
                    </div>
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-utc">--:--</div>
                        <div class="clock-label-digital">TU</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="overlay-content">
        '''
        
        # Generar les 4 columnes de dades
        html += HTMLGenerator.generar_columnes_dades(periode, metadades, estacio_id, nom_estacio)
        
        # Afegir dades diàries completes
        dades_diari_present = any(var in diari for var, _ in Config.VARIABLES_DIARI_COMPLETES)
        if dades_diari_present:
            html += '''
            <div style="margin-top: 30px; padding: 25px; background: rgba(26, 35, 126, 0.7); border-radius: 10px; border: 2px solid #5c6bc0;">
                <div class="column-title" style="text-align: center; margin-bottom: 20px;">📅 Dades Diàries Completes (Avui)</div>
                <div class="columns-4-container">
            '''
            
            # Dividir les variables diàries en 4 columnes
            vars_per_columna = len(Config.VARIABLES_DIARI_COMPLETES) // 4 + 1
            for i in range(4):
                start_idx = i * vars_per_columna
                end_idx = start_idx + vars_per_columna
                vars_columna = Config.VARIABLES_DIARI_COMPLETES[start_idx:end_idx]
                
                if vars_columna:
                    html += '<div class="column"><div class="data-column">'
                    for var, label in vars_columna:
                        if var in diari and diari[var]:
                            html += f'''
                            <div class="data-item">
                                <div class="data-label">{label}:</div>
                                <div class="data-value">{diari[var]}</div>
                            </div>'''
                    html += '</div></div>'
            
            html += '''
                </div>
            </div>
            '''
        
        html += '''
        </div>
        
        <div style="margin: 30px auto; padding: 15px; background: linear-gradient(145deg, #283593, #1a237e); 
                   border-radius: 10px; border: 2px solid #3949ab; max-width: 600px; text-align: center;">
            <h3 style="color: #4fc3f7; margin-top: 0;">⚠️ AQUEST ÉS UN BANNER FIX</h3>
            <p style="color: #bbdefb;">Aquesta pàgina mostra sempre les dades d\'aquesta estació.</p>
            <p style="color: #bbdefb;">Per veure la rotació automàtica de totes les estacions, ves a <a href="index.html" style="color: #ffcc80; font-weight: bold;">index.html</a></p>
        </div>
        '''
        
        # JavaScript per als rellotges
        html += '''
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                function actualitzarRellotges() {
                    const ara = new Date();
                    
                    // Hora local
                    const horaLocal = ara.toLocaleTimeString('ca-ES', { 
                        hour: '2-digit', 
                        minute: '2-digit',
                        hour12: false 
                    });
                    document.getElementById('hora-local').textContent = horaLocal;
                    
                    // Hora UTC
                    const horaUTC = ara.toUTCString().split(' ')[4];
                    document.getElementById('hora-utc').textContent = horaUTC;
                }
                
                actualitzarRellotges();
                setInterval(actualitzarRellotges, 1000);
            });
        </script>
        '''
        
        html += HTMLGenerator.generar_footer()
        
        # Guardar fitxer
        nom_fitxer = f"index_{id_net}.html"
        output_path = Config.OUTPUT_DIR / nom_fitxer
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        banners_generats.append(output_path)
    
    print(f"✅ Generats {len(banners_generats)} banners individuals")
    return banners_generats

def copiar_estils_existents():
    """Copia estils CSS addicionals si existeixen"""
    estils_origen = Path("estils")
    estils_destinacio = Config.OUTPUT_DIR / "estils"
    
    if estils_origen.exists():
        try:
            shutil.copytree(estils_origen, estils_destinacio, dirs_exist_ok=True)
            print(f"✅ Estils copiats a {estils_destinacio}")
        except Exception as e:
            print(f"⚠️  No s'han pogut copiar els estils: {e}")

# ============================================================================
# FUNCIÓ PRINCIPAL
# ============================================================================
def main():
    print("\n" + "="*80)
    print("🚀 GENERADOR DE BANNERS METEOCAT")
    print("="*80)
    print(f"📁 Directori de sortida: {Config.OUTPUT_DIR.absolute()}")
    
    # Crear directori de sortida
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Copiar estils existents si n'hi ha
    copiar_estils_existents()
    
    # Carregar totes les dades
    print("\n📥 CARREGANT DADES...")
    metadades = DataLoader.llegir_metadades()
    periode_data = DataLoader.llegir_dades_periode()
    diari_data = DataLoader.llegir_dades_diari()
    
    if not metadades or not periode_data:
        print("❌ Dades insuficients per generar banners")
        return
    
    # Generar tots els fitxers HTML
    print("\n🛠️  GENERANT FITXERS HTML...")
    
    # 1. index.html (principal amb rotació)
    generar_index_principal(metadades, periode_data, diari_data)
    
    # 2. banner.html (detall complet amb acordió)
    generar_banner_html(metadades, periode_data, diari_data)
    
    # 3. index_[ID].html (banners individuals)
    banners_individuals = generar_banners_individuals(metadades, periode_data, diari_data)
    
    # Resum final
    print("\n" + "="*80)
    print("✅ GENERACIÓ COMPLETADA")
    print("="*80)
    print(f"📁 Fitxers generats a: {Config.OUTPUT_DIR.absolute()}")
    
    estacions_amb_dades = len([id for id in metadades.keys() if id in periode_data])
    print(f"📊 Resum:")
    print(f"   • Estacions amb metadades: {len(metadades)}")
    print(f"   • Estacions amb dades periòdiques: {len(periode_data)}")
    print(f"   • Estacions amb dades diàries: {len(diari_data)}")
    print(f"   • Estacions amb dades completes: {estacions_amb_dades}")
    print(f"   • Banners individuals generats: {len(banners_individuals)}")
    
    print("\n🎯 Recorda configurar el cron-job.org per executar els scrapers i aquest generador")
    print("   cada hora als minuts 15 i 45.")

if __name__ == "__main__":
    main()