#!/usr/bin/env python3
"""
android_keyboard_simulator.py - Simulateur de clavier Android via ADB.
Automatise la saisie de codes PIN pour tests de sécurité.

Méthodes disponibles :
  - send_key_event(keycode) : Envoi d'une touche
  - type_text(text) : Saisie de texte
  - press_enter() : Validation

Usage:
    python android_keyboard_simulator.py --pin 1234
    python android_keyboard_simulator.py --bruteforce --max-attempts 10
"""

import subprocess
import time
import sys
import argparse

ADB_TARGET = "localhost:5555"

class AndroidKeyboardSimulator:
    """Simulateur de clavier Android via ADB."""

    KEYCODE_0 = 7
    KEYCODE_1 = 8
    KEYCODE_2 = 9
    KEYCODE_3 = 10
    KEYCODE_4 = 11
    KEYCODE_5 = 12
    KEYCODE_6 = 13
    KEYCODE_7 = 14
    KEYCODE_8 = 15
    KEYCODE_9 = 16
    KEYCODE_ENTER = 66
    KEYCODE_DEL = 67
    KEYCODE_CLEAR = 28
    KEYCODE_POWER = 26
    KEYCODE_MENU = 82
    KEYCODE_BACK = 4
    KEYCODE_HOME = 3

    CHIFFRES_KEYCODES = {
        '0': KEYCODE_0, '1': KEYCODE_1, '2': KEYCODE_2, '3': KEYCODE_3,
        '4': KEYCODE_4, '5': KEYCODE_5, '6': KEYCODE_6, '7': KEYCODE_7,
        '8': KEYCODE_8, '9': KEYCODE_9,
    }

    def __init__(self, target=ADB_TARGET, delai_inter_touche=0.1):
        self.target = target
        self.delai_inter_touche = delai_inter_touche
        self._verifier_connexion()

    def _verifier_connexion(self):
        try:
            result = subprocess.run(
                f"adb -s {self.target} get-state",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise ConnectionError(f"ADB non connecté à {self.target}")
        except subprocess.TimeoutExpired:
            raise ConnectionError("Timeout connexion ADB")

    def _adb_shell(self, cmd):
        """Exécute une commande ADB shell."""
        result = subprocess.run(
            f"adb -s {self.target} shell {cmd}",
            shell=True, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip(), result.returncode

    def send_key_event(self, keycode):
        """Envoie un événement clavier."""
        stdout, rc = self._adb_shell(f"input keyevent {keycode}")
        time.sleep(self.delai_inter_touche)
        return rc == 0

    def type_text(self, text):
        """Saisit du texte via ADB."""
        stdout, rc = self._adb_shell(f"input text '{text}'")
        time.sleep(self.delai_inter_touche * 2)
        return rc == 0

    def press_enter(self):
        """Simule la touche Entrée."""
        return self.send_key_event(self.KEYCODE_ENTER)

    def press_del(self):
        """Simule la touche Suppr."""
        return self.send_key_event(self.KEYCODE_DEL)

    def press_power(self):
        """Simule le bouton Power."""
        return self.send_key_event(self.KEYCODE_POWER)

    def press_back(self):
        """Simule le bouton Back."""
        return self.send_key_event(self.KEYCODE_BACK)

    def wake_screen(self):
        """Allume l'écran."""
        self.press_power()
        time.sleep(0.5)
        self.send_key_event(self.KEYCODE_MENU)

    def enter_pin_keyevent(self, pin):
        """Saisit un PIN via keyevents individuels."""
        for c in pin:
            if c in self.CHIFFRES_KEYCODES:
                if not self.send_key_event(self.CHIFFRES_KEYCODES[c]):
                    return False
        return self.press_enter()

    def enter_pin_text(self, pin):
        """Saisit un PIN via input text."""
        return self.type_text(pin) and self.press_enter()

    def unlock_with_pin(self, pin, method="keyevent"):
        """Tente de déverrouiller avec un PIN."""
        self.wake_screen()
        time.sleep(0.5)
        if method == "keyevent":
            return self.enter_pin_keyevent(pin)
        else:
            return self.enter_pin_text(pin)

    def verify_pin(self, pin):
        """Vérifie un PIN via locksettings (sans écran)."""
        stdout, rc = self._adb_shell(f"locksettings verify --old {pin}")
        if "verified successfully" in stdout.lower():
            return True
        elif "didn't match" in stdout.lower():
            return False
        else:
            return None

    def clear_field(self):
        """Efface le champ de saisie."""
        for _ in range(10):
            self.send_key_event(self.KEYCODE_DEL)
        return True

    def get_keycode_for_digit(self, digit):
        """Retourne le keycode pour un chiffre."""
        return self.CHIFFRES_KEYCODES.get(digit, None)

    @staticmethod
    def liste_keycodes():
        """Affiche la liste des keycodes importants."""
        return {
            7: "KEYCODE_0", 8: "KEYCODE_1", 9: "KEYCODE_2",
            10: "KEYCODE_3", 11: "KEYCODE_4", 12: "KEYCODE_5",
            13: "KEYCODE_6", 14: "KEYCODE_7", 15: "KEYCODE_8",
            16: "KEYCODE_9", 66: "KEYCODE_ENTER", 67: "KEYCODE_DEL",
            26: "KEYCODE_POWER", 82: "KEYCODE_MENU",
        }


def demo_simulation(kbd):
    """Démonstration des fonctionnalités du simulateur."""
    print("[1] Test envoi keycode (KEYCODE_MENU)")
    ok = kbd.send_key_event(82)
    print(f"  Résultat: {'✓' if ok else '✗'}")

    print("\n[2] Test type_text (hello)")
    ok = kbd.type_text("hello")
    print(f"  Résultat: {'✓' if ok else '✗'}")

    print("\n[3] Saisie PIN 1234 via keyevents")
    ok = kbd.enter_pin_keyevent("1234")
    print(f"  Résultat: {'✓' if ok else '✗'}")

    print(f"\n[4] Vérification PIN via locksettings (sans écran)")
    for pin in ["1234", "0000"]:
        ok = kbd.verify_pin(pin)
        print(f"  PIN {pin}: {'✓ correct' if ok else '✗ incorrect' if ok is False else '?'}")
        time.sleep(0.5)


def bruteforce_demo(kbd, pin_cible="1234", max_attempts=10):
    """Démonstration de force brute avec vérification directe."""
    print(f"\n[+] Force brute sur PIN {pin_cible}")
    print(f"  Méthode: locksettings verify (pas d'UI)")
    print(f"  Max essais: {max_attempts}\n")

    for i in range(10 ** 4):
        pin = str(i).zfill(4)
        if i >= max_attempts:
            print(f"\n[FIN] Limite de {max_attempts} essais atteinte")
            break

        ok = kbd.verify_pin(pin)
        if ok:
            print(f"  ✓ PIN trouvé: {pin} (essai #{i+1})")
            return pin
        else:
            if (i + 1) % 5 == 0 or i == 0:
                print(f"  [{i+1:3d}] PIN {pin} incorrect", end="\r")
        time.sleep(0.1)

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Simulateur de clavier Android pour tests PIN"
    )
    parser.add_argument("--pin", help="PIN à tester")
    parser.add_argument("--bruteforce", action="store_true",
                        help="Mode force brute")
    parser.add_argument("--max-attempts", type=int, default=10,
                        help="Nombre max de tentatives")
    parser.add_argument("--method", choices=["keyevent", "text"], default="keyevent",
                        help="Méthode de saisie")
    parser.add_argument("--demo", action="store_true",
                        help="Mode démonstration")
    parser.add_argument("--keycodes", action="store_true",
                        help="Afficher les keycodes")

    args = parser.parse_args()

    if args.keycodes:
        print("Keycodes Android pour chiffres:")
        kc = AndroidKeyboardSimulator.liste_keycodes()
        for code, name in sorted(kc.items()):
            print(f"  {code}: {name}")
        return

    try:
        kbd = AndroidKeyboardSimulator()
        print(f"Connecté à {ADB_TARGET}")
    except (ConnectionError, subprocess.TimeoutExpired) as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)

    if args.demo:
        demo_simulation(kbd)
    elif args.bruteforce:
        bruteforce_demo(kbd, args.pin or "1234", args.max_attempts)
    elif args.pin:
        print(f"\nTest PIN {args.pin}...")
        ok = kbd.verify_pin(args.pin)
        if ok:
            print(f"  PIN correct!")
        else:
            print(f"  PIN incorrect")
    else:
        print("Utilisation: python android_keyboard_simulator.py --pin <PIN>")
        print("             python android_keyboard_simulator.py --bruteforce --max-attempts 10")
        print("             python android_keyboard_simulator.py --demo")
        print("             python android_keyboard_simulator.py --keycodes")


if __name__ == "__main__":
    main()
