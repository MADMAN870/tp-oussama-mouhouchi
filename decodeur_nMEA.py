import sys
import re

NMEA_SENTENCES = {
    "$GPGGA": "Global Positioning System Fix Data",
    "$GPGLL": "Geographic Position - Latitude/Longitude",
    "$GPGSA": "GPS DOP and Active Satellites",
    "$GPGSV": "GPS Satellites in View",
    "$GPRMC": "Recommended Minimum Specific GPS/Transit Data",
    "$GPVTG": "Track Made Good and Ground Speed",
    "$GPGST": "GPS Pseudorange Noise Statistics",
    "$GPZDA": "Time and Date",
    "$GPGGA": "Global Positioning System Fix Data",
    "$GPGLL": "Geographic Position - Latitude/Longitude",
    "$GPGSA": "GPS DOP and Active Satellites",
    "$GPGSV": "GPS Satellites in View",
    "$GPRMC": "Recommended Minimum Specific GPS/Transit Data",
    "$GPVTG": "Track Made Good and Ground Speed",
    "$GPGST": "GPS Pseudorange Noise Statistics",
    "$GPZDA": "Time and Date",
    "$GNGGA": "GNSS Fix Data (GPS+GLONASS)",
    "$GNGLL": "GNSS Geographic Position",
    "$GNGSA": "GNSS DOP and Active Satellites",
    "$GNGSV": "GNSS Satellites in View",
    "$GNRMC": "GNSS Recommended Minimum Data",
    "$GNVTG": "GNSS Track Made Good and Ground Speed",
}

def nmea_checksum(sentence):
    if '*' not in sentence:
        return False
    msg, checksum = sentence.split('*')
    msg = msg.lstrip('$')
    calc = 0
    for c in msg:
        calc ^= ord(c)
    return calc == int(checksum.strip(), 16)

def decode_rmc(fields):
    time_str = fields[1]
    lat = fields[3]
    lat_dir = fields[4]
    lon = fields[5]
    lon_dir = fields[6]
    speed_knots = float(fields[7]) if fields[7] else 0.0
    course = float(fields[8]) if fields[8] else 0.0
    date_str = fields[9]
    mag_var = fields[10] if len(fields) > 10 else ""

    lat_dec = float(lat[:2]) + float(lat[2:]) / 60.0
    if lat_dir == 'S':
        lat_dec = -lat_dec
    lon_dec = float(lon[:3]) + float(lon[3:]) / 60.0
    if lon_dir == 'W':
        lon_dec = -lon_dec

    hh = time_str[:2] if len(time_str) >= 6 else "00"
    mm = time_str[2:4] if len(time_str) >= 6 else "00"
    ss = time_str[4:6] if len(time_str) >= 6 else "00"

    dd = date_str[:2] if len(date_str) >= 6 else "00"
    mon = date_str[2:4] if len(date_str) >= 6 else "00"
    yy = date_str[4:6] if len(date_str) >= 6 else "00"

    speed_kmh = speed_knots * 1.852

    return {
        "type": "$GPRMC - Minimum Recommande",
        "latitude": f"{lat_dec:.6f}°",
        "longitude": f"{lon_dec:.6f}°",
        "vitesse": f"{speed_knots:.1f} noeuds ({speed_kmh:.1f} km/h)",
        "cap": f"{course:.1f}°",
        "temps_utc": f"{hh}:{mm}:{ss}",
        "date": f"{dd}/{mon}/20{yy}",
    }

def decode_gsa(fields):
    mode = fields[1]
    fix_type = int(fields[2]) if fields[2] else 0

    mode_desc = {
        "M": "Manuel",
        "A": "Automatique",
    }
    fix_desc = {
        1: "Fix non disponible",
        2: "Fix 2D",
        3: "Fix 3D",
    }

    sat_ids = [f for f in fields[3:15] if f]
    pdop = float(fields[15]) if len(fields) > 15 and fields[15] else 0.0
    hdop = float(fields[16]) if len(fields) > 16 and fields[16] else 0.0
    vdop = float(fields[17]) if len(fields) > 17 and fields[17] else 0.0

    return {
        "type": "$GPGSA - Precision (DOP)",
        "mode": mode_desc.get(mode, mode),
        "type_fix": fix_desc.get(fix_type, f"Inconnu ({fix_type})"),
        "satellites_utilises": len(sat_ids),
        "PDOP": f"{pdop:.1f}",
        "HDOP": f"{hdop:.1f}",
        "VDOP": f"{vdop:.1f}",
        "qualite_dop": "Excellent" if pdop < 2 else "Bon" if pdop < 4 else "Moyen" if pdop < 8 else "Mauvais",
    }

def decode_gsv(fields):
    total_msgs = int(fields[1]) if fields[1] else 0
    msg_num = int(fields[2]) if fields[2] else 0
    total_sats = int(fields[3]) if fields[3] else 0

    sats = []
    for i in range(4, len(fields) - 1, 4):
        if i + 3 < len(fields):
            prn = fields[i]
            elev = fields[i + 1]
            azim = fields[i + 2]
            snr = fields[i + 3]
            sats.append({
                "prn": prn,
                "elevation": f"{elev}°" if elev else "N/A",
                "azimuth": f"{azim}°" if azim else "N/A",
                "snr_db": f"{snr} dB" if snr else "N/A",
            })

    return {
        "type": f"$GPGSV - Satellites en vue (message {msg_num}/{total_msgs})",
        "total_satellites": total_sats,
        "satellites": sats,
    }

def decode_gga(fields):
    lat = fields[2]
    lat_dir = fields[3]
    lon = fields[4]
    lon_dir = fields[5]
    quality = int(fields[6]) if fields[6] else -1
    nsat = int(fields[7]) if fields[7] else 0
    altitude = float(fields[9]) if fields[9] else 0.0

    lat_dec = float(lat[:2]) + float(lat[2:]) / 60.0
    if lat_dir == 'S':
        lat_dec = -lat_dec
    lon_dec = float(lon[:3]) + float(lon[3:]) / 60.0
    if lon_dir == 'W':
        lon_dec = -lon_dec

    quality_desc = {
        0: "Fix non disponible",
        1: "Fix GPS standard",
        2: "Fix DGPS",
        3: "Fix PPS",
        4: "RTK Fix",
        5: "RTK Float",
        6: "Estimation (dead reckoning)",
        7: "Mode manuel",
        8: "Mode simulation",
    }

    return {
        "type": "$GPGGA - Donnees de position",
        "latitude": f"{lat_dec:.6f}°",
        "longitude": f"{lon_dec:.6f}°",
        "qualite": quality_desc.get(quality, f"Inconnu ({quality})"),
        "nb_satellites": nsat,
        "altitude": f"{altitude:.1f} m",
    }

def decode_vtg(fields):
    track_true = float(fields[1]) if fields[1] else 0.0
    track_mag = float(fields[3]) if fields[3] else 0.0
    speed_knots = float(fields[5]) if fields[5] else 0.0
    speed_kmh = float(fields[7]) if fields[7] else 0.0

    return {
        "type": "$GPVTG - Cap et vitesse",
        "cap_vrai": f"{track_true:.1f}°",
        "cap_magnetique": f"{track_mag:.1f}°",
        "vitesse_noeuds": f"{speed_knots:.1f} noeuds",
        "vitesse_kmh": f"{speed_kmh:.1f} km/h",
    }

HANDLERS = {
    "GGA": decode_gga,
    "GLL": lambda f: {"type": "$GPGLL - Position geographique", "fields": f},
    "GSA": decode_gsa,
    "GSV": decode_gsv,
    "RMC": decode_rmc,
    "VTG": decode_vtg,
}

def decode_nmea(sentence):
    sentence = sentence.strip()
    if not sentence or not sentence.startswith("$"):
        return None

    if not nmea_checksum(sentence):
        return {"error": "Checksum invalide"}

    parts = sentence.split('*')
    body = parts[0].lstrip('$')
    fields = body.split(',')

    talker_id = fields[0][:2]
    sentence_type = fields[0][2:]
    full_type = f"${talker_id}{sentence_type}"

    result = {
        "sentence_raw": sentence,
        "talker_id": talker_id,
        "type_code": sentence_type,
        "description": NMEA_SENTENCES.get(full_type, "Type inconnu"),
        "checksum_valide": True,
    }

    handler = HANDLERS.get(sentence_type)
    if handler:
        try:
            decoded = handler(fields)
            result.update(decoded)
        except Exception as e:
            result["error_decodage"] = str(e)
    else:
        result["champs_bruts"] = fields[1:]

    return result

def analyse_fichier_nMEA(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    results = []
    for line in lines:
        decoded = decode_nmea(line)
        if decoded:
            results.append(decoded)

    return results

def afficher_trame(decoded):
    if "error" in decoded:
        print(f"[ERREUR] {decoded['error']}")
        return
    if "error_decodage" in decoded:
        print(f"[ERREUR DECODAGE] {decoded['error_decodage']}")
        return

    print(f"[{decoded.get('type_code', '?')}] {decoded.get('description', '?')}")
    for key, val in decoded.items():
        if key in ('sentence_raw', 'talker_id', 'type_code', 'description', 'checksum_valide', 'satellites'):
            continue
        if isinstance(val, list):
            print(f"  {key}: ")
            for item in val:
                print(f"    - {item}")
        else:
            print(f"  {key}: {val}")
    print()

def generer_trames_simulees():
    import datetime
    now = datetime.datetime.now(datetime.UTC)
    hhmmss = now.strftime("%H%M%S")
    ddmmyy = now.strftime("%d%m%y")

    templates = [
        "$GPGGA,{},4851.3960,N,00221.1320,E,1,08,1.2,35.0,M,49.0,M,,",
        "$GPGSA,A,3,02,05,07,10,13,17,20,24,,,,,",
        "$GPGSV,3,1,12,02,78,045,45,05,62,123,42,07,45,210,38,10,30,045,39",
        "$GPGSV,3,2,12,13,55,300,41,17,40,080,36,20,35,150,40,24,20,200,35",
        "$GPGSV,3,3,12,25,15,090,30,28,08,300,28,30,05,180,25,31,02,045,20",
        "$GPRMC,{},A,4851.3960,N,00221.1320,E,025.4,180.0,{},004.2,W",
        "$GPVTG,180.0,T,175.8,M,025.4,N,047.0,K",
    ]

    sentences = []
    for t in templates:
        filled = t.format(hhmmss, ddmmyy) if "{}" in t else t
        body = filled.lstrip('$')
        calc = 0
        for c in body:
            calc ^= ord(c)
        sentences.append(f"{filled}*{calc:02X}")

    return sentences

def main():
    if len(sys.argv) > 1:
        results = analyse_fichier_nMEA(sys.argv[1])
        print(f"=== Analyse du fichier: {sys.argv[1]} ===")
        print(f"Nombre de trames decodees: {len(results)}")
        for r in results:
            afficher_trame(r)
    else:
        print("=== DECODEUR NMEA - Mode demonstration ===")
        print()

        sentences = generer_trames_simulees()
        for s in sentences:
            print(f"Trame brute: {s}")
            decoded = decode_nmea(s)
            if decoded:
                afficher_trame(decoded)
            print()

        print("=== Analyse des checksums ===")
        test_sentences = [
            "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47",
            "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*48",
            "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A",
        ]
        for s in test_sentences:
            valid = nmea_checksum(s)
            print(f"  {s[:50] if len(s) > 50 else s}... -> Checksum: {'VALIDE' if valid else 'INVALIDE'}")

        print()
        print("=== Structures des trames NMEA ===")
        print("""
$GPGGA:
  $GPGGA,hhmmss.ss,ddmm.mmmm,N,dddmm.mmmm,E,q,ns,hdop,alt,M,geoid,M,age,ref*CS
  hhmmss.ss  Heure UTC
  ddmm.mmmm  Latitude (degrés/minutes)
  N/S        Hémisphère
  dddmm.mmmm Longitude (degrés/minutes)
  E/O        Hémisphère
  q          Qualité (0=invalide, 1=GPS, 2=DGPS)
  ns         Nombre de sat. utilisés
  hdop       Précision horizontale
  alt        Altitude (m)
  geoid      Hauteur du géoïde (m)

$GPRMC:
  $GPRMC,hhmmss.ss,A,ddmm.mmmm,N,dddmm.mmmm,E,spd,cog,ddmmyy,mv,mvE*CS
  A          Statut (A=actif, V=invalide)
  spd        Vitesse (noeuds)
  cog        Cap (degrés)
  ddmmyy     Date
  mv/mvE     Déclinaison magnétique

$GPGSA:
  $GPGSA,mode,fix,prn1...prn12,pdop,hdop,vdop*CS
  mode       M=manuel, A=automatique
  fix        1=pas de fix, 2=2D, 3=3D
  prn1..12   PRN des satellites utilisés
  pdop       Précision 3D
  hdop       Précision horizontale
  vdop       Précision verticale

$GPGSV:
  $GPGSV,msg,total,nsat,prn,elev,azim,snr,...,*CS
  msg        N° de message
  total      Total des messages
  nsat       Total satellites en vue
  prn/elev/azim/snr par satellite
        """)

if __name__ == "__main__":
    main()
