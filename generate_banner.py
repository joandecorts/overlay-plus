#!/usr/bin/env python3
"""
generate_banner.py - Overlay Plus
Genera latest_meteo_data.xlsx i actualitza index.html amb dades reals.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# ============================================================================
# CONFIGURACIÓ - AJUSTA AQUESTES RUTES SI CAL
# ============================================================================
CONFIG_DIR = 'config'                     # On està config_banner.py
SCRAPED_DATA_DIR = 'src/data'             # On els teus scrapers guarden .json individuals
OUTPUT_DATA_DIR = 'src/data'              # On es guardaran latest_meteo_data.*
HTML_FILE = 'index.html'                  # El teu overlay principal

# ============================================================================
# 1. IMPORTAR CONFIGURACIÓ
# ============================================================================
sys.path.insert(0, CONFIG_DIR)
try:
    from config_banner import STATIONS
    print(f"✅ Configuració carregada. Estacions actives: {len(STATIONS)}")
except ImportError as e:
    print(f"❌ Error important config_banner.py: {e}")
    sys.exit(1)

# ============================================================================
# 2. LLEGIR DADES DELS SCRAPERS (.json individuals)
# ============================================================================
def llegir_dades_scrapers():
    """Llegeix els fitxers JSON que els teus scrapers han generat."""
    dades_estacions = []
    
    for estacio in STATIONS:
        # Ruta esperada: src/data/CODESTACIO.json (ex: src/data/XJ.json)
        ruta_fitxer = os.path.join(SCRAPED_DATA_DIR, f"{estacio['code']}.json")
        
        # Valors per defecte
        dades_estacio = {
            'code': estacio['code'],
            'display_name': estacio['display_name'],
            'TX': '--',   # Temperatura màxima
            'TN': '--',   # Temperatura mínima
            'PPT': '--',  # Precipitació
            'updated': datetime.now().strftime('%H:%M')
        }
        
        try:
            with open(ruta_fitxer, 'r', encoding='utf-8') as f:
                dades = json.load(f)
                # Suposem que el JSON té les claus 'TX', 'TN', 'PPT'
                dades_estacio.update({
                    'TX': dades.get('TX', '--'),
                    'TN': dades.get('TN', '--'),
                    'PPT': dades.get('PPT', '--')
                })
            print(f"   ✅ {estacio['code']}: {dades_estacio['TX']}°C / {dades_estacio['TN']}°C")
        except FileNotFoundError:
            print(f"   ⚠️  {estacio['code']}: No s'ha trobat {ruta_fitxer}")
        except Exception as e:
            print(f"   ⚠️  {estacio['code']}: Error llegint dades ({e})")
        
        dades_estacions.append(dades_estacio)
    
    return dades_estacions

# ============================================================================
# 3. GENERAR FITXERS UNIFICATS (latest_meteo_data.*)
# ============================================================================
def generar_fitxers_unificats(dades):
    """Genera latest_meteo_data.xlsx, .json i .csv"""
    # Crear DataFrame
    df = pd.DataFrame(dades)
    
    # Assegurar columnes necessàries
    columnes = ['display_name', 'code', 'TX', 'TN', 'PPT', 'updated']
    for col in columnes:
        if col not in df.columns:
            df[col] = '--'
    
    # Excel (el que més ens interessa)
    ruta_excel = os.path.join(OUTPUT_DATA_DIR, 'latest_meteo_data.xlsx')
    df.to_excel(ruta_excel, index=False)
    
    # JSON
    ruta_json = os.path.join(OUTPUT_DATA_DIR, 'latest_meteo_data.json')
    df.to_json(ruta_json, orient='records', force_ascii=False, indent=2)
    
    # CSV
    ruta_csv = os.path.join(OUTPUT_DATA_DIR, 'latest_meteo_data.csv')
    df.to_csv(ruta_csv, index=False, encoding='utf-8')
    
    print(f"\n📁 Fitxers generats a {OUTPUT_DATA_DIR}/")
    print(f"   📊 latest_meteo_data.xlsx ({len(df)} estacions)")
    print(f"   📋 latest_meteo_data.json")
    print(f"   📄 latest_meteo_data.csv")
    
    return df

# ============================================================================
# 4. MODIFICAR L'INDEX.HTML (LA PART MÉS IMPORTANT)
# ============================================================================
def actualitzar_html(dades):
    """
    Reemplaça les 4 targetes fixes del index.html per les 33 estacions reals.
    AQUEST Codi ESTÀ AJUSTAT AL TEU HTML EXACTE.
    """
    try:
        with open(HTML_FILE, 'r', encoding='utf-8') as f:
            html = f.read()
    except FileNotFoundError:
        print(f"❌ No es pot llegir {HTML_FILE}. Verifica la ruta.")
        return False
    
    # Busquem el contenidor de les targetes
    inici_marcador = '<div class="container">'
    fi_marcador = '</div>\n    </div>\n  </body>\n</html>'
    
    if inici_marcador not in html:
        print("❌ No es troba el contenidor de targetes al HTML.")
        return False
    
    # Generem HTML per a CADASCUNA de les 33 estacions
    targetes_html = '\n'
    for estacio in dades:
        # Determinar classe CSS segons temperatura (per als colors)
        def classe_temp(valor):
            try:
                t = float(str(valor).replace('--', '0'))
                if t > 30: return 'hot'
                elif t < 5: return 'cold'
            except:
                pass
            return 'normal'
        
        targetes_html += f'''
        <div class="card">
            <div class="card-header">
                <h3>{estacio["display_name"]}</h3>
                <span class="station-code">{estacio["code"]}</span>
            </div>
            <div class="card-body">
                <div class="data-row">
                    <span class="label">Temp. Màx:</span>
                    <span class="value {classe_temp(estacio['TX'])}">
                        {estacio['TX']}°C
                    </span>
                </div>
                <div class="data-row">
                    <span class="label">Temp. Mín:</span>
                    <span class="value {classe_temp(estacio['TN'])}">
                        {estacio['TN']}°C
                    </span>
                </div>
                <div class="data-row">
                    <span class="label">Precipitació:</span>
                    <span class="value precip">
                        {estacio['PPT']}mm
                    </span>
                </div>
                <div class="data-row timestamp">
                    <span class="label">Actualitzat:</span>
                    <span class="value">{estacio['updated']}</span>
                </div>
            </div>
        </div>\n'''
    
    # Reemplaçar tot el contingut entre els marcadors
    parts = html.split(inici_marcador)
    if len(parts) >= 2:
        final_part = parts[1].split(fi_marcador)
        if len(final_part) >= 2:
            nou_contingut = parts[0] + inici_marcador + targetes_html + fi_marcador + final_part[1]
            
            # Guardar
            with open(HTML_FILE, 'w', encoding='utf-8') as f:
                f.write(nou_contingut)
            
            print(f"✅ {len(dades)} targetes inserides a {HTML_FILE}")
            return True
    
    print("❌ Error en el reemplaçament HTML.")
    return False

# ============================================================================
# EXECUCIÓ PRINCIPAL
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 GENERANT OVERLAY AMB DADES REALS")
    print("=" * 60)
    
    # Passos
    print("1. Llegint dades dels scrapers...")
    dades = llegir_dades_scrapers()
    
    print("\n2. Generant fitxers unificats...")
    generar_fitxers_unificats(dades)
    
    print("\n3. Actualitzant overlay (index.html)...")
    actualitzar_html(dades)
    
    print("\n" + "=" * 60)
    print(f"✅ PROCÉS COMPLETAT")
    print(f"   📍 Estacions: {len(dades)}")
    print(f"   🕐 Hora: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
