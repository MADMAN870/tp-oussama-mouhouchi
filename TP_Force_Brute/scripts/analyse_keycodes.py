#!/usr/bin/env python3
"""
analyse_keycodes.py - Analyse des keycodes Android pour simulation clavier
via ADB. Étudie les codes de touches utilisés pour la saisie de PIN.
"""

ANDROID_KEYCODES = {
    0: "KEYCODE_UNKNOWN",
    1: "KEYCODE_MENU",
    2: "KEYCODE_SOFT_RIGHT",
    3: "KEYCODE_HOME",
    4: "KEYCODE_BACK",
    5: "KEYCODE_CALL",
    6: "KEYCODE_ENDCALL",
    7: "KEYCODE_0",
    8: "KEYCODE_1",
    9: "KEYCODE_2",
    10: "KEYCODE_3",
    11: "KEYCODE_4",
    12: "KEYCODE_5",
    13: "KEYCODE_6",
    14: "KEYCODE_7",
    15: "KEYCODE_8",
    16: "KEYCODE_9",
    17: "KEYCODE_STAR",
    18: "KEYCODE_POUND",
    19: "KEYCODE_DPAD_UP",
    20: "KEYCODE_DPAD_DOWN",
    21: "KEYCODE_DPAD_LEFT",
    22: "KEYCODE_DPAD_RIGHT",
    23: "KEYCODE_DPAD_CENTER",
    24: "KEYCODE_VOLUME_UP",
    25: "KEYCODE_VOLUME_DOWN",
    26: "KEYCODE_POWER",
    27: "KEYCODE_CAMERA",
    28: "KEYCODE_CLEAR",
    29: "KEYCODE_A",
    30: "KEYCODE_B",
    31: "KEYCODE_C",
    32: "KEYCODE_D",
    33: "KEYCODE_E",
    34: "KEYCODE_F",
    35: "KEYCODE_G",
    36: "KEYCODE_H",
    37: "KEYCODE_I",
    38: "KEYCODE_J",
    39: "KEYCODE_K",
    40: "KEYCODE_L",
    41: "KEYCODE_M",
    42: "KEYCODE_N",
    43: "KEYCODE_O",
    44: "KEYCODE_P",
    45: "KEYCODE_Q",
    46: "KEYCODE_R",
    47: "KEYCODE_S",
    48: "KEYCODE_T",
    49: "KEYCODE_U",
    50: "KEYCODE_V",
    51: "KEYCODE_W",
    52: "KEYCODE_X",
    53: "KEYCODE_Y",
    54: "KEYCODE_Z",
    55: "KEYCODE_COMMA",
    56: "KEYCODE_PERIOD",
    57: "KEYCODE_ALT_LEFT",
    58: "KEYCODE_ALT_RIGHT",
    59: "KEYCODE_SHIFT_LEFT",
    60: "KEYCODE_SHIFT_RIGHT",
    61: "KEYCODE_TAB",
    62: "KEYCODE_SPACE",
    63: "KEYCODE_SYM",
    64: "KEYCODE_EXPLORER",
    65: "KEYCODE_ENVELOPE",
    66: "KEYCODE_ENTER",
    67: "KEYCODE_DEL",
    68: "KEYCODE_GRAVE",
    69: "KEYCODE_MINUS",
    70: "KEYCODE_EQUALS",
    71: "KEYCODE_LEFT_BRACKET",
    72: "KEYCODE_RIGHT_BRACKET",
    73: "KEYCODE_BACKSLASH",
    74: "KEYCODE_SEMICOLON",
    75: "KEYCODE_APOSTROPHE",
    76: "KEYCODE_SLASH",
    77: "KEYCODE_AT",
    78: "KEYCODE_NUM",
    79: "KEYCODE_HEADSETHOOK",
    80: "KEYCODE_FOCUS",
    81: "KEYCODE_PLUS",
    82: "KEYCODE_MENU",
    83: "KEYCODE_NOTIFICATION",
    84: "KEYCODE_SEARCH",
    85: "KEYCODE_TAG_LAST",
}

KEYCODES_CHIFFRES = {
    '0': 7, '1': 8, '2': 9, '3': 10, '4': 11,
    '5': 12, '6': 13, '7': 14, '8': 15, '9': 16,
}

def simuler_saisie_pin(pin):
    """
    Génère les commandes ADB pour simuler la saisie d'un PIN.
    Retourne une liste de commandes input keyevent.

    Deux méthodes :
    1. input keyevent <KEYCODE> : Envoie un événement clavier
    2. input text <TEXTE> : Saisit du texte directement
    """
    print(f"  PIN: {pin}")
    print(f"  Méthode 1 - keyevent individuel:")
    for c in pin:
        kc = KEYCODES_CHIFFRES[c]
        print(f"    adb shell input keyevent {kc}  # {ANDROID_KEYCODES[kc]}")
    print(f"    adb shell input keyevent 66     # KEYCODE_ENTER (validation)")

    print(f"  Méthode 2 - input text:")
    print(f"    adb shell input text {pin}")
    print(f"    adb shell input keyevent 66     # KEYCODE_ENTER (validation)")
    print()

def analyser_saisie_ecran_verrouillage():
    """
    Analyse du flux d'événements pour déverrouillage d'écran.
    """
    print("  Séquences de déverrouillage courantes via ADB:")
    print()

    sequences = {
        "PIN simple": [
            ("input keyevent 26", "Allumer l'écran"),
            ("input keyevent 82", "Déverrouiller (swipe)"),
            ("input text 1234", "Saisir le PIN"),
            ("input keyevent 66", "Valider"),
        ],
        "Swipe puis PIN": [
            ("input keyevent 26", "Allumer l'écran"),
            ("input touchscreen swipe 300 1000 300 500", "Swipe vers le haut"),
            ("input keyevent 8", "Touche 1"),
            ("input keyevent 9", "Touche 2"),
            ("input keyevent 10", "Touche 3"),
            ("input keyevent 11", "Touche 4"),
            ("input keyevent 66", "Valider"),
        ],
        "PIN avec délai": [
            ("input keyevent 26", "Allumer l'écran"),
            ("sleep 0.5", "Attendre"),
            ("input touchscreen swipe 300 1000 300 500", "Swipe"),
            ("sleep 0.3", "Attendre"),
            ("input text 0000", "Saisir PIN"),
            ("input keyevent 66", "Valider"),
        ],
    }

    for nom, cmds in sequences.items():
        print(f"  [{nom}]")
        for cmd, desc in cmds:
            print(f"    adb shell {cmd:50s} # {desc}")
        print()

def tester_entree_clavier_via_adb():
    """
    Teste la saisie clavier simulée via ADB sur l'appareil cible.
    """
    import subprocess

    ADB_TARGET = "localhost:5555"

    def adb(cmd):
        result = subprocess.run(
            f"adb -s {ADB_TARGET} shell {cmd}",
            shell=True, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip(), result.returncode

    print("  Test des méthodes de saisie ADB:")

    # Test 1: input text
    print(f"\n  1. input text 'test123':")
    stdout, rc = adb("input text 'test123'")
    print(f"     Retour: {stdout[:100] if stdout else 'OK'}")

    # Test 2: keyevent individuels
    print(f"\n  2. input keyevent 8 9 10 11 (1 2 3 4):")
    for kc in [8, 9, 10, 11]:
        stdout, rc = adb(f"input keyevent {kc}")
    print(f"     Retour: OK")

    # Test 3: ENTER
    print(f"\n  3. input keyevent 66 (ENTER):")
    stdout, rc = adb("input keyevent 66")
    print(f"     Retour: {stdout[:100] if stdout else 'OK'}")

    # Test 4: DEL
    print(f"\n  4. input keyevent 67 (DEL):")
    stdout, rc = adb("input keyevent 67")
    print(f"     Retour: {stdout[:100] if stdout else 'OK'}")

def main():
    print("=" * 60)
    print("  ANALYSE DES KEYCODES ANDROID")
    print("  Simulation de clavier via ADB")
    print("=" * 60)

    # Partie 1: Mapping keycodes chiffres
    print("\n[1] KEYCODES DES CHIFFRES\n")
    print("  Touche   | KeyCode | Nom")
    print("  ---------|---------|-------------------")
    for chiffre in '0123456789':
        kc = KEYCODES_CHIFFRES[chiffre]
        print(f"  {chiffre}         | {kc}       | {ANDROID_KEYCODES[kc]}")

    # Partie 2: Simulation saisie PIN
    print("\n[2] SIMULATION DE SAISIE PIN\n")
    for pin in ["1234", "0000", "9876", "2580"]:
        simuler_saisie_pin(pin)

    # Partie 3: Séquences de déverrouillage
    print("[3] SÉQUENCES DE DÉVERROUILLAGE\n")
    analyser_saisie_ecran_verrouillage()

    # Partie 4: Codes spéciaux importants
    print("[4] CODES SPÉCIAUX POUR BRUTE FORCE\n")
    specs = [
        (66, "KEYCODE_ENTER", "Valider le PIN"),
        (67, "KEYCODE_DEL", "Effacer un caractère"),
        (4, "KEYCODE_BACK", "Revenir en arrière"),
        (26, "KEYCODE_POWER", "Allumer/éteindre l'écran"),
        (82, "KEYCODE_MENU", "Ouvrir le menu / déverrouiller"),
        (28, "KEYCODE_CLEAR", "Effacer tout le champ"),
        (61, "KEYCODE_TAB", "Changer de champ"),
        (62, "KEYCODE_SPACE", "Espace"),
    ]
    for kc, nom, desc in specs:
        print(f"  KeyCode {kc:2d} ({nom:20s}) - {desc}")

    # Partie 5: Délais recommandés
    print("\n[5] DÉLAIS RECOMMANDÉS ENTRE TENTATIVES\n")
    delais = [
        (0.0, "Immédiat", "Détecté immédiatement, risque de verrouillage rapide"),
        (0.5, "Rapide", "Peut passer inaperçu, 5h pour 10k combinaisons"),
        (1.0, "Modéré", "Équilibre risque/vitesse, 2h45 pour 10k combinaisons"),
        (2.0, "Lent", "Discret, mais 5h30 pour 10k combinaisons"),
        (5.0, "Très lent", "Très discret, 14h pour 10k combinaisons"),
    ]
    for delai, nom, desc in delais:
        total_pins = 10000
        temps_total = total_pins * delai
        print(f"  {delai:4.1f}s ({nom:12s}) - {desc}")
        print(f"      Temps total pour {total_pins} combinaisons: {temps_total/3600:.1f}h")

    # Partie 6: Test réel si ADB disponible
    print("\n[6] TEST RÉEL VIA ADB\n")
    try:
        tester_entree_clavier_via_adb()
    except Exception as e:
        print(f"  Test non disponible: {e}")

    print("\n" + "=" * 60)
    print("  ANALYSE TERMINÉE")
    print("=" * 60)

if __name__ == "__main__":
    main()
