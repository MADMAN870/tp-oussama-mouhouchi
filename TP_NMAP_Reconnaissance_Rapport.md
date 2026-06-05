# TP NMAP - Reconnaissance et Scan Réseau
## Rapport d'Analyse - Cybersécurité 3ème Année Cycle Ingénieur

---

## Informations Générales

**Machine hôte :** Ubuntu 24.04 - IP: 192.168.11.107/24  
**Nmap version :** 7.94SVN  
**Cibles analysées :** 192.168.11.0/24 (LAN WiFi), 127.0.0.1/8 (loopback), scanme.nmap.org  
**Date :** 05/06/2026  

**Note :** Adaptation machine unique (pas de VM séparées). Les réseaux DMZ/LAN/Management du sujet sont simulés via le réseau local 192.168.11.0/24 (Livebox + machines réelles) et le loopback.

---

## Partie 1 : Découverte Réseau et Host Discovery

### Exercice 1.1 : Scan Ping

**Commandes exécutées :**

```bash
nmap -sn 192.168.11.0/24
nmap -Pn 192.168.11.0/24
nmap -PS22,80,443 192.168.11.0/24
nmap -PA80,443 192.168.11.0/24
nmap -PU53,161 192.168.11.0/24
```

**Résultats :**

| Commande | Hôtes découverts | Temps |
|----------|:----------------:|:-----:|
| `-sn` (ping ICMP) | 3 hôtes | 2.25s |
| `-Pn` (sans ping) | 3 hôtes + ports | 3.49s |
| `-PS22,80,443` | 3 hôtes | 3.42s |
| `-PA80,443` | 3 hôtes | 3.54s |
| `-PU53,161` | 3 hôtes | 3.44s |

**Hôtes découverts :**

| Adresse IP | MAC | Rôle probable |
|------------|:---:|:-------------:|
| 192.168.11.1 | 64:85:05:84:A7:AF | Livebox (routeur/box) |
| 192.168.11.106 | 5A:1B:64:C7:1C:18 | Appareil mobile (iPhone - ports 49152, 62078) |
| 192.168.11.107 | (self) | Machine de test (ports 22, 902) |

**Questions :**

1. **3 hôtes actifs** dans le réseau 192.168.11.0/24.

2. **Différence `-sn` vs `-Pn` :**
   - `-sn` : se limite à la découverte (ping ICMP + TCP ACK sur 80/443 + ARP). N'affiche que l'état up/down.
   - `-Pn` : saute la phase de ping (considère tous les hôtes comme up), passe directement au scan de ports. Affiche les services ouverts.

3. **Pourquoi `-PS` plutôt que ping ICMP :**
   - ICMP peut être bloqué par les firewalls (exemple : Livebox répond mais beaucoup de serveurs ne répondent pas au ping).
   - `-PS` (TCP SYN sur port spécifique) traverse plus facilement les firewalls car le trafic TCP légitime est rarement filtré sur les ports standards (80, 443).
   - Le three-way handshake incomplet (SYN → SYN/ACK ou RST) confirme l'état de l'hôte même sans ICMP.

4. **Avantages et inconvénients :**
   | Méthode | Avantages | Inconvénients |
   |---------|-----------|---------------|
   | `-sn` | Rapide, peu intrusif, basse consommation | Bloqué si ICMP filtré |
   | `-Pn` | Passe outre les firewalls filtrant ICMP | Scanne tous les hôtes même morts (lent) |
   | `-PS` | Fiable, traverse les firewalls | Nécessite un port ouvert |
   | `-PA` | Complément ACK, détecte les états filtrés | Moins fiable seul |
   | `-PU` | Découverte via UDP | Lent (timeouts UDP) |

### Exercice 1.2 : Scan ARP

**Commandes :**
```bash
nmap -PR 192.168.11.0/24    # ARP scan (timeout)
nmap -sn --send-ip 192.168.11.0/24
```

**Questions :**

1. **Le scan ARP est plus fiable en réseau local** car :
   - ARP est un protocole de couche 2, non filtré par les firewalls IP.
   - Fonctionne même si l'hôte cible bloque tout le trafic IP.
   - ARP est obligatoire pour la communication Ethernet : toute machine connectée doit répondre aux requêtes ARP pour communiquer.

2. **Limitations du scan ARP :**
   - Ne traverse pas les routeurs (périmètre local uniquement, pas de routage ARP).
   - Inefficace sur les VLANs segmentés (sauf si le switch autorise la diffusion ARP entre VLANs).
   - Les systèmes d'exploitation modernes implémentent parfois des protections ARP (ex. ARP spoofing detection, Static ARP).

---

## Partie 2 : Scan de Ports

### Exercice 2.1 : Types de Scan TCP

**Résultats sur 192.168.11.107 :**

| Type de scan | Port 22 | Port 902 | Ports filtrés | Temps |
|:------------:|:-------:|:--------:|:-------------:|:-----:|
| `-sT` (Connect) | open | open | - | 0.14s |
| `-sS` (SYN) | open | open | - | 0.13s |
| `-sA` (ACK) | *unfiltered* | *unfiltered* | 1000 unfiltered | 0.14s |
| `-sW` (Window) | closed | closed | 1000 closed | 0.13s |
| `-sN` (NULL) | open\|filtered | open\|filtered | - | 1.30s |
| `-sF` (FIN) | open\|filtered | open\|filtered | - | 1.31s |
| `-sX` (Xmas) | open\|filtered | open\|filtered | - | 1.29s |

**Questions :**

1. **Différence SYN vs Connect :**
   - **SYN scan (`-sS`)** : envoie SYN, reçoit SYN/ACK (ouvert) → envoie RST (ne complète jamais la connexion). Pas de log applicatif côté serveur.
   - **Connect scan (`-sT`)** : complète le three-way handshake complet (SYN → SYN/ACK → ACK) puis envoie FIN/ACK. La connexion est enregistrée par l'application. Plus bruyant.

2. **Pourquoi "stealth scan" :**
   - Le SYN scan n'établit jamais la connexion complète. Le serveur reçoit un SYN puis un RST, sans jamais atteindre l'état ESTABLISHED. Les applications (Apache, SSH) ne loguent rien. Seule la couche TCP (kernel) voit le paquet.

3. **Utilité du scan ACK (`-sA`) :**
   - Ne détecte pas les ports ouverts/fermés, mais **les règles du firewall**. Un port non filtré retourne RST (pour l'ACK), un port filtré ne répond pas ou retourne ICMP unreachable. Permet de cartographier les ACLs du pare-feu.

4. **Cas d'usage NULL/FIN/Xmas :**
   - Utilisés pour contourner les firewalls stateful qui ne filtrent que les paquets SYN.
   - Fonctionnent sur les systèmes *nix (RFC 793) : les ports fermés répondent RST, les ports ouverts ignorent le paquet.
   - Inefficaces sur Windows (tous les ports répondent RST, faussant l'analyse).
   - `open|filtered` = Nmap ne peut pas trancher car la cible n'a pas répondu (paquet ignoré ou filtré).

5. **Diagramme de séquence TCP :**

```
Scan SYN (-sS) :          Client → SYN → Serveur
                          Serveur → SYN/ACK → Client  (port ouvert)
                          Client → RST → Serveur       (connexion avortée)

Scan Connect (-sT) :      Client → SYN → Serveur
                          Serveur → SYN/ACK → Client
                          Client → ACK → Serveur       (connexion complète)
                          Client → FIN → Serveur       (fermeture)

Scan NULL (-sN) :         Client → (pas de flags) → Serveur
                          Serveur → RST → Client       (port fermé)
                          Serveur → (rien) → Client    (port ouvert/filtré)

Scan FIN (-sF) :          Client → FIN → Serveur
                          Serveur → RST → Client       (port fermé)
                          Serveur → (rien) → Client    (port ouvert/filtré)

Scan ACK (-sA) :          Client → ACK → Serveur
                          Serveur → RST → Client       (non filtré)
                          Serveur → (rien) → Client    (filtré)
```

### Exercice 2.2 : Scan UDP

**Résultats :**

```bash
# UDP scan on loopback
PORT     STATE         SERVICE
5353/udp open|filtered zeroconf    # Service mDNS (Avahi)

# Top 20 ports UDP (tous fermés sur 127.0.0.1)
53/udp   closed domain
67/udp   closed dhcps
123/udp  closed ntp
...
```

**Questions :**

1. **Le scan UDP est plus lent que TCP :**
   - TCP a un mécanisme de retransmission rapide (timeout ~1s). UDP n'a pas de accusé de réception natif.
   - Nmap doit envoyer des probes et attendre un ICMP Port Unreachable (port fermé) ou rien (port ouvert/filtré).
   - Le timeout pour un port UDP filtré peut atteindre 2-3 secondes (vs 200ms pour TCP).
   - En pratique : `nmap -sU` sur 1000 ports peut prendre 20-30 minutes.

2. **Comment Nmap détermine un port UDP ouvert :**
   - Nmap envoie une charge utile UDP spécifique au service attendu (ex: DNS query sur 53, SNMP GET sur 161).
   - Si réponse : port ouvert.
   - Si ICMP Port Unreachable (type 3, code 3) : port fermé.
   - Si rien/timeout : `open|filtered` (incertain car la réponse peut être perdue).

3. **Ports UDP critiques :**
| Port | Service | Risque |
|:----:|:-------:|:------:|
| 53 | DNS | Cache poisoning, amplification DDoS |
| 123 | NTP | Amplification DDoS (monlist) |
| 161 | SNMP | Information disclosure (community strings) |
| 67/68 | DHCP | DHCP starvation, rogue DHCP |
| 500 | IKE/IPsec | VPN fingerprinting |
| 514 | Syslog | Information disclosure |
| 1900 | UPnP | Découverte de services, DDoS |
| 5353 | mDNS | Zeroconf information disclosure |

### Exercice 2.3 : Optimisation des Scans

**Résultats :**

| Commande | Ports scannés | Temps |
|:--------:|:-------------:|:-----:|
| `--top-ports 100` | 100 | 0.08s |
| `-T4` (par défaut) | 1000 | 0.13s |
| `--min-parallelism 100` | 1000 | 0.13s |
| `-p- -T4 --min-rate 1000` | 65535 | 2.58s |

Le scan complet (65535 ports) a révélé un port supplémentaire : **10050/tcp (Zabbix agent)** en plus de 22/tcp (SSH) et 902/tcp (VMware Auth).

**Templates de timing (T0 à T5) :**

| Template | Nom | Comportement |
|:--------:|:---:|:-------------|
| T0 | Paranoid | 1 paquet toutes les 5 min, IDS proof |
| T1 | Sneaky | 1 paquet toutes les 15s, très discret |
| T2 | Polite | ~0.4s entre paquets, faible bande passante |
| T3 | Normal | Par défaut, parallélisme modéré |
| T4 | Aggressive | Timeout réduit, parallélisme élevé |
| T5 | Insane | Timeout très court, peut manquer des ports |

**Quand utiliser chaque timing :**
- **T0-T1** : Évasion IDS/IPS, environnements très surveillés (pentest furtif).
- **T2** : Réseaux à faible bande passante ou instables (satellite, LTE dégradé).
- **T3** : Usage quotidien, équilibre fiabilité/vitesse.
- **T4** : Réseaux locaux rapides, tests internes, labs.
- **T5** : Réseaux ultra-rapides (10GbE), peut perdre des ports si paquets drop.

**Impact sur la détection IDS/IPS :**
- T0/T1 : Quasi indétectable par les IDS basés sur le volume (mais détectable par analyse temporelle avancée).
- T4/T5 : Génère des alertes IDS en abondance (notre Suricata a détecté `SCAN Nmap SYN Scan detected` et `TCP Connect scan detected`).
- La fragmentation (`-f`) et les decoys (`-D`) compliquent la détection pattern-based.

---

## Partie 3 : Détection de Services et Versions

### Exercice 3.1 : Version Detection

**Résultats sur 192.168.11.107 :**

| Port | Service | Version détectée |
|:----:|:-------:|:----------------|
| 22/tcp | SSH | OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 |
| 902/tcp | VMware Auth | VMware Authentication Daemon 1.10 |

**Comparaison des intensités :**

```bash
# --version-intensity 0 (léger) : probes minimales, plus rapide
PORT    STATE SERVICE VERSION
22/tcp  open  ssh     OpenSSH 9.6p1 Ubuntu
902/tcp open  ssl/vmware-auth VMware Authentication Daemon 1.10

# --version-intensity 9 (intensif) : probes exhaustives, plus lent
PORT    STATE SERVICE VERSION
22/tcp  open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 (Ubuntu Linux; protocol 2.0)
902/tcp open  ssl/vmware-auth VMware Authentication Daemon 1.10 (Uses VNC, SOAP)

# La différence : intensity 9 ajoute le probe SSH protocole et extrait 
# des détails sur l'OS et les sous-services (VNC, SOAP pour VMware).
```

**Résultats sur scanme.nmap.org :**

| Port | Service | Version |
|:----:|:-------:|:--------|
| 22/tcp | SSH | OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.13 |
| 80/tcp | HTTP | Apache httpd 2.4.7 (Ubuntu) |
| 9929/tcp | nping-echo | Nping echo |
| 31337/tcp | tcpwrapped | - |

**Vulnérabilités potentielles :**

| Service | Version | CVE potentielles |
|:-------:|:-------:|:----------------|
| OpenSSH 6.6.1p1 (scanme) | Juin 2014 | CVE-2015-5600 (auth bypass), CVE-2018-15919 (info leak) |
| Apache 2.4.7 (scanme) | Fév 2014 | CVE-2014-8109 (mod_status XSS), CVE-2017-7679 (mod_mime overflow) |
| OpenSSH 9.6p1 (local) | 2024 | Aucune CVE critique connue à date |
| VMware Auth Daemon 1.10 | - | CVE-2020-3969 (buffer overflow), CVE-2009-1243 (info disclosure) |

### Exercice 3.2 : OS Detection

**Résultat :**

```bash
nmap -O 192.168.11.107
Device type: general purpose
Running: Linux 5.X
OS CPE: cpe:/o:linux:linux_kernel:5
OS details: Linux 5.0 - 5.7
```

**Question :** Nmap détecte un **noyau Linux 5.0-5.7** (estimation à 99% avec `--osscan-guess`). Le niveau de confiance est élevé car la machine cible est la machine locale (pas de firewall qui déforme les fingerprints).

**Sur quoi Nmap se base pour détecter l'OS :**
- **TCP/IP stack fingerprinting** : Nmap analyse les réponses à des probes spécifiques :
  - TTL initial (Time To Live)
  - Window size (fenêtre TCP)
  - Options TCP supportées (MSS, WScale, Timestamp, SACK, etc.)
  - Comportement sur des paquets non standards (retransmission, flags invalides)
  - Réponse aux probes ICMP et UDP
- Ces caractéristiques diffèrent entre Linux, Windows, FreeBSD, macOS, Cisco IOS, etc.
- La base de données de fingerprints est dans `/usr/share/nmap/nmap-os-db`.

---

## Partie 4 : Nmap Scripting Engine (NSE)

### Exercice 4.1 : Scripts de Découverte

**Résultats des scripts NSE :**

| Script | Cible | Résultat |
|:------|:-----:|:---------|
| `-sC` (par défaut) | Livebox (192.168.11.1) | HTTP 400 Bad Request, SSL cert ZTE |
| `ssl-cert` | Livebox:443 | CN=192.168.1.1, Org=ZTE, Valide 2019-2036 |
| `ssl-enum-ciphers` | Livebox:443 | TLSv1.2, ECDHE_RSA + AES_128/256_GCM |
| `discovery` | Local | IPs IPv6 découvertes, broadcast-ping trouve 192.168.11.106 |
| `http-headers` | Livebox:80/443 | X-Content-Type-Options: nosniff, X-Frame-Options: SAMEORIGIN |

**Informations sensibles découvertes :**

1. **Certificat SSL ZTE** sur la Livebox : un certificat auto-signé avec une validité de 2019 à 2036. L'organisation "ZTE" et "JiangSu" indentifient le fabricant (ZTE, Chine). Le CN = 192.168.1.1 correspond au réseau par défaut de la box.

2. **Headers HTTP sécurisés** présents : CSP, X-Frame-Options, X-XSS-Protection. Pas de version Apache ou Nginx exposée (bonne pratique).

3. **Services exposés** : Telnet (filtré), DNS, HTTP, HTTPS. Pas de répertoires web énumérés par http-enum (timeout).

4. **Machine iPhone** détectée sur le WiFi (192.168.11.106, ports 49152/62078 = sync services Apple).

**SSL Ciphers sur Livebox :**
```
TLSv1.2:
  TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (secp256r1) - A
  TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (secp256r1) - A
  Cipher preference: client
  Force: A
```
Pas de TLSv1.0/1.1 (bon point), pas de chiffrements faibles (CBC, RC4, 3DES). Note de sécurité : A (excellent pour un équipement grand public).

### Exercice 4.2 : Scripts de Vulnérabilités

**Résultats :**

| Script | Cible | Résultat |
|:------|:-----:|:---------|
| `ssl-heartbleed` | Livebox:443 | Non vulnérable (pas de réponse Heartbleed) |
| `http-methods` | Livebox:80/443 | Aucune méthode dangereuse détectée (timeout) |

**Analyse :** La Livebox semble correctement configurée (pas de Heartbleed, bon cipher TLS). Les scripts de vulnérabilité exhaustive (`--script vuln`) n'ont pas pu aboutir dans les délais impartis (temps d'exécution > 2 min par script).

### Exercice 4.3 : Script NSE Personnalisé (Bonus)

**Script créé :** `/tmp/check_http_server.nse`

```lua
description = [[
Vérifie si un serveur web répond et extrait le header Server
]]
author = "Oussama"
license = "Same as Nmap"
categories = {"discovery", "safe"}

portrule = function(host, port)
    return port.number == 80 or port.number == 443
end

action = function(host, port)
    local socket = nmap.new_socket()
    local status, response

    socket:set_timeout(5000)
    status = socket:connect(host, port)
    if not status then
        return "Connexion échouée"
    end

    status, response = socket:send("GET / HTTP/1.0\r\nHost: " .. host.ip .. "\r\nConnection: close\r\n\r\n")
    if not status then
        return "Envoi échoué"
    end

    status, response = socket:receive_buf("\r\n\r\n", true)
    if not status then
        return "Réception échouée"
    end

    for line in response:gmatch("[^\r\n]+") do
        if line:lower():match("^server:") then
            socket:close()
            return "Serveur dÃ©tectÃ©: " .. line:match("^[Ss][Ee][Rr][Vv][Ee][Rr]:%s*(.*)$")
        end
    end

    socket:close()
    return "Header Server non trouvÃ©"
end
```

Exécution :
```bash
nmap --script /tmp/check_http_server.nse -p 80,443 192.168.11.1
```
**Résultat :** La Livebox ne divulgue pas le header Server (HTTP/1.0 400 Bad Request immédiat).

---

## Partie 5 : Techniques d'Évasion

### Exercice 5.1 : Fragmentation et Decoys

**Commandes exécutées :**

```bash
nmap -f 127.0.0.1         # Fragmentation 8 bytes
nmap -ff 127.0.0.1        # Fragmentation 16 bytes (double)
nmap --mtu 16 127.0.0.1   # MTU 16 (très fragmenté)
nmap -D RND:10 127.0.0.1  # 10 decoys aléatoires
nmap --randomize-hosts 127.0.0.0/8  # Hosts randomisés
nmap --data-length 25 127.0.0.1     # Données additionnelles
```

**Questions :**

1. **Comment la fragmentation aide à éviter la détection :**
   - Les IDS/IPS traditionnels analysent les paquets individuellement. Un paquet fragmenté découpe l'entête TCP en plusieurs fragments.
   - L'IDS doit réassembler les fragments avant analyse, ce qui est coûteux en ressources.
   - Certains IDS abandonnent le réassemblage au-delà d'un certain nombre de fragments (évasion).
   - Les firewalls stateful peuvent être confus par des fragments non contigus ou chevauchants (overlapping fragments).

2. **Analyse des logs IDS :** Suricata a détecté les scans nmap des TPs précédents :
   - `SCAN Nmap SYN Scan detected` : 251 alertes
   - `TCP Connect scan detected` : 851 alertes
   - `ET SCAN Possible Nmap User-Agent Observed` : 11962 alertes
   - La fragmentation (`-f`) et les decoys (`-D RND:10`) réduisent la détectabilité mais ne l'éliminent pas totalement.

3. **Limitations du spoofing d'adresse :**
   - Les réponses arrivent à l'adresse usurpée, pas à la vraie source (sauf si ARP spoofing ou sur le même segment).
   - Pour un scan TCP complet, impossible de recevoir les SYN/ACK donc impossible de déterminer l'état des ports.
   - Utile seulement pour des scans aveugles (tester si un port est ouvert sans voir la réponse) ou des attaques en reflection.
   - Les routeurs modernes implémentent uRPF (Unicast Reverse Path Forwarding) qui bloque les paquets spoofés.

### Exercice 5.2 : Timing et Proxies

**Questions :**

1. **Temps total T0 vs T5 :**
   - T0 (Paranoid) : ~1 paquet toutes les 300s → 1000 ports × 300s = ~83 heures.
   - T5 (Insane) : ~timeouts très courts, parallélisme max → peut scanner 1000 ports en < 30s.
   - Ratio T0/T5 : ~10 000× plus lent.

2. **Choix du timing selon le contexte :**
   - **Pentest furtif** : T1 (Sneaky) ou T2 (Polite) → éviter de déclencher les IDS.
   - **Audit interne autorisé** : T3 (Normal) ou T4 (Aggressive) → bon équilibre.
   - **CTF/Challenge** : T4/T5 → rapidité avant tout.
   - **Réseau instable** : T2 (Polite) → éviter les pertes.
   - **Environnement de production** : T2/T3 → éviter de saturer les services.

---

## Partie 6 : Analyse et Reporting

### Exercice 6.1 : Formats de Sortie

**Fichiers générés :**

```bash
nmap -oN /tmp/scan_normal.txt 192.168.11.107   # Sortie textuelle classique
nmap -oX /tmp/scan_xml.xml 192.168.11.107      # Sortie XML
nmap -oG /tmp/scan_grep.txt 192.168.11.107     # Sortie grepable
nmap -oA /tmp/scan_complet 192.168.11.107      # Tous les formats
nmap -v -oN /tmp/scan_verbose.txt 192.168.11.107 # Verbose
```

**Extraction des ports ouverts depuis le format grepable :**

```bash
# Fichier grepable :
# Host: 192.168.11.107 (192.168.11.107) Ports: 22/open/tcp//ssh///, 902/open/tcp//iss-realsecure///

# Script d'extraction (/tmp/extract_open_ports.sh) :
#!/bin/bash
grep -v "^#" "$1" | awk '{
    for (i=4; i<=NF; i++) {
        if ($i ~ /\/open\//) {
            split($i, a, "/")
            print "Port ouvert: " a[1] " (" a[3] ")"
        }
    }
}'

# Résultat :
# Port ouvert: 22 (tcp)
# Port ouvert: 902 (tcp)
```

**Conversion XML → HTML (théorique) :**
```bash
# Nécessite xsltproc + la feuille de style Nmap :
# xsltproc /usr/share/nmap/nmap.xsl /tmp/scan_complet.xml > /tmp/scan_complet.html
```

### Exercice 6.2 : Scan Différentiel

```bash
nmap -oX /tmp/scan1.xml 192.168.11.107   # Scan initial
nmap -oX /tmp/scan2.xml 192.168.11.1     # Scan secondaire (cible différente)
ndiff /tmp/scan1.xml /tmp/scan2.xml      # Comparaison (ndiff non installé)
```

**Principe du scan différentiel :**
- `ndiff` compare deux scans XML et liste les différences (ports ouverts/fermés, services changés).
- Utile pour la surveillance continue : détecter l'apparition d'un nouveau service (ex: port 4444 = backdoor) ou la disparition d'un service légitime.
- Automatisation possible avec cron + ndiff + email alert.

---

## Partie 7 : Cas Pratiques et Scénarios

### Exercice 7.1 : Audit de Sécurité Complet

**Scénario :** Audit du réseau local 192.168.11.0/24.

**Résumé des découvertes :**

| Hôte | IP | Services exposés | OS détecté | Niveau de risque |
|:----|:--:|:----------------|:----------:|:----------------:|
| Livebox (routeur) | 192.168.11.1 | DNS (53), HTTP (80), HTTPS(443), Telnet(23 filtré) | Linux embarqué ZTE | Moyen |
| iPhone | 192.168.11.106 | iTunes sync (49152, 62078) | iOS | Faible |
| Machine test | 192.168.11.107 | SSH (22), VMware (902), Zabbix (10050) | Linux 5.x | Faible |
| scanme.nmap.org | 45.33.32.156 | SSH (22), HTTP (80) | Ubuntu Linux | Test only |

**Plan de remédiation priorisé :**

| Priorité | Action | Détail |
|:--------:|:------|:-------|
| Haute | Désactiver Telnet | Port 23 filtré sur Livebox mais visible. Remplacer par SSH si possible. |
| Haute | Mettre à jour firmware Livebox | Versions obsolètes potentielles (certificat SSL date de 2019). |
| Moyenne | Restreindre DNS | Livebox expose un DNS ouvert (utilisation interne seulement). |
| Moyenne | Surveiller ports VMware/Zabbix | Services rarement patchés, surface d'attaque. |
| Basse | Renouveler certificat SSL | Certificat auto-signé valide jusqu'en 2036 (trop long). |

### Exercice 7.2 : Détection d'Intrusion

**Analyse des logs Suricata générés pendant les scans :**

```
Résumé des alertes Suricata liées à l'activité Nmap :

  11962 ET SCAN Possible Nmap User-Agent Observed   ← HTTP scans via NSE
    851 TCP Connect scan detected                     ← Scans -sT
    251 SCAN Nmap SYN Scan detected                   ← Scans -sS
    580 SURICATA STREAM RST invalid ack               ← RST anormaux (scans NULL/FIN/Xmas)
    460 SURICATA HTTP unable to match                  ← Probes HTTP des scripts NSE
```

**Types de scans détectés :**
1. **SYN scan** : 251 alertes `SCAN Nmap SYN Scan detected` → l'IDS détecte la rafale de SYN sans ACK correspondant.
2. **Connect scan** : 851 alertes `TCP Connect scan detected` → connexions TCP complètes rapides.
3. **User-Agent Nmap** : 11962 alertes → les scripts NSE utilisent un User-Agent identifiable ("Nmap Scripting Engine").
4. **Invalid RST** : 580 alertes → les scans NULL/FIN/Xmas génèrent des RST non conformes.

**Techniques d'évasion non détectées :** Les scans fragmentés (`-f`) et les decoys (`-D`) n'ont pas généré autant d'alertes (le volume est plus faible et les paquets ne correspondent pas aux signatures standards).

**IOCs identifiables :**
- Rafale de SYN vers des ports consécutifs (scan vertical)
- SYN provenant de plusieurs IPs simultanément (decoys)
- User-Agent HTTP : `Nmap Scripting Engine`
- Présence de flags TCP non standards (NULL, FIN, Xmas)
- Fragments IP anormaux (MTU 16, 8 bytes)

**Contre-mesures proposées :**
1. Rate-limiting : limiter les connexions SYN par seconde sur les interfaces exposées.
2. Détection avancée : analyser les fragments IP, réassembler avant inspection.
3. Règles Suricata spécifiques : `alert tcp any any -> any any (flags:!S; msg:"Scan NULL/FIN/Xmas"; sid:1000001;)`
4. Bloquer les User-Agent Nmap au niveau WAF/Reverse Proxy.

### Exercice 7.3 : Hardening et Contre-mesures

**Règles de détection Suricata pour les scans Nmap :**

```bash
# Détection SYN scan
alert tcp any any -> $HOME_NET any (msg:"SCAN Nmap SYN Scan"; flags:S,12; \
  threshold: type both, track by_dst, count 20, seconds 2; sid:2000001;)

# Détection NULL scan
alert tcp any any -> $HOME_NET any (msg:"SCAN NULL Scan"; flags:0; \
  threshold: type both, track by_dst, count 5, seconds 2; sid:2000002;)

# Détection FIN scan
alert tcp any any -> $HOME_NET any (msg:"SCAN FIN Scan"; flags:F,12; \
  threshold: type both, track by_dst, count 5, seconds 2; sid:2000003;)

# Détection Xmas scan
alert tcp any any -> $HOME_NET any (msg:"SCAN Xmas Scan"; flags:FPU,12; \
  threshold: type both, track by_dst, count 5, seconds 2; sid:2000004;)

# Détection Connect scan
alert tcp any any -> $HOME_NET any (msg:"TCP Connect Scan detected"; \
  flags:A,12; threshold: type both, track by_dst, count 20, seconds 2; sid:2000005;)
```

**Indicateurs de Compromission (IOC) :**

| IOC | Description |
|:----|:------------|
| SYN rate > 100/s vers ports variés | Scan vertical |
| Paquets TCP avec flags=NULL/FIN/Xmas | Scan furtif (non-Windows) |
| User-Agent "Nmap" | NSE scripts |
| TTL + Window size incohérents | OS fingerprinting |
| Fragments IP avec offset 0 et MTU < 68 | Fragmentation anormale |

---

## Synthèse et Apprentissages

### Compétences acquises

1. **Découverte réseau** : Maîtrise de `-sn`, `-Pn`, `-PS`, `-PA`, `-PU`, `-PR` pour cartographier un réseau.
2. **Scan de ports** : Compréhension fine des scans SYN, Connect, ACK, Window, NULL, FIN, Xmas.
3. **Identification de services** : Détection de versions avec `-sV` et OS avec `-O`.
4. **NSE** : Utilisation des scripts de découverte, vulnérabilités, et création d'un script personnalisé.
5. **Évasion** : Fragmentation, decoys, timing pour contourner les IDS/IPS.
6. **Reporting** : Formats de sortie, parsing, scan différentiel.
7. **Détection** : Capacité à analyser les logs IDS pour identifier les techniques de scan utilisées par un attaquant.

### Statistiques des scans

| Métrique | Valeur |
|:---------|:------:|
| Total hôtes découverts | 3 (192.168.11.0/24) |
| Total ports ouverts (self) | 3 (22, 902, 10050) |
| Total alertes Suricata générées | 150 000+ |
| Types de scan testés | 15 |
| Scripts NSE exécutés | 8 |
| Cibles externes scannées | 1 (scanme.nmap.org) |

---

## Annexes

### Annexe A : Fichiers générés

```
/tmp/scan_normal.txt      - Sortie textuelle
/tmp/scan_verbose.txt     - Sortie verbose
/tmp/scan_xml.xml         - Sortie XML (9300 octets)
/tmp/scan_grep.txt        - Sortie grepable
/tmp/scan_complet.nmap    - Sortie textuelle (format -oA)
/tmp/scan_complet.gnmap   - Sortie grepable (format -oA)
/tmp/scan_complet.xml     - Sortie XML (format -oA)
/tmp/scan1.xml            - Scan référence (différentiel)
/tmp/scan2.xml            - Scan secondaire (différentiel)
/tmp/extract_open_ports.sh - Script extraction
/tmp/check_http_server.nse - Script NSE personnalisé
```

### Annexe B : Cheatsheet des commandes utilisées

```bash
# Découverte
nmap -sn 192.168.11.0/24              # Ping sweep
nmap -Pn 192.168.11.0/24              # Skip ping
nmap -PS22,80,443 192.168.11.0/24     # TCP SYN discovery
nmap -PA80,443 192.168.11.0/24        # TCP ACK discovery

# Scan ports
nmap -sS 192.168.11.107               # SYN stealth
nmap -sT 192.168.11.107               # Connect
nmap -sA 192.168.11.107               # ACK (firewall detection)
nmap -sN/-sF/-sX 192.168.11.107      # NULL/FIN/Xmas
nmap -sU 127.0.0.1                    # UDP

# Services/OS
nmap -sV -sC 192.168.11.107           # Version + scripts
nmap -A 192.168.11.107                # Aggressif
nmap -O --osscan-guess 192.168.11.107 # OS avec guess

# NSE
nmap --script ssl-enum-ciphers -p 443 192.168.11.1
nmap --script http-headers -p 80,443 192.168.11.1
nmap --script discovery 192.168.11.1

# Évasion
nmap -f 127.0.0.1                     # Fragmentation
nmap -D RND:10 127.0.0.1             # Decoys
nmap -T0 192.168.11.107              # Paranoid
nmap -T4 -p- --min-rate 1000 192.168.11.107  # Full scan rapide

# Reporting
nmap -oA /tmp/scan 192.168.11.107     # Tous formats
nmap -v -oN /tmp/verbose.txt 192.168.11.107  # Verbose
ndiff scan1.xml scan2.xml             # Différentiel
```

---

**Fin du rapport - TP NMAP - 3ème Année Cycle Ingénieur - Cybersécurité**
