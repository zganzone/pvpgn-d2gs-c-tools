#!/usr/bin/env python3
"""
Minimalistic script to extract essential character stats and progression status, 
excluding items and relying on the D2S file only for character status.
"""
import os
import glob
from typing import Dict, Any, Optional

# =======================================================
# --- КОНФИГУРАЦИЯ ---
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
# =======================================================

# --- D2LIB ЗАРЕЖДАНЕ ---
os.environ['D2_DATA_PATH'] = D2_DATA_DIR
try:
    from d2lib.files import D2SFile
    print(f"[*] D2SFile imported. Data path: {D2_DATA_DIR}")
except ImportError:
    print("[!!!] ERROR: Failed to import d2lib.files.D2SFile. Is d2lib installed?")
    exit(1)
# ------------------------------------

def get_progression_status(progression_value: Optional[int]) -> str:
    """Конвертира Progression Bitmask в четлив статус."""
    if progression_value is None:
        return "N/A"
    
    # Progression: Bitmask (1=A1, 2=A2, 4=A3, 8=A4, 16=A5) completed for Normal difficulty
    
    status_parts = []
    if (progression_value & 1) == 1:
        status_parts.append("Act I Complete")
    if (progression_value & 2) == 2:
        status_parts.append("Act II Complete")
    if (progression_value & 4) == 4:
        status_parts.append("Act III Complete")
    if (progression_value & 8) == 8:
        status_parts.append("Act IV Complete")
    if (progression_value & 16) == 16:
        status_parts.append("Act V Complete")
        
    if not status_parts:
        return "Not Started (Act I Town)"
        
    return ", ".join(status_parts) + f" (Value: {progression_value})"


def run_status_report():
    
    print(f"\n===============================================")
    print(f"  D2 CHARACTER STATUS REPORT ({len(glob.glob(os.path.join(CHAR_DIR, '*')))} files found)")
    print(f"===============================================")
    
    for path in sorted(glob.glob(os.path.join(CHAR_DIR, "*"))):
        char_fname = os.path.basename(path)
        
        try:
            d2s = D2SFile(path)
        except Exception:
            print(f"  [!] {char_fname:<20} | Status: UNREADABLE FILE")
            continue

        char_name = getattr(d2s, "char_name", None) or char_fname 
        char_level = getattr(d2s, "char_level", 0)
        char_class = getattr(d2s, "char_class", "N/A")
        progression = getattr(d2s, "progression", None)
        
        prog_status = get_progression_status(progression)
        
        print(f"  [+] {char_name:<20} | Level: {char_level:<3} | Class: {char_class:<10} | Location: Lobby/Offline | Progress: {prog_status}")


if __name__ == "__main__":
    run_status_report()
