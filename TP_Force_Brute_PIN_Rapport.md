# TP : Attaque par Force Brute sur Code PIN Android

**Auteur :** Oussama Mouhouchi  
**Date :** 05/06/2026  
**Environnement :** Ubuntu 24.04 - Cible : Redroid Android 14 (Docker, localhost:5555)  

---

## Introduction théorique

### Qu'est-ce qu'une attaque par force brute ?

Méthode exhaustive consistant à tester toutes les combinaisons possibles jusqu'à trouver la bonne. Garantie de succès mais coût temporel potentiellement rédhibitoire.

### Complexité théorique des codes PIN

| Longueur | Combinaisons | Temps (1 essai/s) | Temps (avec throttling 32s/4 essais) |
|----------|-------------|-------------------|--------------------------------------|
| 4 chiffres | 10 000 | ~2h45 | ~22 heures |
| 5 chiffres | 100 000 | ~27h45 | ~9 jours |
| 6 chiffres | 1 000 000 | ~11 jours | ~92 jours |
| 8 chiffres | 100 000 000 | ~3 ans | ~25 ans |

---

## Exercice 1 : Analyse du code source

### Script ADBBruteforce.py (conceptuel)

Le script génère les combinaisons avec `range(10 ** n)` et `str().zfill()` :

```python
for i in range(10 ** int(args.number)):
    combinations.append(str(i).zfill(int(args.number)))
```

**Questions :**
- **Génération :** `range(10^n)` boucle de 0 à 9999 pour PIN 4 chiffres, `zfill()` padde avec des zéros.
- **Commande ADB :** `adb shell input text <PIN>` puis `adb shell input keyevent 66` (ENTER).
- **Détection déverrouillage :** Surveillance de `dumpsys window` ou `dumpsys power` pour détecter l'état du verrouillage.
- **Délai :** `time.sleep(delai)` entre chaque tentative (configurable, défaut ~0.5s).

### Scripts fournis dans ce TP

| Script | Rôle |
|--------|------|
| `demo_bruteforce_limite.py` | Force brute limitée à 10 tentatives |
| `analyse_keycodes.py` | Mapping keycodes Android et séquences |
| `generer_dictionnaire.py` | Générateur de dictionnaires PIN |
| `android_keyboard_simulator.py` | Simulateur clavier via ADB |

---

## Exercice 2 : Configuration de l'environnement

### Vérifications

```bash
$ python3 --version
Python 3.12.3

$ adb devices
localhost:5555    device

$ adb -s localhost:5555 shell getprop ro.build.version.release
14

$ adb -s localhost:5555 shell locksettings set-pin 2580
Pin set to '2580'
```

### Appareil de test

- **Modèle :** Redroid 14.0.0 x86_64 (Docker)
- **PIN défini :** `2580`
- **Connexion :** ADB TCP (localhost:5555) avec root

---

## Exercice 3 : Simulation contrôlée

### Test des 10 premières combinaisons (0000-0009)

```
[0] PIN 0 -> incorrect
[1] PIN 1 -> incorrect
[2] PIN 2 -> incorrect
[3] PIN 3 -> incorrect
[4]→[9] THROTTLED (rate limiting activé après 4 essais)
```

### Observation du rate limiting

```
Essais 1-4:   Réponse immédiate (incorrect)
Essai 5:      "Request throttled"
Essai 6-30:   "Request throttled" (persistant)
Temps throttle: ~30 secondes
Après 30s:    Nouveau test possible ✓
```

### Test avec dictionnaire

| Dictionnaire | Entrées | PIN 2580 trouvé ? |
|-------------|---------|-------------------|
| `pins_courants.txt` | 85 | Non |
| `pins_patterns.txt` | 101 | Non |
| `pins_sequentiels_100.txt` | 100 | Non |
| **Test manuel direct** | 1 | **Oui ✓** |

### Mesure de performance

| Métrique | Valeur |
|----------|--------|
| Temps pour 30 essais (batch) | 34 954 ms |
| Temps moyen par essai (batch) | 1 165 ms |
| Essais avant throttling | 4 |
| Durée throttling | ~30 secondes |
| Essais par fenêtre de 32s | 4 |

---

## Exercice 4 : Analyse du simulateur clavier

### Keycodes Android pour les chiffres

| Touche | KeyCode | Constante |
|--------|---------|-----------|
| 0 | 7 | `KEYCODE_0` |
| 1 | 8 | `KEYCODE_1` |
| 2 | 9 | `KEYCODE_2` |
| 3 | 10 | `KEYCODE_3` |
| 4 | 11 | `KEYCODE_4` |
| 5 | 12 | `KEYCODE_5` |
| 6 | 13 | `KEYCODE_6` |
| 7 | 14 | `KEYCODE_7` |
| 8 | 15 | `KEYCODE_8` |
| 9 | 16 | `KEYCODE_9` |
| Entrée | 66 | `KEYCODE_ENTER` |
| Effacer | 67 | `KEYCODE_DEL` |

### Méthodes de saisie

```python
send_key_event(keycode)  # Envoi d'une touche (input keyevent)
type_text(text)          # Saisie de texte (input text)
press_enter()            # Validation (KEYCODE_ENTER)
```

**Exemple de séquence de déverrouillage :**
```bash
adb shell input keyevent 26         # Allumer écran
adb shell input keyevent 82         # Menu/déverrouillage
adb shell input text 2580           # Saisir PIN
adb shell input keyevent 66         # Valider
```

### Délais configurés

| Délai | Usage | Impact |
|-------|-------|--------|
| 0.1s | Entre keycodes | Minimise détection |
| 0.5s | Après wake | Stabilisation écran |
| 1.0s | Recommandé entre tentatives | Évite throttling UI |
| 32s | Minimum entre lots (via locksettings) | Contourne throttling |

---

## Exercice 5 : Contre-mesures Android

### Mécanismes de protection observés

| Mécanisme | Observation | Seuil |
|-----------|-------------|-------|
| **Throttling** | "Request throttled" après 4-5 essais | ~4 essais, durée ~30s |
| **Verrouillage** | Pas de verrouillage permanent observé (root ADB) | N/A |
| **Effacement** | Non configuré sur redroid | Optionnel |
| **Biométrie** | Non disponible sur redroid | Hardware dépendant |
| **Secure Element** | Géré par TEE (Trusted Execution Environment) | Matériel |

### Analyse détaillée

**1. Délai exponentiel :**
- Android implémente un délai croissant (30s, 1min, 5min, 30min, 1h)
- Via `locksettings` command, le throttle est de ~30s constant
- L'interface utilisateur a des délais plus stricts que l'API shell

**2. Verrouillage temporaire :**
- Après 5 échecs : verrouillage 30s
- Après 10 échecs : verrouillage 1min
- Après 15+ échecs : escalade jusqu'à 24h
- Effacement possible après 10 échecs (paramétrable)

**3. Effacement automatique :**
```bash
# Activer effacement après 10 échecs
adb shell locksettings set-disabled --old <PIN> false

# Via paramètres Android
Paramètres > Sécurité > Verrouillage écran > Effacer données
```

**4. Biométrie :**
- Empreinte, visage, iris
- Complète le PIN (déverrouillage sans code)
- Limite : contournée si biométrie non disponible
- Stockée dans TrustZone/TEE séparément

**5. Chiffrement :**
- FDE (Full Disk Encryption) : chiffre toutes les données
- PIN requis au démarrage (Before First Unlock - BFU)
- Après déverrouillage : After First Unlock (AFU) - mémoire vive
- Le PIN protège la clé de déchiffrement, pas les données directement

---

## Analyse de sécurité

### Vulnérabilités exploitées

| Vulnérabilité | Impact | Niveau de risque |
|--------------|--------|------------------|
| Interface ADB activée | Contrôle à distance complet | Critique |
| Root sur l'appareil | Bypass des restrictions utilisateur | Critique |
| `locksettings` API accessible | Brute force sans UI | Élevé |
| Throttling court (30s) | 4 essais/32s ≈ 450/jour | Moyen |
| PIN 4 chiffres | Seulement 10 000 combinaisons | Faible |

### Facteurs limitants

| Facteur | Impact réel sur l'attaque |
|---------|--------------------------|
| **Throttling** | ~30s après 4 essais → max ~11 520 essais/jour (théorique) |
| **Détection** | L'écran s'allume à chaque tentative (via UI) |
| **ADB débranché** | Mode non-root : vérification via UI seulement |
| **Samsung/Google** | Délais > 24h après 20 échecs (One UI, Pixel) |

### Tableau comparatif : DigiSpark vs ADB

| Critère | DigiSpark (USB HID) | ADB (shell) |
|---------|--------------------|-------------|
| **Cible** | Appareil physique | Appareil avec ADB |
| **Débit** | ~50 essais/min | ~240 essais/min (batch) |
| **Détection** | Émulation clavier | Commande système |
| **Root requis** | Non | Oui (pour locksettings) |
| **Portabilité** | Matériel dédié | Simple câble USB |
| **Throttling** | Interface utilisateur | Shell (moins strict) |

---

## Recommandations

### Pour les utilisateurs

1. **PIN à 6 chiffres minimum** → 1M combinaisons
2. **PIN alphanumérique** si possible → 36^4 = 1.6M combinaisons
3. **Éviter les PINs courants** (1234, 0000, dates, années)
4. **Activer l'effacement automatique** après 10 échecs
5. **Désactiver ADB** sur l'appareil en condition normale

### Pour les développeurs

1. **Rate limiting côté serveur** (même pour les API système)
2. **Délai exponentiel** : 1s → 5s → 30s → 5min → 1h
3. **Notification utilisateur** après chaque tentative échouée
4. **Biométrie comme facteur supplémentaire** (multi-factor)
5. **Journalisation** des tentatives pour détection d'intrusion

### Pour les fabricants

1. **Désactiver `locksettings` shell en mode non-root**
2. **Imposer un délai minimum** entre les appels API
3. **Hardware rate limiter** dans le secure element
4. **Délai exponentiel côté Trusted Execution Environment (TEE)**
5. **Wipe data après X échecs** (option activée par défaut)

---

## Conclusion

Cette analyse démontre que brute-forcer un PIN Android est théoriquement possible mais **pratiquement limité** par :

- **Throttling système** (~30s après 4 essais → max 450 PINs/jour)
- **Détection physique** (écran allumé, notifications)
- **Verrouillage progressif** (jusqu'à 24h sur matériel récent)
- **Complexité** : un PIN à 6 chiffres nécessite ~9 jours avec throttling

L'attaque via ADB root (`locksettings verify --old <PIN>`) contourne partiellement ces mécanismes mais reste limitée. La combinaison **PIN long + effacement auto + biométrie + ADB désactivé** offre une protection robuste.

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `TP_Force_Brute_PIN_Rapport.md` | Ce rapport |
| `scripts/demo_bruteforce_limite.py` | Force brute limitée (10 essais) |
| `scripts/analyse_keycodes.py` | Analyse des keycodes Android |
| `scripts/generer_dictionnaire.py` | Générateur de dictionnaires |
| `scripts/android_keyboard_simulator.py` | Simulateur clavier ADB |
| `dictionnaires/pins_courants.txt` | 85 PINs les plus courants |
| `dictionnaires/pins_patterns.txt` | 101 PINs basés sur motifs |
| `dictionnaires/pins_sequentiels_100.txt` | 100 PINs séquentiels |
| `dictionnaires/pins_combines.txt` | Fusion des 3 dictionnaires |

---

## Réponses aux questions de compréhension

### Q1 : Temps pour PIN 5 chiffres (1 essai/s)

10^5 = 100 000 combinaisons × 1s = **~27h45** (théorique).  
Avec throttling réel (4 essais/32s) : **~9 jours**.

### Q2 : PINs alphanumériques vs numériques

36 caractères (A-Z + 0-9) vs 10 chiffres → **360 000** combinaisons pour 4 caractères (vs 10 000), soit **36× plus complexe**.

### Q3 : DigiSpark vs ADB

| Aspect | DigiSpark | ADB |
|--------|-----------|-----|
| Matériel | Nécessite ATTiny85 | Simple câble USB |
| Débit | ~50/min (UI) | ~240/min (batch avec locksettings) |
| Furtivité | Émulation HID (visible) | Commande système (invisible) |
| Root | Non requis | Requis pour locksettings |

### Q4 : Protection Android

- Délai exponentiel
- Verrouillage temporaire
- Effacement des données
- Chiffrement FDE
- Secure Element (TEE)
- Limitation des tentatives API
