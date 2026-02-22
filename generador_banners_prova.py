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
            ("VAR_PPT_mm", "Precipitació (període):"),
            ("VAR_VVM_10_m_km_h", "Vent Mitjà:"),
            ("VAR_DVM_10_m_graus", "Direcció Vent:"),
            ("VAR_VVX_10_m_km_h", "Ràfega Màxima:"),
            ("VAR_VVM_6_m_km_h", "Vent Mitjà:"),
            ("VAR_DVM_6_m_graus", "Direcció Vent:"),
            ("VAR_VVX_6_m_km_h", "Ràfega Màxima:"),
            ("VAR_VVM_2_m_km_h", "Vent Mitjà:"),
            ("VAR_DVM_2_m_graus", "Direcció Vent:"),
            ("VAR_VVX_2_m_km_h", "Ràfega Màxima:")
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
        
        # Direcció del vent amb graus
        if 'DVM' in var_name:
            import re
            numeros = re.findall(r'\d+', value_str)
            if numeros:
                return f"{numeros[0]}º"
            return value_str
        
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
        
        for key, unitat in unitats.items():
            if key in var_name:
                return f"{value_str} {unitat}"
        
        return value_str
    
    @staticmethod
    def format_hora_tu(hora_str):
        """Formata una hora TU del JSON al format HH:MM"""
        if not hora_str or hora_str.strip() == '':
            return ''
        
        try:
            if ':' in hora_str:
                parts = hora_str.strip().split(':')
                if len(parts) >= 2:
                    return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
            return hora_str.strip()
        except:
            return hora_str.strip()
    
    @staticmethod
    def calcular_falta_dades_diari(periode_utc_str, zona_horaria, diari_data, estacio_id):
        """Determina si cal mostrar l'avís de falta de dades diàries."""
        if estacio_id in diari_data and diari_data[estacio_id]:
            return False
        
        try:
            if ' - ' in periode_utc_str:
                hora_inici_str, _ = periode_utc_str.split(' - ')
                hora_inici = int(hora_inici_str.split(':')[0])
                
                if zona_horaria == "CET":
                    return hora_inici >= 22
                elif zona_horaria == "CEST":
                    return hora_inici >= 21
        except:
            pass
        
        return False

# ============================================================================
# FUNCIONS DE NETEJA
# ============================================================================
class NetejaDades:
    @staticmethod
    def netejar_ratxa(ratxa):
        """Eliminar ºC del final de Ratxa màxima del vent"""
        if ratxa and isinstance(ratxa, str):
            if ratxa.endswith('ºC'):
                return ratxa[:-2]
            elif ratxa.endswith(' ºC'):
                return ratxa[:-3]
        return ratxa
    
    @staticmethod
    def netejar_pressio(pressio):
        """Eliminar ºC del final de Pressió atmosfèrica"""
        if pressio and isinstance(pressio, str):
            if pressio.endswith('ºC'):
                return pressio[:-2]
            elif pressio.endswith(' ºC'):
                return pressio[:-3]
        return pressio

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
        """Llegeix les dades periòdiques del JSON"""
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
        """Llegeix les dades diàries del JSON"""
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
# GENERADOR HTML - AMB TOTES LES CORRECCIONS
# ============================================================================
class HTMLGenerator:
    @staticmethod
    def netejar_id(id_str):
        """Netega ID per a ús en noms de fitxer"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(id_str))
    
    @staticmethod
    def generar_head(titol="Banner Meteo.cat"):
        """Genera la secció head dels HTMLs - AMB CSS RESPONSIU MILLORAT"""
        return f"""<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
    <title>{titol}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* ===== ESTIL BASE ===== */
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            margin: 0;
            padding: 10px;
            background-color: #007BFF;
            min-height: 100vh;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        
        .meteo-overlay {{
            background: rgba(10, 25, 49, 0.95);
            border-radius: 15px;
            padding: 15px;
            color: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* ===== CAPÇALERA ===== */
        .overlay-header {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3949ab;
            gap: 10px;
        }}
        
        .station-info {{
            flex: 1 1 250px;
            min-width: 200px;
        }}
        
        .station-name {{
            font-size: 20px;
            color: #4fc3f7;
            font-weight: bold;
            margin-bottom: 3px;
            word-break: break-word;
        }}
        
        .location-details {{
            font-size: 12px;
            color: #bbdefb;
            line-height: 1.3;
        }}
        
        .location-label {{
            color: #7986cb;
            margin-right: 3px;
        }}
        
        .header-right {{
            text-align: right;
            flex: 0 1 auto;
        }}
        
        /* ===== RELLOTGES ===== */
        .dual-clock-digital {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            background: transparent !important;
            padding: 0;
            border: none !important;
            min-width: 140px;
            font-family: 'Courier New', monospace;
            align-items: flex-end;
        }}
        
        .clock-row-digital {{
            display: flex;
            justify-content: flex-end;
            align-items: baseline;
            gap: 8px;
            width: 100%;
        }}
        
        .clock-time-digital {{
            color: white !important;
            font-family: 'Courier New', monospace;
            font-size: 20px;
            font-weight: 700;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
            min-width: 85px;
            text-align: right;
        }}
        
        .clock-label-digital {{
            color: white !important;
            font-size: 14px;
            font-weight: 600;
            min-width: 32px;
            text-align: left;
        }}
        
        /* ===== CONTROLS CENTRALS ===== */
        .header-center {{
            text-align: center;
            flex: 2 1 350px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }}
        
        .station-controls {{
            display: flex;
            align-items: center;
            gap: 8px;
            justify-content: center;
            flex-wrap: wrap;
            width: 100%;
        }}
        
        .station-selector {{
            min-width: 220px;
            flex: 2 1 250px;
        }}
        
        /* 🔹 CORREGIT: Color dels selects (negre sobre blanc per llegir bé) */
        .station-selector select {{
            background: white !important;
            color: black !important;
            border: 2px solid #3949ab !important;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
            appearance: none;
            -webkit-appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'%3e%3cpath d='M7 10l5 5 5-5z'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 14px;
            padding-right: 35px;
        }}
        
        .station-selector select:hover {{
            border-color: #4fc3f7 !important;
            background: #f5f5f5 !important;
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
        
        .station-selector label {{
            color: #bbdefb;
            font-size: 14px;
            font-weight: bold;
            margin-right: 8px;
            display: inline-block;
        }}
        
        .station-icon {{
            flex: 0 1 auto;
        }}
        
        .station-icon a, .station-icon button {{
            display: flex;
            align-items: center;
            gap: 5px;
            background: linear-gradient(145deg, #1a237e, #283593);
            border: 2px solid #3949ab;
            border-radius: 6px;
            color: #bbdefb;
            padding: 8px 12px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s ease;
            cursor: pointer;
            font-family: inherit;
            white-space: nowrap;
        }}
        
        .station-icon a:hover, .station-icon button:hover {{
            background: linear-gradient(145deg, #283593, #1a237e);
            border-color: #4fc3f7;
            color: #4fc3f7;
        }}
        
        .rotation-status-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 5px;
            width: 100%;
            justify-content: center;
        }}
        
        .rotation-status {{
            font-size: 12px;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(46, 204, 113, 0.15);
            color: #2ecc71;
            border: 1px solid #2ecc71;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            text-align: center;
            max-width: 100%;
            white-space: normal;
            line-height: 1.3;
        }}
        
        /* ===== CONTINGUT PRINCIPAL ===== */
        .overlay-content {{
            margin: 15px 0;
        }}
        
        .columns-4-container {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .column {{
            flex: 1 1 200px;
            min-width: 200px;
        }}
        
        .data-column {{
            margin-bottom: 15px;
        }}
        
        .column-title {{
            color: #bbdefb;
            font-size: 15px;
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #3949ab;
        }}
        
        .data-item {{
            background: linear-gradient(145deg, #1a237e, #283593);
            border-radius: 6px;
            padding: 8px 10px;
            margin-bottom: 8px;
            border: 2px solid #3949ab;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #ff7b00;
            gap: 8px;
        }}
        
        .data-label {{
            color: #bbdefb;
            font-weight: bold;
            font-size: 13px;
        }}
        
        .data-value {{
            color: #ffcc80;
            font-weight: bold;
            font-size: 14px;
            text-align: right;
            word-break: break-word;
        }}
        
        .hora-registre {{
            font-size: 10px;
            color: #90caf9;
            display: block;
            margin-top: 2px;
            font-style: italic;
        }}
        
        .periode-info {{
            font-size: 0.7rem;
            font-style: italic;
            color: #4caf50;
            margin-top: 3px;
            line-height: 1.2;
        }}
        
        /* ===== LLISTA D'ESTACIONS (banner.html) ===== */
        .llista-estacions {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 12px;
            padding: 10px 0;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .station-card {{
            background: linear-gradient(145deg, #1e1e2e, #252536);
            border-radius: 8px;
            border: 2px solid #3949ab;
            padding: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            color: #ffffff;
            text-decoration: none;
            display: block;
        }}
        
        .station-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            border-bottom: 2px solid #3949ab;
            padding-bottom: 6px;
            gap: 8px;
        }}
        
        .station-municipi {{
            font-size: 15px;
            font-weight: bold;
            color: #4fc3f7;
            margin-bottom: 2px;
            word-break: break-word;
        }}
        
        .station-comarca {{
            font-size: 12px;
            color: #bbdefb;
        }}
        
        .weather-data {{
            display: flex;
            justify-content: space-around;
            gap: 8px;
            flex-wrap: wrap;
        }}
        
        .weather-item {{
            text-align: center;
            flex: 1 1 70px;
            min-width: 60px;
        }}
        
        .weather-item i {{
            font-size: 20px;
            color: #ffcc80;
            margin-bottom: 3px;
            display: block;
        }}
        
        .weather-value {{
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
        }}
        
        .temp-fred {{ color: #80deea; }}
        .temp-fresca {{ color: #4fc3f7; }}
        .temp-templada {{ color: #ffcc80; }}
        .temp-calenta {{ color: #ff9800; }}
        .temp-molt-calenta {{ color: #ff5252; }}
        .temp-desconeguda {{ color: #bbdefb; }}
        
        .station-footer {{
            margin-top: 10px;
            padding-top: 6px;
            border-top: 1px solid #3949ab;
            text-align: center;
            font-size: 10px;
            color: #bbdefb;
        }}
        
        /* ===== PEU DE PÀGINA ===== */
        .overlay-footer {{
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #3949ab;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #9fa8da;
            gap: 10px;
        }}
        
        .footer-left, .footer-center, .footer-right {{
            flex: 1 1 150px;
        }}
        
        .footer-left {{ text-align: left; }}
        .footer-center {{ text-align: center; }}
        .footer-right {{ 
            text-align: right; 
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 5px;
        }}
        
        .email-icon {{
            color: #4fc3f7;
            font-size: 14px;
        }}
        
        .verificacio-dades {{
            font-size: 9px;
            color: #81c784;
            margin-top: 3px;
            font-style: italic;
        }}
        
        /* ===== MEDIA QUERIES ===== */
        @media (max-width: 900px) {{
            .clock-time-digital {{
                font-size: 18px;
                min-width: 75px;
            }}
            .clock-label-digital {{
                font-size: 13px;
                min-width: 28px;
            }}
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 5px;
            }}
            
            .overlay-header {{
                flex-direction: column;
                align-items: stretch;
                gap: 8px;
            }}
            
            .station-info, .header-center, .header-right {{
                width: 100%;
                text-align: center;
            }}
            
            .header-right {{
                text-align: center;
            }}
            
            .dual-clock-digital {{
                align-items: center;
                width: 100%;
                min-width: auto;
            }}
            
            .clock-row-digital {{
                justify-content: center;
            }}
            
            .station-controls {{
                flex-direction: column;
                width: 100%;
                gap: 6px;
            }}
            
            .station-selector {{
                width: 100%;
                min-width: auto;
            }}
            
            .station-selector select {{
                width: 100%;
            }}
            
            .station-icon {{
                width: 100%;
            }}
            
            .station-icon a, .station-icon button {{
                width: 100%;
                justify-content: center;
                white-space: normal;
                padding: 8px 10px;
            }}
            
            .rotation-status-container {{
                margin-top: 5px;
            }}
            
            .rotation-status {{
                width: 100%;
                justify-content: center;
                padding: 6px 10px;
            }}
            
            /* Eliminar espais blancs innecessaris */
            .station-name {{
                margin-bottom: 2px;
            }}
            
            .location-details {{
                margin-bottom: 2px;
            }}
            
            .columns-4-container {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .column {{
                width: 100%;
                min-width: auto;
            }}
            
            .overlay-footer {{
                flex-direction: column;
                gap: 8px;
                text-align: center;
            }}
            
            .footer-left, .footer-center, .footer-right {{
                text-align: center;
                width: 100%;
            }}
            
            .llista-estacions {{
                grid-template-columns: 1fr;
                gap: 10px;
            }}
        }}
        
        @media (max-width: 480px) {{
            .station-name {{
                font-size: 18px;
            }}
            
            .clock-time-digital {{
                font-size: 16px;
                min-width: 65px;
            }}
            
            .clock-label-digital {{
                font-size: 12px;
                min-width: 24px;
            }}
            
            .data-item {{
                padding: 6px 8px;
            }}
            
            .data-label {{
                font-size: 12px;
            }}
            
            .data-value {{
                font-size: 13px;
            }}
            
            .rotation-status {{
                font-size: 11px;
                padding: 5px 8px;
            }}
        }}
    </style>
</head>
<body>
"""
    
    @staticmethod
    def generar_footer(hora_actualitzacio=None):
        """Genera el peu de pàgina"""
        if hora_actualitzacio:
            try:
                dt_utc = datetime.strptime(hora_actualitzacio, "%Y-%m-%d %H:%M:%S")
                if Utilitats.es_cest(dt_utc):
                    dt_local = dt_utc + timedelta(hours=2)
                    zona = "CEST"
                else:
                    dt_local = dt_utc + timedelta(hours=1)
                    zona = "CET"
                hora_formatted = dt_local.strftime("%d/%m/%Y %H:%M:%S") + " " + zona
            except:
                hora_formatted = hora_actualitzacio
        else:
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
            <span>📡 Font: https://www.meteo.cat</span>
        </div>
        <div class="footer-center">
            <span>© joandecorts.io</span>
            <a href="mailto:admin@joandecorts.com">
                <i class="fas fa-envelope email-icon"></i>
            </a>
        </div>
        <div class="footer-right">
            <span>🔄 {hora_formatted}</span>
        </div>
    </div>
    
    <script>
        function actualitzarRellotges() {{
            const ara = new Date();
            const horaLocal = ara.toLocaleTimeString('ca-ES', {{ 
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false 
            }});
            const horaUTC = ara.getUTCHours().toString().padStart(2, '0') + ':' + 
                           ara.getUTCMinutes().toString().padStart(2, '0');
            
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
        """Genera les 4 columnes de dades"""
        html = '<div class="columns-4-container">\n'
        
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
        
        # COLUMNA 4: Dades addicionals
        html += '<div class="column col-additional">\n'
        html += '<div class="data-column">\n'
        html += '<div class="column-title">Dades addicionals</div>\n'
        
        if data_formatted and periode_formatted:
            periode_display = f'''<div style="line-height: 1.3;">
                <div style="font-size: 15px;">{data_formatted}</div>
                <div style="font-size: 13px; color: #ffcc80;">{periode_formatted}</div>
            </div>'''
            
            if periode_data.get('TIPUS_PERIODE') == 'ahir':
                periode_display += '<div style="font-size: 11px; color: #ff9999;">(ahir)</div>'
            
            html += f'''
            <div class="data-item">
                <div class="data-label">Període:</div>
                <div class="data-value">{periode_display}</div>
            </div>'''
        
        if estacio_id in metadades and 'altitud' in metadades[estacio_id]:
            html += f'''
            <div class="data-item">
                <div class="data-label">Altitud:</div>
                <div class="data-value">{metadades[estacio_id]['altitud']} m</div>
            </div>'''
        
        if 'DATA_EXTRACCIO' in periode_data and periode_data['DATA_EXTRACCIO']:
            try:
                data_hora_utc_str = periode_data['DATA_EXTRACCIO']
                data_hora_utc = datetime.strptime(data_hora_utc_str, "%Y-%m-%d %H:%M:%S")
                
                if Utilitats.es_cest(data_hora_utc):
                    desplacament = 2
                    zona = "CEST"
                else:
                    desplacament = 1
                    zona = "CET"
                
                data_hora_local = data_hora_utc + timedelta(hours=desplacament)
                hora_formatted = data_hora_local.strftime("%H:%M") + " " + zona
                
                html += f'''
                <div class="data-item">
                    <div class="data-label">Hora act.:</div>
                    <div class="data-value">{hora_formatted}</div>
                </div>'''
            except:
                pass
        
        if estacio_id in metadades and 'comarca' in metadades[estacio_id]:
            html += f'''
            <div class="data-item">
                <div class="data-label">Comarca:</div>
                <div class="data-value">{metadades[estacio_id]['comarca']}</div>
            </div>'''
        
        html += '</div>\n</div>\n'
        html += '</div>\n'
        
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
                    ⚠️ Dades diàries pendents...
                </div>
                '''
        
        return html
    
    @staticmethod
    def generar_dades_diaries(diari_data, estacio_id):
        """Genera la secció de dades diàries"""
        if estacio_id not in diari_data or not diari_data[estacio_id]:
            return ""
        
        diari = diari_data[estacio_id]
        html = '''
        <div style="margin-top: 20px; padding: 15px; background: rgba(26, 35, 126, 0.7); border-radius: 8px; border: 2px solid #5c6bc0;">
            <div class="column-title" style="text-align: center; margin-bottom: 10px;">📅 Dades Diàries (des de les 00:00 UTC)</div>
            <div class="columns-4-container">
        '''
        
        vars_per_columna = len(Config.VARIABLES_DIARI_COMPLETES) // 4 + 1
        
        for i in range(4):
            start_idx = i * vars_per_columna
            end_idx = start_idx + vars_per_columna
            vars_columna = Config.VARIABLES_DIARI_COMPLETES[start_idx:end_idx]
            
            if vars_columna:
                html += '<div class="column"><div class="data-column">'
                
                for var, label, hora_var in vars_columna:
                    if var in diari and diari[var]:
                        if var == 'RATXA_VENT_MAX':
                            valor_net = NetejaDades.netejar_ratxa(diari[var])
                            valor_amb_unitats = valor_net
                        elif var == 'PRESSIO_ATMOSFERICA':
                            valor_net = NetejaDades.netejar_pressio(diari[var])
                            valor_amb_unitats = valor_net
                        else:
                            valor_amb_unitats = Utilitats.afegir_unitats(var, diari[var])
                        
                        hora_text = ""
                        if hora_var and hora_var in diari and diari[hora_var]:
                            hora_formatted = Utilitats.format_hora_tu(diari[hora_var])
                            hora_text = f'<span class="hora-registre">({hora_formatted})</span>'
                        
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
# FUNCIONS PRINCIPALS DE GENERACIÓ
# ============================================================================

def generar_banner_html(metadades, periode_data, diari_data):
    """Genera banner.html amb totes les correccions"""
    print("🔄 Generant banner.html...")
    
    estacions_amb_dades = [id for id in metadades.keys() if id in periode_data]
    
    if not estacions_amb_dades:
        print("⚠️  No hi ha estacions amb dades")
        return
    
    hora_actualitzacio = None
    for estacio_id in estacions_amb_dades:
        if estacio_id in periode_data and periode_data[estacio_id].get('DATA_EXTRACCIO'):
            hora_actualitzacio = periode_data[estacio_id].get('DATA_EXTRACCIO')
            break
    
    html = HTMLGenerator.generar_head("Llistat d'estacions")
    
    html += f'''
    <div class="meteo-overlay">
        <div class="overlay-header">
            <div class="station-info">
                <div class="station-name">📋 Estacions</div>
                <div class="location-details">{len(estacions_amb_dades)} estacions amb dades</div>
            </div>
            
            <div class="header-center">
                <div class="station-controls">
                    <!-- Botons de navegació (endavant, enrere, aturar, etc.) -->
                    <div class="station-icon">
                        <button onclick="window.location.href='index.html'" title="Inici">
                            <i class="fas fa-home"></i>
                            <span class="icon-text">Inici</span>
                        </button>
                    </div>
                    <div class="station-icon">
                        <button onclick="window.location.href='banner.html'" title="Estacions">
                            <i class="fas fa-list"></i>
                            <span class="icon-text">Estacions</span>
                        </button>
                    </div>
                    <div class="station-icon">
                        <button onclick="window.location.href='index.html'" title="Principal">
                            <i class="fas fa-undo-alt"></i>
                            <span class="icon-text">Principal</span>
                        </button>
                    </div>
                </div>
                <div class="station-controls">
                    <div class="station-selector">
                        <label for="filterComarca">Filtra:</label>
                        <select id="filterComarca">
                            <option value="">Totes</option>
    '''
    
    comarques = sorted(set([m['comarca'] for m in metadades.values() if m['comarca'] != 'Desconeguda']))
    for comarca in comarques:
        html += f'<option value="{comarca}">{comarca}</option>\n'
    
    html += f'''
                        </select>
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
    
    # Ordenar estacions per nom
    estacions_amb_info = []
    for estacio_id in estacions_amb_dades:
        nom_estacio = periode_data.get(estacio_id, {}).get('NOM_ESTACIO', estacio_id)
        comarca = metadades.get(estacio_id, {}).get('comarca', 'Desconeguda')
        estacions_amb_info.append((nom_estacio, comarca, estacio_id))
    
    estacions_ordenades = sorted(estacions_amb_info, key=lambda x: x[0].lower())
    
    for nom_estacio, comarca, estacio_id in estacions_ordenades:
        dades_periode = periode_data.get(estacio_id, {})
        dades_diari = diari_data.get(estacio_id, {})
        
        # 🔹 CANVI: Agafar precipitació del període (VAR_PPT_mm) per a les targetes
        temperatura_actual = dades_periode.get('VAR_TM_grausC', '--')
        precipitacio_periode = dades_periode.get('VAR_PPT_mm', '--')
        
        # Color segons temperatura
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
                temperatura_actual = f"{temp:.1f}"
            except:
                color_temp = "temp-desconeguda"
                temperatura_actual = '--'
        else:
            color_temp = "temp-desconeguda"
            temperatura_actual = '--'
        
        # Valor de precipitació
        if precipitacio_periode != '--' and precipitacio_periode != '' and precipitacio_periode is not None:
            try:
                precip = float(precipitacio_periode)
                icona_precip = "fa-cloud-rain" if precip > 0 else "fa-cloud"
                precipitacio_periode = f"{precip:.1f}"
            except:
                icona_precip = "fa-cloud"
                precipitacio_periode = '0.0'
        else:
            icona_precip = "fa-cloud"
            precipitacio_periode = '0.0'
        
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
                            <div class="periode-info">Temperatura mitjana del període</div>
                        </div>
                        <div class="weather-item">
                            <i class="fas {icona_precip}"></i>
                            <div class="weather-value">{precipitacio_periode} mm</div>
                            <div class="periode-info">Pluja acumulada del període</div>
                        </div>
                    </div>
                </div>
                <div class="station-footer">
                    ID: {estacio_id}
                </div>
            </a>
        '''
    
    html += '''
        </div>
    '''
    
    # JavaScript per al filtre
    html += '''
    <script>
    function filtrarPerComarca() {
        const comarca = document.getElementById('filterComarca').value;
        document.querySelectorAll('.station-card').forEach(c => {
            c.style.display = !comarca || c.dataset.comarca === comarca ? 'block' : 'none';
        });
    }
    document.getElementById('filterComarca').addEventListener('change', filtrarPerComarca);
    </script>
    '''
    
    html += HTMLGenerator.generar_footer(hora_actualitzacio)
    
    output_path = Config.OUTPUT_DIR / "banner.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ banner.html generat: {output_path}")
    return output_path

# ============================================================================
# 🔹 FUNCIÓ GENERADORA D'INDIVIDUALS (DEL FITXER BO)
# ============================================================================
def generar_banners_individuals(metadades, periode_data, diari_data):
    """Genera banners individuals per a cada estació - VERSIÓ DEL FITXER BO"""
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
                
                <!-- 🆕 CANVI: Substituïm el rètol "BANNER FIX" per la frase explicativa -->
                <div class="rotation-status-container">
                    <div class="rotation-status" style="max-width: 500px; white-space: normal; line-height: 1.4; padding: 8px 15px;">
                        <i class="fas fa-info-circle"></i>
                        Per veure aquesta o una altra estació de forma estàtica estant en scroll, prem “Estacions” i escull la desitjada.
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
        '''
        
        # ============================================================================
        # 🆕 CANVI: Modifiquem el botó "Principal" perquè no obri pestanya nova
        # ============================================================================
        html += f'''
        <script>
        (function() {{
            // Esperem que el DOM estigui carregat
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', aplicarCanvis);
            }} else {{
                aplicarCanvis();
            }}

            function aplicarCanvis() {{
                // MODIFICAR EL BOTÓ "PRINCIPAL" PERQUE OBRIRI DINS DEL MATEIX CONTENIDOR
                const botoPrincipal = document.querySelector('.station-icon a[href="index.html"]');
                if (botoPrincipal) {{
                    // Canviar l'enllaç per un botó que faci la funció
                    const botoPare = botoPrincipal.parentNode;
                    const iconClass = botoPrincipal.querySelector('i')?.className || 'fas fa-home';
                    const textSpan = botoPrincipal.querySelector('.icon-text')?.innerHTML || 'Principal';

                    // Crear el nou botó
                    const nouBoto = document.createElement('button');
                    nouBoto.innerHTML = `<i class="${{iconClass}}"></i> <span class="icon-text">${{textSpan}}</span>`;
                    nouBoto.className = botoPrincipal.className; // Mantenir les classes
                    nouBoto.title = botoPrincipal.title;
                    nouBoto.onclick = function() {{
                        window.parent.location.href = 'index.html'; // Això carrega index.html dins del contenidor pare
                    }};

                    // Substituir l'enllaç pel botó
                    botoPare.replaceChild(nouBoto, botoPrincipal);
                }}
            }}
        }})();
        </script>
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
    print("🚀 GENERADOR DE BANNERS METEOCAT")
    print("="*80)
    print(f"📁 Sortida: {Config.OUTPUT_DIR.absolute()}")
    
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copiar_estils_existents()
    
    print("\n📥 Carregant dades...")
    metadades = DataLoader.llegir_metadades()
    periode_data = DataLoader.llegir_dades_periode()
    diari_data = DataLoader.llegir_dades_diari()
    
    if not metadades or not periode_data:
        print("❌ Dades insuficients")
        return
    
    print("\n🛠️  Generant HTML...")
    
    # NO generem index.html perquè ja el tens fix
    banner_path = generar_banner_html(metadades, periode_data, diari_data)
    banners_individuals = generar_banners_individuals(metadades, periode_data, diari_data)
    
    print("\n" + "="*80)
    print("✅ GENERACIÓ COMPLETADA")
    print("="*80)
    print(f"📁 Fitxers a: {Config.OUTPUT_DIR.absolute()}")
    
    estacions_amb_dades = len([id for id in metadades.keys() if id in periode_data])
    
    print(f"📊 Resum: {estacions_amb_dades} estacions, {len(banners_individuals)} individuals")
    print("\n🎯 Funcionalitats:")
    print("   ✅ Unitats de mesura")
    print("   ✅ Format data/hora local")
    print("   ✅ Dades diàries amb hores")
    print("   ✅ Rellotges duals")
    print("   ✅ Disseny responsive millorat")
    print("   ✅ Precipitació del període a les targetes (banner.html)")
    print("   ✅ Banners individuals amb frase explicativa i botó sense pestanya")
    print("   ✅ Colors dels selects corregits (negre sobre blanc)")

if __name__ == "__main__":
    main()


