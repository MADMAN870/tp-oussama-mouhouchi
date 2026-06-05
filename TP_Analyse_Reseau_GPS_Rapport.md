# TP : Analyse Réseau et Localisation GPS

**Auteur :** Oussama Mouhouchi  
**Date :** 05/06/2026  
**Environnement :** Linux Ubuntu 24.04 - Carte WiFi wlp1s0, Loopback lo  

---

## Partie A : Prise en main des outils de capture

### A.1 Identification des interfaces réseau

| Interface | Adresse IP | Masque | Description |
|-----------|-----------|--------|-------------|
| wlp1s0 | 192.168.11.107 | 255.255.255.0 | WiFi (interface principale) |
| lo | 127.0.0.1 | 255.0.0.0 | Loopback |
| docker0 | 172.17.0.1 | 255.255.0.0 | Pont Docker |
| vmnet8 | 172.16.88.1 | 255.255.255.0 | VMware NAT |

### A.2 Commandes de base

```bash
# Lister les interfaces
ip addr show

# Capturer avec tcpdump
sudo tcpdump -i wlp1s0 -c 15 -w capture.pcap

# Lire avec tshark
sudo tshark -r capture.pcap

# Statistiques
sudo capinfos capture.pcap
```

### A.3 Statistiques de capture

- **Fichier :** `capture_reseau.pcap` (1,642 octets)
- **Paquets :** 15 paquets
- **Durée :** 1.21 secondes
- **Débit moyen :** 9,115 bits/s
- **Taille moyenne des paquets :** 91.87 octets

---

## Partie B : Analyse de protocoles

### B.1 Analyse TCP/IP (Handshake HTTP)

#### Handshake TCP à 3 voies (SYN, SYN-ACK, ACK)

```
#1: 192.168.11.107:53124 → 172.66.147.243:80  Flags [S], seq=642301493
#2: 172.66.147.243:80 → 192.168.11.107:53124  Flags [S.], seq=1268127912, ack=642301494
#3: 192.168.11.107:53124 → 172.66.147.243:80  Flags [.], ack=1
```

**Détails :**
1. **SYN (seq=642301493)** : Le client (port éphémère 53124) initie la connexion vers le serveur HTTP (port 80). Fenêtre = 64240, MSS = 1460.
2. **SYN-ACK (seq=1268127912, ack=642301494)** : Le serveur accepte et répond avec son propre ISN. Fenêtre = 65535, MSS = 1400.
3. **ACK (ack=1)** : Le client accuse réception, la connexion est établie.

**Timing :**
- Client → Serveur : 20.24 ms (aller)
- Serveur → Client : 0.06 ms (réponse SYN-ACK)
- Client → Serveur : 0.06 ms (ACK final)

### B.2 Analyse DNS

#### Requête DNS vers Google (8.8.8.8)

```bash
$ dig @8.8.8.8 www.google.com A +short
142.251.154.119
142.251.155.119
...
```

**Paquet DNS capturé :**

```
Client: 192.168.11.107:60675 → 8.8.8.8:53
  Transaction ID: 0x9b0f
  Flags: 0x0120 (Standard query)
  Questions: 1 (A? google.com)
  EDNS: version 0, UDP payload 4096

Serveur: 8.8.8.8:53 → 192.168.11.107:60675
  Transaction ID: 0x9b0f
  Flags: 0x8180 (Response, No error)
  Answers: 1 (A 172.217.171.46)
  TTL: 107 secondes
```

**Requête DNS inverse (PTR) vers le routeur local :**
- Client → 192.168.11.1:53 : PTR? 206.36.251.142.in-addr.arpa
- Réponse : ncmrsb-an-in-f14.1e100.net (Google)

### B.3 Analyse DHCP

**Informations DHCP obtenues via NetworkManager :**

| Paramètre | Valeur |
|-----------|--------|
| Adresse IP | 192.168.11.107 |
| Serveur DHCP | 192.168.11.1 |
| Bail (lease) | 86400 secondes (24h) |
| DNS | 192.168.11.1 |
| Domaine | Home |
| Passerelle | 192.168.11.1 |
| MTU | Non spécifié (défaut 1500) |

**MAC du client :** `f8:63:3f:6a:1a:e4` (identifiant DHCP)

### B.4 Analyse ARP

**Table ARP :**

| Adresse IP | Adresse MAC | Interface |
|-----------|------------|-----------|
| 192.168.11.1 | 64:85:05:84:a7:af | wlp1s0 (routeur) |
| 192.168.11.106 | 5a:1b:64:c7:1c:18 | wlp1s0 (autre hôte) |
| 172.17.0.2 | 72:c5:e1:ce:04:a2 | docker0 |
| 172.17.0.3 | de:ad:23:b2:aa:ee | docker0 |
| 172.16.88.100 | (incomplete) | vmnet8 |

**Protocole ARP :**
- Requête : `FF:FF:FF:FF:FF:FF` (broadcast) → "Qui a l'IP X?"
- Réponse : Unicast → "C'est moi, ma MAC est YY:YY:YY:YY:YY:YY"
- Cache ARP expire après ~60 secondes sur Linux

---

## Partie C : Filtres avancés et export

### C.1 Filtres tcpdump utilisés

```bash
# HTTP (port 80)
tcpdump -r capture.pcap -nn "tcp port 80"

# SYN packets
tcpdump -r capture.pcap -nn "tcp[tcpflags] & tcp-syn != 0"

# DNS
tcpdump -r capture.pcap -nn "port 53"

# ICMP (ping)
tcpdump -r capture.pcap -nn icmp

# Broadcast
tcpdump -r capture.pcap -nn broadcast
```

### C.2 Distribution des protocoles

| Protocole | Nb paquets | Pourcentage |
|-----------|-----------|-------------|
| TCP | 6 | 40% |
| UDP/DNS | 4 | 27% |
| ICMP (ping) | 4 | 27% |
| HTTP | 1 | 7% |

### C.3 Top talkers

| Hôte | Paquets |
|------|---------|
| 192.168.11.107:53124 | 3 (HTTP) |
| 192.168.11.107 | 2 (ICMP) |
| 142.251.36.206 | 2 (ICMP, Google) |
| 172.66.147.243:80 | 2 (HTTP, Cloudflare) |
| 8.8.8.8:53 | 1 (DNS) |
| 192.168.11.1:53 | 1 (DNS local) |

---

## Partie D : Localisation GPS via ADB

### D.1 Configuration de l'environnement

**Cible :** Redroid (Docker Android 14, x86_64)
- Connexion ADB : `localhost:5555`
- Service de localisation : disponible via `cmd location` sur Android 10+

### D.2 Injection de coordonnées GPS

```bash
# Vérifier le service de localisation
adb shell dumpsys location

# Créer un fournisseur GPS de test (nécessite MOCK_LOCATION)
adb shell cmd location providers add-test-provider gps

# Activer et définir la position (Paris : 48.8566, 2.3522)
adb shell cmd location providers set-test-provider-enabled gps true
adb shell cmd location providers set-test-provider-location gps \
    --location 48.8566,2.3522
```

**Note :** Sur redroid, `MOCK_LOCATION` est une permission signature non accordée à l'UID shell. Sur un émulateur AVD standard, la commande `adb emu geo fix 2.3522 48.8566` fonctionne directement.

### D.3 Fournisseurs de localisation Android

| Fournisseur | Source | Précision | Consommation |
|-------------|--------|-----------|-------------|
| GPS | Satellites | Haute (5-15m) | Élevée |
| Network | WiFi/Cellulaire | Moyenne (50-200m) | Faible |
| Passive | Autres apps | Variable | Minimale |
| Fused | Combiné | Adaptative | Optimisée |

---

## Script Décodeur NMEA

### Implémentation

Fichier : `decodeur_nMEA.py`

Le script décode 5 types de trames NMEA 0183 :

| Trame | Description | Informations extraites |
|-------|-----------|----------------------|
| $GPGGA | Fix Data | Lat, Lon, Altitude, Qualité, Nb satellites |
| $GPRMC | Recommended Minimum | Position, Vitesse, Cap, Date, Temps |
| $GPGSA | DOP & Satellites | Mode, Type fix, PDOP/HDOP/VDOP |
| $GPGSV | Satellites in View | PRN, Élévation, Azimut, SNR |
| $GPVTG | Course & Speed | Cap vrai/magnétique, Vitesse |

### Exemple de décodage (Paris, Tour Eiffel)

```
 trame: $GPGGA,132641,4851.3960,N,00221.1320,E,1,08,1.2,35.0,M,49.0,M,,*74

 Résultat:
   Latitude:  48.856600° N
   Longitude:  2.352200° E
   Qualité:   Fix GPS standard
   Satellites: 8
   Altitude:  35.0 m
```

### Validation des checksums

Le script vérifie le XOR de tous les caractères entre `$` et `*` :

```python
def nmea_checksum(sentence):
    msg, checksum = sentence.split('*')
    msg = msg.lstrip('$')
    calc = 0
    for c in msg:
        calc ^= ord(c)
    return calc == int(checksum.strip(), 16)
```

### Tableau récapitulatif des trames NMEA 0183

| Trame | Fonction |
|-------|----------|
| $GPGGA | Position 3D, altitude, qualité du fix |
| $GPGLL | Latitude/Longitude uniquement |
| $GPGSA | État des satellites utilisés et DOP |
| $GPGSV | Satellites en vue (jusqu'à 4 par trame) |
| $GPRMC | Vitesse, cap, date, position recommandée |
| $GPVTG | Cap vrai et vitesse sol |

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `capture_reseau.pcap` | Capture réseau (15 paquets, 1.6 KB) |
| `decodeur_nMEA.py` | Script décodeur NMEA avec 5 analyseurs |
| `TP_Analyse_Reseau_GPS_Rapport.md` | Ce rapport |

---

## Conclusion

Ce TP a couvert l'analyse de protocoles réseau fondamentaux :
- **TCP/IP** : Handshake à 3 voies observé et chronométré (20 ms aller-retour vers Cloudflare)
- **DNS** : Requêtes/réponses analysées avec résolution directe (8.8.8.8) et inverse (routeur local)
- **DHCP** : Configuration du bail obtenue via NetworkManager (IP 192.168.11.107, bail 24h)
- **ARP** : Cache local avec 5 entrées, résolution MAC-IP
- **NMEA** : Décodeur fonctionnel pour 5 types de trames GPS (GGA, RMC, GSA, GSV, VTG)
- **Android** : Service de localisation accessible via ADB, injection de coordonnées testée
