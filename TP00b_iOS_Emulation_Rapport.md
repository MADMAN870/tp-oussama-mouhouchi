# TP 00b - Installation et Configuration d'un Émulateur iOS pour la Cybersécurité
## Rapport d'Analyse - Oussama MOUHOUCHI 4IIRCIRA

---

## Informations Générales

**Plateforme hôte :** Ubuntu 24.04 LTS - x86_64  
**Environnement :** Linux natif (adaptation depuis Windows)  
**Date :** 05/06/2026  
**Outils installés :** MobSF (Docker), Ghidra (téléchargé), Python 3, class-dump equivalent  

---

## Introduction Théorique

### Émulation iOS : Les Défis

Contrairement à Android, Apple ne fournit pas d'émulateur iOS officiel pour Windows/Linux. Les options disponibles :

| Solution | Type | Plateforme | Usage |
|:---------|:----:|:-----------|:------|
| Xcode Simulator | Simulateur | macOS uniquement | Développement |
| Corellium | Émulateur ARM | Cloud (web) | Sécurité (payant) |
| Appetize.io | Streaming | Web/Cloud | Tests rapides |
| UTM (QEMU) | VM iOS | macOS/Linux | Recherche |
| Analyse statique | Outils | Multi-plateforme | Sécurité (gratuit) |

### Simulateur vs Émulateur

| Aspect | Simulateur | Émulateur |
|:-------|:----------:|:---------:|
| Architecture | x86 (native PC) | ARM (comme iPhone) |
| Performance | Rapide | Plus lent |
| Compatibilité | Apps recompilées | Apps réelles |
| Sécurité | Limitée | Complète |

---

## Exercice 1 : Extraction d'un fichier IPA

### Création d'un échantillon IPA

Un fichier IPA (iOS App Store Package) a été créé pour l'analyse :

```bash
Structure de l'IPA :
MySecureApp.ipa
└── Payload/
    └── MyApp.app/
        ├── Info.plist          # Métadonnées + permissions
        ├── MySecureApp         # Binaire exécutable
        ├── AppIcon.png         # Icône
        └── Main.storyboardc    # Interface
```

### Analyse avec le script d'extraction

```bash
python3 extraire_ipa.py MySecureApp.ipa

=== INFORMATIONS DE L'APPLICATION ===
Bundle ID      : com.example.myapp
Version        : 2.4.1
Build          : 42
Nom            : MySecureApp
Executable     : MySecureApp
SDK minimum    : 14.0

=== PERMISSIONS DEMANDEES ===
  NSBluetoothAlwaysUsageDescription  : Se connecter aux peripheriques Bluetooth
  NSCameraUsageDescription           : Cette application utilise la camera pour scanner des QR codes
  NSContactsUsageDescription         : Synchroniser vos contacts avec votre reseau professionnel
  NSFaceIDUsageDescription           : Deverrouiller lapplication avec Face ID
  NSLocationWhenInUseUsageDescription: Utilise votre position pour afficher des offres locales
  NSMicrophoneUsageDescription       : Permet denregistrer des videos avec son
  NSPhotoLibraryUsageDescription     : Acceder a vos photos pour les partager

=== SECURITE (ATS) ===
  [!] ATS DESACTIVE (NSAllowsArbitraryLoads = true)
      -> Trafic HTTP non chiffre autorise
```

### Script d'extraction utilisé

```python
#!/usr/bin/env python3
import zipfile, plistlib, os, sys

def extract_ipa(ipa_path, output_dir):
    with zipfile.ZipFile(ipa_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

def analyze_info_plist(app_path):
    plist_path = os.path.join(app_path, "Info.plist")
    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)

    print(f"Bundle ID: {plist.get('CFBundleIdentifier', 'N/A')}")
    print(f"Version: {plist.get('CFBundleShortVersionString', 'N/A')}")
    # Permissions
    perm_keys = [k for k in plist.keys() if 'Usage' in k or 'Privacy' in k]
    for key in sorted(perm_keys):
        print(f"  {key}: {plist[key]}")
    return plist
```

---

## Exercice 2 : Installation de MobSF

### Installation via Docker

```bash
# Télécharger l'image MobSF (~1.5 GB)
docker pull opensecurity/mobile-security-framework-mobsf:latest

# Lancer le conteneur
docker run -d --rm -p 8000:8000 --name mobsf \
  opensecurity/mobile-security-framework-mobsf:latest
```

**Statut :** MobSF est accessible sur http://localhost:8000

### Fonctionnalités MobSF

- Analyse statique des binaires iOS/Android
- Détection de permissions excessives
- Analyse des ATS (App Transport Security)
- Extraction des URLs, API keys, tokens
- Scan de vulnérabilités (OWASP Mobile Top 10)
- Génération de rapports PDF

### Utilisation pour l'analyse iOS

1. Uploader le fichier `.ipa`
2. MobSF extrait automatiquement :
   - Le binaire Mach-O
   - Le fichier `Info.plist`
   - Les entitlements
   - Les frameworks embarqués
3. Résultats :
   - Liste des permissions
   - Analyse de sécurité (ATS, TLS)
   - Détection de code suspect
   - Rapport PDF exportable

---

## Exercice 3 : Analyse avec Ghidra

### Installation

```bash
# Ghidra 11.3.1 (nécessite Java 21+)
wget https://github.com/NationalSecurityAgency/ghidra/releases/download/\
Ghidra_11.3.1_build/ghidra_11.3.1_PUBLIC_20250212.zip
unzip ghidra_11.3.1_PUBLIC_20250212.zip -d /opt/
ln -sf /opt/ghidra_11.3.1_PUBLIC/ghidraRun /usr/local/bin/ghidra
```

### Analyse d'un binaire Mach-O

1. **Extraire le binaire** de l'IPA :
   ```bash
   unzip MySecureApp.ipa
   cd Payload/*.app/
   file MySecureApp  # Vérifier le type Mach-O
   ```

2. **Importer dans Ghidra** :
   - `File → Import File` → sélectionner le binaire
   - Langage : x86:LE:64:default (ou ARM:LE:64 pour iOS natif)
   - `Analyze → Auto-Analyze`

3. **Éléments à analyser** :
   - Fonctions (Symbol Tree)
   - Chaînes de caractères (Search → For Strings)
   - Imports/Exports
   - Appels système
   - URLs et endpoints API

4. **Indicateurs de sécurité** :
   - Fonctions de jailbreak detection
   - Chiffrement / Keychain
   - Certificats SSL embarqués
   - URLs de C2 (Command & Control)

---

## Exercice 4 : Corellium (Documentation)

### Présentation

Corellium est la solution professionnelle d'émulation iOS :
- **Émulation ARM complète** au niveau matériel
- **Support iOS 12 à 17**
- **Jailbreak intégré** (root complet)
- **Snapshots** illimités pour les tests
- **SSH natif** + Frida pré-installé

### Configuration

```bash
# 1. Créer un compte sur https://www.corellium.com/
# 2. Choisir un plan (essai gratuit disponible)
# 3. Créer une instance iOS

# Connexion SSH après création :
ssh root@<ip_instance>
# Mot de passe par défaut : alpine

# Installation de Frida :
apt update
apt install frida
frida-ps -U  # Lister les processus
```

### Avantages pour la Cybersécurité

| Fonctionnalité | Utilité |
|:---------------|:--------|
| Accès root/jailbreak | Analyse de malware, hooking |
| Snapshots | Retour arrière après exploitation |
| SSH natif | Automation, scripts distants |
| Frida intégré | Dynamic instrumentation |
| API REST | CI/CD, tests automatisés |

---

## Exercice 5 : Analyse des permissions iOS

### Analyse de l'IPA test (`MySecureApp`)

| Permission | Clé Info.plist | Justification | Risque |
|:-----------|:---------------|:--------------|:------:|
| Appareil photo | `NSCameraUsageDescription` | Scanner QR codes | Faible |
| Microphone | `NSMicrophoneUsageDescription` | Enregistrement vidéo | Moyen |
| Localisation | `NSLocationWhenInUseUsageDescription` | Offres locales | Moyen |
| Contacts | `NSContactsUsageDescription` | Sync réseau pro | **Élevé** |
| Photos | `NSPhotoLibraryUsageDescription` | Partage photos | Moyen |
| Face ID | `NSFaceIDUsageDescription` | Déverrouillage | Faible |
| Bluetooth | `NSBluetoothAlwaysUsageDescription` | Périphériques BT | Faible |

### Évaluation des risques

- **Permission excessive :** `NSContactsUsageDescription` — une app de scan QR n'a pas besoin des contacts
- **ATS désactivé :** `NSAllowsArbitraryLoads = true` — le trafic HTTP non chiffré est autorisé
- **Recommandations :**
  1. Supprimer la permission Contacts (non nécessaire pour l'app)
  2. Activer ATS (`NSAllowsArbitraryLoads = false`)
  3. Ajouter des exceptions ATS uniquement pour les domaines légitimes

### Permissions iOS sensibles (OWASP)

| Permission | Clé | Risque |
|:-----------|:----|:------:|
| Caméra | NSCameraUsageDescription | Capture photo/vidéo |
| Micro | NSMicrophoneUsageDescription | Écoute audio |
| Localisation | NSLocationWhenInUse/Always | Tracking |
| Contacts | NSContactsUsageDescription | Exfiltration |
| Photos | NSPhotoLibraryUsageDescription | Vol de données |
| Face ID | NSFaceIDUsageDescription | Usurpation biométrie |
| Bluetooth | NSBluetoothAlwaysUsageDescription | Proximité tracking |

---

## Synthèse et Questions

### Questions de compréhension

1. **Pourquoi pas d'émulateur iOS officiel pour Windows ?**
   - Apple restreint iOS aux appareils Apple (stratégie verticale)
   - Le simulateur Xcode nécessite l'API Metal (macOS only)
   - L'émulation ARM complète est techniquement complexe et légalement limitée par les EULA Apple

2. **Différence simulateur vs émulateur ?**
   - **Simulateur** : traduit les appels iOS en équivalents macOS (x86 natif) — rapide mais pas identique à un vrai iPhone
   - **Émulateur** : exécute le vrai code ARM iOS — plus lent mais fidèle au comportement réel

3. **Avantages Corellium ?**
   - Émulation ARM complète (pas de traduction)
   - Jailbreak natif + root
   - Snapshots pour rollback
   - Frida/SSH intégrés
   - API pour automation

4. **Structure d'un IPA ?**
   ```
   .ipa = archive ZIP
   ├── Payload/
   │   └── App.app/
   │       ├── Info.plist      # Métadonnées
   │       ├── AppBinary       # Binaire Mach-O
   │       ├── Frameworks/     # Librairies
   │       ├── entitlements.plist # Droits d'accès
   │       └── .lproj/         # Localisations
   └── SwiftSupport/           # Runtime Swift
   ```

### Outils installés et fonctionnels

| Outil | Statut | Port/Accès |
|:------|:------|:-----------|
| MobSF | ✅ Running | http://localhost:8000 |
| Ghidra 11.3.1 | ✅ Téléchargé | `/opt/ghidra_11.3.1_PUBLIC/` |
| Script extraction IPA | ✅ Fonctionnel | `/tmp/extraire_ipa.py` |
| Docker | ✅ Disponible | redroid + MobSF |
| Java 21 | ✅ Installé | OpenJDK 21.0.11 |

---

**Rapport TP 00b terminé — Tous les exercices réalisés et documentés.**
