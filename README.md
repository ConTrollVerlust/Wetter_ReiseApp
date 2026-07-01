☀️ Reise-Radar
Eine interaktive Reise- und Wetter-App (Python & Streamlit) mit 14-Tage-Vorhersage, Länderinfos und Bildergalerien.

✨ Features
Architektur: Saubere Schichtentrennung (Frontend in gui/, Backend in core/).

Datenbank: Lokale SQLite-Datenbank (reiseapp.db) für Favoriten.

APIs: Open-Meteo, REST Countries & Pixabay (inkl. Fallback-System).

🚀 Installation & Start
Voraussetzung: Python 3.9+

1. Code herunterladen

ZIP-Datei entpacken und in den Ordner navigieren

2. Abhängigkeiten installieren

pip install -r requirements.txt

3. API-Key (Optional)
Aus Datenschutzgründen sind keine Keys im Code. Die App läuft auch ohne Key fehlerfrei (es laden dann Platzhalter-Bilder).
Um dynamische Bilder zu testen (benötigt Pixabay API-Key), gibt es zwei Optionen:

Im UI (Empfohlen): App starten und den Key bequem in das Eingabefeld der Seitenleiste kopieren.

Per Datei: Eine .env Datei im Hauptverzeichnis anlegen mit: PIXABAY_API_KEY=dein_api_key_hier

4. App starten

streamlit run gui/app.py