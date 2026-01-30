#!/usr/bin/env python3
# scraper_periode_intelligent.py - Estratègia intel·ligent: 1 període avui + 4 períodes ahir
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
import time
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

# --- IMPORTACIÓ DE LA CONFIGURACIÓ CENTRAL ---
try:
    from config_banner import STATIONS, TODAY, DATA_DIR
    print("✅ Configuració importada correctament des de 'config_banner.py'")
except ImportError as e:
    print(f"❌ Error important la configuració: {e}")
    sys.exit(1)

# --- CONFIGURACIÓ ---
BASE_URL = "https://www.meteo.cat/observacions/xema/dades"
DELAI_ENTRE_PETICIONS = 1  # Segons entre peticions
MAX_INTENTS_AVUI = 6  # Màxim de períodes a provar cap enrere per a avui (3 hores)
MAX_PERIODES_AHIR = 4  # Número de períodes a capturar d'ahir (2 hores)

# Diccionari de columnes esperades (posició → nom curt)
MAP_COLUMNES = {
    0: "PERIODE",
    1: "TM",   # Temperatura mitjana
    2: "TX",   # Temperatura màxima
    3: "TN",   # Temperatura mínima
    4: "HR",   # Humitat relativa
    5: "PPT",  # Precipitació
    6: "VVM",  # Velocitat vent mitjana
    7: "DVM",  # Direcció vent mitjana
    8: "VVX",  # Ratxa màxima vent
    9: "PM",   # Pressió atmosfèrica
    10: "RS"   # Radiació solar
}

def obtenir_info_estacio(codi_estacio):
    """Obtenir nom de l'estació des de config_banner.py"""
    for estacio in STATIONS:
        if estacio.get('code') == codi_estacio:
            return {
                'nom': estacio.get('display_name', estacio.get('name', codi_estacio)),
                'nom_original': estacio.get('name', '')
            }
    return {'nom': codi_estacio, 'nom_original': ''}

def neteja_valor(text):
    """Netega i formata el text per a valors de cel·la"""
    if not text or text in ['(s/d)', '-', '', 'N/D', 's/d', 'N/A']:
        return ''
    text = text.replace(',', '.')
    text = ' '.join(text.split())
    return text

def calcular_hora_inicial_avui():
    """Calcula l'hora UTC inicial per començar la cerca retroactiva"""
    ara_utc = datetime.utcnow()
    
    # Ajustar: restem 40 minuts per al retard típic de publicació
    hora_ajustada = ara_utc - timedelta(minutes=40)
    
    # Arrodonim cap avall a la mitja hora anterior
    # Ex: 13:50 → 13:30, 14:20 → 14:00
    if hora_ajustada.minute >= 30:
        minut_ajustat = 30
    else:
        minut_ajustat = 0
    
    hora_inicial = hora_ajustada.replace(minute=minut_ajustat, second=0, microsecond=0)
    
    # Si l'hora ajustada és molt propera a ara, potser caldrà anar més enrere
    if (ara_utc - hora_inicial).seconds < 1800:  # Menys de 30 minuts
        hora_inicial = hora_inicial - timedelta(minutes=30)
    
    return hora_inicial

def extreure_periode_desde_url(codi_estacio, data_hora_utc, es_ahir=False):
    """
    Extreu períodes vàlids d'una URL específica
    
    Retorna:
    - Si es_ahir=False: Llista amb 0 o 1 períodes (l'últim vàlid)
    - Si es_ahir=True: Llista amb fins a MAX_PERIODES_AHIR períodes (els darrers vàlids)
    """
    # Format: 2026-01-20T13:30Z
    data_str = data_hora_utc.strftime("%Y-%m-%d")
    hora_str = data_hora_utc.strftime("%H:%M")
    url = f"{BASE_URL}?codi={codi_estacio}&dia={data_str}T{hora_str}Z"
    
    # Obtenir info de l'estació (per utilitzar més endavant)
    info_estacio = obtenir_info_estacio(codi_estacio)
    
    try:
        resposta = requests.get(url, timeout=15)  # Timeout més llarg per a ahir
        resposta.raise_for_status()
    except requests.exceptions.Timeout:
        return []  # Retornem llista buida
    except requests.exceptions.RequestException:
        return []  # Retornem llista buida
    
    soup = BeautifulSoup(resposta.text, 'html.parser')
    taula = soup.find('table', {'class': 'tblperiode'})
    
    if not taula:
        return []
    
    files = taula.find_all('tr')
    if len(files) < 2:
        return []
    
    # Buscar totes les files vàlides
    periodes_trobats = []
    
    for i in range(len(files)-1, 0, -1):  # Des del final (més recents)
        cel·les = files[i].find_all(['td', 'th'])
        if len(cel·les) < 2:
            continue
        
        periode_text = cel·les[0].get_text(strip=True)
        if not re.search(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}', periode_text):
            continue
        
        # Comprovar si té dades vàlides
        dades_valides = 0
        for idx in range(1, min(len(cel·les), 11)):  # Comprovar fins a 10 columnes
            valor = cel·les[idx].get_text(strip=True)
            if valor and valor not in ['(s/d)', '-', '', 'N/D', 's/d']:
                dades_valides += 1
        
        if dades_valides >= 1:  # Almenys una dada vàlida
            # Crear registre
            registre = {
                'ID_ESTAC': codi_estacio,
                'NOM_ESTACIO': info_estacio['nom'],
                'NOM_ORIGINAL': info_estacio['nom_original'],
                'DATA_UTC': data_str,
                'HORA_CONSULTA_UTC': hora_str,
                'URL_FONT': url,
                'DATA_EXTRACCIO': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'ESTAT': 'OK',
                'ES_AHIR': 'SÍ' if es_ahir else 'NO',
                'PERIODE_UTC': periode_text
            }
            
            # Columnes amb noms Meteo.cat
            for pos, nom in MAP_COLUMNES.items():
                if pos < len(cel·les):
                    valor = cel·les[pos].get_text(strip=True)
                    registre[nom] = neteja_valor(valor)
                else:
                    registre[nom] = ''
            
            # Columnes genèriques numerades (Col_00 a Col_10)
            for idx in range(min(len(cel·les), 11)):  # Máxim 11 columnes
                nom_col = f"Col_{idx:02d}"
                valor = cel·les[idx].get_text(strip=True)
                registre[nom_col] = neteja_valor(valor)
            
            # Capçaleres per a estudi
            primera_fila = taula.find('tr')
            capçaleres = []
            if primera_fila:
                for th in primera_fila.find_all('th'):
                    text = th.get_text(strip=True, separator=' ')
                    capçaleres.append(text)
            
            registre['CAPÇALERES_TROBADES'] = len(capçaleres)
            registre['CAPÇALERES_LLISTAT'] = ', '.join(capçaleres)
            
            periodes_trobats.append(registre)
            
            # Si no és ahir, només volem un període
            if not es_ahir:
                break
            
            # Si és ahir, limitem als darrers MAX_PERIODES_AHIR períodes
            if len(periodes_trobats) >= MAX_PERIODES_AHIR:
                break
    
    return periodes_trobats

def cerca_periode_avui(codi_estacio):
    """Cerca retroactiva per al dia actual (retorna 0 o 1 període)"""
    hora_inicial = calcular_hora_inicial_avui()
    intents = 0
    
    print(f"      ⏰ Cerca començant a: {hora_inicial.strftime('%H:%M')} UTC")
    
    while intents < MAX_INTENTS_AVUI:
        periodes = extreure_periode_desde_url(codi_estacio, hora_inicial, es_ahir=False)
        
        if periodes:  # Si troba almenys un període
            periode = periodes[0]
            print(f"      ✅ Trobat període: {periode.get('PERIODE_UTC', 'N/D')}")
            return periode
        else:
            # Provem 30 minuts abans
            hora_inicial = hora_inicial - timedelta(minutes=30)
            intents += 1
            print(f"      🔄 Provant 30 min abans: {hora_inicial.strftime('%H:%M')} UTC")
            time.sleep(0.5)  # Petita pausa entre intents
    
    # Si arriba aquí, no ha trobat res
    print(f"      ❌ No trobat després de {MAX_INTENTS_AVUI} intents")
    return {
        'ID_ESTAC': codi_estacio,
        'NOM_ESTACIO': obtenir_info_estacio(codi_estacio)['nom'],
        'ESTAT': f'NO_TROBAT_AFTER_{MAX_INTENTS_AVUI}_INTENTS',
        'ES_AHIR': 'NO',
        'PERIODE_UTC': '',
        'DATA_EXTRACCIO': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def obtenir_periodes_ahir(codi_estacio):
    """Obtenir els darrers períodes vàlids d'ahir (fins a 4 períodes = 2 hores)"""
    ahir = datetime.utcnow() - timedelta(days=1)
    ahir_mitjanit = ahir.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"      📅 Consultant ahir ({ahir.strftime('%Y-%m-%d')})...")
    periodes = extreure_periode_desde_url(codi_estacio, ahir_mitjanit, es_ahir=True)
    
    if periodes:
        print(f"      ✅ Trobats {len(periodes)} períodes d'ahir")
        for p in periodes[:2]:  # Mostra només els primers 2 per no saturar
            print(f"        • {p.get('PERIODE_UTC', 'N/D')}")
        if len(periodes) > 2:
            print(f"        • ... i {len(periodes)-2} més")
    else:
        print(f"      ⚠️  Sense dades d'ahir")
    
    return periodes

def detectar_capcaleres_estacio(codi_estacio):
    """Detecta totes les capçaleres disponibles per a una estació"""
    url = f"{BASE_URL}?codi={codi_estacio}"
    
    info_estacio = obtenir_info_estacio(codi_estacio)
    resultats = {
        'ID_ESTAC': codi_estacio,
        'NOM_ESTACIO': info_estacio['nom'],
        'NOM_ORIGINAL': info_estacio['nom_original'],
        'URL_FONT': url,
        'ESTAT': 'OK',
        'CAPÇALERES_TROBADES': 0,
        'CAPÇALERES_LLISTAT': ''
    }
    
    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        resultats['ESTAT'] = f'ERROR: {str(e)[:50]}'
        return resultats
    
    soup = BeautifulSoup(resposta.text, 'html.parser')
    taula = soup.find('table', {'class': 'tblperiode'})
    
    if not taula:
        resultats['ESTAT'] = 'NO_TAULA_TROBADA'
        return resultats
    
    primera_fila = taula.find('tr')
    capçaleres = []
    
    if primera_fila:
        for th in primera_fila.find_all('th'):
            text = th.get_text(strip=True, separator=' ')
            if text:
                capçaleres.append(text)
    
    if not capçaleres:
        resultats['ESTAT'] = 'NO_CAPÇALERES_TROBADES'
        return resultats
    
    resultats['CAPÇALERES_TROBADES'] = len(capçaleres)
    resultats['CAPÇALERES_LLISTAT'] = ', '.join(capçaleres)
    
    # Afegir cada capçalera com a columna
    for i, cap in enumerate(capçaleres):
        resultats[f'Col_{i:02d}'] = cap
    
    return resultats

def executa_scraping_intelligent(llista_estacions, mode):
    """Executa el scraping en mode intel·ligent"""
    totes_dades = []
    totes_capcaleres = []
    
    print(f"\n🚀 Iniciant execució INTEL·LIGENT en mode '{mode}'...")
    print(f"🕐 Hora actual UTC: {datetime.utcnow().strftime('%H:%M')}")
    print(f"📊 Configuració: 1 període avui + {MAX_PERIODES_AHIR} períodes ahir")
    print("-" * 80)
    
    for idx, estacio in enumerate(llista_estacions, 1):
        codi = estacio.get('code')
        nom = estacio.get('display_name', estacio.get('name', codi))
        
        periodes_estacio = []
        capcaleres_info = None
        
        if mode in ['dades', 'tot']:
            print(f"[{idx:3}/{len(llista_estacions)}] 📥 {nom} ({codi})...")
            
            # 1. Cerca per a avui (1 període)
            print(f"      🌅 Buscant període actual...")
            periode_avui = cerca_periode_avui(codi)
            if periode_avui.get('ESTAT') == 'OK':
                periodes_estacio.append(periode_avui)
            
            # 2. Cerca per a ahir (fins a 4 períodes)
            print(f"      🌙 Buscant períodes d'ahir...")
            periodes_ahir = obtenir_periodes_ahir(codi)
            periodes_estacio.extend(periodes_ahir)
            
            totes_dades.extend(periodes_estacio)
            
            # Si hem trobat períodes, agafem les capçaleres del primer
            if periodes_estacio and periodes_estacio[0].get('ESTAT') == 'OK':
                capcaleres_info = {
                    'ID_ESTAC': codi,
                    'NOM_ESTACIO': nom,
                    'ESTAT': 'OK',
                    'CAPÇALERES_TROBADES': periodes_estacio[0].get('CAPÇALERES_TROBADES', 0),
                    'CAPÇALERES_LLISTAT': periodes_estacio[0].get('CAPÇALERES_LLISTAT', ''),
                    'URL_FONT': periodes_estacio[0].get('URL_FONT', '')  # CORRECCIÓ: Afegir URL_FONT
                }
            
            print(f"      📊 Resultat: {len(periodes_estacio)} períodes trobats")
        
        if mode in ['capcaleres', 'tot']:
            if mode == 'capcaleres':
                print(f"[{idx:3}/{len(llista_estacions)}] 🔍 {nom} ({codi})...", end=' ', flush=True)
            
            # Si ja tenim capçaleres de la consulta anterior, les reutilitzem
            if mode == 'tot' and capcaleres_info:
                pass  # Ja tenim les capçaleres
            else:
                # Sinó, fem una consulta específica
                capcaleres_info = detectar_capcaleres_estacio(codi)
            
            # Afegir a la llista
            if capcaleres_info:
                totes_capcaleres.append(capcaleres_info)
            
            if mode == 'capcaleres':
                if capcaleres_info and capcaleres_info.get('ESTAT') == 'OK':
                    capcaleres = capcaleres_info.get('CAPÇALERES_TROBADES', 0)
                    print(f"{capcaleres} capçaleres")
                else:
                    estat = capcaleres_info.get('ESTAT', 'DESCONEGUT') if capcaleres_info else 'ERROR'
                    print(estat)
        
        time.sleep(DELAI_ENTRE_PETICIONS)
    
    return totes_dades, totes_capcaleres

def generar_excel_intelligent(dades_periode, dades_capcaleres):
    """Genera Excel amb totes les dades"""
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    nom_base = f"periode_intelligent_{timestamp}"
    directori_dades = Path(DATA_DIR)
    directori_dades.mkdir(parents=True, exist_ok=True)
    
    ruta_excel = directori_dades / f"{nom_base}.xlsx"
    
    with pd.ExcelWriter(ruta_excel, engine='openpyxl') as writer:
        # FULLA 1: DADES DEL PERÍODE
        if dades_periode:
            df_periode = pd.DataFrame(dades_periode)
            
            # Columnes ordenades: metadades → noms Meteo.cat → columnes genèriques
            columnes_metadades = [
                'ID_ESTAC', 'NOM_ESTACIO', 'NOM_ORIGINAL', 'DATA_UTC',
                'PERIODE_UTC', 'ES_AHIR', 'ESTAT', 'DATA_EXTRACCIO',
                'HORA_CONSULTA_UTC', 'URL_FONT', 'CAPÇALERES_TROBADES', 'CAPÇALERES_LLISTAT'
            ]
            
            columnes_meteo = ['TM', 'TX', 'TN', 'HR', 'PPT', 'VVM', 'DVM', 'VVX', 'PM', 'RS']
            columnes_genèriques = sorted([c for c in df_periode.columns if c.startswith('Col_')])
            
            # Crear llista ordenada
            columnes_finals = []
            for cols in [columnes_metadades, columnes_meteo, columnes_genèriques]:
                for col in cols:
                    if col in df_periode.columns and col not in columnes_finals:
                        columnes_finals.append(col)
            
            # Afegir qualsevol altra columna que hagi quedat
            for col in df_periode.columns:
                if col not in columnes_finals:
                    columnes_finals.append(col)
            
            df_periode = df_periode[columnes_finals]
            df_periode.to_excel(writer, sheet_name='Dades_Període', index=False)
            print(f"💾 Fulla 'Dades_Període': {len(dades_periode)} períodes")
        
        # FULLA 2: ESTUDI DE CAPÇALERES
        if dades_capcaleres:
            df_capcaleres = pd.DataFrame(dades_capcaleres)
            
            # Reordenar columnes per a millor visualització
            columnes_ordenades = [
                'ID_ESTAC', 'NOM_ESTACIO', 'ESTAT', 
                'CAPÇALERES_TROBADES', 'CAPÇALERES_LLISTAT', 'URL_FONT'
            ]
            
            # CORRECCIÓ: Filtrar només les columnes que existeixen
            columnes_existents = [col for col in columnes_ordenades if col in df_capcaleres.columns]
            
            # Afegir columnes Col_00, Col_01, etc. ordenades
            columnes_col = sorted([c for c in df_capcaleres.columns if c.startswith('Col_')])
            columnes_existents.extend(columnes_col)
            
            # Afegir qualsevol altra columna
            for col in df_capcaleres.columns:
                if col not in columnes_existents:
                    columnes_existents.append(col)
            
            df_capcaleres = df_capcaleres[columnes_existents]
            df_capcaleres.to_excel(writer, sheet_name='Estudi_Capçaleres', index=False)
            print(f"💾 Fulla 'Estudi_Capçaleres': {len(dades_capcaleres)} estacions")
            
            # FULLA 3: RESUM DE CAPÇALERES
            resum_data = []
            columnes_capcaleres = [c for c in df_capcaleres.columns if c.startswith('Col_')]
            
            for col in columnes_capcaleres:
                estacions_amb_capcalera = df_capcaleres[col].notna().sum()
                percentatge = (estacions_amb_capcalera / len(dades_capcaleres)) * 100 if len(dades_capcaleres) > 0 else 0
                
                resum_data.append({
                    'CAPCALERA': col,
                    'NOM_REAL': df_capcaleres[col].iloc[0] if not df_capcaleres[col].isna().all() else '',
                    'ESTACIONS_AMB_AQUESTA_CAPCALERA': estacions_amb_capcalera,
                    'PERCENTATGE': f"{percentatge:.1f}%"
                })
            
            if resum_data:
                df_resum = pd.DataFrame(resum_data)
                df_resum = df_resum.sort_values('ESTACIONS_AMB_AQUESTA_CAPCALERA', ascending=False)
                df_resum.to_excel(writer, sheet_name='Resum_Capçaleres', index=False)
                print(f"💾 Fulla 'Resum_Capçaleres': {len(columnes_capcaleres)} capçaleres")
    
    print(f"📊 Excel intel·ligent guardat: {ruta_excel}")
    return ruta_excel

def guardar_json_intelligent(dades_periode, dades_capcaleres):
    """Guarda dades en format JSON"""
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    nom_base = f"periode_intelligent_{timestamp}"
    directori_dades = Path(DATA_DIR)
    
    ruta_json = directori_dades / f"{nom_base}.json"
    
    dades_json = {
        'metadata': {
            'data_extractcio': datetime.now().isoformat(),
            'hora_utc_actual': datetime.utcnow().strftime('%H:%M'),
            'hora_local_actual': datetime.now().strftime('%H:%M'),
            'total_periodes': len(dades_periode) if dades_periode else 0,
            'total_estacions_estudi': len(dades_capcaleres) if dades_capcaleres else 0,
            'max_intents_avui': MAX_INTENTS_AVUI,
            'max_periodes_ahir': MAX_PERIODES_AHIR,
            'estratègia': 'intel·ligent_retroactiva'
        },
        'dades_periode': dades_periode if dades_periode else [],
        'estudi_capcaleres': dades_capcaleres if dades_capcaleres else []
    }
    
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(dades_json, f, ensure_ascii=False, indent=2)
    
    print(f"📋 JSON intel·ligent guardat: {ruta_json}")
    return ruta_json

# --- EXECUCIÓ PRINCIPAL ---
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧠 SCRAPER PERÍODE INTEL·LIGENT - Cerca retroactiva per 2 dies")
    print("="*80)
    print(f"🕐 Hora actual: {datetime.now().strftime('%H:%M')} LT")
    print(f"🕐 Hora UTC: {datetime.utcnow().strftime('%H:%M')} UTC")
    print(f"📅 Avui: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"📅 Ahir: {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}")
    
    # SELECCIÓ D'ESTACIONS
    print(f"\n📋 Estacions disponibles: {len(STATIONS)}")
    print("\n🎯 SELECCIÓ D'ESTACIONS:")
    print("1. TOTES les estacions")
    print("2. Mode PROVES (Z3, XI, XJ, C6, UO, W1)")
    print("3. Excloure estacions problemàtiques")
    
    try:
        opcio_estacions = int(input("\n👉 Selecciona opció (1-3): ").strip() or "1")
    except:
        opcio_estacions = 1
    
    if opcio_estacions == 1:
        estacions_a_processar = STATIONS
    elif opcio_estacions == 2:
        codis_prova = ['Z3', 'XI', 'XJ', 'C6', 'UO', 'W1']
        estacions_a_processar = [s for s in STATIONS if s.get('code') in codis_prova]
    elif opcio_estacions == 3:
        codis_excloure = ['UO']
        estacions_a_processar = [s for s in STATIONS if s.get('code') not in codis_excloure]
    else:
        estacions_a_processar = STATIONS
    
    print(f"▶️  Estacions seleccionades: {len(estacions_a_processar)}")
    
    # MODE D'EXECUCIÓ
    print("\n🎯 MODE D'EXECUCIÓ:")
    print("1. 📥 Capturar DADES del període (per al banner)")
    print("2. 🔍 Estudi de CAPÇALERES disponibles")
    print("3. ⚡ FER TOT (Captura dades + Estudi capçaleres)")
    
    try:
        opcio_mode_input = input("\n👉 Selecciona mode (1-3): ").strip()
        opcio_mode = int(opcio_mode_input) if opcio_mode_input else 3
    except:
        opcio_mode = 3
    
    modes = {1: 'dades', 2: 'capcaleres', 3: 'tot'}
    mode_seleccionat = modes.get(opcio_mode, 'tot')
    
    # CONFIRMACIÓ
    print(f"\n📋 RESUM DE L'EXECUCIÓ:")
    print(f"   • Estacions: {len(estacions_a_processar)}")
    print(f"   • Mode: {mode_seleccionat}")
    print(f"   • Estratègia: 1 període avui + {MAX_PERIODES_AHIR} períodes ahir")
    print(f"   • Cerca retroactiva: {MAX_INTENTS_AVUI} intents màxims")
    
    continuar = input("\n▶️  Continuar amb l'execució? (s/n): ").strip().lower()
    if continuar != 's':
        print("⏹️  Execució cancel·lada.")
        sys.exit(0)
    
    # EXECUCIÓ
    dades_periode, dades_capcaleres = executa_scraping_intelligent(estacions_a_processar, mode_seleccionat)
    
    # GENERACIÓ DE FITXERS
    if dades_periode or dades_capcaleres:
        print("\n" + "="*80)
        print("💾 GENERANT FITXERS DE SORTIDA")
        print("="*80)
        
        # Excel
        ruta_excel = generar_excel_intelligent(dades_periode, dades_capcaleres)
        
        # JSON
        ruta_json = guardar_json_intelligent(dades_periode, dades_capcaleres)
        
        # RESUM FINAL
        print("\n" + "="*80)
        print("📊 RESULTATS FINALS")
        print("="*80)
        
        if dades_periode:
            periodes_avui = sum(1 for d in dades_periode if d.get('ES_AHIR') == 'NO' and d.get('ESTAT') == 'OK')
            periodes_ahir = sum(1 for d in dades_periode if d.get('ES_AHIR') == 'SÍ' and d.get('ESTAT') == 'OK')
            periodes_error = sum(1 for d in dades_periode if d.get('ESTAT') != 'OK')
            
            print(f"✅ PERÍODES TROBATS:")
            print(f"   • Avui: {periodes_avui} períodes vàlids")
            print(f"   • Ahir: {periodes_ahir} períodes vàlids")
            print(f"   • Errors: {periodes_error} períodes amb errors")
            
            # Variables amb dades
            vars_amb_dades = {}
            for d in dades_periode:
                if d.get('ESTAT') == 'OK':
                    for var in ['TM', 'TX', 'TN', 'HR', 'PPT', 'VVM', 'DVM', 'VVX', 'PM', 'RS']:
                        if d.get(var) and d[var] != '':
                            vars_amb_dades[var] = vars_amb_dades.get(var, 0) + 1
            
            total_periodes_valids = periodes_avui + periodes_ahir
            if total_periodes_valids > 0:
                print(f"\n📈 VARIABLES TROBADES (en {total_periodes_valids} períodes vàlids):")
                for var, compte in sorted(vars_amb_dades.items()):
                    percent = (compte / total_periodes_valids) * 100
                    print(f"   • {var}: {compte}/{total_periodes_valids} ({percent:.1f}%)")
        
        if dades_capcaleres:
            estacions_ok = sum(1 for d in dades_capcaleres if d.get('ESTAT') == 'OK')
            print(f"\n🔍 ESTUDI DE CAPÇALERES: {estacions_ok}/{len(dades_capcaleres)} estacions")
        
        print(f"\n📁 Directori: {DATA_DIR}")
        print(f"📊 Excel: {Path(ruta_excel).name}")
        print(f"📋 JSON: {Path(ruta_json).name}")
        
        # MOSTRA RÀPIDA
        if dades_periode:
            print("\n👁️  MOSTRA RÀPIDA (primer període de cada tipus):")
            print("-" * 60)
            
            # Període d'avui
            for d in dades_periode:
                if d.get('ESTAT') == 'OK' and d.get('ES_AHIR') == 'NO':
                    print(f"🌅 PERÍODE AVUI:")
                    print(f"   🏠 {d.get('NOM_ESTACIO', '')} ({d.get('ID_ESTAC', '')})")
                    print(f"   🕐 {d.get('PERIODE_UTC', 'N/D')} UTC")
                    print(f"   🌡️ TM: {d.get('TM', 'N/D')}°C | TX: {d.get('TX', 'N/D')}°C | TN: {d.get('TN', 'N/D')}°C")
                    break
            
            # Període d'ahir
            for d in dades_periode:
                if d.get('ESTAT') == 'OK' and d.get('ES_AHIR') == 'SÍ':
                    print(f"\n🌙 PERÍODE AHIR:")
                    print(f"   🏠 {d.get('NOM_ESTACIO', '')} ({d.get('ID_ESTAC', '')})")
                    print(f"   🕐 {d.get('PERIODE_UTC', 'N/D')} UTC")
                    print(f"   🌡️ TM: {d.get('TM', 'N/D')}°C | TX: {d.get('TX', 'N/D')}°C")
                    break
        
        print("\n" + "="*80)
        print("🎉 PROCÉS INTEL·LIGENT COMPLETAT AMB ÈXIT")
        print("="*80)
    else:
        print("\n❌ No s'han obtingut dades.")