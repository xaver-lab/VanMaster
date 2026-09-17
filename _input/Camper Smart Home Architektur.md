# **System-Architektur & Tech-Stack Dokumentation: Camper Smart Home**

**Projektziel:** Eigenes, modulares, KI-entwickeltes Smart-Home-, Steuerungs- und Überwachungssystem für einen Camper.

**Entwicklungsansatz:** 100 % KI-generierter Code (Claude Code auf dem Laptop), entkoppeltes Multi-Node-System, Edge-to-Laptop Daten-Sync, autonomes Visual-Testing, weltweit erreichbar.

# **1\. Hardware & Netzwerktopologie**

* **Zentrale (Master-Node):** Einer der drei folgenden Chips, abhängig vom finalen Energie-Budget:  
  * **Option 1: Raspberry Pi Zero 2 W** (Maximales Stromsparen, \~0,5W, Micro-SD) \- Fokus auf minimalen Energieverbrauch für kleine Batteriekapazitäten.  
  * **Option 2: Odroid M1S** (Der Sweet-Spot, \~1,5W, eMMC/NVMe) \- Bester Kompromiss aus Effizienz und RAM-Reserven für Docker.  
  * **Option 3: Raspberry Pi 4 / 5** (Performance, \~2,5W \- 4W) \- Volle Kompatibilität und Power, wenn das Strombudget unkritisch ist.  
  * **Aufgaben:** Backend (FastAPI), Kurzzeit-Datenbank, MQTT-Broker, Logik-Engine, Web-Dashboard-Hosting.  
* **Sensorik & Aktorik (Satelliten):** ESP32 v6 Mikrocontroller  
  * **Aufgaben:** Auslesen von Sensoren (Temperatur BME280/SHT31, Tank-Füllstände, MPU-6050 Neigung, Reed-Kontakte, PIR-Bewegung) & Schalten von Relais (Licht, Pumpe, Heizung).  
* **Remote-Zugriff & Connectivity:**  
  * **Tailscale (Mesh-VPN):** Verschlüsselte P2P-Verbindung zwischen Master, Laptop und Smartphone ohne offene Ports/Portfreigaben.  
  * **Camper-WLAN Router:** Bietet ein lokales Subnetz (192.168.8.x) für alle Geräte. *(Single Point of Failure beachten\!)*  
  * *(Optional)* Cloudflare Tunnel: Für den Zugriff per Handy-Browser ohne VPN-App.

# **2\. Backend & Daten-Architektur (Master-Node)**

* **Core-Framework:** Python 3.12+ mit FastAPI und Pydantic v2 (strikte Typisierung, AsyncIO).  
* **Echtzeit-Kommunikation:**  
  * **MQTT (Mosquitto):** Nachrichtenbus für Telemetriedaten (`camper/v1/{node_id}/{sensor}/state`).  
  * **WebSockets:** Für Latenz-freie Live-Updates im Frontend-Dashboard.  
* **Datenhaltung (Edge-to-Laptop Sync):**  
  * **Kurzzeitspeicher (Camper-Node):** SQLite (mit WAL) oder In-Memory (Redis). Nutzt einen Ringpuffer (TTL), um Daten nach z.B. 24h zu löschen. Schont SD-Karten und spart RAM.  
  * **Langzeitspeicher & Analytics (Entwicklungs-Laptop):** Nutzt DuckDB oder TimescaleDB. Synchronisiert sich automatisch via FastAPI-Endpunkt, sobald der Laptop im Netz ist.  
  * **JSON-Structured-Logging:** Einziges Log-Format für einfaches Parsing.  
* **Software-Architektur:** Dynamic Driver System (Plugin-Architektur). Sensoren erben von einer abstrakten `Base-Driver`\-Klasse und registrieren sich automatisch.

# **3\. Firmware (ESP32 Nodes)**

* **Entwicklungs-Framework:** PlatformIO (C++).  
* **Update-Mechanismus:** OTA (Over-The-Air) Updates via Wi-Fi.  
* **Sicherheit & Notlauf (Offline-Fähigkeit):**  
  * Unabhängige Notlauf-Logik (z. B. Pumpe stoppt, wenn der Pi-Master ausfällt).  
  * Automatische WLAN- & MQTT-Reconnection-Loops.  
  * Hardware-Watchdogs (WDT) für Neustart bei System-Freezes.  
  * Physische Fallback-Schalter per Interrupt für kritische Systeme (Licht, Pumpe).

# **4\. Hardware-Schnittstellen für zukunftsfähigen Ausbau**

* **I²C / 1-Wire:** Für Standard-Sensoren.  
* **RS485 Transceiver (MAX485 / Modbus RTU):** Für Standheizung, Wechselrichter.  
* **CAN-Bus Transceiver (MCP2515 / TJA1051):** Fahrzeug-CAN, Victron VE.CAN, RV-C.  
* **VE.Direct (UART-USB):** Victron SmartShunts / Solarregler.

# **5\. Frontend & Mobile UI (PWA)**

* **Basis:** Responsive Web-Interface mit semantischen IDs/Data-Attributen für KI-Testing (z.B. `data-testid`).  
* **PWA-Feature:** Als App-Icon auf dem Smartphone speicherbar.  
* **Sicherheits-UI & Watchdogs:**  
  * Hauptschalter (12V): "Slide to Toggle" zur Vermeidung versehentlichen Schaltens.  
  * Standheizung: Backend-Watchdog (Batterie-Prüfung) und Auto-Off-Timer.

# **6\. KI-Entwicklungs-Workflow (Claude Code)**

* **Entwicklung:** Claude Code läuft auf dem Laptop und greift via SSH zu. LLM-freundlich durch isolierte Plugin-Struktur (Driver).  
* **Visual-Testing Loop:**  
  * Playwright-Skript öffnet UI in verschiedenen Viewports.  
  * Erzeugt Screenshots und fängt Fehler ab.  
  * Claude liest Bilder/Logs autonom und fixt CSS/JS direkt im Code.

# **🎯 Überprüfungs-Auftrag an Claude (Prompt-Vorlage)**

"Hallo Claude\! Ich habe hier die finale System-Architektur für mein Camper Smart-Home-Projekt zusammengestellt. Das System nutzt eine Edge-to-Laptop Sync-Strategie, um den Master-Node zu entlasten. Bitte analysiere das Konzept auf folgende Punkte:

* **Hardware & Stromverbrauch:** Wir haben drei Master-Nodes zur Auswahl. Welcher passt am besten zu einem Setup, das Docker nutzt, aber wenig Strom verbrauchen soll?  
* **Sicherheit & Autarkie:** Sind die ESP32-Notläufe und physischen Fallback-Schalter ausreichend, wenn der Camper-Router oder Master-Node ausfällt?  
* **Daten-Konzept:** Ist der SQLite-Ringpuffer (Edge) mit automatischem DuckDB-Sync (Laptop) robust genug implementierbar?  
* **Verbesserungsvorschläge:** Welche konkreten Schritte würdest du für die ersten Code-Zeilen empfehlen?"

