#!/usr/bin/env python3
# scraper_resum_diari_fix.py - Genera Excel formatat, CSV i JSON amb noms fixos

# 🔧 1. PRIMER: Importar els mòduls bàsics i configurar el camí PER TROBAR config_banner
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

# 🔧 2. ARA SÍ: Importar la configuració central
try:
    from config_banner import STATIONS, TODAY, DATA_DIR
    print("✅ Configuració importada correctament des de 'config_banner.py'")
except ImportError as e:
    print(f"❌ Error important la configuració: {e}")
    sys.exit(1)

# --- CONFIGURACIÓ ---
DIA_CONSULTA = TODAY.strftime("%Y-%m-%d")
BASE_URL = "https://www.meteo.cat/observacions/xema/dades"
DELAI_ENTRE_PETICIONS = 1
HORA_CONSULTA = "T09:00Z"

# Diccionari de variables
MAP_VARIABLES = {
    'Temperatura mitjana': 'TEMPERATURA_MITJANA_DIA',
    'Temperatura màxima': 'TEMPERATURA_MAXIMA_DIA',
    'Temperatura mínima': 'TEMPERATURA_MINIMA_DIA',
    'Humitat relativa mitjana': 'HUMITAT_MITJANA_DIA',
    'Precipitació acumulada': 'PRECIPITACIO_ACUM_DIA',
    'Gruix de neu màxim': 'GRUIX_NEU_MAX',
    'Ratxa màxima del vent': 'RATXA_VENT_MAX',
    'Irradiació solar global': 'RADIACIO_GLOBAL',
    'Pressió atmosfèrica': 'PRESSIO_ATMOSFERICA'
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
    """Netega i formata el text"""
    if not text or text in ['(s/d)', '-', '', 'N/D', 's/d']:
        return ''
    text = text.replace('MJ/m 2', 'MJ/m2')
    return ' '.join(text.split())

def extreu_resum_diari_per_estacio(codi_estacio, dia):
    """Extreu dades d'una estació"""
    url = f"{BASE_URL}?codi={codi_estacio}&dia={dia}{HORA_CONSULTA}"
    
    info_estacio = obtenir_info_estacio(codi_estacio)
    
    resultats = {nom_var: '' for nom_var in MAP_VARIABLES.values()}
    resultats['ID_ESTAC'] = codi_estacio
    resultats['NOM_ESTACIO'] = info_estacio['nom']
    resultats['NOM_ORIGINAL'] = info_estacio['nom_original']
    resultats['DATA_DIA'] = dia
    resultats['DATA_EXTRACCIO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resultats['URL_FONT'] = url

    try:
        resposta = requests.get(url, timeout=15)
        resposta.raise_for_status()
    except:
        return resultats

    soup = BeautifulSoup(resposta.text, 'html.parser')
    taules = soup.find_all('table')
    taula_trobada = None

    for taula in taules:
        text_anterior = taula.find_previous(['h2', 'h3', 'strong', 'b'])
        if text_anterior and 'Resum diari' in str(text_anterior):
            taula_trobada = taula
            break
    
    if not taula_trobada:
        for taula in taules:
            if 'Temperatura mitjana' in str(taula):
                taula_trobada = taula
                break

    if not taula_trobada:
        return resultats

    files = taula_trobada.find_all('tr')
    for fila in files:
        cel·les = fila.find_all(['td', 'th'])
        if len(cel·les) >= 2:
            text_clau = cel·les[0].get_text(strip=True)
            for text_web, nom_variable in MAP_VARIABLES.items():
                if text_web in text_clau:
                    valor = ' '.join(cel.get_text(strip=True, separator=' ') for cel in cel·les[1:])
                    resultats[nom_variable] = neteja_valor(valor)
                    break

    return resultats

def executa_scraping_estacions(llista_estacions, dia):
    """Executa per totes les estacions"""
    totes_dades = []
    
    print(f"\n🚀 Iniciant scraping per a {len(llista_estacions)} estacions...")
    print(f"📅 Data: {dia}{HORA_CONSULTA}")
    print("-" * 70)

    for idx, estacio in enumerate(llista_estacions, 1):
        codi = estacio.get('code')
        nom = estacio.get('display_name', estacio.get('name', codi))
        print(f"[{idx:3}/{len(llista_estacions)}] 🔍 {nom} ({codi})...", end=' ', flush=True)

        dades = extreu_resum_diari_per_estacio(codi, dia)
        totes_dades.append(dades)
        
        dades_trobades = sum(1 for nom_var in MAP_VARIABLES.values() if dades.get(nom_var))
        print(f"{dades_trobades} vars" if dades_trobades > 0 else "sense dades")

        time.sleep(DELAI_ENTRE_PETICIONS)

    return totes_dades

def genera_excel_formatat(df, ruta_excel):
    """Genera un arxiu Excel amb format professional"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
        from openpyxl.utils import get_column_letter
        
        writer = pd.ExcelWriter(ruta_excel, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Dades_Meteo')
        worksheet = writer.sheets['Dades_Meteo']
        
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        border = Border(
            left=Side(style='thin'), 
            right=Side(style='thin'),
            top=Side(style='thin'), 
            bottom=Side(style='thin')
        )
        center_alignment = Alignment(horizontal='center', vertical='center')
        
        for col in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
            cell.border = border
            
            col_letter = get_column_letter(col)
            max_length = max(
                df.iloc[:, col-1].astype(str).map(len).max(),
                len(str(df.columns[col-1]))
            )
            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 30)
        
        for row in worksheet.iter_rows(min_row=2, max_row=len(df)+1, max_col=len(df.columns)):
            for cell in row:
                cell.border = border
                if cell.column in [1, 2, 4]:
                    cell.alignment = Alignment(vertical='center')
        
        worksheet.freeze_panes = 'C2'
        
        writer.close()
        print(f"💼 Excel formatat guardat: {ruta_excel}")
        return True
        
    except ImportError:
        print("⚠️  openpyxl no instal·lat, generant Excel sense format")
        df.to_excel(ruta_excel, index=False)
        return True
    except Exception as e:
        print(f"❌ Error generant Excel: {e}")
        return False

def guarda_tots_formats(totes_dades, data_consulta):
    """Guarda en tots els formats: Excel, CSV i JSON amb noms fixos"""
    if not totes_dades:
        return None, None, None

    df = pd.DataFrame(totes_dades)
    
    columnes_metadades = [
        'ID_ESTAC', 'NOM_ESTACIO', 'NOM_ORIGINAL',
        'DATA_DIA', 'DATA_EXTRACCIO', 'URL_FONT'
    ]
    
    columnes_meteo = [c for c in df.columns if c in MAP_VARIABLES.values()]
    columnes_meteo_ordenades = sorted(columnes_meteo)
    columnes_ordenades = columnes_metadades + columnes_meteo_ordenades
    df = df[columnes_ordenades]
    
    directori_dades = Path(DATA_DIR)
    directori_dades.mkdir(parents=True, exist_ok=True)
    
    # NOMS FIXOS SIEMPRE IGUALES
    nom_excel = "resum_diari_meteocat.xlsx"
    nom_csv = "resum_diari_meteocat.csv"
    nom_json = "resum_diari_meteocat.json"
    
    # 1. EXCEL FORMATAT
    ruta_excel = directori_dades / nom_excel
    excel_ok = genera_excel_formatat(df, ruta_excel)
    
    # 2. CSV SIMPLE
    ruta_csv = directori_dades / nom_csv
    df.to_csv(ruta_csv, index=False, encoding='utf-8-sig')
    print(f"📄 CSV simple guardat: {ruta_csv}")
    
    # 3. JSON PER AL BANNER
    ruta_json = directori_dades / nom_json
    
    dades_json = {
        'metadata': {
            'data_consulta': data_consulta,
            'hora_consulta': HORA_CONSULTA,
            'data_extractcio': datetime.now().isoformat(),
            'total_estacions': len(totes_dades),
            'formats_generats': ['Excel', 'CSV', 'JSON'],
            'variables_capturades': list(MAP_VARIABLES.values())
        },
        'estacions': totes_dades
    }
    
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(dades_json, f, ensure_ascii=False, indent=2)
    print(f"📋 JSON per al banner: {ruta_json}")
    
    return ruta_excel, ruta_csv, ruta_json if excel_ok else (None, ruta_csv, ruta_json)

# --- EXECUCIÓ PRINCIPAL ---
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌤️  SCRAPER DE RESUM DIARI - NOMS FIXOS")
    print("="*70)
    print(f"⏰ Hora: {HORA_CONSULTA}")
    print(f"📅 Data: {DIA_CONSULTA}")
    print(f"📋 Estacions: {len(STATIONS)}")
    
    # EXECUCIÓ DIRECTA SENSE PREGUNTAS
    estacions_a_processar = STATIONS
    
    # SCRAPING
    dades = executa_scraping_estacions(estacions_a_processar, DIA_CONSULTA)
    
    # GUARDAR
    if dades:
        ruta_excel, ruta_csv, ruta_json = guarda_tots_formats(dades, DIA_CONSULTA)
        
        print("\n" + "="*70)
        print("📊 FITXERS GENERATS (NOMS FIXOS)")
        print("="*70)
        print(f"📊 Excel: resum_diari_meteocat.xlsx")
        print(f"📄 CSV:   resum_diari_meteocat.csv")
        print(f"📋 JSON:  resum_diari_meteocat.json")
        print(f"📁 Directori: {DATA_DIR}")
        print("="*70)
    else:

        print("\n❌ No s'han obtingut dades.")
