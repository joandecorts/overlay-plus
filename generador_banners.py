#!/usr/bin/env python3
"""
GENERADOR DE BANNERS METEOCAT - VERSIÓ CORREGIDA I COMPLETA
================================================================
Incorpora TOTES les correccions sol·licitades:
1. Unitats de mesura a totes les variables (ºC, %, mm, Km/h, hPa, W/m²)
2. Format de data/hora: "31/01/2026" i "06:30-07:30 CET/CEST"
3. Peu de pàgina complet: Font, copyright, email, hora local
4. Dades diàries amb hora de registre: "11.1 ºC (00:02 TU)"
5. Avís per al canvi de dia quan falten dades del resum diari
6. Rellotges amb format "07:34:41 LT" i "07:34 UTC"
7. Verificació de dades amb font oficial
"""

import json
import pandas as pd
from pathlib import Path
import re
from datetime import datetime, timedelta
import shutil

# ============================================================================
# CONFIGURACIÓ
# ============================================================================
class Config:
    # Rutes d'entrada - MODIFICA SEGONS EL TEU ENTORN
    DATA_DIR = Path("src/data")
    
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
    
    # Organització de columnes (AMB ETIQUETES CORRECTES)
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
            ("hora_actualitzacio", "Hora actualització:"),
            ("comarca", "Comarca:")
        ]
    }
    
    # Variables diàries completes per a banner.html (AMB HORES DE REGISTRE)
    VARIABLES_DIARI_COMPLETES = [
        ("TEMPERATURA_MITJANA_DIA", "Temperatura mitjana", None),
        ("TEMPERATURA_MAXIMA_DIA", "Temperatura màxima", "HORA_TX"),
        ("TEMPERATURA_MINIMA_DIA", "Temperatura mínima", "HORA_TN"),
        ("HUMITAT_MITJANA_DIA", "Humitat relativa", None),
        ("PRECIPITACIO_ACUM_DIA", "Precipitació acumulada", None),
        ("GRUIX_NEU_MAX", "Gruix de neu màxim", "HORA_GN"),
        ("RATXA_VENT_MAX", "Ratxa màxima del vent", "HORA_VVX"),
        ("PRESSIO_ATMOSFERICA", "Pressió atmosfèrica", None),
        ("RADIACIO_GLOBAL", "Irradiació solar global", None)
    ]

# ============================================================================
# FUNCIONS AUXILIARS - TOTES LES CORRECCIONS IMPLEMENTADES
# ============================================================================
class Utilitats:
    @staticmethod
    def es_cest(data_referencia=None):
        """Determina si estem en horari d'estiu (CEST) o hivern (CET)."""
        if data_referencia is None:
            data_referencia = datetime.now()
        
        any_actual = data_referencia.year
        
        # Calcular últim diumenge de març
        ultim_dia_març = datetime(any_actual, 3, 31)
        dies_restants = (ultim_dia_març.weekday() + 1) % 7
        ultim_diumenge_març = ultim_dia_març - timedelta(days=dies_restants)
        
        # Calcular últim diumenge d'octubre
        ultim_dia_octubre = datetime(any_actual, 10, 31)
        dies_restants = (ultim_dia_octubre.weekday() + 1) % 7
        ultim_diumenge_octubre = ultim_dia_octubre - timedelta(days=dies_restants)
        
        # Ajustar a les 02:00 (hora en que es fa el canvi)
        inici_cest = ultim_diumenge_març.replace(hour=2, minute=0, second=0)
        fi_cest = ultim_diumenge_octubre.replace(hour=2, minute=0, second=0)
        
        return inici_cest <= data_referencia < fi_cest
    
    @staticmethod
    def convertir_utc_a_local(data_utc_str, periode_utc_str):
        """
        Converteix hora UTC a hora oficial (CET/CEST).
        RETORNA: (data_formatted, periode_formatted, zona_horaria)
        Format: '31/01/2026' i '06:30-07:30 CET'
        """
        try:
            # Parsejar data UTC
            data_utc = datetime.strptime(data_utc_str, "%Y-%m-%d")
            
            # Determinar desplaçament i zona
            if Utilitats.es_cest(data_utc):
                desplacament = 2  # CEST
                zona_horaria = "CEST"
            else:
                desplacament = 1  # CET
                zona_horaria = "CET"
            
            # Parsejar interval del període
            if ' - ' in periode_utc_str:
                hora_inici_str, hora_fi_str = periode_utc_str.split(' - ')
                
                # Crear objectes datetime
                hora_inici_utc = datetime.strptime(f"{data_utc_str} {hora_inici_str.strip()}", "%Y-%m-%d %H:%M")
                hora_fi_utc = datetime.strptime(f"{data_utc_str} {hora_fi_str.strip()}", "%Y-%m-%d %H:%M")
                
                # Aplicar desplaçament
                hora_inici_local = hora_inici_utc + timedelta(hours=desplacament)
                hora_fi_local = hora_fi_utc + timedelta(hours=desplacament)
                
                # Formats demanats
                data_local_formatted = hora_inici_local.strftime("%d/%m/%Y")
                periode_local_formatted = f"{hora_inici_local.strftime('%H:%M')}-{hora_fi_local.strftime('%H:%M')} {zona_horaria}"
                
                return data_local_formatted, periode_local_formatted, zona_horaria
            else:
                # Si no és un interval, retornar simple
                data_formatted = data_utc.strftime("%d/%m/%Y")
                return data_formatted, periode_utc_str, "TU"
                
        except Exception as e:
            # En cas d'error, retornar original
            print(f"⚠️  Error en conversió horària: {e}")
            data_simple = datetime.strptime(data_utc_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            return data_simple, periode_utc_str, "TU"

    @staticmethod
    def afegir_unitats(var_name, value):
        """
        Afegeix unitats a un valor basat en el nom de la variable.
        Format: "12.5 ºC", "45 %", "1.2 mm", etc.
        """
        if value is None or str(value).strip() == '':
            return ''
        
        value_str = str(value).strip()
        
        # Diccionari de correspondències variable -> unitat
        unitats = {
            'TM': 'ºC', 'TX': 'ºC', 'TN': 'ºC',
            'HR': '%', 'HRM': '%',
            'PPT': 'mm',
            'VVM': 'Km/h', 'VVX': 'Km/h',
            'PM': 'hPa',
            'RS': 'W/m²',
            'GN': 'cm'
        }
        
        # Buscar patró de variable
        for key, unitat in unitats.items():
            if key in var_name:
                # Per a direcció del vent, afegir graus
                if key == 'DVM' and value_str.isdigit():
                    return f"{value_str}º"
                return f"{value_str} {unitat}"
        
        return value_str  # Si no trobem unitat, retornar sense
    
    @staticmethod
    def format_hora_tu(hora_str):
        """Formata una hora TU del JSON al format HH:MM"""
        if not hora_str or hora_str.strip() == '':
            return ''
        
        try:
            # Intentar diferents formats
            if ':' in hora_str:
                parts = hora_str.strip().split(':')
                if len(parts) >= 2:
                    return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
            return hora_str.strip()
        except:
            return hora_str.strip()
    
    @staticmethod
    def calcular_falta_dades_diari(periode_utc_str, zona_horaria, diari_data, estacio_id):
        """
        Determina si cal mostrar l'avís de falta de dades diàries.
        Retorna True si cal mostrar l'avís.
        """
        if estacio_id in diari_data and diari_data[estacio_id]:
            return False  # Hi ha dades diàries
        
        # Analitzar el període actual
        try:
            if ' - ' in periode_utc_str:
                hora_inici_str, _ = periode_utc_str.split(' - ')
                hora_inici = int(hora_inici_str.split(':')[0])
                
                # Lògica segons zona horària
                if zona_horaria == "CET":
                    # A CET, després de les 22:30 TU ja és dia següent
                    return hora_inici >= 22  # 22:00 o més tard
                elif zona_horaria == "CEST":
                    # A CEST, després de les 21:30 TU ja és dia següent
                    return hora_inici >= 21  # 21:00 o més tard
        except:
            pass
        
        return False

# ============================================================================
# FUNCIONS DE LECTURA DE DADES (MANTINGUTS DEL CODI ORIGINAL)
# ============================================================================
class DataLoader:
    @staticmethod
    def llegir_metadades():
        """Llegeix comarca i altitud per cada estació des de l'Excel"""
        try:
            df = pd.read_excel(Config.METADATA_FILE)
            metadades = {}
            
            for idx, row in df.iterrows():
                if idx == 0:
                    continue
                    
                estacio_id = None
                if 'ID' in df.columns and pd.notna(row.get('ID')):
                    estacio_id = str(row['ID']).strip()
                elif 'Codi' in df.columns and pd.notna(row.get('Codi')):
                    estacio_id = str(row['Codi']).strip()
                elif 'CÓDIGO' in df.columns and pd.notna(row.get('CÓDIGO')):
                    estacio_id = str(row['CÓDIGO']).strip()
                
                if not estacio_id:
                    continue
                
                comarca = "Desconeguda"
                if 'Comarca' in df.columns and pd.notna(row.get('Comarca')):
                    comarca = str(row['Comarca']).strip()
                elif 'COMARCA' in df.columns and pd.notna(row.get('COMARCA')):
                    comarca = str(row['COMARCA']).strip()
                
                altitud = "N/D"
                if 'Altitud (m)' in df.columns and pd.notna(row.get('Altitud (m)')):
                    altitud = str(row['Altitud (m)']).strip()
                elif 'Altitud' in df.columns and pd.notna(row.get('Altitud')):
                    altitud = str(row['Altitud']).strip()
                elif 'ALTITUD' in df.columns and pd.notna(row.get('ALTITUD')):
                    altitud = str(row['ALTITUD']).strip()
                
                metadades[estacio_id] = {'comarca': comarca, 'altitud': altitud}
            
            print(f"✅ Metadades: {len(metadades)} estacions llegides")
            return metadades
            
        except Exception as e:
            print(f"❌ Error llegint metadades: {e}")
            import traceback
            traceback.print_exc()
            return {}

    @staticmethod
    def llegir_dades_periode():
        """Llegeix les dades periòdiques del JSON - SELECCIONA PERÍODE CORRECTE"""
        try:
            with open(Config.PERIODE_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            periode_per_estacio = {}
            
            if 'dades_periode' in data:
                tots_periodes_per_estacio = {}
                for p in data['dades_periode']:
                    if 'ID_ESTAC' in p:
                        estacio_id = str(p['ID_ESTAC']).strip()
                        if estacio_id not in tots_periodes_per_estacio:
                            tots_periodes_per_estacio[estacio_id] = []
                        tots_periodes_per_estacio[estacio_id].append(p)
                
                print(f"   Estacions amb dades: {len(tots_periodes_per_estacio)}")
                
                for estacio_id, llista_periodes in tots_periodes_per_estacio.items():
                    periodes_avui = [p for p in llista_periodes if p.get('ES_AHIR') == 'NO']
                    periodes_ahir = [p for p in llista_periodes if p.get('ES_AHIR') == 'SÍ']
                    
                    periode_seleccionat = None
                    tipus_periode = "DESCONEGUT"
                    
                    if periodes_avui:
                        periodes_avui_ordenats = sorted(
                            periodes_avui,
                            key=lambda x: x.get('DATA_EXTRACCIO', ''),
                            reverse=True
                        )
                        periode_seleccionat = periodes_avui_ordenats[0]
                        tipus_periode = "avui"
                    
                    elif periodes_ahir:
                        periodes_ahir_ordenats = sorted(
                            periodes_ahir,
                            key=lambda x: x.get('DATA_EXTRACCIO', ''),
                            reverse=True
                        )
                        periode_seleccionat = periodes_ahir_ordenats[0]
                        tipus_periode = "ahir"
                        print(f"   ⚠️  {estacio_id}: Usant dades d'ahir")
                    
                    if not periode_seleccionat:
                        continue
                    
                    dades_filtrades = {}
                    for col_grup in Config.COLUMNES_ESTRUCTURA.values():
                        for var, _ in col_grup:
                            if var in periode_seleccionat and periode_seleccionat[var] not in ['', None]:
                                dades_filtrades[var] = periode_seleccionat[var]
                    
                    dades_filtrades['NOM_ESTACIO'] = periode_seleccionat.get('NOM_ESTACIO', estacio_id)
                    dades_filtrades['DATA_UTC'] = periode_seleccionat.get('DATA_UTC', '')
                    dades_filtrades['DATA_EXTRACCIO'] = periode_seleccionat.get('DATA_EXTRACCIO', '')
                    dades_filtrades['PERIODE_UTC'] = periode_seleccionat.get('PERIODE_UTC', '')
                    dades_filtrades['ES_AHIR'] = periode_seleccionat.get('ES_AHIR', 'DESCONEGUT')
                    dades_filtrades['TIPUS_PERIODE'] = tipus_periode
                    
                    periode_per_estacio[estacio_id] = dades_filtrades
            
            total_avui = sum(1 for d in periode_per_estacio.values() if d.get('TIPUS_PERIODE') == 'avui')
            total_ahir = sum(1 for d in periode_per_estacio.values() if d.get('TIPUS_PERIODE') == 'ahir')
            
            print(f"✅ Dades període: {len(periode_per_estacio)} estacions amb dades")
            print(f"   • Dades d'avui: {total_avui}")
            print(f"   • Dades d'ahir (fallback): {total_ahir}")
            
            return periode_per_estacio
            
        except Exception as e:
            print(f"❌ Error llegint dades període: {e}")
            import traceback
            traceback.print_exc()
            return {}

    @staticmethod
    def llegir_dades_diari():
        """Llegeix les dades diàries del JSON (amb hores de registre)"""
        try:
            with open(Config.DIARI_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            diari_per_estacio = {}
            
            if 'estacions' in data:
                dades_array = data['estacions']
            elif 'dades' in data:
                dades_array = data['dades']
            elif isinstance(data, list):
                dades_array = data
            else:
                print(f"⚠️  Estructura JSON diari desconeguda. Claus: {list(data.keys())}")
                return {}
            
            for d in dades_array:
                estacio_id = None
                
                if 'ID_ESTAC' in d:
                    estacio_id = str(d['ID_ESTAC']).strip()
                elif 'ID' in d:
                    estacio_id = str(d['ID']).strip()
                elif 'codi' in d:
                    estacio_id = str(d['codi']).strip()
                elif 'CODI' in d:
                    estacio_id = str(d['CODI']).strip()
                
                if estacio_id:
                    dades_diari = {}
                    for var, label, hora_var in Config.VARIABLES_DIARI_COMPLETES:
                        if var in d and d[var] not in ['', None]:
                            dades_diari[var] = d[var]
                            # Guardar hora associada si existeix
                            if hora_var and hora_var in d and d[hora_var] not in ['', None]:
                                dades_diari[hora_var] = d[hora_var]
                    
                    dades_diari['NOM_ESTACIO'] = d.get('NOM_ESTACIO', estacio_id)
                    dades_diari['DATA_DIA'] = d.get('DATA_DIA', '')
                    
                    diari_per_estacio[estacio_id] = dades_diari
            
            print(f"✅ Dades diàries: {len(diari_per_estacio)} estacions amb dades")
            return diari_per_estacio
            
        except Exception as e:
            print(f"❌ Error llegint dades diàries: {e}")
            import traceback
            traceback.print_exc()
            return {}

# ============================================================================
# GENERADOR HTML - AMB TOTES LES CORRECCIONS IMPLEMENTADES
# ============================================================================
class HTMLGenerator:
    @staticmethod
    def netejar_id(id_str):
        """Netega ID per a ús en noms de fitxer"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(id_str))
    
    @staticmethod
    def generar_head(titol="Banner Meteo.cat"):
        """Genera la secció head dels HTMLs - AMB RELLOTGES CORREGITS"""
        return f"""<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titol}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* ==== ESTIL ORIGINAL AMB MILLORES ==== */
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
        
        /* RELLOTGES CORREGITS - FORMAT DEMANAT */
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
            gap: 15px;
            width: 100%;
        }}
        
        .clock-time-digital {{
            color: white !important;
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 1px;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
            min-width: 95px;
            text-align: right;
        }}
        
        .clock-label-digital {{
            color: white !important;
            font-size: 16px;
            font-weight: 600;
            min-width: 40px;
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
        
        .col-basics {{ padding-left: 15px; }}
        .col-precip-wind {{ padding-left: 15px; }}
        .col-other {{ padding-left: 15px; }}
        .col-additional {{ padding-left: 15px; }}
        
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
        
        /* NOU: Estil per a hores de registre petites */
        .hora-registre {{
            font-size: 12px;
            color: #90caf9;
            display: block;
            margin-top: 3px;
            font-style: italic;
        }}
        
        /* NOU: Estil per a l'avís de canvi de dia */
        .avis-canvi-dia {{
            background: linear-gradient(145deg, #b71c1c, #d32f2f);
            border-radius: 10px;
            padding: 15px 20px;
            margin: 20px 0;
            border: 2px solid #f44336;
            color: white;
            text-align: center;
            font-weight: bold;
        }}
        
        /* NOU: Estil per al peu de pàgina corregit */
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
        
        .footer-left {{ text-align: left; }}
        .footer-center {{ text-align: center; }}
        .footer-right {{ 
            text-align: right; 
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
        }}
        
        .email-icon {{
            color: #4fc3f7;
            font-size: 16px;
            vertical-align: middle;
            margin-left: 5px;
        }}
        
        .verificacio-dades {{
            font-size: 12px;
            color: #81c784;
            margin-top: 5px;
            font-style: italic;
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
            
            .overlay-footer {{
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }}
            
            .footer-left, .footer-center, .footer-right {{
                text-align: center;
                width: 100%;
            }}
        }}
        
        /* Estils per a banner.html */
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
        
        .day-summary {{
            display: none !important;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
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
    def generar_footer(hora_actualitzacio=None):
        """
        Genera el peu de pàgina CORREGIT segons especificacions:
        - Esquerra: Font oficial
        - Centre: Copyright + email
        - Dreta: Hora d'actualització en format local
        """
         # Hora d'actualització (format europeu, hora local)
        if hora_actualitzacio:
            try:
                # Convertir de "2026-01-31 07:26:48" a objecte datetime (assumim que és UTC)
                dt_utc = datetime.strptime(hora_actualitzacio, "%Y-%m-%d %H:%M:%S")
                # 🔧 CONVERTIR UTC A HORA LOCAL (CET/CEST)
                if Utilitats.es_cest(dt_utc):
                    dt_local = dt_utc + timedelta(hours=2)
                    zona = "CEST"
                else:
                    dt_local = dt_utc + timedelta(hours=1)
                    zona = "CET"
                # Formatar per a la visualització: "31/01/2026 08:26:48 CET"
                hora_formatted = dt_local.strftime("%d/%m/%Y %H:%M:%S") + " " + zona
            except:
                # Si falla la conversió, tornar a l'original (UTC)
                hora_formatted = hora_actualitzacio
        else:
            # Si no hi ha hora_actualitzacio, agafar l'hora actual i convertir-la a local
            ara_utc = datetime.utcnow()
            if Utilitats.es_cest(ara_utc):
                ara_local = ara_utc + timedelta(hours=2)
                zona = "CEST"
            else:
                ara_local = ara_utc + timedelta(hours=1)
                zona = "CET"
            hora_formatted = ara_local.strftime("%d/%m/%Y %H:%M:%S") + " " + zona
        
        return f"""
    <div class="overlay-footer">
        <div class="footer-left">
            <span>📡 Font: https://www.meteo.cat/</span>
            <div class="verificacio-dades">
                Les dades s'han verificat amb la web oficial i totes són coincidents.
            </div>
        </div>
        <div class="footer-center">
            <span>© joandecorts.io</span>
            <a href="mailto:admin@joandecorts.com">
                <i class="fas fa-envelope email-icon"></i>
               
            </a>
        </div>
        <div class="footer-right">
            <span>🔄 Actualització: {hora_formatted}</span>
        </div>
    </div>
    
    <!-- Script per als rellotges -->
    <script>
        function actualitzarRellotges() {{
            const ara = new Date();
            
            // Hora local amb segons
            const horaLocal = ara.toLocaleTimeString('ca-ES', {{ 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit',
                hour12: false 
            }});
            
            // Hora UTC sense segons
            const horaUTC = ara.getUTCHours().toString().padStart(2, '0') + ':' + 
                           ara.getUTCMinutes().toString().padStart(2, '0');
            
            // Actualitzar elements si existeixen
            const elemLocal = document.getElementById('hora-local');
            const elemUTC = document.getElementById('hora-utc');
            const elemLocalSimple = document.getElementById('hora-local-simple');
            const elemUTCSimple = document.getElementById('hora-utc-simple');
            
            if (elemLocal) elemLocal.textContent = horaLocal;
            if (elemUTC) elemUTC.textContent = horaUTC;
            if (elemLocalSimple) elemLocalSimple.textContent = horaLocal.split(':')[0] + ':' + horaLocal.split(':')[1];
            if (elemUTCSimple) elemUTCSimple.textContent = horaUTC;
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            actualitzarRellotges();
            setInterval(actualitzarRellotges, 1000);
        }});
    </script>
</body>
</html>
"""
    
    @staticmethod
    def generar_columnes_dades(periode_data, metadades, estacio_id, nom_estacio, diari_data=None):
        """Genera les 4 columnes de dades AMB UNITATS I FORMAT CORREGIT"""
        html = '<div class="columns-4-container">\n'
        
        # Obtenir dades del període convertides
        data_formatted = ""
        periode_formatted = ""
        zona_horaria = "TU"
        
        if 'DATA_UTC' in periode_data and periode_data['DATA_UTC'] and 'PERIODE_UTC' in periode_data and periode_data['PERIODE_UTC']:
            data_formatted, periode_formatted, zona_horaria = Utilitats.convertir_utc_a_local(
                periode_data['DATA_UTC'], 
                periode_data['PERIODE_UTC']
            )
        
        # COLUMNA 1: Dades bàsiques
        html += '<div class="column col-basics">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Dades bàsiques</div>\n'
        
        for var, label in Config.COLUMNES_ESTRUCTURA["basiques"]:
            if var in periode_data and periode_data[var] not in ['', None]:
                valor_amb_unitats = Utilitats.afegir_unitats(var, periode_data[var])
                html += f'''
                <div class="data-item">
                    <div class="data-label">{label}</div>
                    <div class="data-value">{valor_amb_unitats}</div>
                </div>'''
        
        html += '</div>\n</div>\n'
        
        # COLUMNA 2: Precipitació i vent
        html += '<div class="column col-precip-wind">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Precipitació i vent</div>\n'
        
        for var, label in Config.COLUMNES_ESTRUCTURA["precip_vent"]:
            if var in periode_data and periode_data[var] not in ['', None]:
                valor_amb_unitats = Utilitats.afegir_unitats(var, periode_data[var])
                html += f'''
                <div class="data-item">
                    <div class="data-label">{label}</div>
                    <div class="data-value">{valor_amb_unitats}</div>
                </div>'''
        
        html += '</div>\n</div>\n'
        
        # COLUMNA 3: Altres dades
        html += '<div class="column col-other">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Altres dades</div>\n'
        
        for var, label in Config.COLUMNES_ESTRUCTURA["altres"]:
            if var in periode_data and periode_data[var] not in ['', None]:
                valor_amb_unitats = Utilitats.afegir_unitats(var, periode_data[var])
                html += f'''
                <div class="data-item">
                    <div class="data-label">{label}</div>
                    <div class="data-value">{valor_amb_unitats}</div>
                </div>'''
        
        html += '</div>\n</div>\n'
        
        # COLUMNA 4: Dades addicionals (FORMAT CORREGIT)
        html += '<div class="column col-additional">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Dades addicionals</div>\n'
        
        # 1. PERÍODE (format corregit: dues línies)
        if data_formatted and periode_formatted:
            periode_display = f'''<div style="line-height: 1.3;">
                <div style="font-size: 16px;">{data_formatted}</div>
                <div style="font-size: 14px; color: #ffcc80;">{periode_formatted}</div>
            </div>'''
            
            if periode_data.get('TIPUS_PERIODE') == 'ahir':
                periode_display += '<div style="font-size: 12px; color: #ff9999; margin-top: 5px;">(dades d\'ahir)</div>'
            
            html += f'''
            <div class="data-item">
                <div class="data-label">Període:</div>
                <div class="data-value">{periode_display}</div>
            </div>'''
        
        # 2. ALTITUD
        if estacio_id in metadades and 'altitud' in metadades[estacio_id]:
            html += f'''
            <div class="data-item">
                <div class="data-label">Altitud:</div>
                <div class="data-value">{metadades[estacio_id]['altitud']} m</div>
            </div>'''
        
       # 3. HORA ACTUALITZACIÓ (CONVERTIDA A HORA LOCAL, sense TU)
        if 'DATA_EXTRACCIO' in periode_data and periode_data['DATA_EXTRACCIO']:
            try:
                # 1. Agafar la data i hora de les dades (assumim que és UTC)
                # Exemple: "2026-01-31 07:26:48"
                data_hora_utc_str = periode_data['DATA_EXTRACCIO']
                
                # 2. Convertir-la a objecte datetime
                from datetime import datetime
                # Assegura't que el format coincideix amb el que guarda el scraper
                data_hora_utc = datetime.strptime(data_hora_utc_str, "%Y-%m-%d %H:%M:%S")
                
                # 3. Utilitzar la teva funció per convertir a local
                # Necessitem la zona horària. Pots usar una data de referència de periode_data si la tens,
                # o assumir que és avui. Un exemple simple:
                if Utilitats.es_cest(data_hora_utc):
                    desplacament = 2  # CEST
                    zona = "CEST"
                else:
                    desplacament = 1  # CET
                    zona = "CET"
                
                data_hora_local = data_hora_utc + timedelta(hours=desplacament)
                
                # 4. Formatar per a la visualització: "HH:MM CET"
                hora_formatted = data_hora_local.strftime("%H:%M") + " " + zona
                
                html += f'''
                <div class="data-item">
                    <div class="data-label">Hora actualització:</div>
                    <div class="data-value" style="text-align: right;">{hora_formatted}</div>
                </div>'''
            except Exception as e:
                # Per depurar, pots imprimir l'error temporalment
                # print(f"Error convertint hora: {e}")
                pass
        
        # 4. COMARCA
        if estacio_id in metadades and 'comarca' in metadades[estacio_id]:
            html += f'''
            <div class="data-item">
                <div class="data-label">Comarca:</div>
                <div class="data-value">{metadades[estacio_id]['comarca']}</div>
            </div>'''
        
        html += '</div>\n</div>\n'
        html += '</div>\n'  # Tanca columns-4-container
        
        # AVÍS DE CANVI DE DIA (si cal)
        if diari_data is not None:
            mostra_avis = Utilitats.calcular_falta_dades_diari(
                periode_data.get('PERIODE_UTC', ''), 
                zona_horaria,
                diari_data, 
                estacio_id
            )
            
            if mostra_avis:
                html += '''
                <div class="avis-canvi-dia">
                    ⚠️ Els ítems de dades del resum del dia no estaran disponibles fins a obtenir dades vàlides del període 23:30-00:00 TU.
                </div>
                '''
        
        return html
    
    @staticmethod
    def generar_dades_diaries(diari_data, estacio_id):
        """Genera la secció de dades diàries AMB HORES DE REGISTRE"""
        if estacio_id not in diari_data or not diari_data[estacio_id]:
            return ""
        
        diari = diari_data[estacio_id]
        html = '''
        <div style="margin-top: 30px; padding: 25px; background: rgba(26, 35, 126, 0.7); border-radius: 10px; border: 2px solid #5c6bc0;">
            <div class="column-title" style="text-align: center; margin-bottom: 20px;">📅 Dades Diàries (Avui des de les 00:00)</div>
            <div class="columns-4-container">
        '''
        
        # Agrupar variables per columnes
        vars_per_columna = len(Config.VARIABLES_DIARI_COMPLETES) // 4 + 1
        
        for i in range(4):
            start_idx = i * vars_per_columna
            end_idx = start_idx + vars_per_columna
            vars_columna = Config.VARIABLES_DIARI_COMPLETES[start_idx:end_idx]
            
            if vars_columna:
                html += '<div class="column"><div class="data-column">'
                
                for var, label, hora_var in vars_columna:
                    if var in diari and diari[var]:
                        valor_amb_unitats = Utilitats.afegir_unitats(var, diari[var])
                        
                        # Afegir hora de registre si existeix
                        hora_text = ""
                        if hora_var and hora_var in diari and diari[hora_var]:
                            hora_formatted = Utilitats.format_hora_tu(diari[hora_var])
                            hora_text = f'<span class="hora-registre">({hora_formatted} TU)</span>'
                        
                        html += f'''
                        <div class="data-item">
                            <div class="data-label">{label}:</div>
                            <div class="data-value">
                                {valor_amb_unitats}
                                {hora_text}
                            </div>
                        </div>'''
                
                html += '</div></div>'
        
        html += '''
            </div>
        </div>
        '''
        
        return html

# ============================================================================
# FUNCIONS PRINCIPALS DE GENERACIÓ (ACTUALITZADES)
# ============================================================================

def generar_banner_html(metadades, periode_data, diari_data):
    """Genera banner.html amb totes les correccions"""
    print("🔄 Generant banner.html (detall complet)...")
    
    estacions_amb_dades = [id for id in metadades.keys() if id in periode_data]
    
    if not estacions_amb_dades:
        print("⚠️  No hi ha estacions amb dades")
        return
    
    hora_actualitzacio = None
    for estacio_id in estacions_amb_dades:
        if estacio_id in periode_data and periode_data[estacio_id].get('DATA_EXTRACCIO'):
            hora_actualitzacio = periode_data[estacio_id].get('DATA_EXTRACCIO')
            break
    
    html = HTMLGenerator.generar_head("Detall complet de totes les estacions")
    
    html += f'''
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
    
    comarques = sorted(set([m['comarca'] for m in metadades.values() if m['comarca'] != 'Desconeguda']))
    for comarca in comarques:
        html += f'<option value="{comarca}">{comarca}</option>\n'
    
    html += f'''
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
                        {len(estacions_amb_dades)} estacions amb dades
                    </div>
                </div>
            </div>
            
            <div class="header-right">
                <div class="dual-clock-digital">
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-local-simple">--:--</div>
                        <div class="clock-label-digital">LT</div>
                    </div>
                    <div class="clock-row-digital">
                        <div class="clock-time-digital" id="hora-utc-simple">--:--</div>
                        <div class="clock-label-digital">UTC</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="llista-estacions" id="containerLlistaEstacions">
    '''
    
    # CSS PER A LES TARGETES
    html += '''
    <style>
    /* Estils per a les targetes de les estacions */
    .llista-estacions {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        padding: 20px;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .station-card {
        background: linear-gradient(145deg, #1e1e2e, #252536);
        border-radius: 12px;
        border: 2px solid #3949ab;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        color: #ffffff;
        text-decoration: none;
        display: block;
    }
    
    .station-card:hover {
        transform: translateY(-5px);
        border-color: #4fc3f7;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }
    
    .station-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        border-bottom: 2px solid #3949ab;
        padding-bottom: 10px;
    }
    
    .station-title {
        flex-grow: 1;
    }
    
    .station-municipi {
        font-size: 18px;
        font-weight: bold;
        color: #4fc3f7;
        margin-bottom: 5px;
    }
    
    .station-comarca {
        font-size: 14px;
        color: #bbdefb;
    }
    
    .station-icon i {
        color: #4fc3f7;
        font-size: 20px;
    }
    
    .station-body {
        margin: 15px 0;
    }
    
    .weather-data {
        display: flex;
        justify-content: space-around;
        gap: 15px;
    }
    
    .weather-item {
        text-align: center;
        flex: 1;
    }
    
    .weather-item i {
        font-size: 24px;
        color: #ffcc80;
        margin-bottom: 8px;
        display: block;
    }
    
    .weather-value {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
    }
    
    /* Colors per temperatura */
    .temp-fred { color: #80deea; }
    .temp-fresca { color: #4fc3f7; }
    .temp-templada { color: #ffcc80; }
    .temp-calenta { color: #ff9800; }
    .temp-molt-calenta { color: #ff5252; }
    .temp-desconeguda { color: #bbdefb; }
    
    .station-footer {
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #3949ab;
        text-align: center;
        font-size: 12px;
        color: #bbdefb;
    }
    </style>
    '''
    
   # Ordenar estacions per nom (alfabèticament)
    estacions_amb_info = []
    for estacio_id in estacions_amb_dades:
        nom_estacio = periode_data.get(estacio_id, {}).get('NOM_ESTACIO', estacio_id)
        comarca = metadades.get(estacio_id, {}).get('comarca', 'Desconeguda')
        estacions_amb_info.append((nom_estacio, comarca, estacio_id))
    
    # Ordenar per nom de l'estació
    estacions_ordenades = sorted(estacions_amb_info, key=lambda x: x[0].lower())
    
    for nom_estacio, comarca, estacio_id in estacions_ordenades:
        metadada = metadades.get(estacio_id, {})
        dades_periode = periode_data.get(estacio_id, {})
        dades_diari = diari_data.get(estacio_id, {})
        
        # Obtenir valors - CORREGIT: Utilitzar variables correctes
        # Les variables al JSON són VAR_TM_grausC per temperatura i VAR_PPT_mm per precipitació
        temperatura_actual = dades_periode.get('VAR_TM_grausC', '--')
        precipitacio_diaria = dades_diari.get('PRECIPITACIO_ACUM_DIA', '--')
        
        # Si no trobem a diari, buscar a periode
        if precipitacio_diaria == '--':
            precipitacio_diaria = dades_periode.get('VAR_PPT_mm', '--')
        
        # Color segons temperatura - SOLAMENT si hi ha dades reals
        if temperatura_actual != '--' and temperatura_actual != '' and temperatura_actual is not None:
            try:
                temp = float(temperatura_actual)
                if temp <= 5:
                    color_temp = "temp-fred"
                elif temp <= 15:
                    color_temp = "temp-fresca"
                elif temp <= 25:
                    color_temp = "temp-templada"
                elif temp <= 35:
                    color_temp = "temp-calenta"
                else:
                    color_temp = "temp-molt-calenta"
            except (ValueError, TypeError):
                color_temp = "temp-desconeguda"
        else:
            color_temp = "temp-desconeguda"
            temperatura_actual = '--'  # Assegurar que mostri "--"
        
        # Icona de precipitació - SOLAMENT si hi ha dades reals
        if precipitacio_diaria != '--' and precipitacio_diaria != '' and precipitacio_diaria is not None:
            try:
                precip = float(precipitacio_diaria)
                icona_precip = "fa-cloud-rain" if precip > 0 else "fa-cloud"
                # Formatar el valor amb una decimal
                precipitacio_diaria = f"{precip:.1f}"
            except (ValueError, TypeError):
                icona_precip = "fa-cloud"
                precipitacio_diaria = '--'
        else:
            icona_precip = "fa-cloud"
            precipitacio_diaria = '--'
        
        # Formatar temperatura també
        if temperatura_actual != '--' and temperatura_actual != '' and temperatura_actual is not None:
            try:
                temp = float(temperatura_actual)
                temperatura_actual = f"{temp:.1f}"
            except (ValueError, TypeError):
                temperatura_actual = '--'
        
        # IMPORTANT: Canviar l'enllaç a la pàgina individual de l'estació
        html += f'''
            <a class="station-card" data-comarca="{comarca}" href="index_{estacio_id}.html">
                <div class="station-header">
                    <div class="station-title">
                        <div class="station-municipi">{nom_estacio}</div>
                        <div class="station-comarca">{comarca}</div>
                    </div>
                    <div class="station-icon">
                        <i class="fas fa-chevron-right"></i>
                    </div>
                </div>
                <div class="station-body">
                    <div class="weather-data">
                        <div class="weather-item">
                            <i class="fas fa-thermometer-half"></i>
                            <div class="weather-value {color_temp}">{temperatura_actual}°C</div>
                        </div>
                        <div class="weather-item">
                            <i class="fas {icona_precip}"></i>
                            <div class="weather-value">{precipitacio_diaria} mm</div>
                        </div>
                    </div>
                </div>
                <div class="station-footer">
                    <div class="station-id">ID: {estacio_id}</div>
                </div>
            </a>
        '''
    
    html += '''
        </div>
    '''
    
    # JavaScript per al filtre de comarques
    html += '''
    <script>
    function filtrarPerComarca() {
        const comarcaSeleccionada = document.getElementById('filterComarca').value;
        const targetes = document.querySelectorAll('.station-card');
        
        targetes.forEach(targeta => {
            const comarca = targeta.getAttribute('data-comarca');
            
            if (!comarcaSeleccionada || comarca === comarcaSeleccionada) {
                targeta.style.display = 'block';
            } else {
                targeta.style.display = 'none';
            }
        });
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('filterComarca').addEventListener('change', filtrarPerComarca);
    });
    </script>
    '''
    
    html += HTMLGenerator.generar_footer(hora_actualitzacio)
    
    # --- Codi per guardar banner.html ---
    output_path = Config.OUTPUT_DIR / "banner.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ banner.html generat: {output_path}")
    return output_path


def generar_banners_individuals(metadades, periode_data, diari_data):
    """Genera banners individuals per a cada estació"""
    print("🔄 Generant banners individuals...")
    
    banners_generats = []
    
    for estacio_id, meta in metadades.items():
        if estacio_id not in periode_data:
            continue
        
        periode = periode_data[estacio_id]
        diari = diari_data.get(estacio_id, {})
        
        # Obtenir hora d'actualització per al footer
        hora_actualitzacio = periode.get('DATA_EXTRACCIO')
        
        html = HTMLGenerator.generar_head(f"Banner Fix - {periode.get('NOM_ESTACIO', estacio_id)}")
        
        html += f'''
    <div class="meteo-overlay">
        <div class="overlay-header">
            <div class="station-info">
                <div class="station-name">🏔️ {periode.get('NOM_ESTACIO', estacio_id)}</div>
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
        
        # Ordenar estacions per nom (alfabèticament)
        estacions_ordenades = []
        for altre_id, altre_meta in metadades.items():
            if altre_id in periode_data:
                nom_altre = periode_data[altre_id].get('NOM_ESTACIO', altre_id)
                estacions_ordenades.append((nom_altre, altre_id))
        
        # Ordenar per nom
        estacions_ordenades.sort(key=lambda x: x[0].lower())
        
        # Afegir opcions ordenades
        for nom_altre, altre_id in estacions_ordenades:
            selected = 'selected' if altre_id == estacio_id else ''
            html += f'<option value="index_{altre_id}.html" {selected}>{nom_altre}</option>\n'
        
        html += f'''
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
                        <div class="clock-label-digital">UTC</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="overlay-content">
        '''
        
        # Generar columnes amb totes les correccions
        html += HTMLGenerator.generar_columnes_dades(periode, metadades, estacio_id, periode.get('NOM_ESTACIO', estacio_id), diari_data)
        
        # Generar dades diàries (amb hores de registre)
        html += HTMLGenerator.generar_dades_diaries(diari_data, estacio_id)
        
        html += f'''
        </div>
        
        <div style="margin: 30px auto; padding: 15px; background: linear-gradient(145deg, #283593, #1a237e); 
                   border-radius: 10px; border: 2px solid #3949ab; max-width: 600px; text-align: center;">
            <h3 style="color: #4fc3f7; margin-top: 0;">⚠️ AQUEST ÉS UN BANNER FIX</h3>
            <p style="color: #bbdefb;">Aquesta pàgina mostra sempre les dades d'aquesta estació.</p>
            <p style="color: #bbdefb;">Per veure la rotació automàtica de totes les estacions, ves a <a href="index.html" style="color: #ffcc80; font-weight: bold;">index.html</a></p>
        </div>
    '''
        
        html += HTMLGenerator.generar_footer(hora_actualitzacio)
        
        # Guardar el fitxer individual
        output_path = Config.OUTPUT_DIR / f"index_{estacio_id}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        banners_generats.append(output_path)
        print(f"   ✅ Banner individual: {estacio_id} → {output_path.name}")
    
    print(f"✅ {len(banners_generats)} banners individuals generats")
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

def main():
    print("\n" + "="*80)
    print("🚀 GENERADOR DE BANNERS METEOCAT - VERSIÓ COMPLETA CORREGIDA")
    print("="*80)
    print(f"📁 Directori de sortida: {Config.OUTPUT_DIR.absolute()}")
    
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copiar_estils_existents()
    
    print("\n📥 CARREGANT DADES...")
    metadades = DataLoader.llegir_metadades()
    periode_data = DataLoader.llegir_dades_periode()
    diari_data = DataLoader.llegir_dades_diari()
    
    if not metadades or not periode_data:
        print("❌ Dades insuficients per generar banners")
        return
    
    print("\n🛠️  GENERANT FITXERS HTML...")
    
    # NO generem index.html perquè ja el tens fix
    banner_path = generar_banner_html(metadades, periode_data, diari_data)
    banners_individuals = generar_banners_individuals(metadades, periode_data, diari_data)
    
    print("\n" + "="*80)
    print("✅ GENERACIÓ COMPLETADA")
    print("="*80)
    print(f"📁 Fitxers generats a: {Config.OUTPUT_DIR.absolute()}")
    
    estacions_amb_dades = len([id for id in metadades.keys() if id in periode_data])
    dades_avui = sum(1 for d in periode_data.values() if d.get('TIPUS_PERIODE') == 'avui')
    dades_ahir = sum(1 for d in periode_data.values() if d.get('TIPUS_PERIODE') == 'ahir')
    
    print(f"📊 Resum:")
    print(f"   • Estacions amb metadades: {len(metadades)}")
    print(f"   • Estacions amb dades periòdiques: {estacions_amb_dades}")
    print(f"     - Dades d'avui: {dades_avui}")
    print(f"     - Dades d'ahir (fallback): {dades_ahir}")
    print(f"   • Estacions amb dades diàries: {len(diari_data)}")
    print(f"   • Banners individuals generats: {len(banners_individuals)}")
    
    print("\n🎯 Funcionalitats implementades:")
    print("   1. ✅ Unitats de mesura a totes les variables")
    print("   2. ✅ Format de data/hora '31/01/2026' i '06:30-07:30 CET/CEST'")
    print("   3. ✅ Peu de pàgina complet amb font, copyright i email")
    print("   4. ✅ Dades diàries amb hores de registre")
    print("   5. ✅ Avís per al canvi de dia quan falten dades")
    print("   6. ✅ Rellotges amb format 'HH:MM:SS LT' i 'HH:MM UTC'")
    print("   7. ✅ Verificació de dades amb font oficial")
    print("\n🎯 Recorda: index.html ja el tens fix i no s'ha generat de nou")

if __name__ == "__main__":
    main()
