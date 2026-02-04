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
        # 🔧 CANVI CLAU: Passa respostes automàtiques (1, 1, s) a l'entrada del scraper
        # Això resol l'error EOFError en entorns no interactius com GitHub Actions
        respostes_automatiques = b"1\n1\ns\n"  # Bytes, no text
        
        result = subprocess.run(
            comanda,
            shell=False,  # Important: shell=False perque funcioni input=
            input=respostes_automatiques,
            capture_output=False  # No capturem output per evitar problemes d'encoding
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
    
    print("\n📥 EXECUTANT SCRAPERS...")
    
    # 1. Scraper període
    if not executar_script_simple(
        "scraper_periode_complet.py",
        ["python", str(SCRIPTS_DIR / "scraper_periode_complet.py")]
    ):
        print("❌ Primer scraper fallat. Aturant.")
        return 1
    
    # 2. Scraper diari
    if not executar_script_simple(
        "scraper_resum_diari_final.py", 
        ["python", str(SCRIPTS_DIR / "scraper_resum_diari_final.py")]
    ):
        print("❌ Segon scraper fallat. Aturant.")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ TOTS ELS SCRAPERS COMPLETATS")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
