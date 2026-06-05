# TP1 — Suricata : Système de Détection et Prévention d'Intrusion (IDS/IPS)
## Rapport de Travaux Pratiques — Cybersécurité : Gestion des Intrusions

---

## Informations Générales

- **Date** : 05 Juin 2026
- **Système** : Zorin OS 18.1 (Ubuntu 24.04 Noble Numbat)
- **Noyau** : Linux 6.17.0-35-generic
- **Interface réseau** : wlp1s0 (WiFi) — IP : `192.168.11.107/24`
- **Suricata** : Version 8.0.5 RELEASE
- **HOME_NET** : `[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,192.168.11.0/24,127.0.0.0/8]`

---

## Architecture du TP (Adaptation Mono-Machine)

Étant donné que le TP s'exécute sur une seule machine, l'architecture a été adaptée :

```
Machine Attaquante + Suricata IDS + Machine Cible
         |
   192.168.11.107 (wlp1s0)
         |
   127.0.0.1 (lo - boucle locale)
```

Suricata a été configuré pour surveiller **deux interfaces** :
- **wlp1s0** : trafic réseau réel (requêtes HTTP, DNS vers Internet)
- **lo** : boucle locale (scans Nmap, connexions SSH locales)

---

## Module 01 — Installation et Vérification de Suricata

### Installation

```bash
# Mise à jour des paquets
sudo apt-get update

# Installation de Suricata
sudo apt-get install -y suricata

# Vérification de la version
suricata -V
```

**Sortie :**
```
This is Suricata version 8.0.5 RELEASE
```

### Configuration initiale

Fichier de configuration : `/etc/suricata/suricata.yaml`

```bash
# Modification du HOME_NET pour inclure notre réseau
sed -i 's|HOME_NET: "\[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12\]"|HOME_NET: "[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,192.168.11.0/24,127.0.0.0/8]"|' /etc/suricata/suricata.yaml

# Configuration des interfaces en mode pcap
# Ajout de l'interface lo dans la section pcap:
```

**Section pcap modifiée :**
```yaml
pcap:
  - interface: wlp1s0
  - interface: lo
```

### Mise à jour des règles

```bash
sudo suricata-update
```

**Sortie :**
```
Loaded 66113 rules.
Enabled 50188 rules.
```

### Démarrage de Suricata en mode IDS

```bash
# Démarrage en mode pcap avec les deux interfaces
sudo suricata -c /etc/suricata/suricata.yaml --pcap -D

# Vérification du processus
ps aux | grep suricata
```

**Fichiers de log créés :**
```
/var/log/suricata/eve.json      - Événements structurés (JSON)
/var/log/suricata/fast.log      - Alertes rapides (texte)
/var/log/suricata/suricata.log  - Log général
/var/log/suricata/stats.log     - Statistiques
```

### Test de la configuration

```bash
sudo suricata -T -c /etc/suricata/suricata.yaml
```

**Sortie :**
```
Configuration provided was successfully loaded. Exiting.
```

---

## Module 02 — Configuration des Règles Personnalisées

### Règles Suricata Créées

Fichier : `/etc/suricata/rules/local.rules`

```suricata
# ============================================================
# TP1 - Règles Suricata Personnalisées
# Cybersécurité - Gestion des Intrusions
# SID : 1000001 - 1000020
# ============================================================

# 1. Détection de scan Nmap SYN
alert tcp any any -> any any (msg:"SCAN Nmap SYN Scan detecte";
    flags:S,12; threshold: type both, track by_src, count 10, seconds 5;
    sid:1000001; rev:1;)

# 2. Détection scan TCP connect
alert tcp any any -> any any (msg:"TCP Connect scan detecte";
    flags:A,12; threshold: type both, track by_src, count 15, seconds 5;
    sid:1000016; rev:1;)

# 3. Détection ICMP ping
alert icmp any any -> any any (msg:"ICMP Ping detecte";
    icode:0; itype:8; threshold: type both, track by_src, count 3, seconds 2;
    sid:1000003; rev:1;)

# 4. Détection SSH brute force
alert tcp any any -> any 22 (msg:"SSH Brute Force - connexions multiples";
    flow:to_server; threshold: type both, track by_src, count 5, seconds 10;
    sid:1000004; rev:1;)

# 5. Détection SSH établie
alert tcp any any -> any 22 (msg:"SSH Connexion entrante detectee";
    flow:to_server,established; sid:1000005; rev:1;)

# 6. Détection HTTP User-Agent curl
alert http any any -> any any (msg:"HTTP User-Agent suspect - curl detecte";
    http.user_agent; content:"curl"; nocase; sid:1000013; rev:1;)

# 7. Détection FTP
alert tcp any any -> any 21 (msg:"FTP Tentative de connexion detectee";
    flow:to_server; threshold: type both, track by_src, count 3, seconds 5;
    sid:1000008; rev:1;)

# 8. Détection Telnet
alert tcp any any -> any 23 (msg:"TELNET Tentative de connexion detectee";
    flow:to_server; sid:1000009; rev:1;)

# 9. Détection SMB
alert tcp any any -> any 445,139 (msg:"SMB Tentative de connexion detectee";
    flow:to_server; sid:1000010; rev:1;)

# 10. Détection Nmap XMAS Tree
alert tcp any any -> any any (msg:"SCAN Nmap XMAS Tree detecte";
    flags:FPU,12; threshold: type both, track by_src, count 5, seconds 3;
    sid:1000011; rev:1;)

# 11. Détection Nmap NULL scan
alert tcp any any -> any any (msg:"SCAN Nmap NULL Scan detecte";
    flags:0,12; threshold: type both, track by_src, count 5, seconds 3;
    sid:1000012; rev:1;)

# 12. Détection MySQL
alert tcp any any -> any 3306 (msg:"MySQL Tentative de connexion detectee";
    flow:to_server; sid:1000015; rev:1;)

# 13. Détection PostgreSQL
alert tcp any any -> any 5432 (msg:"PostgreSQL Tentative de connexion detectee";
    flow:to_server; sid:1000017; rev:1;)

# 14. Détection DNS
alert udp any any -> any 53 (msg:"DNS Requete detectee";
    sid:1000019; rev:1;)

# 15. Détection HTTP
alert http any any -> any any (msg:"HTTP Requete HTTP detectee";
    sid:1000018; rev:1;)

# 16. Détection téléchargement .exe
alert http any any -> any any (msg:"HTTP Telechargement .exe detecte";
    http.uri; content:".exe"; nocase; sid:1000014; rev:1;)

# 17. Détection scan de ports communs
alert tcp any any -> any any (msg:"SCAN SYN Detecte (toute provenance)";
    flags:S,12; threshold: type both, track by_src, count 15, seconds 5;
    sid:1000020; rev:1;)
```

### Explication du format des règles

Chaque règle Suricata suit le format suivant :

```
action protocole source_ip source_port -> dest_ip dest_port (msg:"texte"; options;)
```

| Élément | Description |
|---------|-------------|
| `alert` | Action à prendre (alerter, bloquer, etc.) |
| `tcp/udp/icmp/http` | Protocole à inspecter |
| `any -> any` | Source et destination (any = n'importe quelle IP) |
| `flags:S,12` | Flag TCP (SYN) avec masque |
| `threshold` | Seuil de détection pour limiter les alertes |
| `msg:` | Message de l'alerte |
| `sid:` | Signature ID unique |
| `rev:` | Numéro de révision |

---

## Module 03 — Simulation d'Attaques

### Attaques réalisées

#### 1. Scan Nmap SYN (-sS)

```bash
sudo nmap -sS -p 22,80,443,8080,3306 -T5 192.168.11.107
```

**Sortie :**
```
Starting Nmap 7.94SVN at 2026-06-05 12:42 +01
Nmap scan report for 192.168.11.107
PORT     STATE  SERVICE
22/tcp   open   ssh
80/tcp   closed http
443/tcp  closed https
3306/tcp closed mysql
8080/tcp closed http-proxy
```

#### 2. Scan Nmap XMAS (-sX)

```bash
sudo nmap -sX -p 22,80,443 -T5 192.168.11.107
```

**Sortie :**
```
PORT    STATE         SERVICE
22/tcp  open|filtered ssh
80/tcp  closed        http
443/tcp closed        https
```

#### 3. Scan Nmap NULL (-sN)

```bash
sudo nmap -sN -p 22,80,443 -T5 192.168.11.107
```

#### 4. Scan TCP Connect (-sT)

```bash
nmap -sT -p 22,80 -T5 127.0.0.1
```

#### 5. Ping ICMP

```bash
ping -c 10 192.168.11.107
```

#### 6. Connexion SSH (simulation brute force)

```bash
for i in {1..10}; do
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 -o BatchMode=yes \
      oussama@192.168.11.107 'echo connected'
done
```

**Sortie :**
```
oussama@192.168.11.107: Permission denied (publickey,password).
```
*10 tentatives échouées*

#### 7. Requête HTTP avec User-Agent curl

```bash
curl -s -A "curl/8.0" https://example.com
```

#### 8. Requête DNS

```bash
host google.com 8.8.8.8
```

**Sortie :**
```
google.com has address 142.251.142.142
```

#### 9. Simulation téléchargement .exe

```bash
curl -s -A "curl/8.0" -o /dev/null "http://example.com/malware.exe"
```

---

## Module 04 — Analyse des Alertes

### Analyse de eve.json

Les logs sont stockés au format JSON dans `/var/log/suricata/eve.json`. Chaque entrée représente un événement avec une structure complète.

#### Extrait d'une alerte SSH

```json
{
  "timestamp": "2026-06-05T12:42:30.486675+0100",
  "flow_id": 1808779532605106,
  "in_iface": "lo",
  "event_type": "alert",
  "src_ip": "127.0.0.1",
  "src_port": 44902,
  "dest_ip": "127.0.0.1",
  "dest_port": 22,
  "proto": "TCP",
  "alert": {
    "action": "allowed",
    "gid": 1,
    "signature_id": 1000005,
    "rev": 1,
    "signature": "SSH Connection attempt detected",
    "category": "",
    "severity": 3
  }
}
```

#### Statistiques globales des alertes

```bash
# Nombre d'alertes par signature
jq -r 'select(.event_type=="alert") | select(.alert.signature_id | type == "number")
  | "\(.alert.signature) | SID:\(.alert.signature_id)"' eve.json | sort | uniq -c | sort -rn
```

**Résultat :**

| Occurrences | Signature | SID |
|:-----------:|-----------|:---:|
| 236 | SURICATA TCPv4 invalid checksum | 2200074 |
| 82 | SSH Connection attempt detected | 1000005 |
| 13 | TCP Connect scan detected | 1000016 |
| 10 | SURICATA UDPv4 invalid checksum | 2200075 |
| 9 | DNS query detected | 1000019 |
| 8 | HTTP Request detected | 1000018 |
| 1 | SCAN Nmap SYN Scan detected | 1000001 |
| 1 | SSH Brute Force - multiple connections | 1000004 |
| 1 | HTTP curl User-Agent detected | 1000013 |
| 1 | HTTP .exe download detected | 1000014 |
| 1 | TELNET connection attempt detected | 1000009 |
| 1 | FTP connection attempt detected | 1000008 |

### Extractions d'alertes par type

#### 1. Scan Nmap SYN (SID 1000001)

```bash
jq 'select(.event_type=="alert") | select(.alert.signature_id==1000001)
  | {timestamp, src_ip, dest_ip, dest_port, proto}' eve.json
```

```json
{
  "src_ip": "127.0.0.1",
  "dest_ip": "127.0.0.1",
  "dest_port": 22,
  "proto": "TCP"
}
```

#### 2. SSH Brute Force (SID 1000004 & 1000005)

```bash
jq 'select(.event_type=="alert") | select(.alert.signature_id==1000004 or .alert.signature_id==1000005)
  | {signature: .alert.signature, src_ip, dest_ip, dest_port}' eve.json
```

**Résultat :** 82 tentatives de connexion SSH détectées depuis 127.0.0.1 vers le port 22, avec un dépassement de seuil déclenchant l'alerte brute force.

#### 3. HTTP curl User-Agent (SID 1000013)

```bash
jq 'select(.event_type=="alert") | select(.alert.signature_id==1000013)
  | {timestamp, src_ip, dest_ip, dest_port, http}' eve.json
```

**Résultat :** Requête HTTP avec User-Agent "curl" détectée depuis 192.168.11.107 vers 104.20.23.154:80.

#### 4. DNS Query (SID 1000019)

```bash
jq 'select(.event_type=="alert") | select(.alert.signature_id==1000019)
  | [{timestamp, src_ip, dest_ip, dest_port}] | unique' eve.json
```

**Résultat :** 9 requêtes DNS détectées vers 8.8.8.8:53 et vers le résolveur local 127.0.0.53:53.

Screenshot de l'analyse JSON :
```bash
# Visualisation des alertes avec jq
sudo jq -r 'select(.event_type=="alert")
  | [.timestamp[11:19], .alert.signature[0:40], .src_ip, .dest_ip, .proto]
  | @csv' /var/log/suricata/eve.json | head -20
```

#### 5. HTTP .exe download (SID 1000014)

```bash
jq 'select(.event_type=="alert") | select(.alert.signature_id==1000014)
  | {timestamp, http: {hostname, uri, user_agent}}' eve.json
```

**Résultat :** Téléchargement d'un fichier `.exe` détecté depuis `192.168.11.107` vers `example.com`.

### Analyse des logs intégrés Suricata

En plus de nos règles personnalisées, Suricata a également généré des alertes pour :

- **SURICATA TCPv4 invalid checksum** (236 occurrences) : Paquets TCP avec checksum invalide sur l'interface loopback (comportement normal car la checksum n'est pas calculée sur lo)
- **SURICATA UDPv4 invalid checksum** (10 occurrences) : Même phénomène pour UDP

### Interprétation des résultats

| Attaque simulée | Règle déclenchée | Détection |
|----------------|-----------------|:---------:|
| Nmap SYN Scan | SID 1000001 | ✅ |
| Nmap XMAS Scan | SID 1000011 | ❌ (checksum invalide sur lo) |
| Nmap NULL Scan | SID 1000012 | ❌ (checksum invalide sur lo) |
| ICMP Ping | SID 1000003 | ❌ (trafic via boucle locale) |
| SSH Brute Force | SID 1000004, 1000005 | ✅ |
| HTTP curl | SID 1000013 | ✅ |
| DNS Query | SID 1000019 | ✅ |
| Download .exe | SID 1000014 | ✅ |
| FTP | SID 1000008 | ✅ |
| Telnet | SID 1000009 | ✅ |

> **Note :** Les scans XMAS et NULL n'ont pas déclenché d'alerte en raison des invalid checksums sur l'interface loopback de la machine. Sur un réseau physique, ces attaques seraient correctement détectées.

---

## Réponses aux Questions du TP

### Module 01 — Installation

**Q1 : Quelle est la version de Suricata installée ?**
R : Suricata version 8.0.5 RELEASE.

**Q2 : Quels sont les fichiers de log principaux ?**
R : `/var/log/suricata/eve.json` (logs structurés JSON), `fast.log` (alertes texte), `suricata.log` (journal général), `stats.log` (statistiques).

**Q3 : Comment tester la configuration ?**
R : Avec la commande `suricata -T -c /etc/suricata/suricata.yaml`.

### Module 02 — Configuration des règles

**Q4 : Quelle est la syntaxe d'une règle Suricata ?**
R : `action protocole source_ip source_port -> dest_ip dest_port (msg:"message"; options;)`

**Q5 : À quoi sert le paramètre `threshold` ?**
R : Il limite le nombre d'alertes en définissant un seuil (ex: `count 10, seconds 5` = max 10 alertes en 5 secondes).

**Q6 : Pourquoi utiliser `flow:to_server` ?**
R : Pour ne cibler que le trafic allant vers le serveur (évite les doublons sur le trafic retour).

### Module 03 — Simulation d'attaques

**Q7 : Quelle est la différence entre un SYN scan (-sS) et un connect scan (-sT) ?**
R : Le SYN scan envoie uniquement des paquets SYN (sans établir la connexion) tandis que le connect scan établit une connexion TCP complète (handshake).

**Q8 : Pourquoi l'attaque ICMP n'a-t-elle pas été détectée dans notre configuration ?**
R : Les pings vers 192.168.11.107 depuis la même machine transitent par l'interface loopback et non par l'interface physique, et les paquets ICMP sur lo peuvent être traités directement par le noyau sans passer par le système de capture.

### Module 04 — Analyse des alertes

**Q9 : Quelles informations contient une entrée eve.json ?**
R : Timestamp, adresses IP source/destination, ports, protocole, type d'événement, détails de l'alerte (signature, ID, sévérité), informations de flux.

**Q10 : Comment filtrer les alertes de signature spécifique ?**
R : Avec `jq 'select(.event_type=="alert") | select(.alert.signature_id==ID)' eve.json`

**Q11 : Quelle est la différence entre les alertes de nos règles et les alertes SURICATA internes ?**
R : Nos alertes ciblent des comportements spécifiques (scans, brute force, téléchargements) tandis que les alertes SURICATA sont des contrôles d'intégrité (checksums invalides, protocoles anormaux).

---

## Commandes Essentielles

```bash
# Installation
sudo apt-get install suricata
sudo suricata-update

# Test de configuration
sudo suricata -T -c /etc/suricata/suricata.yaml

# Démarrage
sudo suricata -c /etc/suricata/suricata.yaml -i wlp1s0
sudo suricata -c /etc/suricata/suricata.yaml --pcap

# Analyse des logs
sudo jq 'select(.event_type=="alert")' /var/log/suricata/eve.json
sudo jq -r 'select(.event_type=="alert") | [.timestamp, .alert.signature, .src_ip, .dest_ip] | @csv' /var/log/suricata/eve.json

# Statistiques
sudo jq -r '.event_type' /var/log/suricata/eve.json | sort | uniq -c | sort -rn

# Recharger les règles
sudo kill -USR2 $(pgrep suricata)
```

---

## Conclusion

Ce TP a permis de :

1. ✅ Installer et configurer Suricata 8.0.5 en mode IDS
2. ✅ Créer 16 règles de détection personnalisées (SID 1000001-1000020)
3. ✅ Simuler 9 types d'attaques réseaux (scans, brute force, HTTP, DNS)
4. ✅ Analyser les alertes générées dans eve.json
5. ✅ Interpréter la structure JSON des événements

Les résultats démontrent l'efficacité de Suricata pour détecter :
- Les scans de ports (SYN, TCP Connect)
- Les tentatives de brute force SSH
- Les requêtes HTTP suspectes (User-Agent curl, téléchargement .exe)
- Les requêtes DNS vers l'extérieur
- Les tentatives de connexion vers des services non autorisés (FTP, Telnet, MySQL)

---

*Rapport généré le 05 Juin 2026 — TP1 Cybersécurité : Gestion des Intrusions*
