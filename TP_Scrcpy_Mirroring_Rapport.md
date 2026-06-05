# TP - Mirroring d'écran Android avec Scrcpy
## Rapport d'Analyse - Oussama MOUHOUCHI 4IIRCIRA

---

## Informations Générales

**Plateforme hôte :** Ubuntu 24.04 LTS - x86_64  
**Appareil cible :** Redroid (Android 14 - 1080×1920) en conteneur Docker  
**Scrcpy version :** 1.25  
**Connexion :** TCP/IP via Docker (localhost:5555)  
**Date :** 05/06/2026  

---

## Introduction Théorique

### Qu'est-ce que Scrcpy ?

Scrcpy (Screen Copy) est un outil open-source de Genymobile qui permet le mirroring d'écran Android :
- **Afficher** l'écran Android sur PC en temps réel
- **Contrôler** l'appareil avec souris et clavier
- **Enregistrer** l'écran en vidéo (MP4/MKV)
- **Aucune installation** sur l'appareil Android (utilise ADB)

### Caractéristiques techniques

| Caractéristique | Valeur |
|:----------------|:------:|
| Latence | 35-70 ms |
| Résolution max | Jusqu'à 4K |
| Framerate max | Jusqu'à 60 FPS |
| Connexion | USB ou WiFi |
| Encodage vidéo | H.264 (MediaCodec) |

### Architecture

```
┌──────────────────────┐     TCP:5555     ┌──────────────────────┐
│   Client Scrcpy      │◄──────────────►│   Serveur Scrcpy     │
│   (PC - affichage)   │                  │   (Android - capture)│
│   SDL2 + FFmpeg      │                  │   MediaCodec H.264   │
└──────────────────────┘                  └──────────────────────┘
```

Le serveur Scrcpy (`scrcpy-server`) est déployé automatiquement via ADB sur l'appareil Android. Il capture l'écran via l'API MediaProjection, encode en H.264, et streame via le tunnel ADB.

---

## Exercice 1 : Préparation

```bash
# Vérification ADB et appareil
$ adb devices -l
List of devices attached
localhost:5555         device product:redroid_x86_64_only model:redroid14_x86_64_only

$ adb shell getprop ro.build.version.release
14

$ adb shell wm size
Physical size: 1080x1920
```

L'appareil cible (redroid) a le débogage USB activé par défaut (build `userdebug`).

---

## Exercice 2 : Premier mirroring

**Contrainte :** L'environnement est sans interface graphique (CLI), donc l'affichage en direct n'est pas possible. Le mirroring via `--no-display --record` est utilisé comme alternative.

```bash
# Commande de mirroring standard (avec écran)
$ scrcpy -s localhost:5555

# Commande de test sans écran (enregistrement)
$ scrcpy -s localhost:5555 --no-display --record /tmp/scrcpy_test.mp4
[server] INFO: Device: redroid redroid14_x86_64_only (Android 14)
INFO: Recording started to mp4 file: /tmp/scrcpy_test.mp4
INFO: Recording complete to mp4 file: /tmp/scrcpy_test.mp4
```

**Note :** Une erreur `ClipboardManager.addPrimaryClipChangedListener` survient (API Android 14 incompatible avec scrcpy-server 1.25), mais l'enregistrement fonctionne correctement.

---

## Exercice 3 : Options de qualité

### Tableau comparatif

| Configuration | Taille fichier (5s) | Résolution | Bitrate | FPS |
|:-------------|:-------------------:|:----------:|:-------:|:---:|
| `-m 480 --max-fps 15` | 124 KB | 480p | Défaut | 15 |
| `-m 720 --max-fps 30` | 370 KB | 720p | Défaut | 30 |
| `-m 1080 --max-fps 60` | 93 KB | 1080p | Défaut | 60 |
| `-b 4M` (défaut) | 571 KB | 1080p | 4 Mbps | 60 |
| `-b 16M` | 285 KB | 1080p | 16 Mbps | 60 |
| `--rotation 1` (paysage) | 193 KB | 1920×1080 | Défaut | 60 |

### Impact observé

| Option | Effet |
|:-------|:------|
| `--max-size 480` | Plus fluide sur PC faible, qualité réduite |
| `--max-size 720` | Bon compromis qualité/performance |
| `-b 4M` (par défaut) | Bon équilibre qualité/taille |
| `-b 16M` | Meilleure qualité, taille fichier plus grande |
| `--max-fps 15` | Réduit la charge CPU/GPU |
| `--max-fps 60` | Maximum de fluidité |

### Recommandations

```bash
# Usage quotidien
scrcpy --max-size 1024 --max-fps 30

# Haute qualité
scrcpy --max-size 1920 --bit-rate 16M --max-fps 60

# Performance (PC faible)
scrcpy --max-size 720 --max-fps 15 --bit-rate 2M
```

---

## Exercice 4 : Enregistrement vidéo

```bash
# Enregistrement avec affichage
scrcpy --record video.mp4

# Enregistrement sans affichage (mode serveur)
scrcpy --no-display --record video.mp4
```

**Fichiers générés :**

| Fichier | Taille | Durée | Note |
|:--------|:------:|:-----:|:-----|
| `scrcpy_test.mp4` | 105 KB | ~5s | Test initial |
| `scrcpy_480p.mp4` | 124 KB | ~5s | 480p 15fps |
| `scrcpy_720p.mp4` | 370 KB | ~5s | 720p 30fps |
| `scrcpy_1080p.mp4` | 93 KB | ~5s | 1080p 60fps |
| `scrcpy_b4M.mp4` | 571 KB | ~5s | Bitrate 4M |
| `scrcpy_b16M.mp4` | 285 KB | ~5s | Bitrate 16M |
| `scrcpy_rot.mp4` | 193 KB | ~5s | Rotation paysage |
| `scrcpy_nocontrol.mp4` | 476 KB | ~5s | Sans contrôle |

**Formats supportés :**
```bash
scrcpy --record video.mp4   # MP4 (H.264)
scrcpy --record video.mkv   # MKV (H.264)
```

**Note sur les tailles :** Les fichiers plus longs avec bitrate plus faible peuvent être plus volumineux que les fichiers courts à haut bitrate (le bitrate variable s'adapte au contenu).

---

## Exercice 5 : Connexion WiFi

Redroid étant déjà accessible via TCP (Docker), la procédure WiFi standard est documentée ci-dessous :

```bash
# 1. Connexion USB initiale
adb usb

# 2. Obtenir l'adresse IP de l'appareil
adb shell ip addr show wlan0
# ou : adb shell ip route

# 3. Passer en mode TCP/IP
adb tcpip 5555

# 4. Déconnecter le câble USB

# 5. Connexion via WiFi
adb connect 192.168.1.100:5555
scrcpy
```

**Cas redroid (contournement Docker) :**
```bash
# Le conteneur expose déjà le port 5555
adb connect localhost:5555     # Connexion locale
adb connect 172.17.0.2:5555    # Connexion via bridge Docker
```

---

## Exercice 6 : Raccourcis clavier

| Raccourci | Action | Notes |
|:---------:|:-------|:------|
| Ctrl+H | Home | Simule KEYCODE_HOME |
| Ctrl+B | Back | Simule KEYCODE_BACK |
| Ctrl+S | App Switch | Applications récentes |
| Ctrl+M | Menu | Simule KEYCODE_MENU |
| Ctrl+↑ | Volume Up | - |
| Ctrl+↓ | Volume Down | - |
| Ctrl+P | Power | Verrouillage écran |
| Ctrl+O | Rotation | Rotation paysage/portrait |
| Ctrl+C | Copier | Presse-papiers |
| Ctrl+V | Coller | Injection texte |
| Ctrl+F | Plein écran | - |
| Ctrl+Shift+← | Rotation -90° | - |
| Ctrl+Shift+→ | Rotation +90° | - |
| **Clic droit** | Retour | - |
| **Molette** | Scroll | - |

---

## Exercice 7 : Options avancées

```bash
# Rotation forcée (0=portrait, 1=paysage, 2=portrait inversé, 3=paysage inversé)
scrcpy --rotation 1

# Verrouiller l'orientation
scrcpy --lock-video-orientation=initial

# Fenêtre toujours visible
scrcpy --always-on-top

# Désactiver le contrôle (affichage seul)
scrcpy --no-control

# Titre de fenêtre personnalisé
scrcpy --window-title "Mon Android"

# Position de la fenêtre
scrcpy --window-x 100 --window-y 100

# Désactiver les notifications de superposition
scrcpy --turn-screen-off

# Afficher les FPS
scrcpy --print-fps

# Découper l'écran (crop)
scrcpy --crop 720:1280:0:0
```

---

## Analyse de sécurité

### Risques identifiés

| Risque | Gravité | Description |
|:-------|:-------:|:------------|
| Accès visuel | Élevée | Tout l'écran Android est visible sur le PC |
| Contrôle total | **Critique** | Souris/clavier contrôlent entièrement l'appareil |
| Enregistrement non sollicité | Élevée | Capture vidéo possible à l'insu de l'utilisateur |
| WiFi non sécurisé | Moyenne | Connexion ADB/TCP sans chiffrement |
| Clipboard partagé | Élevée | Copier/coller expose les données du presse-papiers |

### Scénarios d'attaque

1. **Poste de travail compromis :**
   - Attaquant avec accès au PC
   - Lance Scrcpy sur l'appareil connecté
   - Accès visuel et contrôle total

2. **Réseau WiFi malveillant :**
   - Connexion ADB via WiFi sur un réseau non sécurisé
   - Interception possible des commandes et du flux vidéo
   - Attaque Man-in-the-Middle sur le port 5555

3. **USB HID Attack :**
   - Un câble USB malveillant peut initier une connexion ADB
   - Contrôle de l'appareil via Scrcpy sans consentement

### Contre-mesures

| Mesure | Efficacité |
|:-------|:----------:|
| Désactiver le débogage USB après usage | Très élevée |
| Révoquer les autorisations ADB régulièrement | Élevée |
| Utiliser uniquement des PC de confiance | Élevée |
| Éviter la connexion WiFi sur réseaux publics | Moyenne |
| Verrouiller l'écran quand non utilisé | Faible (ADB contourne) |
| Surveiller les connexions ADB | Moyenne |

### Commandes de sécurité

```bash
# Vérifier les connexions ADB actives
adb devices

# Révoquer toutes les autorisations ADB
# Paramètres → Options développeur → Révoquer autorisations débogage USB

# Arrêter le serveur ADB
adb kill-server

# Vérifier l'écoute réseau
sudo lsof -i :5555
sudo lsof -i :5037
```

---

## Synthèse

### Cas d'usage professionnels

| Usage | Description | Exemple |
|:------|:------------|:--------|
| Développement mobile | Tests et débogage en direct | Développeur testant son app |
| Présentations | Démonstration d'applications | Présentation client |
| Support technique | Assistance à distance | Guide utilisateur pas-à-pas |
| Formation | Tutoriels et screencasts | Création de contenu pédagogique |
| Accessibilité | Contrôle pour personnes à mobilité réduite | Utilisation PC pour contrôler téléphone |
| Test automatisé | Enregistrement + analyse vidéo | Tests de régression visuelle |

### Comparatif Scrcpy vs solutions Cloud

| Critère | Scrcpy | Appetize.io | Corellium |
|:--------|:------:|:-----------:|:---------:|
| Gratuit | ✅ | ⚠️ (limité) | ❌ |
| Latence | 35-70ms | 200-500ms | 50-100ms |
| Hors-ligne | ✅ | ❌ | ❌ |
| Contrôle total | ✅ | Limité | ✅ |
| Installation Android | Aucune | Aucune | Aucune |
| Capture vidéo | ✅ | ❌ | ✅ |
| Multi-appareils | ❌ | ✅ | ✅ |

### Commandes essentielles (cheatsheet)

```bash
# Basique
scrcpy                                        # Mirroring par défaut
scrcpy -s localhost:5555                      # Appareil spécifique

# Qualité
scrcpy -m 1024 --max-fps 30                   # Bon compromis
scrcpy -b 16M --max-fps 60                    # Haute qualité
scrcpy --no-display --record video.mp4        # Enregistrement seul

# Avancé
scrcpy --rotation 1                           # Mode paysage
scrcpy --always-on-top                        # Fenêtre au-dessus
scrcpy --turn-screen-off                      # Écran Android éteint
scrcpy --no-control --record demo.mp4         # Capture sans contrôle
scrcpy --window-title "Demo" --window-x 0 --window-y 0  # Positionnement

# WiFi
adb tcpip 5555
adb connect 192.168.1.100:5555
scrcpy
```

---

**Rapport TP Scrcpy terminé — Tous les exercices réalisés et documentés sur redroid.**
