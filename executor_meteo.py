#!/usr/bin/env python3
"""
executor_meteo.py - Versió simple sense problemes d'encoding
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configuració
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "src"

def executar_script_simple(nom_script, comanda):
    """Executa un script sense preocupar-se de l'encoding"""
    print(f"▶  Executant {nom_script}...")
    
    try:
        # Executa sense capturar output (evita problemes d'encoding)
        result = subprocess.run(
            comanda,
            shell=True  # <-- Això evita problemes d'encoding
        )
        
        if result.returncode == 0:
            print(f"✅ {nom_script} completat")
            return True
        else:
            print(f"❌ {nom_script} fallat (codi: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error executant {nom_script}: {e}")
        return False

def main():
    """Executa tot en ordre"""
    print("=" * 60)
    print("🚀 EXECUTOR SIMPLE METEO.CAT")
    print("=" * 60)
    
    # Scrapers
    print("\n📥 EXECUTANT SCRAPERS...")
    scraper1 = executar_script_simple(
        "scraper_periode_complet.py", 
        f'python "{SCRIPTS_DIR / "scraper_periode_complet.py"}"'
    )
    
    if not scraper1:
        print("❌ Primer scraper fallat. Aturant.")
        sys.exit(1)
    
    scraper2 = executar_script_simple(
        "scraper_resum_diari_final.py",
        f'python "{SCRIPTS_DIR / "scraper_resum_diari_final.py"}"'
    )
    
    if not scraper2:
        print("❌ Segon scraper fallat. Aturant.")
        sys.exit(1)
    
    # Generador de banners
    print("\n🎨 GENERANT BANNERS INDIVIDUALS...")
    if not executar_script_simple("generador_banners.py", "python generador_banners.py"):
        print("❌ generador_banners.py fallat")
        sys.exit(1)
    
    # Integrador
    print("\n🌐 GENERANT BANNERS GENERALS...")
    if not executar_script_simple("integrador.py", "python integrador.py"):
        print("❌ integrador.py fallat")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 TOT COMPLETAT CORRECTAMENT!")
    print("=" * 60)

if __name__ == "__main__":
    main()