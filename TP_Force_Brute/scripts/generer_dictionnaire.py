#!/usr/bin/env python3
"""
generer_dictionnaire.py - Générateur de dictionnaires de codes PIN
pour tests de sécurité (cadre pédagogique uniquement).

Types de dictionnaires générés :
  - sequentiel: PINs séquentiels (0000, 0001, ...)
  - patterns: PINs basés sur des motifs clavier
  - courants: PINs les plus fréquents
  - aleatoire: PINs aléatoires
  - dates: PINs basés sur des dates (MMDD, DDMM, YYMM)
  - complet: Tout en un
"""

import itertools
import random
import os
import argparse
from datetime import datetime

def generer_sequentiel(longueur=4, debut=0, fin=None):
    """Génère des PINs séquentiels."""
    if fin is None:
        fin = 10 ** longueur - 1
    for i in range(debut, min(fin + 1, 10 ** longueur)):
        yield str(i).zfill(longueur)

def generer_patterns():
    """Génère des PINs basés sur des motifs clavier."""
    patterns = set()

    # Motifs linéaires (haut-bas, gauche-droite)
    for i in range(10):
        patterns.add(f"{i}{(i+1)%10}{(i+2)%10}{(i+3)%10}")  # 0123, 1234...
        patterns.add(f"{i}{(i+3)%10}{(i+6)%10}{(i+9)%10}")  # 0369, 1470...
        patterns.add(f"{(i)%10}{(i+2)%10}{(i+4)%10}{(i+6)%10}")  # 0246, 1357...

    # Motifs en croix
    for centre in range(1, 9):
        haut = centre - 3 if centre > 3 else None
        bas = centre + 3 if centre < 7 else None
        gauche = centre - 1 if centre % 3 != 1 else None
        droite = centre + 1 if centre % 3 != 0 else None
        for v in [haut, bas, gauche, droite]:
            if v is not None and 0 <= v <= 9:
                patterns.add(f"{centre}{v}{centre}{v}")
                patterns.add(f"{centre}{centre}{v}{v}")

    # Motifs répétés
    for i in range(10):
        patterns.add(f"{i}{i}{i}{i}")  # 0000, 1111...
        patterns.add(f"{i}{(i+1)%10}{(i+1)%10}{(i+2)%10}")  # 0112, 1223...
        patterns.add(f"{i}{i}{(i+1)%10}{(i+1)%10}")  # 0011, 1122...

    # Motifs symétriques
    for a in range(10):
        for b in range(10):
            patterns.add(f"{a}{b}{b}{a}")  # 1221, 3443...
            patterns.add(f"{a}{a}{b}{b}")  # 1122, 2233...

    # Années communes
    for an in range(1950, 2030):
        patterns.add(str(an))

    return sorted(patterns)

def generer_courants():
    """PINs les plus courants selon les études de sécurité."""
    return [
        "1234", "1111", "0000", "1212", "7777", "1004", "2000", "4444",
        "2222", "6969", "9999", "3333", "5555", "6666", "1122", "1313",
        "8888", "4321", "2001", "1010", "1230", "1994", "1000", "1233",
        "4322", "1221", "4141", "2002", "2020", "2021", "2022", "2023",
        "2024", "2025", "2026", "1986", "1987", "1988", "1989", "1990",
        "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998",
        "1999", "2000", "2001", "2002", "2003", "2004", "2005",
        "1337", "1100", "1012", "3311", "0120", "1342", "1492",
        "2121", "2134", "2223", "2233", "2244", "2255", "2378",
        "2468", "2555", "2569", "2580", "2589", "2626", "2678",
        "2684", "2739", "2777", "2828", "2987", "3012", "3030",
        "3110", "3131", "3210", "3256", "3310", "3322", "3344",
        "4242", "4321", "4444", "4545", "4567", "4646", "4747",
        "4848", "4949", "5000", "5050", "5115", "5151", "5226",
        "5309", "5337", "5432", "5454", "5505", "5555", "5656",
        "5757", "5858", "5959", "6000", "6060", "6116", "6161",
        "6227", "6338", "6446", "6543", "6565", "6666", "6767",
        "6868", "6969", "7000", "7070", "7117", "7171", "7228",
        "7339", "7447", "7557", "7654", "7676", "7777", "7878",
        "7987", "8000", "8080", "8118", "8181", "8229", "8349",
        "8458", "8568", "8675", "8765", "8787", "8888", "8989",
        "9000", "9090", "9119", "9191", "9220", "9339", "9449",
        "9559", "9669", "9779", "9876", "9898", "9999",
    ]

def generer_dates():
    """Génère des PINs basés sur des dates (format MMDD et DDMM)."""
    dates = set()
    for mois in range(1, 13):
        for jour in range(1, 32):
            try:
                datetime(2024, mois, jour)
                dates.add(f"{mois:02d}{jour:02d}")
                dates.add(f"{jour:02d}{mois:02d}")
            except ValueError:
                pass
    return sorted(dates)

def generer_aleatoire(nb=1000, longueur=4):
    """Génère des PINs aléatoires."""
    pins = set()
    while len(pins) < nb:
        pins.add(''.join(str(random.randint(0, 9)) for _ in range(longueur)))
    return sorted(pins)

def exporter(pins, chemin, nom):
    """Exporte une liste de PINs vers un fichier."""
    chemin_complet = os.path.join(chemin, nom)
    with open(chemin_complet, 'w') as f:
        f.write('\n'.join(pins))
    print(f"  Créé: {chemin_complet} ({len(pins)} entrées)")
    return len(pins)

def main():
    parser = argparse.ArgumentParser(
        description="Générateur de dictionnaires de codes PIN"
    )
    parser.add_argument("--sortie", default="../dictionnaires",
                        help="Dossier de sortie")
    parser.add_argument("--types", nargs="+",
                        choices=["sequentiel", "patterns", "courants", "dates",
                                 "aleatoire", "complet"],
                        default=["sequentiel", "patterns", "courants"],
                        help="Types de dictionnaires à générer")
    parser.add_argument("--longueur", type=int, default=4,
                        help="Longueur des PINs séquentiels")
    parser.add_argument("--nb-aleatoire", type=int, default=500,
                        help="Nombre de PINs aléatoires")
    parser.add_argument("--stats", action="store_true",
                        help="Afficher les statistiques")

    args = parser.parse_args()

    dossier_sortie = os.path.join(os.path.dirname(__file__), args.sortie)
    os.makedirs(dossier_sortie, exist_ok=True)

    print("=" * 60)
    print("  GÉNÉRATEUR DE DICTIONNAIRES PIN")
    print("  Usage pédagogique uniquement")
    print("=" * 60)
    print(f"\n  Dossier sortie: {dossier_sortie}")
    print(f"  Types: {', '.join(args.types)}\n")

    total = 0

    if "sequentiel" in args.types:
        pins_seq = list(generer_sequentiel(args.longueur, fin=999))
        exporter(pins_seq, dossier_sortie, f"pins_sequentiels_{len(pins_seq)}.txt")

    if "patterns" in args.types:
        pins_pat = generer_patterns()
        exporter(pins_pat, dossier_sortie, "pins_patterns.txt")

    if "courants" in args.types:
        pins_cour = generer_courants()
        exporter(pins_cour, dossier_sortie, "pins_courants.txt")

    if "dates" in args.types:
        pins_dates = generer_dates()
        exporter(pins_dates, dossier_sortie, "pins_dates.txt")

    if "aleatoire" in args.types:
        pins_alea = generer_aleatoire(args.nb_aleatoire, args.longueur)
        exporter(pins_alea, dossier_sortie, "pins_aleatoires.txt")

    if "complet" in args.types:
        tous = set()
        tous.update(generer_sequentiel(args.longueur, fin=999))
        tous.update(generer_patterns())
        tous.update(generer_courants())
        tous.update(generer_dates())
        tous.update(generer_aleatoire(200, args.longueur))
        exporter(sorted(tous), dossier_sortie, "pins_complet.txt")

    if args.stats:
        print("\n  [STATISTIQUES]")
        for f in sorted(os.listdir(dossier_sortie)):
            if f.endswith('.txt'):
                path = os.path.join(dossier_sortie, f)
                with open(path) as fh:
                    lines = [l.strip() for l in fh if l.strip()]
                print(f"  {f:40s} {len(lines):6d} entrées")

    print("\n  Génération terminée.")

if __name__ == "__main__":
    main()
