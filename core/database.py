"""
Backend-Logik: Datenbank-Modul (core/database.py)

WAS MACHT DIESE DATEI?
Hier verwalten wir unsere "Gedächtnis-Stütze". Damit die App sich Favoriten merken
kann, speichern wir sie lokal auf deinem Computer in einer kleinen Datei namens
'reiseapp.db' (eine SQLite-Datenbank).

Warum SQLite?
Es ist super leichtgewichtig. Man braucht keinen riesigen Server, sondern nur
eine einfache Datei. Das ist ideal für kleine Apps wie unsere.
"""

import sqlite3
import os

# Pfad zu unserer Datenbank-Datei.
# Wir speichern sie im Ordner 'daten', damit es im Projektordner sauber bleibt.
DB_PATH = "daten/reiseapp.db"

# Sicherstellen, dass der Ordner 'daten' existiert. Falls nicht -> erstellen.
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Wir verbinden uns mit der Datenbank-Datei.
# 'check_same_thread=False' ist wichtig für Streamlit, damit sich die App
# nicht über mehrere Fenster hinweg in die Quere kommt.
connection = sqlite3.connect(DB_PATH, check_same_thread=False)

def create_tables_if_needed():
    """
    Diese Funktion läuft einmal beim Starten.
    Sie prüft, ob die Tabelle 'locations' schon existiert. Falls nicht, erstellt sie sie.
    Das ist unser Grundgerüst, in dem Namen, GPS-Koordinaten und Favoriten-Status landen.
    """
    cursor = connection.cursor()

    # SQL-Befehl: Erstelle Tabelle 'locations', falls sie noch fehlt.
    # id: Eindeutige Nummer für jeden Eintrag.
    # city_name: Der Name der Stadt (darf nur einmal vorkommen: UNIQUE).
    # lat/lon: Koordinaten, damit wir nicht immer die API fragen müssen.
    # is_favorite: 1 wenn Favorit, 0 wenn nur Verlauf.
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS locations
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       city_name TEXT UNIQUE,
                       lat REAL,
                       lon REAL,
                       is_favorite INTEGER DEFAULT 0
                   )
                   ''')
    connection.commit() # Änderungen speichern

def add_to_history(city_name, lat, lon):
    """
    Speichert eine Stadt in den Suchverlauf.
    'INSERT OR IGNORE' ist ein genialer Trick: Wenn die Stadt schon in der Tabelle steht,
    passiert einfach nichts. So vermeiden wir Fehler, wenn man dieselbe Stadt mehrmals sucht.
    """
    cursor = connection.cursor()
    cursor.execute('''
                   INSERT OR IGNORE INTO locations (city_name, lat, lon, is_favorite)
                   VALUES (?,?,?,0)
                   ''', (city_name, lat, lon))
    connection.commit()

def set_favorite(city_name, status):
    """
    Markiert eine Stadt als Favorit (1) oder entfernt den Status wieder (0).
    Hier suchen wir die Zeile mit dem 'city_name' und ändern nur die Spalte 'is_favorite'.
    """
    cursor = connection.cursor()
    cursor.execute("UPDATE locations SET is_favorite = ? WHERE city_name = ?", (status, city_name))
    connection.commit()

def delete_location(city_name):
    """
    Löscht eine Stadt komplett aus der Datenbank.
    """
    cursor = connection.cursor()
    cursor.execute("DELETE FROM locations WHERE city_name = ?", (city_name,))
    connection.commit()

def get_favorites():
    """
    Holt alle Städte aus der Datenbank, die den Status 'is_favorite = 1' haben.
    Das ist das, was wir später in der Sidebar als Favoriten-Liste anzeigen.
    """
    cursor = connection.cursor()

    cursor.execute("SELECT city_name, lat, lon FROM locations WHERE is_favorite = 1")
    # gibt alle gefundenen Zeilen als Liste zurück
    return cursor.fetchall()

# --- Initialisierung ---
# Sobald diese Datei geladen wird, stellen wir sicher, dass die Datenbank-Tabelle bereit ist.
create_tables_if_needed()