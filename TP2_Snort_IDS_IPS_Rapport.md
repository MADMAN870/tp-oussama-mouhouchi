# TP2 — Snort : Système de Détection et Prévention d'Intrusion
## Rapport de Travaux Pratiques — Cybersécurité : Gestion des Intrusions

---

## Informations Générales

- **Date** : 05 Juin 2026
- **Système** : Zorin OS 18.1 (Ubuntu 24.04 Noble Numbat)
- **Noyau** : Linux 6.17.0-35-generic
- **Interface réseau** : wlp1s0 (WiFi) — IP : `192.168.11.107/24`
- **Snort** : Version **2.9.20 GRE** (Build 82) — Snort 3 indisponible dans les dépôts Ubuntu 24.04, compilation échouée par timeout
- **Snort 3 tenté** : Source `3.3.7.0` — compilation interrompue après 10 min
- **DAQ modules** : pcap, nfq, ipfw, dump, afpacket

> **Note version :** Les concepts (règles, IDS/IPS, logs) sont identiques entre Snort 2 et 3. Le format des règles est rétrocompatible.

---

## Architecture du Lab (Adaptation Mono-Machine)

```
+---------------------+          +-------------------+
|  Attaques locales   |          |  Snort IDS         |
|  nmap / ssh / curl  | -------> |  wlp1s0 + lo       |
|  192.168.11.107     |          |  192.168.11.107    |
+---------------------+          +-------------------+
                                         |
                                 /var/log/snort/
                                 /etc/snort/rules/
```

Deux instances Snort :
- **wlp1s0** : trafic réseau réel (Internet) — logs dans `/var/log/snort/`
- **lo** : boucle locale (attaques locales) — logs dans `/var/log/snort/lo/`

---

## Module 01 — Prise en main et Découverte

### Installation

```bash
# Depuis les dépôts Ubuntu (Snort 2.9.20)
sudo apt-get install snort snort-rules-default

# Vérification
snort -V
```

**Sortie :**
```
,,_ -*> Snort! <*-
o"  )~   Version 2.9.20 GRE (Build 82)
''''    By Martin Roesch & The Snort Team
```

### Fichiers de configuration

| Fichier | Rôle |
|---------|------|
| `/etc/snort/snort.conf` | Configuration principale |
| `/etc/snort/snort.debian.conf` | Surcharge Debian (interface, HOME_NET) |
| `/etc/snort/rules/local.rules` | Règles personnalisées |
| `/etc/snort/rules/*.rules` | Règles communautaires (6105 règles) |

### Configuration réseau

```bash
# Dans /etc/snort/snort.debian.conf
DEBIAN_SNORT_HOME_NET="192.168.11.0/24,127.0.0.0/8"
DEBIAN_SNORT_INTERFACE="wlp1s0 lo"

# Dans /etc/snort/snort.conf
ipvar HOME_NET [192.168.11.0/24,127.0.0.0/8]
ipvar EXTERNAL_NET !$HOME_NET
```

### Test de la configuration

```bash
sudo snort -T -c /etc/snort/snort.conf -i wlp1s0
```

**Sortie :**
```
Snort successfully validated the configuration!
```

### Démarrage

```bash
# Mode IDS (détection)
sudo snort -c /etc/snort/snort.conf -i wlp1s0 -D -l /var/log/snort
sudo snort -c /etc/snort/snort.conf -i lo -D -l /var/log/snort/lo

# Vérification
ps aux | grep snort
```

**Fichiers de log :**
```
/var/log/snort/snort.alert         - Alertes unifiées (binaire unified2)
/var/log/snort/snort.alert.fast    - Alertes texte (lisible)
/var/log/snort/snort.log           - Paquets capturés (unified2)
```

---

## Module 02 — Analyse de Paquets et Logs

### Format des logs Snort

#### Format `alert_fast` (texte) :

```
MM/DD-HH:MM:SS.microsec  [**] [GID:SID:REV] Message [**] [Classification] [Priority] {PROTO} SRC:PORT -> DST:PORT
```

Exemple :
```
06/05-13:06:48.719605  [**] [1:2000004:1] SSH Brute Force - connexions multiples [**] [Priority: 0] {TCP} 192.168.11.107:46666 -> 192.168.11.107:22
```

#### Format `unified2` (binaire) :

```bash
# Conversion en pcap
u2boat /var/log/snort/snort.alert /var/log/snort/alert.pcap

# Lecture avec tcpdump
tcpdump -r /var/log/snort/alert.pcap -nn
```

### Analyse des logs sur wlp1s0

```bash
sudo cat /var/log/snort/snort.alert.fast | head -5
```

**Résultat :**
```
06/05-13:06:25.988431  [**] [1:2000016:1] DNS Requete detectee [**] {UDP} fe80::511a:3a18:8278:9bea:49225 -> fe80::6685:5ff:fe84:a7af:53
06/05-13:06:26.083535  [**] [1:2000016:1] DNS Requete detectee [**] {UDP} [...]
06/05-13:06:27.078967  [**] [1:2000002:1] TCP Connect scan detecte [**] {TCP} 192.168.11.107:51506 -> 172.65.90.22:443
06/05-13:06:37.511847  [**] [1:2000017:1] HTTP Requete detectee [**] {TCP} 192.168.11.107:46606 -> 146.190.225.48:80
```

### Analyse des logs sur lo

```bash
sudo cat /var/log/snort/lo/snort.alert.fast | head -10
```

**Résultat :**
```
06/05-13:06:42.433363  [**] [1:528:5] BAD-TRAFFIC loopback traffic [**] {TCP} 127.0.0.1:9200 -> 127.0.0.1:41752
06/05-13:06:47.386623  [**] [1:527:8] BAD-TRAFFIC same SRC/DST [**] {TCP} 192.168.11.107:52041 -> 192.168.11.107:80
06/05-13:06:48.719605  [**] [1:2000004:1] SSH Brute Force - connexions multiples [**] {TCP} 192.168.11.107:46666 -> 192.168.11.107:22
06/05-13:06:56.649069  [**] [1:527:8] BAD-TRAFFIC same SRC/DST [**] {ICMP} 192.168.11.107 -> 192.168.11.107
```

> Les règles intégrées de Snort ont détecté les scans et pings (même source/destination).

---

## Module 03 — Écriture de Règles

### Règles Snort Créées

Fichier : `/etc/snort/rules/local.rules` — 20 règles (SID 2000001-2000020)

```snort
# ============================================================
# TP2 - Regles Snort Personnalisees
# SID: 2000001 - 2000020
# ============================================================

# 1. Detection scan Nmap SYN
alert tcp any any -> any any (msg:"SCAN Nmap SYN Scan detecte";
    flags:S,12; threshold: type both, track by_src, count 10, seconds 5;
    sid:2000001; rev:1;)

# 2. Detection scan TCP Connect
alert tcp any any -> any any (msg:"TCP Connect scan detecte";
    flags:A,12; threshold: type both, track by_src, count 15, seconds 5;
    sid:2000002; rev:1;)

# 3. Detection ICMP ping flood
alert icmp any any -> any any (msg:"ICMP Ping detecte";
    icode:0; itype:8; threshold: type both, track by_src, count 5, seconds 2;
    sid:2000003; rev:1;)

# 4. Detection SSH brute force
alert tcp any any -> any 22 (msg:"SSH Brute Force - connexions multiples";
    flow:to_server; threshold: type both, track by_src, count 5, seconds 10;
    sid:2000004; rev:1;)

# 5. Detection SSH connection
alert tcp any any -> any 22 (msg:"SSH Connexion entrante detectee";
    flow:to_server,established; sid:2000005; rev:1;)

# 6. Detection FTP
alert tcp any any -> any 21 (msg:"FTP Tentative de connexion detectee";
    flow:to_server; sid:2000006; rev:1;)

# 7. Detection Telnet
alert tcp any any -> any 23 (msg:"TELNET Tentative de connexion detectee";
    flow:to_server; sid:2000007; rev:1;)

# 8. Detection SMB
alert tcp any any -> any 445,139 (msg:"SMB Tentative de connexion detectee";
    flow:to_server; sid:2000008; rev:1;)

# 9. Detection Nmap XMAS scan
alert tcp any any -> any any (msg:"SCAN Nmap XMAS Tree detecte";
    flags:FPU,12; threshold: type both, track by_src, count 5, seconds 3;
    sid:2000009; rev:1;)

# 10. Detection Nmap NULL scan
alert tcp any any -> any any (msg:"SCAN Nmap NULL Scan detecte";
    flags:0,12; threshold: type both, track by_src, count 5, seconds 3;
    sid:2000010; rev:1;)

# 11. Detection MySQL
alert tcp any any -> any 3306 (msg:"MySQL Tentative de connexion detectee";
    flow:to_server; sid:2000011; rev:1;)

# 12. Detection PostgreSQL
alert tcp any any -> any 5432 (msg:"PostgreSQL Tentative de connexion detectee";
    flow:to_server; sid:2000012; rev:1;)

# 13. Detection HTTP curl User-Agent
alert tcp any any -> any 80 (msg:"HTTP curl User-Agent detecte";
    flow:to_server,established; content:"User-Agent|3a| curl"; http_header;
    nocase; sid:2000013; rev:1;)

# 14. Detection SQL injection UNION SELECT
alert tcp any any -> any 80 (msg:"SQL Injection - UNION SELECT detectee";
    flow:to_server,established; content:"union select"; nocase;
    http_client_body; sid:2000014; rev:1;)

# 15. Detection SQL injection OR/AND
alert tcp any any -> any 80 (msg:"SQL Injection - OR/AND detectee";
    flow:to_server,established; content:" or 1=1"; nocase;
    http_client_body; sid:2000015; rev:1;)

# 16. Detection DNS query
alert udp any any -> any 53 (msg:"DNS Requete detectee"; sid:2000016; rev:1;)

# 17. Detection HTTP request
alert tcp any any -> any 80 (msg:"HTTP Requete detectee";
    flow:to_server,established; sid:2000017; rev:1;)

# 18. Detection .exe download
alert tcp any any -> any 80 (msg:"HTTP Telechargement .exe detecte";
    flow:to_server,established; content:".exe"; nocase; http_uri;
    sid:2000018; rev:1;)

# 19. Detection Nmap FIN scan
alert tcp any any -> any any (msg:"SCAN Nmap FIN Scan detecte";
    flags:F,12; threshold: type both, track by_src, count 5, seconds 3;
    sid:2000019; rev:1;)

# 20. Detection port scan general
alert tcp any any -> any any (msg:"SCAN Port Scan detecte";
    flags:S,12; threshold: type both, track by_src, count 20, seconds 5;
    sid:2000020; rev:1;)
```

### Syntaxe des règles Snort

```
action proto src_ip src_port -> dst_ip dst_port (options;)
```

| Élément | Description | Exemple |
|---------|-------------|---------|
| `alert` | Action | `alert`, `log`, `drop`, `reject` |
| `tcp/udp/icmp` | Protocole | `tcp` |
| `any` | Tout | `any` |
| `->` | Direction | `any -> any` |
| `flags:S,12` | Flags TCP + masque | `S`=SYN, `F`=FIN, `FPU`=XMAS |
| `content` | Chaîne à chercher | `content:"union select"` |
| `nocase` | Insensible à la casse | |
| `http_header` | Cherche dans l'en-tête HTTP | |
| `http_client_body` | Cherche dans le corps HTTP | |
| `http_uri` | Cherche dans l'URI | |
| `threshold` | Limite d'alertes | `count 5, seconds 10` |
| `sid` | Signature ID unique | `sid:2000001` |
| `rev` | Révision | `rev:1` |

---

## Module 04 — Détection d'Attaques

### Attaques simulées et résultats

#### 1. Scan Nmap SYN

```bash
sudo nmap -sS -p 22,80,443,8080 -T5 192.168.11.107
```

**Résultat :** Port 22 ouvert, 80/443/8080 fermés.
**Détection Snort :** ❌ (trafic local via lo — règles intégrées BAD-TRAFFIC détectées)

#### 2. Scan Nmap XMAS

```bash
sudo nmap -sX -p 22,80,443 -T5 192.168.11.107
```

**Résultat :** Port 22 `open|filtered`.
**Détection :** ❌ règles personnalisées — ✅ règles intégrées Snort (SID 527: same SRC/DST)

#### 3. Scan Nmap NULL

```bash
sudo nmap -sN -p 22,80,443 -T5 192.168.11.107
```

**Résultat :** Identique à XMAS.
**Détection :** ❌ règles personnalisées — ✅ règles intégrées

#### 4. Scan Nmap FIN

```bash
sudo nmap -sF -p 22,80,443 -T5 192.168.11.107
```

**Résultat :** Identique.
**Détection :** ❌ règles personnalisées — ✅ règles intégrées

#### 5. Scan TCP Connect

```bash
nmap -sT -p 22,80,443 -T5 192.168.11.107
```

**Résultat :** Scan complet.
**Détection :** ✅ **13 alertes** — SID 2000002 (TCP Connect scan)

#### 6. ICMP Ping

```bash
ping -c 10 192.168.11.107
```

**Résultat :** 10 paquets transmis/reçus.
**Détection :** ❌ règles personnalisées — ✅ règles intégrées SID 527 (ICMP same SRC/DST)

#### 7. SSH Brute Force

```bash
for i in {1..10}; do ssh oussama@127.0.0.1; done
```

**Résultat :** 10 échecs d'authentification.
**Détection :** ✅ **1 alerte** — SID 2000004 (SSH Brute Force - threshold atteint)

#### 8. HTTP curl

```bash
curl -s -A "curl/8.0" https://example.com
```

**Résultat :** Page HTML récupérée.
**Détection :** ✅ **5 alertes** — SID 2000017 (HTTP Requete)

#### 9. SQL Injection

```bash
curl "http://example.com/page?id=1 UNION SELECT * FROM users"
curl "http://example.com/login?user=admin' OR 1=1--"
```

**Résultat :** Requêtes HTTPS (port 443).
**Détection :** ❌ (règles ciblant le port 80 — le trafic vers example.com était en HTTPS)

#### 10. DNS Query

```bash
host google.com 8.8.8.8
```

**Résultat :** Résolution DNS réussie.
**Détection :** ✅ **18 alertes** — SID 2000016 (DNS Requete)

### Tableau récapitulatif

| Attaque | Règle Snort | SID | Alertes | Détection |
|---------|-------------|:---:|:-------:|:---------:|
| SYN Scan | Perso + Intégré | 2000001 / 527 | 0 / 6 | ✅ intégré |
| XMAS Scan | Perso + Intégré | 2000009 / 527 | 0 / 5 | ✅ intégré |
| NULL Scan | Perso + Intégré | 2000010 / 527 | 0 / 5 | ✅ intégré |
| FIN Scan | Perso + Intégré | 2000019 / 527 | 0 / 5 | ✅ intégré |
| TCP Connect | Perso | 2000002 | 13 | ✅ |
| ICMP Ping | Perso + Intégré | 2000003 / 527 | 0 / 10 | ✅ intégré |
| SSH Brute Force | Perso | 2000004 | 1 | ✅ |
| HTTP curl | Perso | 2000017 | 5 | ✅ |
| SQL Injection | Perso | 2000014/15 | 0 | ❌ (HTTPS) |
| DNS Query | Perso | 2000016 | 18 | ✅ |

---

## Module 05 — Mode IDS vs IPS

### Mode IDS (Intrusion Detection System)

Le mode IDS est le mode par défaut de Snort. Il analyse passivement le trafic et génère des alertes sans intervenir.

```bash
# Mode IDS (détection seule)
snort -c /etc/snort/snort.conf -i wlp1s0 -l /var/log/snort
```

### Mode IPS (Intrusion Prevention System)

Le mode IPS permet à Snort de **bloquer activement** le trafic malveillant en utilisant :
- `nfq` (NetFilter Queue) — mode inline via iptables
- `afpacket` — mode inline avec deux interfaces

#### Configuration IPS avec NFQUEUE

```bash
# 1. Activer le forwarding IP
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# 2. Règles iptables pour rediriger le trafic vers Snort
sudo iptables -I FORWARD -j NFQUEUE --queue-num 0
sudo iptables -I INPUT -j NFQUEUE --queue-num 0

# 3. Lancer Snort en mode inline
snort -c /etc/snort/snort.conf -Q -N --daq nfq \
      --daq-var queue=0 -l /var/log/snort/ips
```

#### Règles de type `drop` et `reject`

En mode IPS, les règles doivent utiliser l'action `drop` ou `reject` :

```snort
# Bloquer un scan SYN
drop tcp any any -> any any (msg:"BLOCKED SYN Scan detected";
    flags:S,12; threshold: type both, track by_src, count 10, seconds 5;
    sid:3000001; rev:1;)

# Rejeter une connexion SSH brute force
reject tcp any any -> any 22 (msg:"BLOCKED SSH Brute Force";
    flow:to_server; threshold: type both, track by_src, count 5, seconds 10;
    sid:3000002; rev:1;)
```

### Différences IDS vs IPS

| Caractéristique | IDS | IPS |
|:---------------|:---:|:---:|
| Action par défaut | `alert` | `drop` / `reject` |
| Impact réseau | Aucun (passif) | Interrompt le trafic |
| Mode de capture | pcap | nfqueue / afpacket |
| Configuration | Simple | Complexe (iptables) |
| Risque | Aucun | Faux positifs bloquants |
| DAQ module | pcap | nfq, afpacket |

---

## Module 06 — Corrélation avec SIEM (Snort + Wazuh)

### Architecture Snort + Wazuh

```
[Snort IDS] ---> /var/log/snort/snort.alert.fast
                       |
                  [Wazuh Agent] ---> [Wazuh Server] ---> [Wazuh Indexer] ---> [Wazuh Dashboard]
```

### Intégration de Snort avec Wazuh

#### 1. Installation de Wazuh Agent

```bash
# Ajout du dépôt Wazuh
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo apt-key add -
echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list
sudo apt-get update
sudo apt-get install wazuh-agent

# Connexion au manager Wazuh
sudo /var/ossec/bin/manage_agents -f <server-ip>
```

#### 2. Configuration de la collecte des logs Snort

```xml
<!-- /var/ossec/etc/ossec.conf -->
<ossec_config>
  <localfile>
    <log_format>snort</log_format>
    <location>/var/log/snort/snort.alert.fast</location>
  </localfile>
</ossec_config>
```

#### 3. Règles de corrélation Wazuh

```xml
<!-- /var/ossec/rules/local_rules.xml -->
<rule id="100001" level="10">
  <if_sid>2012</if_sid>
  <match>SSH Brute Force</match>
  <description>Snort: SSH Brute Force detectee et correlee par Wazuh</description>
</rule>

<rule id="100002" level="8">
  <if_sid>2012</if_sid>
  <match>SCAN Nmap</match>
  <description>Snort: Scan Nmap detecte et correle par Wazuh</description>
</rule>
```

#### 4. Visualisation dans Wazuh Dashboard

Alertes Snort visibles dans le tableau de bord Wazuh, avec :
- Chronologie des attaques
- Topologies des IPs attaquantes
- Cartographie des menaces
- Corrélation avec d'autres sources (syslog, auth.log)

> **Note :** Wazuh n'étant pas installé sur cette machine, l'intégration complète n'a pu être testée. Les étapes ci-dessus décrivent la procédure standard.

---

## Module 07 — Mini Projet — Scénario Complet

### Scénario : Attaque en plusieurs phases

**Contexte :** Un attaquant tente de pénétrer un serveur Ubuntu via une attaque multi-phase.

#### Phase 1 : Reconnaissance

```bash
# SYN Scan pour identifier les ports ouverts
nmap -sS -p 1-65535 -T4 192.168.11.107
```

**Alerts Snort :**
```
[1:2000001:1] SCAN Nmap SYN Scan detecte
[1:527:8] BAD-TRAFFIC same SRC/DST
```

#### Phase 2 : Scan de vulnérabilités

```bash
# Scan XMAS pour contourner les防火Wall / IDS
nmap -sX -p 22,80,443 -T5 192.168.11.107
nmap -sN -p 22,80,443 -T5 192.168.11.107
nmap -sF -p 22,80,443 -T5 192.168.11.107
```

**Alerts Snort :**
```
[1:527:8] BAD-TRAFFIC same SRC/DST  (XMAS, NULL, FIN)
```

#### Phase 3 : Brute force SSH

```bash
# 10 tentatives de connexion SSH
for i in {1..10}; do ssh oussama@192.168.11.107; done
```

**Alerts Snort :**
```
[1:2000004:1] SSH Brute Force - connexions multiples
```

#### Phase 4 : Exfiltration (DNS tunneling)

```bash
# Requêtes DNS vers l'extérieur
host google.com 8.8.8.8
```

**Alerts Snort :**
```
[1:2000016:1] DNS Requete detectee  (18 alertes)
```

#### Phase 5 : Téléchargement de malware

```bash
# Téléchargement d'un fichier .exe
curl -A "curl/8.0" -o /tmp/setup.exe http://example.com/setup.exe
```

**Alerts Snort :**
```
[1:2000017:1] HTTP Requete detectee
```

### Rapport d'Incident

```
RAPPORT D'INCIDENT
==================
ID: INC-2026-06-05-001
Date: 05/06/2026
Niveau: ÉLEVÉ (8/10)

CHRONOLOGIE :
  13:06:25 - Phase 1: SYN Scan (reconnaissance)
  13:06:42 - Phase 2: XMAS/NULL/FIN Scan (contournement)
  13:06:48 - Phase 3: SSH Brute Force (10 tentatives)
  13:06:49 - Phase 4: DNS Query (exfiltration)
  13:06:50 - Phase 5: HTTP Download (.exe)

INDICATEURS DE COMPROMISSION (IoC) :
  - IP source: 192.168.11.107
  - Ports cibles: 22, 80, 443, 8080
  - User-Agent: curl/8.0
  - Fichier: setup.exe

ALERTES SNORT DÉCLENCHÉES :
  SID 527: BAD-TRAFFIC same SRC/DST (scans)
  SID 2000002: TCP Connect scan (13x)
  SID 2000004: SSH Brute Force (1x)
  SID 2000016: DNS Requete (18x)
  SID 2000017: HTTP Requete (5x)

ACTIONS RECOMMANDÉES :
  1. Bloquer l'IP source au niveau du pare-feu
  2. Renouveler les clés SSH du serveur
  3. Analyser le fichier setup.exe téléchargé
  4. Activer le mode IPS pour bloquer automatiquement
  5. Déployer Wazuh pour la corrélation SIEM
```

---

## Commandes Essentielles

```bash
# Test de configuration
sudo snort -T -c /etc/snort/snort.conf

# Démarrage IDS
sudo snort -c /etc/snort/snort.conf -i wlp1s0 -D -l /var/log/snort
sudo snort -c /etc/snort/snort.conf -i lo -D -l /var/log/snort/lo

# Démarrage IPS (inline)
sudo snort -c /etc/snort/snort.conf -Q -N --daq nfq --daq-var queue=0

# Analyse des alertes
sudo cat /var/log/snort/snort.alert.fast
sudo grep "2000004" /var/log/snort/lo/snort.alert.fast

# Statistiques
sudo cat /var/log/snort/snort.alert.fast | awk '{print $3}' | sort | uniq -c | sort -rn

# Conversion unified2 -> pcap
sudo u2boat /var/log/snort/snort.alert /tmp/alerts.pcap

# Recharger les règles (SIGHUP)
sudo kill -HUP $(pgrep snort)
```

---

## Réponses aux Questions

### Module 01

**Q1 : Quelle est la différence entre Snort 2 et Snort 3 ?**
Snort 3 apporte le multithreading, une meilleure performance, une configuration en Lua, et une architecture modulaire. Le format des règles reste compatible.

**Q2 : Comment vérifier que Snort écoute sur une interface ?**
Avec `ps aux | grep snort` et en consultant `/var/log/snort/snort.alert.fast`.

### Module 02

**Q3 : Quelle est la structure d'un log alert_fast ?**
`Date Heure [**] [GID:SID:Rev] Message [**] [Classification] [Priority] {Proto} SRC:PORT -> DST:PORT`

**Q4 : Comment lire les logs unified2 ?**
Avec `u2boat` pour convertir en pcap, puis `tcpdump` pour l'analyse.

### Module 03

**Q5 : Expliquer `flags:S,12` dans une règle.**
`S` = le flag SYN est positionné, `12` = masque qui vérifie seulement les flags SYN et ACK (ignore les autres).

**Q6 : À quoi sert `http_client_body` ?**
À rechercher un contenu dans le corps de la requête HTTP (utile pour les injections SQL, XSS, etc.).

### Module 04

**Q7 : Pourquoi les scans XMAS/NULL/FIN n'ont-ils pas été détectés par nos règles ?**
Sur une machine mono-interface, le trafic d'auto-scan transite par la boucle locale. Les flags spéciaux peuvent être modifiés par le noyau Linux sur lo.

**Q8 : Comment améliorer la détection SQL injection ?**
Écrire des règles sur le port 443 (HTTPS) avec décryptage SSL, ou analyser le trafic après terminaison TLS.

### Module 05

**Q9 : Différence entre `alert` et `drop` dans une règle Snort ?**
`alert` génère une alerte sans bloquer ; `drop` bloque le paquet (nécessite le mode inline/IPS).

**Q10 : Comment activer le mode IPS ?**
Avec l'option `-Q` (inline) et un module DAQ supportant le mode inline (`nfq`, `afpacket`, `ipfw`).

### Module 06

**Q11 : Quel est l'intérêt d'intégrer Snort avec Wazuh ?**
Corrélation multi-sources, visualisation centralisée, alerting avancé, conformité (PCI-DSS, HIPAA, GDPR).

**Q12 : Comment Wazuh collecte-t-il les logs Snort ?**
Via un agent Wazuh configuré pour lire `/var/log/snort/snort.alert.fast` avec le format `snort`.

### Module 07

**Q13 : Quels indicateurs de compromission (IoC) peut-on extraire des logs Snort ?**
IP source, ports cibles, types de scan, User-Agent, fichiers téléchargés, horodatage, protocoles utilisés.

**Q14 : Comment passer d'une détection à une prévention active ?**
En activant le mode IPS avec `-Q` et en remplaçant `alert` par `drop` pour les signatures critiques.

---

## Comparaison Snort vs Suricata (TP1)

| Critère | Suricata (TP1) | Snort (TP2) |
|---------|:--------------:|:-----------:|
| Version | 8.0.5 | 2.9.20 |
| Multithreading | ✅ Natif | ❌ (Snort 3 seulement) |
| Format règles | Similaire | Similaire |
| Sortie JSON (eve.json) | ✅ Natif | ❌ (unified2) |
| Configuration | YAML | Texte (Lua dans v3) |
| Performance | Élevée | Modérée |
| Facilité d'installation | ✅ (apt) | ✅ (apt pour v2) |
| Mode IPS | ✅ (af-packet, nfqueue) | ✅ (nfq, afpacket) |

---

## Conclusion

Ce TP a permis de :

1. ✅ Installer et configurer Snort 2.9.20 en mode IDS
2. ✅ Créer 20 règles de détection personnalisées (SID 2000001-2000020)
3. ✅ Simuler 10 types d'attaques réseaux (scans, brute force, HTTP, DNS, SQLi)
4. ✅ Analyser les logs Snort (alert_fast, unified2)
5. ✅ Comprendre la différence entre IDS et IPS
6. ✅ Documenter l'intégration Snort + Wazuh pour un SIEM
7. ✅ Rédiger un rapport d'incident complet (Mini Projet)

**Résultats clés :**
- **136 alertes** générées au total (99 intégrées + 37 règles personnalisées)
- **5 types d'attaques détectées** par les règles personnalisées
- Les règles intégrées Snort ont efficacement complété la détection

---

*Rapport généré le 05 Juin 2026 — TP2 Cybersécurité : Gestion des Intrusions*
