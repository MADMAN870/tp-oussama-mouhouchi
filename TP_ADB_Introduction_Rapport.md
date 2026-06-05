# TP - Introduction à ADB (Android Debug Bridge)
## Rapport d'Analyse - Oussama MOUHOUCHI 4IIRCIRA

---

## Informations Générales

**Plateforme hôte :** Ubuntu 24.04 LTS - x86_64  
**Appareil cible :** Redroid (Android 14 - x86_64) en conteneur Docker  
**ADB version :** 1.0.41 (34.0.4-debian)  
**Date :** 05/06/2026  

---

## Architecture ADB

ADB fonctionne selon un modèle client-serveur à 3 composants :

```
┌──────────────┐     port 5037     ┌──────────────┐     TCP:5555     ┌──────────────────┐
│   Client     │◄──────────────►│   Serveur     │◄──────────────►│   Démon (adbd)   │
│  (PC/Linux)  │                  │  (PC/Linux)   │                  │  (Android/Redroid)│
└──────────────┘                  └──────────────┘                  └──────────────────┘
```

- **Client** : commandes ADB tapées dans le terminal
- **Serveur** : processus arrière-plan sur le PC (port 5037)
- **Démon (adbd)** : s'exécute sur l'appareil Android (port 5555)

---

## Exercice 1 : Installation d'ADB

ADB déjà installé via le package `android-sdk-platform-tools` :

```bash
$ adb version
Android Debug Bridge version 1.0.41
Version 34.0.4-debian
Installed as /usr/lib/android-sdk/platform-tools/adb
```

---

## Exercice 2 : Activation du débogage USB

Sur redroid, le débogage est activé par défaut (image `userdebug`). Aucune manipulation nécessaire.

```bash
# Vérification du type de build
$ adb -s localhost:5555 shell getprop ro.build.type
userdebug
```

---

## Exercice 3 : Première connexion

```bash
$ adb devices -l
List of devices attached
emulator-5554          device product:redroid_x86_64_only model:redroid14_x86_64_only
localhost:5555         device product:redroid_x86_64_only model:redroid14_x86_64_only
```

**Deux connexions actives :**
- `emulator-5554` : connexion interne du conteneur
- `localhost:5555` : connexion TCP depuis l'hôte

---

## Exercice 4 : Commandes ADB essentielles

| Commande | Résultat |
|:---------|:---------|
| `getprop ro.product.model` | `redroid14_x86_64_only` |
| `getprop ro.build.version.release` | `14` |
| `getprop ro.build.version.sdk` | `34` |
| `pm list packages` | 113 packages installés |
| `screencap -p > screenshot.png` | PNG 1080×1920 (1.2 MB) |
| `df -h /` | Overlay 233G (22G libre) |

```bash
# Capture d'écran de redroid
adb -s localhost:5555 exec-out screencap -p > /tmp/screenshot_redroid.png
```

---

## Exercice 5 : Connexion sans fil

Redroid est déjà accessible via TCP (pas besoin de câble USB ni de WiFi).

```bash
# Adresse IP du conteneur
$ adb -s localhost:5555 shell ip addr show eth0
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0

# Connexion directe via Docker
$ adb connect localhost:5555
connected to localhost:5555
```

**Procédure standard (pour un vrai appareil) :**
```bash
adb usb                    # Connexion USB
adb shell ip addr show wlan0  # Obtenir IP
adb tcpip 5555             # Activer TCP/IP
# Débrancher le câble
adb connect <IP>:5555      # Connexion WiFi
```

---

## Exercice 6 : Extraction de données système

```bash
# Toutes les propriétés système
$ adb shell getprop | wc -l
560 propriétés

# Fingerprint Android
$ adb shell getprop ro.build.fingerprint
redroid/redroid_x86_64_only/redroid_x86_64_only:14/UD2A.240505.001.W1/eng.frank.20240527.155732:userdebug/test-keys

# Patch de sécurité
$ adb shell getprop ro.build.version.security_patch
2024-05-05

# Services système
$ adb shell service list | wc -l
238 services

# État de la batterie (redroid : sans batterie réelle)
$ adb shell dumpsys battery
  status: 2
  level: 0
  temperature: 0
```

**Sauvegarde des propriétés :**
```bash
adb shell getprop > system_properties.txt
adb logcat -d > logs.txt
```

---

## Exercice 7 : Gestion des applications

| Commande | Résultat |
|:---------|:---------|
| `pm list packages -s` | 113 applications système |
| `pm list packages -3` | 0 applications tierces |
| `pm list packages -d` | `com.android.nfc` (désactivée) |
| `pm path com.android.settings` | `/system/system_ext/priv-app/Settings/Settings.apk` |

```bash
# Forcer l'arrêt d'une app
adb shell am force-stop com.android.settings

# Lister les APK système
adb shell pm list packages -f | head -5
package:/system/system_ext/priv-app/Launcher3/Launcher3.apk=com.android.launcher3
package:/system/system_ext/priv-app/Settings/Settings.apk=com.android.settings
...
```

---

## Exercice 8 : Logcat et débogage

```bash
# Logs d'erreur uniquement
$ adb logcat -d *:E
--------- beginning of kernel
06-05 13:03:57.088 E init    : mkdir("/dev/pts", 0755) failed File exists
06-05 13:03:57.088 E init    : mount("sysfs", "/sys", "sysfs", 0, NULL) failed Device or resource busy
...
--------- beginning of system
06-05 13:03:57.507 E vold    : Failed to opendir: No such file or directory

# Sauvegarde complète
$ adb logcat -d > redroid_logcat.txt
# Résultat : 24 571 lignes de logs
```

---

## Exercice 9 : Manipulation du système de fichiers

```bash
# Structure racine
$ adb shell ls -la /
drwxr-xr-x   root   root    .dockerenv
drwxr-xr-x   root   root    acct
drwxr-xr-x   root   root    apex
lrwxrwxrwx   root   root    bin -> /system/bin
drwxr-xr-x   root   root    data
drwxr-xr-x   root   root    dev
drwxr-xr-x   root   root    etc -> /system/etc
drwxr-xr-x   root   root    system
drwxr-xr-x   root   root    sdcard

# Transfert de fichiers (push/pull)
$ adb push /tmp/test_push.txt /sdcard/
$ adb shell cat /sdcard/test_push.txt
Hello from ADB
$ adb pull /sdcard/test_push.txt /tmp/test_pulled.txt

# Espace disque
$ adb shell df -h
Filesystem      Size  Used Avail Use% Mounted on
overlay         233G  211G   22G  91% /
/dev/sda2       233G  211G   22G  91% /data
/dev/fuse       233G  211G   22G  91% /mnt/user/0/emulated

# Recherche de fichiers
$ adb shell find /sdcard -name "*.png" -type f
/sdcard/Pictures/Screenshots/screenshot_1726645543.png
```

---

## Exercice 10 : Simulation d'entrées utilisateur

```bash
# Touches système
adb shell input keyevent KEYCODE_HOME    # Accueil
adb shell input keyevent KEYCODE_BACK    # Retour
adb shell input keyevent KEYCODE_POWER   # Veille

# Saisie de texte
adb shell input text "HelloADB"

# Tap (clic) à une position donnée
adb shell input tap 500 500

# Swipe (glissement)
adb shell input swipe 100 500 400 500 300
```

**Touches utiles (keyevent) :**

| Code | Action |
|:----:|:-------|
| 3 | HOME |
| 4 | BACK |
| 24 | VOLUME_UP |
| 25 | VOLUME_DOWN |
| 26 | POWER |
| 82 | MENU |
| 84 | SEARCH |
| 187 | RECENT_APPS |

---

## Exercice 11 : Backup et restauration

**Note :** `adb backup` est déprécié depuis Android 14 et nécessite une confirmation sur l'écran de l'appareil. Sans interface graphique, la commande bloque.

```bash
# Backup complet (nécessite interaction utilisateur)
$ adb backup -apk -shared -all -f backup.ab
Now unlock your device and confirm the backup operation...

# Alternative : extraction d'APK depuis le chemin
$ adb shell pm path com.android.settings
package:/system/system_ext/priv-app/Settings/Settings.apk

# Extraction d'une APK
$ adb pull /system/system_ext/priv-app/Settings/Settings.apk settings.apk
```

---

## Analyse de sécurité

### Risques identifiés avec ADB

| Risque | Description | Niveau |
|:-------|:------------|:------:|
| Accès complet | ADB donne un shell root (userdebug) | **Critique** |
| Extraction de données | Pull de fichiers sensibles, APK, logs | **Élevé** |
| Installation d'APK | Possibilité de sideloader des apps non signées | **Élevé** |
| Exécution de commandes | Accès shell avec privilèges `root` | **Critique** |
| Capture d'écran/Keylogging | screencap + input tap/text | **Élevé** |

### Bonnes pratiques

1. **Désactiver le débogage USB** après utilisation
2. **Ne pas connecter** l'appareil à des PC non fiables
3. **Révoquer les autorisations** régulièrement :
   ```bash
   adb usb           # Repasser en mode USB
   adb kill-server   # Arrêter le serveur ADB
   ```
4. **Utiliser `adb shell` avec prudence** — les commandes sont exécutées en tant que `root` sur userdebug
5. **Surveiller les connexions ADB** :
   ```bash
   adb devices               # Lister les connexions actives
   netstat -an | grep 5555   # Vérifier qui écoute sur le port
   ```

---

## Synthèse des commandes

### Cheatsheet

```bash
# Découverte
adb devices              # Lister les appareils
adb start-server         # Démarrer le serveur
adb kill-server          # Arrêter le serveur

# Connexion
adb connect <IP>:5555    # WiFi
adb usb                  # USB
adb tcpip 5555           # Passage en mode TCP

# Informations
adb shell getprop        # Propriétés système
adb shell service list   # Services
adb shell dumpsys        # Diagnostics

# Applications
adb shell pm list packages  # Lister les apps
adb shell pm path <pkg>     # Chemin APK
adb shell pm clear <pkg>    # Vider cache
adb shell am force-stop <pkg>  # Forcer arrêt

# Fichiers
adb push <local> <remote>   # Copier PC → Appareil
adb pull <remote> <local>   # Copier Appareil → PC
adb shell ls -la /sdcard/   # Explorer

# Capture
adb exec-out screencap -p > screen.png  # Screenshot
adb shell screenrecord /sdcard/video.mp4  # Enregistrement
adb logcat -d > logs.txt                  # Logs

# Input
adb shell input tap x y           # Clic
adb shell input swipe x1 y1 x2 y2 # Glissement
adb shell input text "Hello"      # Texte
adb shell input keyevent <code>   # Touche

# Backup
adb backup -apk -all -f backup.ab   # Backup complet
adb restore backup.ab               # Restauration
```

**Nombre total de commandes exécutées :** 50+  
**Données extraites :** Screenshot (1080×1920), 560 propriétés système, 24571 lignes de logs  
**Applications :** 113 système, 0 tierce, 1 désactivée (NFC)

---

**Rapport TP ADB terminé — Tous les exercices réalisés sur redroid (Android 14).**
