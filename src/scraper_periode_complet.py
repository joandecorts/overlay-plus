#!/usr/bin/env python3
# scraper_periode_intelligent.py - Estratègia intel·ligent: 1 període avui + 4 períodes ahir

# --- 1. TOTES LES IMPORTACIONS DE LLIBRERIES ESTÀNDARD ---
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- 2. CONFIGURAR EL CAMÍ PER TROBAR EL NOSTRE MÒDUL ---
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

# --- 3. IMPORTAR LA NOSTRA CONFIGURACIÓ CENTRAL ---
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

def neteja_nom_capcalera(text):
    """Netega el nom d'una capçalera per convertir-lo en clau vàlida"""
    if not text:
        return 'DESCONEGUT'
    
    # Netejar caràcters especials
    net = text.strip()
    net = net.replace(' ', '_')
    net = net.replace('(', '')
    net = net.replace(')', '')
    net = net.replace('/', '_')
    net = net.replace('°', 'graus')
    net = net.replace('%', 'perc')
    net = net.replace('.', '')
    net = net.replace(',', '')
    net = net.replace('&', 'i')
    
    # Limitar longitud i assegurar que comença amb lletra
    if net[0].isdigit():
        net = 'VAR_' + net
    
    return net[:50]  # Limitar longitud

def calcular_hora_inicial_avui():
    """Calcula l'hora UTC inicial per començar la cerca retroactiva"""
    ara_utc = datetime.utcnow()
    
    # Ajustar: restem 40 minuts per al retard típic de publicació
    hora_ajustada = ara_utc - timedelta(minutes=20)  # ← TORNA A L'ORIGINAL
    
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
    
    # Obtenir info de l'estació
    info_estacio = obtenir_info_estacio(codi_estacio)
    
    try:
        resposta = requests.get(url, timeout=15)
        resposta.raise_for_status()
    except requests.exceptions.Timeout:
        return []
    except requests.exceptions.RequestException:
        return []
    
    soup = BeautifulSoup(resposta.text, 'html.parser')
    taula = soup.find('table', {'class': 'tblperiode'})
    
    if not taula:
        return []
    
    files = taula.find_all('tr')
    if len(files) < 2:
        return []
    
    # 1️⃣ PRIMER: Obtenir les CAPÇALERES REALS de la taula
    primera_fila = taula.find('tr')
    capçaleres_reals = []
    if primera_fila:
        for th in primera_fila.find_all('th'):
            text = th.get_text(strip=True, separator=' ')
            if text:
                capçaleres_reals.append(text)
    
    # Si no hi ha capçaleres, no podem continuar
    if not capçaleres_reals:
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
        for idx in range(1, len(cel·les)):
            valor = cel·les[idx].get_text(strip=True)
            if valor and valor not in ['(s/d)', '-', '', 'N/D', 's/d']:
                dades_valides += 1
        
        if dades_valides >= 1:
            # Crear registre bàsic
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
                'PERIODE_UTC': periode_text,
                'CAPÇALERES_TROBADES': len(capçaleres_reals),
                'CAPÇALERES_LLISTAT': ', '.join(capçaleres_reals)
            }
            
            # 2️⃣ ASSIGNAR VARIABLES SEGONS ESTRUCTURA REAL
            # IMPORTANT: Cada cel·la correspon a la capçalera en la mateixa posició
            for idx in range(len(cel·les)):
                if idx < len(capçaleres_reals):
                    # Nom de la variable basat en la capçalera real
                    nom_capcalera = capçaleres_reals[idx]
                    nom_clau = f"VAR_{neteja_nom_capcalera(nom_capcalera)}"
                    
                    # Valor de la cel·la
                    valor_raw = cel·les[idx].get_text(strip=True)
                    valor_net = neteja_valor(valor_raw)
                    
                    # Assignar al registre
                    registre[nom_clau] = valor_net
                    
                    # També assignar a MAP_COLUMNES si la posició existeix
                    if idx in MAP_COLUMNES:
                        registre[MAP_COLUMNES[idx]] = valor_net
            
            # 3️⃣ COLUMNES GENÈRIQUES NUMERADES (per compatibilitat)
            for idx in range(len(cel·les)):
                nom_col = f"Col_{idx:02d}"
                valor_raw = cel·les[idx].get_text(strip=True)
                registre[nom_col] = neteja_valor(valor_raw)
            
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
        
        if periodes:
            periode = periodes[0]
            print(f"      ✅ Trobat període: {periode.get('PERIODE_UTC', 'N/D')}")
            
            # Mostrar les variables trobades
            vars_trobades = [k for k in periode.keys() if k.startswith('VAR_')]
            print(f"      📊 Variables: {len(vars_trobades)}")
            
            return periode
        else:
            hora_inicial = hora_inicial - timedelta(minutes=30)
            intents += 1
            print(f"      🔄 Provant 30 min abans: {hora_inicial.strftime('%H:%M')} UTC")
            time.sleep(0.5)
    
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
        # Mostrar les variables del primer període
        if periodes and 'CAPÇALERES_TROBADES' in periodes[0]:
            print(f"      📊 Estructura: {periodes[0]['CAPÇALERES_TROBADES']} variables")
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
    
    # Afegir cada capçalera com a columna amb nom netejat
    for i, cap in enumerate(capçaleres):
        nom_clau = f"CAP_{i:02d}_{neteja_nom_capcalera(cap)}"
        resultats[nom_clau] = cap
    
    # Columnes genèriques per compatibilitat
    for i in range(len(capçaleres)):
        resultats[f'Col_{i:02d}'] = capçaleres[i]
    
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
                    'URL_FONT': periodes_estacio[0].get('URL_FONT', '')
                }
            
            print(f"      📊 Resultat: {len(periodes_estacio)} períodes trobats")
        
        if mode in ['capcaleres', 'tot']:
            if mode == 'capcaleres':
                print(f"[{idx:3}/{len(llista_estacions)}] 🔍 {nom} ({codi})...", end=' ', flush=True)
            
            if mode == 'tot' and capcaleres_info:
                pass  # Ja tenim les capçaleres
            else:
                capcaleres_info = detectar_capcaleres_estacio(codi)
            
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

def generar_fitxers_periode_fixos(dades_periode, dades_capcaleres):
    """Genera els fitxers fixos resum_periode_meteocat amb les dades"""
    directori_dades = Path(DATA_DIR)
    directori_dades.mkdir(parents=True, exist_ok=True)
    
    # Nom dels fitxers fixos (segons especificat)
    nom_base = "resum_periode_meteocat"
    
    # --- GENERAR CSV ---
    if dades_periode:
        df_periode = pd.DataFrame(dades_periode)
        
        # Identificar columnes VAR_ per a ordre
        columnes_var = sorted([c for c in df_periode.columns if c.startswith('VAR_')])
        
        # Columnes ordenades
        columnes_metadades = [
            'ID_ESTAC', 'NOM_ESTACIO', 'NOM_ORIGINAL', 'DATA_UTC',
            'PERIODE_UTC', 'ES_AHIR', 'ESTAT', 'DATA_EXTRACCIO',
            'HORA_CONSULTA_UTC', 'URL_FONT', 'CAPÇALERES_TROBADES', 'CAPÇALERES_LLISTAT'
        ]
        
        columnes_finals = []
        for col in columnes_metadades:
            if col in df_periode.columns:
                columnes_finals.append(col)
        
        # Afegir variables VAR_ ordenades
        var_ordenades = sorted(columnes_var, key=lambda x: (
            int(x.split('_')[1]) if x.split('_')[1].isdigit() else 999,
            x
        ))
        columnes_finals.extend(var_ordenades)
        
        # Afegir la resta de columnes
        columnes_restants = [c for c in df_periode.columns if c not in columnes_finals]
        columnes_finals.extend(columnes_restants)
        
        df_periode = df_periode[columnes_finals]
        ruta_csv = directori_dades / f"{nom_base}.csv"
        df_periode.to_csv(ruta_csv, index=False, encoding='utf-8')
        print(f"💾 CSV periòdic guardat: {ruta_csv}")
    
    # --- GENERAR JSON ---
    dades_json = {
        'metadata': {
            'data_extractcio': datetime.now().isoformat(),
            'hora_utc_actual': datetime.utcnow().strftime('%H:%M'),
            'hora_local_actual': datetime.now().strftime('%H:%M'),
            'total_periodes': len(dades_periode) if dades_periode else 0,
            'total_estacions_estudi': len(dades_capcaleres) if dades_capcaleres else 0,
            'max_intents_avui': MAX_INTENTS_AVUI,
            'max_periodes_ahir': MAX_PERIODES_AHIR,
            'estrategia': 'intel·ligent_retroactiva'
        },
        'dades_periode': dades_periode if dades_periode else [],
        'estudi_capcaleres': dades_capcaleres if dades_capcaleres else []
    }
    
    ruta_json = directori_dades / f"{nom_base}.json"
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(dades_json, f, ensure_ascii=False, indent=2)
    print(f"📋 JSON periòdic guardat: {ruta_json}")
    
    # --- GENERAR EXCEL ---
    if dades_periode or dades_capcaleres:
        ruta_excel = directori_dades / f"{nom_base}.xlsx"
        with pd.ExcelWriter(ruta_excel, engine='openpyxl') as writer:
            # FULLA 1: DADES DEL PERÍODE
            if dades_periode:
                df_periode.to_excel(writer, sheet_name='Dades_Període', index=False)
                print(f"📊 Excel periòdic (full Dades_Període): {len(dades_periode)} períodes")
            
            # FULLA 2: ESTUDI DE CAPÇALERES
            if dades_capcaleres:
                df_capcaleres = pd.DataFrame(dades_capcaleres)
                df_capcaleres.to_excel(writer, sheet_name='Estudi_Capçaleres', index=False)
                print(f"📊 Excel periòdic (full Estudi_Capçaleres): {len(dades_capcaleres)} estacions")
        
        print(f"📊 Excel periòdic guardat: {ruta_excel}")
    
    return ruta_csv, ruta_json, ruta_excel

# --- EXECUCIÓ PRINCIPAL ---
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧠 SCRAPER PERÍODE INTEL·LIGENT - Cerca retroactiva per 2 dies")
    print("="*80)
    print(f"🕐 Hora actual: {datetime.now().strftime('%H:%M')} LT")
    print(f"🕐 Hora UTC: {datetime.utcnow().strftime('%H:%M')} UTC")
    print(f"📅 Avui: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"📅 Ahir: {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}")
    
    # SELECCIÓ D'ESTACIONS - AUTOMÀTICA (TOTES)
    print(f"\n📋 Estacions disponibles: {len(STATIONS)}")
    print("🎯 SELECCIÓ D'ESTACIONS: TOTES (mode automàtic)")
    estacions_a_processar = STATIONS
    print(f"▶️  Estacions seleccionades: {len(estacions_a_processar)}")
    
    # MODE D'EXECUCIÓ - AUTOMÀTIC (FER TOT)
    print("\n🎯 MODE D'EXECUCIÓ: FER TOT (Captura dades + Estudi capçaleres)")
    mode_seleccionat = 'tot'
    
    # CONFIRMACIÓ - AUTOMÀTICA (CONTINUAR)
    print(f"\n📋 RESUM DE L'EXECUCIÓ:")
    print(f"   • Estacions: {len(estacions_a_processar)}")
    print(f"   • Mode: {mode_seleccionat}")
    print(f"   • Estratègia: 1 període avui + {MAX_PERIODES_AHIR} períodes ahir")
    print(f"   • Cerca retroactiva: {MAX_INTENTS_AVUI} intents màxims")
    print(f"   • Fitxers de sortida: resum_periode_meteocat.{{csv,json,xlsx}}")
    
    print("\n▶️  Execució automàtica iniciada...")
    
    # EXECUCIÓ
    dades_periode, dades_capcaleres = executa_scraping_intelligent(estacions_a_processar, mode_seleccionat)
    
    # GENERACIÓ DE FITXERS FIXOS
    if dades_periode or dades_capcaleres:
        print("\n" + "="*80)
        print("💾 GENERANT FITXERS FIXOS DE SORTIDA")
        print("="*80)
        
        ruta_csv, ruta_json, ruta_excel = generar_fitxers_periode_fixos(dades_periode, dades_capcaleres)
        
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
            
            # Analitzar variables VAR_ trobades
            tot_vars = set()
            for d in dades_periode:
                if d.get('ESTAT') == 'OK':
                    for key in d.keys():
                        if key.startswith('VAR_'):
                            tot_vars.add(key)
            
            if tot_vars:
                print(f"\n🔍 VARIABLES DIFERENTS TROBADES ({len(tot_vars)}):")
                for var in sorted(tot_vars)[:10]:
                    estacions_amb_var = sum(1 for d in dades_periode if d.get('ESTAT') == 'OK' and d.get(var) not in ['', None])
                    print(f"   • {var}: {estacions_amb_var} estacions")
                
                if len(tot_vars) > 10:
                    print(f"   • ... i {len(tot_vars)-10} més")
            
            # Neu específicament
            if 'VAR_GN_cm' in tot_vars:
                estacions_neu = sum(1 for d in dades_periode if d.get('ESTAT') == 'OK' and d.get('VAR_GN_cm') not in ['', None])
                print(f"\n❄️  NEU DETECTADA a {estacions_neu} estacions")
        
        print(f"\n📁 Directori: {DATA_DIR}")
        print(f"📄 CSV: {Path(ruta_csv).name}")
        print(f"📋 JSON: {Path(ruta_json).name}")
        print(f"📊 Excel: {Path(ruta_excel).name}")
        
        print("\n" + "="*80)
        print("🎉 PROCÉS INTEL·LIGENT COMPLETAT AMB ÈXIT")
        print("="*80)
    else:

        print("\n❌ No s'han obtingut dades.")

