# nou_integrador.py - Generador unificat del nou sistema
from pathlib import Path
import json
import re
import shutil

print("🚀 INICIANT GENERADOR UNIFICAT DEL NOU SISTEMA...")
print("=" * 60)

# --- PART 1: Obtenir les 35 estacions úniques ---
def obtenir_estacions_uniques():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        ruta_dades = Path(config["ruta_dades"])
        fitxer_periode = ruta_dades / config["fitxer_periode"]
        with open(fitxer_periode, 'r', encoding='utf-8') as f:
            dades = json.load(f)
        llista_periodes = dades.get('dades_periode', [])
        estacions_dict = {}
        for periode in llista_periodes:
            id_estacio = str(periode.get('ID_ESTAC', '')).strip()
            if not id_estacio: continue
            nom = periode.get('NOM_ESTACIO', id_estacio).strip()
            comarca = periode.get('COMARCA', 'Desconeguda')
            if nom:
                estacions_dict[id_estacio] = {
                    'id': id_estacio,
                    'idNet': re.sub(r'[^a-zA-Z0-9_]', '_', id_estacio),
                    'nom': nom,
                    'comarca': comarca
                }
        estacions = list(estacions_dict.values())
        print(f"✅ {len(estacions)} estacions úniques processades")
        return estacions
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return []

estacions = obtenir_estacions_uniques()
if not estacions:
    print("❌ No hi ha dades. Sortint.")
    exit()

# ============================================================================
# CANVI 1/2: ORDENAR LES ESTACIONS PER NOM (ASCENDENT)
# ============================================================================
estacions = sorted(estacions, key=lambda x: x['nom'])
print(f"📊 Estacions ordenades per nom: {len(estacions)}")

# --- PART 2: Generar el NOU index.html (rotador automàtic) ---
print("\n📝 Generant NOU index.html (rotador automàtic)...")

# Llegim la plantilla del nou index.html des d'un arxiu separat
# Però com no el tenim, el definim aquí directament.
html_rotador = '''<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rotador Automàtic - Estacions Meteo.cat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0c2461, #1e3799);
            color: white;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .banner-superior {
            background: rgba(0, 0, 0, 0.7);
            padding: 15px 30px;
            text-align: center;
            border-bottom: 3px solid #4fc3f7;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        .banner-superior h1 {
            color: #4fc3f7;
            font-size: 1.8em;
        }
        .compte-enrere-container {
            text-align: center;
            margin: 30px 0;
            flex-shrink: 0;
        }
        #compteEnrere {
            font-size: 6em;
            font-weight: bold;
            color: #FFD700;
            text-shadow: 0 0 20px rgba(255, 215, 0, 0.7);
            margin: 20px 0;
        }
        .estat-rotacio {
            font-size: 1.5em;
            color: #bbdefb;
        }
        .controls {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-bottom: 30px;
            flex-shrink: 0;
        }
        .btn {
            padding: 12px 30px;
            border: noe;
            border-radius: 50px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primari {
            background: linear-gradient(to right, #4fc3f7, #2979ff);
            color: white;
        }
        .btn-secundari {
            background: linear-gradient(to right, #FF5252, #D32F2F);
            color: white;
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 7px 14px rgba(0,0,0,0.3); }
        .contenidor-iframe {
            flex-grow: 1;
            margin: 0 30px 30px 30px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            background: black;
            min-height: 0;
        }
        #visorEstacio {
            width: 100%;
            height: 100%;
            border: none;
            display: block;
        }
        .enllaços-peu {
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            text-align: center;
            border-top: 2px solid #ff7b00;
            flex-shrink: 0;
        }
        .enllaços-peu a {
            color: #ffcc80;
            margin: 0 15px;
            text-decoration: none;
            font-size: 1.1em;
            font-weight: bold;
        }
        .enllaços-peu a:hover { text-decoration: underline; color: #FFD700; }
    </style>
</head>
<body>
    <div class="banner-superior">
        <h1>🌤️ ROTADOR AUTOMÀTIC - ESTACIONS METEOCAT</h1>
        <div class="estat-rotacio">Estat: <span id="textEstat">🔵 Iniciat</span></div>
    </div>

    <div class="compte-enrere-container">
        <h2>Pròxima rotació en:</h2>
        <div id="compteEnrere">10</div>
        <p class="estat-rotacio">La pàgina es carregarà automàticament</p>
    </div>

    <div class="controls">
        <button id="btnAturar" class="btn btn-primari">⏸️ Aturar Rotació</button>
        <button id="btnForçar" class="btn btn-secundari">⏭️ Forçar Següent Estació</button>
    </div>

    <div class="contenidor-iframe">
        <iframe id="visorEstacio" src=""></iframe>
    </div>

    <div class="enllaços-peu">
        <a href="banner.html">📋 Veure Llistat Complert d'Estacions</a>
        <a href="public/index.html" target="_blank">↗️ Obrir Pàgina Principal (nova pestanya)</a>
    </div>

    <script>
        // CONFIGURACIÓ
        const TEMPS_ROTACIO_MS = 120000; // 120 segons entre estacions
        const COMPTE_ENRERE_INICIAL = 10; // Compte enrere inicial de 10s
        let llistaEstacions = [];
        let indexActual = -1;
        let comptador = COMPTE_ENRERE_INICIAL;
        let timerCompteEnrere = null;
        let timerRotacio = null;
        let rotacioAturada = false;

        // 1. OBTENIR LLISTAT D'ESTACIONS
        function carregarLlistatEstacions() {
            fetch('banner.html')
                .then(resp => resp.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const scriptTag = doc.querySelector('script');
                    if (scriptTag) {
                        const textScript = scriptTag.textContent;
                        const match = textScript.match(/window\.estacionsOrdenades\s*=\s*(\[.*?\]);/s);
                        if (match) {
                            try {
                                llistaEstacions = JSON.parse(match[1]);
                                console.log(`✅ S'han carregat ${llistaEstacions.length} estacions.`);
                                if (llistaEstacions.length > 0) {
                                    iniciarRotacio();
                                }
                            } catch(e) {
                                console.error('Error analitzant dades:', e);
                            }
                        }
                    }
                })
                .catch(err => console.error('Error carregant banner.html:', err));
        }

        // 2. INICIAR SISTEMA DE ROTACIÓ
        function iniciarRotacio() {
            clearInterval(timerCompteEnrere);
            clearTimeout(timerRotacio);
            comptador = COMPTE_ENRERE_INICIAL;
            document.getElementById('compteEnrere').textContent = comptador;
            document.getElementById('textEstat').textContent = '🔵 Rotant';
            document.getElementById('textEstat').style.color = '#4fc3f7';
            rotacioAturada = false;

            timerCompteEnrere = setInterval(() => {
                comptador--;
                document.getElementById('compteEnrere').textContent = comptador;
                if (comptador <= 0) {
                    clearInterval(timerCompteEnrere);
                    carregarSeguentEstacio();
                }
            }, 1000);
        }

        // 3. CARREGAR SEGÜENT ESTACIÓ
        function carregarSeguentEstacio() {
            if (llistaEstacions.length === 0) return;
            indexActual = (indexActual + 1) % llistaEstacions.length;
            const estacio = llistaEstacions[indexActual];
            const urlFitxer = `index_${estacio.id}.html`;
            console.log(`Carregant: ${urlFitxer} - ${estacio.nom}`)

            document.getElementById('visorEstacio').src = urlFitxer;
            document.title = `Rotant: ${estacio.nom}`;

            // Reiniciar compte enrere per a la següent rotació
            comptador = COMPTE_ENRERE_INICIAL;
            document.getElementById('compteEnrere').textContent = comptador;

            if (!rotacioAturada) {
                timerRotacio = setTimeout(carregarSeguentEstacio, TEMPS_ROTACIO_MS);
                timerCompteEnrere = setInterval(() => {
                    comptador--;
                    document.getElementById('compteEnrere').textContent = comptador;
                }, 1000);
            }
        }

        // 4. CONTROL DE BOTONS
        document.getElementById('btnAturar').addEventListener('click', function() {
            rotacioAturada = !rotacioAturada;
            if (rotacioAturada) {
                clearInterval(timerCompteEnrere);
                clearTimeout(timerRotacio);
                this.textContent = '▶️ Reprendre Rotació';
                this.classList.remove('btn-primari');
                this.classList.add('btn-secundari');
                document.getElementById('textEstat').textContent = '⏸️ Aturat';
                document.getElementById('textEstat').style.color = '#FF5252';
                document.getElementById('compteEnrere').textContent = '—';
            } else {
                this.textContent = '⏸️ Aturar Rotació';
                this.classList.remove('btn-secundari');
                this.classList.add('btn-primari');
                iniciarRotacio();
            }
        });

        document.getElementById('btnForçar').addEventListener('click', function() {
            clearInterval(timerCompteEnrere);
            clearTimeout(timerRotacio);
            carregarSeguentEstacio();
            if (!rotacioAturada) {
                iniciarRotacio();
            }
        });

        // 5. INICIAR QUAN ES CARREGUI LA PÀGINA
        document.addEventListener('DOMContentLoaded', carregarLlistatEstacions);
    </script>
</body>
</html>'''

# Escriure el nou index.html
# with open('index.html', 'w', encoding='utf-8') as f:
#   f.write(html_rotador)
# print("   ✅ Nou index.html generat (rotador automàtic)")

# --- PART 3: Generar/Actualitzar banner.html amb enllaç corregit ---
print("\n📝 Actualitzant banner.html...")

# Crear banner.html simple i actualitzat
banner_html = f'''<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Llistat d'Estacions - Meteo.cat</title>
    <style>
        body {{ font-family: Arial; padding: 20px; background: #f0f0f0; }}
        .titol {{ color: #1a237e; text-align: center; }}
        .estacio {{ background: white; padding: 15px; margin: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); cursor: pointer; }}
        .estacio:hover {{ background: #e3f2fd; }}
        .controls {{ text-align: center; margin: 30px 0; }}
        .btn-tornar {{ background: #ff7b00; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; }}
    </style>
</head>
<body>
    <h1 class="titol">📋 LLISTAT COMPLET D'ESTACIONS</h1>
    <p style="text-align: center;">Tens <strong>{len(estacions)}</strong> estacions disponibles.</p>
    <div id="llistat">
'''

# ============================================================================
# CANVI 2/2: CORREGIR ELS ENLLAÇOS (VERSIÓ LOCAL - CORRECTA)
# Utilitza <a href> en lloc d'onclick, tal com fa el teu fitxer local.
# ============================================================================
# AFEGIR CADA ESTACIÓ AL LLISTAT (VERSIÓ LOCAL - CORRECTA)
for estacio in estacions:
    banner_html += f'''
        <div class="estacio">
            <a href="public/estacio_{estacio['id']}.html" class="estacio-link">
                <div class="estacio-nom">{estacio['nom']}</div>
                <div class="estacio-dets">
                    <span class="estacio-codi">{estacio['id']}</span>
                    <span class="estacio-comarca">({estacio['comarca']})</span>
                </div>
            </a>
        </div>
    '''

# --- TANQUEM EL HTML I AFEGIM EL JAVASCRIPT PER AL ROTADOR ---
banner_html += f'''
    </div>
    
    <!-- Enllaç per tornar al rotador -->
    <div class="controls">
        <a href="index.html" class="btn-tornar">↩️ Tornar al Rotador Automàtic</a>
    </div>

    <!-- AQUEST SCRIPT ÉS ESSENCIAL PER AL ROTADOR AUTOMÀTIC -->
    <script>
        // Passem la llista d'estacions ordenades al JavaScript del rotador
        window.estacionsOrdenades = {json.dumps(estacions, ensure_ascii=False)};
    </script>
</body>
</html>'''

# Assegurar que la carpeta 'public' existeix i escriure-hi
Path("public").mkdir(exist_ok=True)
with open('public/banner.html', 'w', encoding='utf-8') as f:
    f.write(banner_html)
print("   ✅ public/banner.html actualitzat (enllaç corregit)")

# --- FI ---
print("\n" + "=" * 60)
print("🎯 GENERACIÓ COMPLETADA!")
print("=" * 60)
print("Els següents fitxers s'han creat/actualitzat:")
print(f"   • ./index.html            (Nou rotador automàtic)")
print(f"   • ./public/banner.html    (Llistat amb {len(estacions)} estacions)")
print(f"   • ./nou_integrador.py     (Aquest mateix script)")
print("\n▶️  Per provar-ho, simplement obre 'index.html' al teu navegador.")
print("   El rotador començarà automàticament després de 10 segons.")
print("=" * 60)
