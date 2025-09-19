# 🚀 Dynamic Messe Stand V4
**Bertrandt Interactive Display System**

## 📋 Übersicht
✅ Behobene Probleme:

Bilderspeicherung im Creator:

Bilder werden jetzt korrekt in data/images/ gespeichert
PIL-Images werden als Referenz gespeichert für bessere Performance
Automatische Pfadverwaltung und Backup-System


Vollbild-Modus für Demo:

Neue Vollbild-Präsentationsansicht mit Tastatursteuerung
Synchronisation zwischen normalem und Vollbild-Modus
Touch-freundliche Bedienung


Symbol- und Emoji-Panel:

Erweiterte Toolbox mit Satzzeichen: . , ; : ! ? - – — ...
Mathematische Symbole: ± × ÷ = ≠ ≤ ≥ ∞ ∑ √
Emoji-Unterstützung: 😀 😊 👍 ❤️ 🎉 🚗 🏠 💡 📱 ⭐
Einfache Einfügung in aktive Textfelder


Tablet-Fernsteuerung:

HTTP-Server auf Port 8080
Responsive Web-Interface für Tablets
Touch-Gesten (Wischen) für Navigation
Echtzeit-Synchronisation
QR-Code-freundliche URL



📱 Tablet-Interface Features:

Touch-Navigation: Wischen nach links/rechts für Folien-Navigation
Tastatursteuerung: Pfeiltasten, Leertaste, ESC, F5, Zahlen 1-9
Auto-Refresh: Automatische Synchronisation alle 3 Sekunden
Responsive Design: Optimiert für verschiedene Bildschirmgrößen
Bilderunterstützung: Anzeige von Creator-Bildern im Tablet-Interface

## 🏗️ Projektstruktur
```
├── main.py                 # Hauptanwendung
├── assets/                 # Bertrandt Logos und Medien
├── content/                # Präsentationsinhalte (Seiten 1-10)
├── core/                   # Kern-Module
│   ├── config.py          # Zentrale Konfiguration
│   ├── logger.py          # Logging-System
│   └── theme.py           # Bertrandt Dark Theme
├── models/                 # Datenmodelle
│   ├── content.py         # Content-Management
│   ├── hardware.py        # Hardware-Verbindungen
│   └── presentation.py    # Präsentations-Logic
├── services/               # Business Logic
│   └── demo.py            # Demo-Services
├── ui/                     # Benutzeroberfläche
│   ├── main_window.py     # Hauptfenster
│   ├── components/        # UI-Komponenten
│   └── tabs/              # Tab-Module
├── presentations/          # Beispiel-Präsentationen
├── docs/                   # Dokumentation
└── logs/                   # Log-Dateien
```

## 🚀 Schnellstart
```bash
# Anwendung starten
python main.py

# Mit Hardware-Verbindungen
python main.py --esp32-port /dev/ttyUSB0

# Ohne Hardware (Demo-Modus)
python main.py --no-hardware

# Debug-Modus
python main.py --debug
```

## 🎨 Features
- **Bertrandt Corporate Design** - Liquid Glass Dark Theme
- **Hardware-Integration** - ESP32 & Arduino GIGA Support
- **Präsentations-Creator** - Drag & Drop Editor
- **Demo-System** - Automatische Präsentationen
- **Responsive Design** - Optimiert für 24" Displays

## 📚 Dokumentation
Siehe `docs/` Verzeichnis für detaillierte Dokumentation:
- Code-Verständnis und Architektur
- ToolBox Design-Konzepte
- Verbesserungsvorschläge

