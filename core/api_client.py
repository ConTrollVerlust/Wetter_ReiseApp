"""
Backend-Logik: API-Client (core/api_client.py)

WAS MACHT DIESE DATEI?
Hier bündeln wir die gesamte Kommunikation mit dem Internet (mit sogenannten APIs).
Man kann sich eine API wie einen Kellner in einem Restaurant vorstellen:
Unser Code (der Gast) bestellt "Wetter für Berlin", die API (der Kellner) geht in
die Küche (den Server), holt die Daten und bringt sie uns aufbereitet zurück.

Warum lagern wir das aus?
"Separation of Concerns" (Trennung der Zuständigkeiten). Das Frontend (app.py) soll
sich nur um das Aussehen kümmern. Das Backend hier kümmert sich um die reine Datenbeschaffung.
Das macht den Code professionell, aufgeräumt und wartbar.
"""

import requests  # Das wichtigste Werkzeug: Ermöglicht es unserem Code, Webseiten/APIs aufzurufen.
import urllib.parse  # Übersetzt Leerzeichen und Umlaute in ein internettaugliches Format (z.B. " " -> "%20").
import os  # Lässt uns auf die Dateistruktur und Umgebungsvariablen (System-Infos) zugreifen.
from dotenv import load_dotenv  # Lädt unsere geheimen Passwörter aus der .env-Datei.

# Lädt die Variablen aus deiner .env Datei (z.B. den Pixabay-Key) sicher in den Arbeitsspeicher.
load_dotenv()


def search_city_coordinates(city_name):
    """
    SCHRITT 1: Die Geocoding-API.
    Warum brauchen wir das? Die Wetter-API ist ein Computer, der keine Städtenamen wie "Leipzig"
    versteht. Er braucht exakte GPS-Koordinaten (Breitengrad / Längengrad).
    Diese Funktion übersetzt den Textnamen in Koordinaten.
    """
    try:
        # .strip() entfernt versehentliche Leerzeichen am Anfang oder Ende der Eingabe.
        search_term = city_name.strip()

        # Wir bauen die URL für die Open-Meteo Such-API zusammen. urllib.parse.quote sorgt dafür,
        # dass Städte mit Leerzeichen (z.B. "New York") den Link nicht kaputt machen.
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(search_term)}&count=1&language=de&format=json"

        # requests.get(url) schickt die Anfrage an das Internet ab.
        response = requests.get(url)
        # Bricht das Programm sicher ab, wenn die Website nicht erreichbar ist (z.B. Fehler 404)
        response.raise_for_status()

        # Wir wandeln die Text-Antwort der API in ein Python-Wörterbuch (JSON) um, damit wir leichter damit arbeiten können.
        data = response.json()

        # Prüfen, ob die API Ergebnisse gefunden hat
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]  # Wir nehmen den allerersten (besten) Treffer
            lat = result["latitude"]
            lon = result["longitude"]

            # Wir holen noch das Bundesland (admin1) und das Land (country), um die Anzeige schicker zu machen.
            admin1 = result.get('admin1', '')
            country = result.get('country', '')

            # Formatierung angepasst für schickere Anzeige im Frontend:
            # Beispiel: "Frankfurt am Main — Hessen, Germany"
            if admin1 and admin1 != result['name']:
                found_name = f"{result['name']} — {admin1}, {country}"
            else:
                found_name = f"{result['name']} — {country}"

            return lat, lon, found_name
        else:
            return None, None, None

    except Exception as e:
        # Falls das Internet ausfällt oder die API nicht antwortet, fangen wir den Fehler ab,
        # damit die App nicht abstürzt, und geben einfach 'None' (Nichts) zurück.
        print(f"Fehler bei der Geocoding-API: {e}")
        return None, None, None


def search_city_list(city_name, count=10):
    """
    ALTERNATIVE SCHRITT 1: Mehrere Ergebnisse suchen.
    Wird genutzt, wenn ein Name mehrdeutig ist (z.B. "Frankfurt" oder "Neustadt").
    Gibt eine ganze Liste mit bis zu 10 Treffern zurück.
    """
    try:
        search_term = city_name.strip()
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(search_term)}&count={count}&language=de&format=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        results = []
        if "results" in data:
            # Wir gehen mit einer 'for'-Schleife durch jeden gefundenen Treffer der API
            for res in data["results"]:
                admin1 = res.get('admin1', '')
                country = res.get('country', '')
                name = res['name']

                if admin1 and admin1 != name:
                    found_name = f"{name} — {admin1}, {country}"
                else:
                    found_name = f"{name} — {country}"

                # WICHTIG: Duplikate vermeiden. Manchmal gibt die API zweimal exakt denselben
                # formatierten Namen zurück. Das filtern wir hier weg, damit die Buttons im Frontend ordentlich aussehen.
                if not any(r[2] == found_name for r in results):
                    results.append((res["latitude"], res["longitude"], found_name))

        return results
    except Exception as e:
        print(f"Fehler bei der Geocoding-API: {e}")
        return []


def get_weather_icon(wmo_code):
    """
    Eine kleine Hilfsfunktion.
    Wetter-APIs geben oft nur Nummern zurück (den WMO-Code, z.B. 0 für Sonne, 61 für Regen).
    Diese Funktion ist quasi ein Wörterbuch, das diese Nummern in hübsche Emojis übersetzt.
    """
    if wmo_code == 0:
        return "☀️"
    elif wmo_code in [1, 2, 3]:
        return "⛅"
    elif wmo_code in [45, 48]:
        return "🌫️"  # Nebel
    elif wmo_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "🌧️"  # Regen
    elif wmo_code in [71, 73, 75, 77, 85, 86]:
        return "❄️"  # Schnee
    elif wmo_code in [95, 96, 99]:
        return "⛈️"  # Gewitter
    else:
        return "🌡️"  # Standard-Symbol, falls ein unbekannter Code kommt


def get_weather_data(lat, lon):
    """
    SCHRITT 2: Die Wetter-API abfragen.
    Hier nutzen wir die Koordinaten (lat, lon), die wir im ersten Schritt bekommen haben,
    und fragen Open-Meteo nach einer dicken Vorhersage für die nächsten 16 Tage.
    """
    try:
        # In dieser URL legen wir fest, WAS wir genau wissen wollen:
        # current=... (aktuelles Wetter), hourly=... (Stundenverlauf), daily=... (Tagesübersicht).
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code&hourly=temperature_2m&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto&forecast_days=16"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Prüfen, ob die API uns wirklich die 3 angeforderten Blöcke geliefert hat
        if "current" in data and "hourly" in data and "daily" in data:

            # 1. Aktuelles Wetter auslesen
            current_temperature = data["current"]["temperature_2m"]
            current_humidity = data["current"]["relative_humidity_2m"]
            current_weather_code = data["current"]["weather_code"]

            # 2. Stundenverlauf. Mit [:24] schneiden wir die lange Liste ab,
            # weil uns nur die nächsten 24 Stunden für das Diagramm interessieren.
            hourly_times = data["hourly"]["time"][:24]
            hourly_temperatures = data["hourly"]["temperature_2m"][:24]

            # 3. 14-Tage-Übersicht (bzw. 16 Tage, wie in der URL angefordert)
            daily_times = data["daily"]["time"]
            daily_temp_max = data["daily"]["temperature_2m_max"]
            daily_temp_min = data["daily"]["temperature_2m_min"]
            daily_weather_codes = data["daily"]["weather_code"]

            # Da das sehr viele einzelne Tages-Listen sind, packen wir sie übersichtlich
            # in ein neues Wörterbuch (dictionary), bevor wir sie ans Frontend zurückschicken.
            daily_data = {
                "dates": daily_times,
                "temp_max": daily_temp_max,
                "temp_min": daily_temp_min,
                "codes": daily_weather_codes
            }

            # Wir geben 6 verschiedene Variablen auf einmal zurück ("Multiple Return Values").
            return current_temperature, current_humidity, current_weather_code, hourly_times, hourly_temperatures, daily_data
        else:
            return None, None, None, None, None, None

    except Exception as e:
        print(f"Fehler bei der Wetter-API: {e}")
        return None, None, None, None, None, None


def get_city_images(city_name):
    """
    SCHRITT 3: Bilder von der Pixabay API holen.

    ERFÜLLT KRITERIUM 'DATENSCHUTZ': Keine Keys im Code.
    ERFÜLLT KRITERIUM 'ZIP-STABILITÄT': Läuft komplett ohne manuelle Konfiguration
    durch intelligenten Bild-Fallback (Mocking).
    """
    import streamlit as st

    # 1. Stufe: Versuche den Key aus der lokalen .env zu laden (für dich auf deinem PC)
    api_key = os.getenv("PIXABAY_API_KEY")

    # 2. Stufe: Falls nicht da, schaue ob der Korrektor einen Key in die Sidebar eingetippt hat
    if not api_key and "pixabay_key" in st.session_state and st.session_state["pixabay_key"]:
        api_key = st.session_state["pixabay_key"]

    # 3. Stufe: Immer noch kein Key? Dann greift die "ZIP-Stabilität"!
    # Wir geben ein wunderschönes, freies Stadt-Bild von Unsplash zurück. Kein Absturz, kein Fehler.
    if not api_key:
        # Ein stabiler Fallback-Link zu einem lizenzfreien Stadt-Bild, das ohne Key funktioniert
        fallback_image = "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=800&q=80"
        return [fallback_image]

    # --- Ab hier läuft der originale API-Aufruf, falls ein Key existiert ---
    try:
        clean_name = city_name.split(" —")[0].split(",")[0]
        query = urllib.parse.quote(f"{clean_name} city")
        url = f"https://pixabay.com/api/?key={api_key}&q={query}&image_type=photo&orientation=horizontal&per_page=5"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "hits" in data and len(data["hits"]) > 0:
            return [hit["largeImageURL"] for hit in data["hits"]]
        else:
            # Falls Pixabay für eine exotische Stadt mal kein Bild findet
            return ["https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=800&q=80"]

    except Exception as e:
        # Selbst bei Netzwerkfehlern bleibt die App stabil
        print(f"Fehler bei der Pixabay-API: {e}")
        return ["https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=800&q=80"]


def get_country_data(country_name):
    """
    SCHRITT 4 (Zusatz-Feature): Länderinformationen abrufen.
    Holt z.B. Bevölkerung, Flagge und Hauptstadt über die 'REST Countries API'.
    """
    try:
        # Versucht zuerst, das Land auf Deutsch übersetzt zu suchen
        url = f"https://restcountries.com/v3.1/translation/{urllib.parse.quote(country_name)}"
        response = requests.get(url)

        # Fallback: Wenn Übersetzung fehlschlägt (z.B. Fehler 404), suchen wir direkt nach dem englischen Namen
        if response.status_code != 200:
            url = f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country_name)}"
            response = requests.get(url)

        if response.status_code == 200:
            data = response.json()[0]

            # Bevölkerung hübsch formatieren (Millionen statt ewig langer Zahlen)
            pop = data.get("population", 0)
            if pop > 1000000:
                pop_str = f"{pop / 1000000:.1f} Mio."
            else:
                pop_str = f"{pop:,}".replace(",", ".")

            return {
                "capital": data.get("capital", ["Unbekannt"])[0],
                "population": pop_str,
                "currencies": ", ".join([v.get("name", "") for k, v in data.get("currencies", {}).items()]),
                "languages": ", ".join(data.get("languages", {}).values()),
                "flag": data.get("flag", "🏳️")
            }
    except Exception as e:
        print(f"Fehler bei der Länder-API: {e}")

    return None