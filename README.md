☀️ Reise-Radar

Eine interaktive Reise- und Wetter-App, gebaut mit Python und Streamlit.
Dieses Projekt bündelt Wetterdaten, eine 14-Tage-Vorhersage, dynamische Länderinformationen und Bildergalerien für eine optimale Reiseplanung.

🚀 Lokale Installation (Für Prüfer/Dozenten)

Voraussetzung: Python 3.9 oder neuer muss installiert sein.

Repository klonen:

git clone <dein-github-link>
cd <dein-ordnername>


Abhängigkeiten installieren:
Installiere alle benötigten Bibliotheken (Streamlit, Pandas, etc.):

pip install -r requirements.txt


Umgebungsvariablen setzen:
Erstelle eine Datei namens .env im Hauptverzeichnis und füge deinen Pixabay API-Key ein:

PIXABAY_API_KEY=dein_api_key_hier


App starten:

streamlit run gui/app.py
