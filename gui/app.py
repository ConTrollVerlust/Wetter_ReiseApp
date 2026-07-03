"""
Hauptdatei des Frontends (gui/app.py)
Diese Datei ist das "Gesicht" unserer App. Sie wird von Streamlit ausgeführt und steuert
die Benutzeroberfläche, nimmt Suchanfragen entgegen und stellt die Daten hübsch dar.
Wichtiges Konzept für Streamlit: Bei jedem Klick auf einen Button wird dieses Skript
von oben nach unten komplett neu ausgeführt!
"""

import sys
# Fügt das Hauptverzeichnis zum Systempfad hinzu, damit Python unsere eigenen
# Ordner ('core' und 'gui') fehlerfrei findet.
sys.path.append(".")

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt

# --- UNSERE EIGENEN MODULE IMPORTIEREN ---
# Hier holen wir uns die "Gehirn"-Funktionen aus dem Backend (Ordner 'core').
from core.api_client import get_weather_data, search_city_coordinates, get_weather_icon, get_city_images, search_city_list
from core.database import add_to_history, set_favorite, delete_location, get_favorites
from gui.components import get_gallery_html
from core.themes import ThemePalette

# --- SESSION STATE (DER NOTIZBLOCK DER APP) ---
# Da Streamlit bei jedem Klick alles vergisst (die Seite lädt neu), nutzen wir
# st.session_state als eine Art Notizblock, der sich Dinge über Ladevorgänge hinweg merkt.
if 'history' not in st.session_state:
    st.session_state['history'] = []               # Merkt sich die letzten Suchanfragen
if 'current_search' not in st.session_state:
    st.session_state['current_search'] = None      # Die Stadt, deren Wetter gerade angezeigt wird
if 'direct_lat_lon' not in st.session_state:
    st.session_state['direct_lat_lon'] = None      # Speichert exakte Koordinaten, um doppelte API-Anfragen zu sparen
if 'search_results_list' not in st.session_state:
    st.session_state['search_results_list'] = None # Speichert die Trefferliste, wenn ein Name mehrdeutig ist (z.B. "Frankfurt")
if 'theme_name' not in st.session_state:
    st.session_state['theme_name'] = ThemePalette.SUMMER.label # Standard-Farbwelt


# --- CALLBACK FUNKTIONEN ---
# Callbacks (Funktionen, die mit 'cb_' beginnen) sind eine elegante Streamlit-Lösung.
# Sie sind direkt an Buttons gekoppelt (on_click=...) und werden ausgeführt,
# BEVOR Streamlit die Seite neu lädt. Das verhindert "Geister-Effekte" beim Löschen.

def cb_remove_history(past_item, past_name):
    """Löscht einen Eintrag aus dem Suchverlauf."""
    if past_item in st.session_state['history']:
        st.session_state['history'].remove(past_item)
    # Wenn wir die Stadt löschen, die wir gerade ansehen, leeren wir auch den Hauptbildschirm
    if st.session_state.get('current_search') == past_name:
        st.session_state['current_search'] = None
        st.session_state['direct_lat_lon'] = None

def cb_load_history(p_lat, p_lon, past_name):
    """Lädt eine Stadt aus dem Verlauf wieder in die Hauptansicht."""
    st.session_state['current_search'] = past_name
    st.session_state['direct_lat_lon'] = (p_lat, p_lon, past_name)
    st.session_state['search_results_list'] = None

def cb_fav_from_history(past_name, p_lat, p_lon, past_item):
    """Speichert eine Stadt aus dem Verlauf als Favorit ab."""
    add_to_history(past_name, p_lat, p_lon)
    set_favorite(past_name, 1)
    if past_item in st.session_state['history']:
        st.session_state['history'].remove(past_item)

def cb_remove_fav(city_name):
    """Löscht eine Stadt aus der Favoriten-Datenbank."""
    delete_location(city_name)
    if st.session_state.get('current_search') == city_name:
        st.session_state['current_search'] = None
        st.session_state['direct_lat_lon'] = None

def cb_load_fav(city_name, fav_lat, fav_lon):
    """Lädt eine Stadt aus den Favoriten in die Hauptansicht."""
    st.session_state['current_search'] = city_name
    st.session_state['direct_lat_lon'] = (fav_lat, fav_lon, city_name)
    st.session_state['search_results_list'] = None

def cb_add_current_fav(found_name, lat, lon):
    """Speichert die gerade angesehene Stadt als Favorit."""
    add_to_history(found_name, lat, lon)
    set_favorite(found_name, 1)
    # Bereinigt den Verlauf, damit die Stadt nicht doppelt auftaucht
    st.session_state['history'] = [h for h in st.session_state['history'] if h[0] != found_name]


# --- THEME UND DESIGN LADEN ---
# Aktuelles Theme als Enum-Objekt auslesen
current_theme = ThemePalette.from_label(st.session_state['theme_name'])

# --- CSS INJECTION FÜR LIVE-THEMING & STEALTH-MODUS ---
# Hier schleusen wir eigenes CSS (Design-Code) ein, um die Standard-Optik von Streamlit zu überschreiben.
st.markdown(f"""
<style>
    /* Hintergrundfarben für App und Seitenleiste anpassen */
    [data-testid="stAppViewContainer"] {{ background-color: {current_theme.bg}; }}
    [data-testid="stSidebar"] {{ background-color: {current_theme.sec_bg}; }}

    /* STEALTH MODUS: Versteckt das Streamlit-Menü oben rechts und den Footer.
       Dadurch sieht es aus wie eine professionelle, eigenständige Webseite. */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Sidebar Kollaps-Button ausblenden, damit die Leiste dauerhaft bleibt */
    [data-testid="stSidebarCollapseButton"] {{ display: none !important; }}

    /* Textfarben anpassen */
    .stApp, h1, h2, h3, h4, h5, h6, p, label {{ color: {current_theme.text} !important; }}
    
    /* Abstände optimieren, damit die App nicht so gequetscht aussieht */
    .block-container {{ padding-top: 1.5rem !important; padding-bottom: 1rem !important; }}
</style>
""", unsafe_allow_html=True)

# Überschrift der App
st.markdown("<h1 style='margin-bottom: 0px; padding-bottom: 0px; margin-top: -30px;'>☀️ Reise-Radar</h1><br>",
            unsafe_allow_html=True)
st.markdown("😎 Finde dein nächstes Reiseziel")


# --- SUCHMASCHINE (EINGABEFORMULAR) ---
# Das Formular bündelt Eingabe und Button. So lädt die App erst neu,
# wenn der Nutzer wirklich auf "Suchen" klickt und nicht bei jedem getippten Buchstaben.
with st.form(key='search_form'):
    col1, col2 = st.columns([0.85, 0.15], vertical_alignment="bottom")
    with col1:
        city_input = st.text_input("Stadt suchen", placeholder="z. B. Frankfurt", label_visibility="collapsed")
    with col2:
        submit_btn = st.form_submit_button("Suchen", use_container_width=True)

# Wenn der Suchen-Button gedrückt wurde:
if submit_btn:
    if city_input.strip(): # Prüft, ob der Text nicht nur aus Leerzeichen besteht
        # API nach Treffern fragen
        results = search_city_list(city_input)

        if results and len(results) > 1:
            # Szenario A: Mehrere Ergebnisse (z.B. "Frankfurt" -> am Main oder an der Oder?)
            st.session_state['search_results_list'] = results
            st.session_state['current_search'] = None
            st.session_state['direct_lat_lon'] = None
        elif results and len(results) == 1:
            # Szenario B: Exakt 1 Ergebnis -> Wir wissen, was gemeint ist und laden es sofort.
            r_lat, r_lon, r_name = results[0]
            st.session_state['search_results_list'] = None
            st.session_state['current_search'] = r_name
            st.session_state['direct_lat_lon'] = (r_lat, r_lon, r_name)
        else:
            # Szenario C: Gar nichts gefunden. Später taucht eine Fehlermeldung auf.
            st.session_state['search_results_list'] = None
            st.session_state['current_search'] = city_input
            st.session_state['direct_lat_lon'] = None

weather_data_to_display = None

# --- AUSWAHLLISTE BEI MEHREREN TREFFERN ---
# Wenn wir vorhin eine Liste mit mehreren Treffern in den Notizblock gelegt haben, zeigen wir jetzt Buttons an.
if st.session_state.get('search_results_list'):
    st.info("🌍 Mehrere Städte gefunden – welche meinst du?")
    for r_lat, r_lon, r_name in st.session_state['search_results_list']:
        if st.button(r_name, key=f"sel_{r_lat}_{r_lon}"):
            # Nutzer hat sich entschieden -> In den Notizblock schreiben, Liste löschen und Seite neu laden.
            st.session_state['current_search'] = r_name
            st.session_state['direct_lat_lon'] = (r_lat, r_lon, r_name)
            st.session_state['search_results_list'] = None
            st.rerun()


# --- DATEN AUS DEM BACKEND (API) HOLEN ---
# Wenn wir eine Stadt festgelegt haben und gerade KEINE Auswahl-Liste anzeigen:
if st.session_state['current_search'] and not st.session_state.get('search_results_list'):

    # Prüfen, ob wir die exakten Koordinaten schon haben (spart eine API-Anfrage)
    if st.session_state['direct_lat_lon'] and st.session_state['direct_lat_lon'][2] == st.session_state['current_search']:
        lat, lon, found_name = st.session_state['direct_lat_lon']
    else:
        # Falls nicht, suchen wir die Koordinaten schnell in der API
        search_query = st.session_state['current_search']
        lat, lon, found_name = search_city_coordinates(search_query)

    # Wenn wir erfolgreiche Koordinaten haben, rufen wir das Wetter ab:
    if lat is not None and lon is not None:
        st.session_state['current_search'] = found_name

        # Stadt in den Verlauf eintragen (und alte, doppelte Einträge entfernen)
        st.session_state['history'] = [h for h in st.session_state['history'] if
                                       (h[0] if isinstance(h, tuple) else h) != found_name]
        st.session_state['history'].append((found_name, lat, lon))

        # DAS HERZSTÜCK: Hier ruft unser Frontend das Backend (api_client.py) auf.
        # Wir bekommen ein Paket mit allen aktuellen und zukünftigen Wetterdaten zurück.
        temp, humidity, weather_code, h_times, h_temps, daily_data = get_weather_data(lat, lon)

        # Wenn Wetterdaten da sind, verpacken wir sie in eine Variable für die Anzeige weiter unten.
        if temp is not None:
            icon = get_weather_icon(weather_code)
            weather_data_to_display = (found_name, lat, lon, temp, humidity, icon, h_times, h_temps, daily_data)


# --- SEITENLEISTE (SIDEBAR) ---
# Alles, was mit 'st.sidebar' beginnt, wird in das Menü auf der linken Seite gerendert.

# 1. Bereich: Favoriten aus der SQLite-Datenbank laden und anzeigen
st.sidebar.header("⭐ Meine Favoriten")
favorites = get_favorites()

if len(favorites) > 0:
    for fav in favorites:
        city_name, fav_lat, fav_lon = fav[0], fav[1], fav[2]
        # Layout: Name links (85% Breite), Löschen-Button rechts (15% Breite)
        col1, col2 = st.sidebar.columns([0.85, 0.15], vertical_alignment="center")
        col1.button(f"❤️ {city_name}", key=f"fav_btn_{city_name}", on_click=cb_load_fav,
                    args=(city_name, fav_lat, fav_lon))
        col2.button("❌", key=f"fav_del_{city_name}", type="tertiary", help="Favorit entfernen", on_click=cb_remove_fav,
                    args=(city_name,))
else:
    st.sidebar.info("Noch keine Favoriten gespeichert.")

st.sidebar.divider()

# 2. Bereich: Suchverlauf (aus dem Session-State Notizblock) anzeigen
st.sidebar.header("🕒 Suchverlauf")

if len(st.session_state['history']) > 0:
    # reversed() sorgt dafür, dass die neuste Suche ganz oben steht
    for past_item in reversed(st.session_state['history']):
        if isinstance(past_item, str):
            continue # Überspringt fehlerhafte alte Einträge

        past_name, p_lat, p_lon = past_item
        col1, col2, col3 = st.sidebar.columns([0.70, 0.15, 0.15], vertical_alignment="center")

        col1.button(f"🔍 {past_name}", key=f"hist_btn_{past_name}", on_click=cb_load_history,
                    args=(p_lat, p_lon, past_name))
        col2.button("❤️", key=f"hist_fav_{past_name}", type="tertiary", help="Direkt als Favorit speichern",
                    on_click=cb_fav_from_history, args=(past_name, p_lat, p_lon, past_item))
        col3.button("❌", key=f"hist_del_{past_name}", type="tertiary", help="Aus Verlauf löschen",
                    on_click=cb_remove_history, args=(past_item, past_name))
else:
    st.sidebar.info("Keine weiteren Suchanfragen.")

st.sidebar.write("")

# 3. Bereich: Einstellungen (Farbwelten / Themes)
with st.sidebar.popover("⚙️ Einstellungen", use_container_width=True):
    st.markdown("**Farbwelt wählen:**")
    all_theme_labels = ThemePalette.get_all_labels()

    # Radio-Buttons zur Auswahl des Themes
    selected_theme = st.radio(
        "Theme",
        all_theme_labels,
        index=all_theme_labels.index(st.session_state['theme_name']),
        label_visibility="collapsed"
    )

    # Wenn der Nutzer ein neues Theme anklickt, speichern wir es im Notizblock und laden die Seite neu.
    if selected_theme != st.session_state['theme_name']:
        st.session_state['theme_name'] = selected_theme
        st.rerun()


# --- HAUPTANSICHT: WETTERDATEN ANZEIGEN ---
# Wenn unser Datenpaket oben erfolgreich gefüllt wurde, bauen wir jetzt das Dashboard auf.
if weather_data_to_display:
    found_name, lat, lon, temp, humidity, icon, h_times, h_temps, daily_data = weather_data_to_display
    st.divider()

    # KOPFBEREICH: Stadtname und Favoriten-Button
    head_col1, head_col2 = st.columns([0.75, 0.25], vertical_alignment="center")
    with head_col1:
        st.subheader(f"Wetter in {found_name}")
    with head_col2:
        # Prüfen, ob die Stadt schon ein Favorit ist, um den Button ggf. zu deaktivieren
        is_already_favorite = any(f[0] == found_name for f in favorites)
        if not is_already_favorite:
            st.button("❤️ Als Favorit speichern", use_container_width=True, on_click=cb_add_current_fav,
                      args=(found_name, lat, lon))
        else:
            st.button("⭐ Gespeichert", disabled=True, use_container_width=True)

    # ZWEI-SPALTEN-LAYOUT: Links Wetterdaten, rechts die Bildergalerie
    col_left, col_right = st.columns([0.55, 0.45], gap="large")

    with col_left:
        # 1. Aktuelle Kennzahlen
        met_col1, met_col2 = st.columns(2)
        met_col1.metric(label="Aktuelle Temperatur", value=f"{temp} °C  {icon}")
        met_col2.metric(label="Luftfeuchtigkeit", value=f"{humidity} % 💧")

        # 2. Liniendiagramm für die stündliche Temperatur
        st.write("")
        st.markdown("**📈 Stündlicher Verlauf**")

        # Für Altair-Diagramme brauchen wir eine Pandas-Tabelle (DataFrame)
        chart_df = pd.DataFrame({
            "Uhrzeit": pd.to_datetime(h_times),
            "Temperatur (°C)": h_temps
        })

        # Altair generiert ein modernes, interaktives Liniendiagramm
        line_chart = alt.Chart(chart_df).mark_line(point=True, color=current_theme.primary).encode(
            x=alt.X('Uhrzeit:T', axis=alt.Axis(format='%H:%M', tickCount=12, title='', labelColor=current_theme.text,
                                               domainColor=current_theme.text)),
            y=alt.Y('Temperatur (°C):Q', scale=alt.Scale(domain=[min(h_temps) - 2, max(h_temps) + 2]), title='',
                    axis=alt.Axis(labelColor=current_theme.text, domainColor=current_theme.text))
        ).properties(
            height=200
        )
        st.altair_chart(line_chart, use_container_width=True)

        # 3. Die 14-Tage-Vorhersage (als schicke kleine Kacheln)
        st.write("")
        st.markdown("**📅 14-Tage-Vorhersage**")

        # Schalter zwischen Woche 1 und Woche 2
        week_view = st.radio("Zeitraum auswählen:", ["Woche 1 (Tage 1-7)", "Woche 2 (Tage 8-14)"], horizontal=True,
                             label_visibility="collapsed")
        start_idx = 0 if "Woche 1" in week_view else 7

        cols = st.columns(7) # 7 Spalten für 7 Tage
        days_de = {"Mon": "Mo", "Tue": "Di", "Wed": "Mi", "Thu": "Do", "Fri": "Fr", "Sat": "Sa", "Sun": "So"}

        for i, col in enumerate(cols):
            idx = start_idx + i
            raw_date = daily_data["dates"][idx]
            dt = pd.to_datetime(raw_date)
            day_name = days_de.get(dt.strftime("%a"), dt.strftime("%a"))
            day_icon = get_weather_icon(daily_data["codes"][idx])
            t_max = round(daily_data["temp_max"][idx])
            t_min = round(daily_data["temp_min"][idx])

            # Wir nutzen hier pures HTML für die Kacheln, damit sie abgerundete Ecken haben
            # und das Design exakt kontrolliert werden kann.
            with col:
                st.markdown(f"""
                <div style="text-align: center; padding: 5px; background-color: {current_theme.sec_bg}; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05);">
                    <div style="font-size: 13px; font-weight: bold;">{day_name}</div>
                    <div style="font-size: 10px; opacity: 0.7;">{dt.strftime('%d.%m.')}</div>
                    <div style="font-size: 18px; margin: 2px 0;">{day_icon}</div>
                    <div style="font-size: 13px; font-weight: bold;">{t_max}°</div>
                    <div style="font-size: 11px; opacity: 0.7;">{t_min}°</div>
                </div>
                """, unsafe_allow_html=True)

    with col_right:
        # 4. Bildergalerie der Pixabay API
        st.markdown(f"**📸 Eindrücke der Region**")
        real_images = get_city_images(found_name)

        if real_images and len(real_images) > 0:
            images_to_show = real_images
        else:
            # Fallback: Wenn Pixabay nichts findet, nutzen wir zufällige Platzhalter-Bilder
            city_seed = found_name.replace(" ", "").replace(",", "")
            images_to_show = [
                f"https://picsum.photos/seed/{city_seed}1/800/600",
                f"https://picsum.photos/seed/{city_seed}2/800/600",
                f"https://picsum.photos/seed/{city_seed}3/800/600",
                f"https://picsum.photos/seed/{city_seed}4/800/600"
            ]

        # Übergibt die Bilder-URLs an unsere eigene HTML-Bildergalerie (components.py)
        html_code = get_gallery_html(images_to_show)
        components.html(html_code, height=450)

# Fehlermeldung, wenn die API keine Daten für die gesuchte Stadt hat
elif st.session_state['current_search'] is not None:
    st.error(f"Das Wetter für '{st.session_state['current_search']}' konnte nicht geladen werden. Tippfehler?")


# --- ZUSATZ-FEATURE: REISEZIELE VERGLEICHEN ---
# Zeigt sich nur, wenn man mindestens 2 Orte in den Favoriten gespeichert hat.
if len(favorites) > 1:
    st.divider()
    st.subheader("⚖️ Reise-Planer: Favoriten vergleichen")
    st.write("Vergleiche die Wetter-Prognose für deine Reiseplanung auf einen Blick.")

    if st.button("Reiseziele analysieren", use_container_width=True):
        compare_data = []
        # st.spinner zeigt einen kleinen Ladekreis, während die App arbeitet
        with st.spinner("Daten werden für die Reiseplanung aufbereitet..."):
            for fav in favorites:
                fname, flat, flon = fav[0], fav[1], fav[2]

                # Holt unsichtbar das Wetter für jeden Favoriten
                ftemp, fhum, fcode, _, _, f_daily = get_weather_data(flat, flon)

                if ftemp is not None and f_daily is not None:
                    max_7_days = max(f_daily["temp_max"][:7])

                    # WMO-Codes (Wetter-IDs), die auf Regen oder Gewitter hindeuten
                    rain_codes = [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]

                    # Logik: Gibt es in den nächsten 7 Tagen Regen?
                    will_rain = any(code in rain_codes for code in f_daily["codes"][:7])

                    # KI-ähnlicher "Koffer-Tipp" basierend auf einfachen Wenn-Dann-Regeln
                    if will_rain:
                        tipp = "Regenschirm einpacken ☂️"
                    elif max_7_days > 26:
                        tipp = "Sonnencreme & Shorts 😎"
                    elif max_7_days < 12:
                        tipp = "Dicke Jacke & Schal 🧥"
                    else:
                        tipp = "Übergangsjacke (Zwiebellook) 👕"

                    # Name verkürzen für die Tabelle (z.B. "Frankfurt am Main" statt dem ganzen Rattenschwanz)
                    city_short = fname.split(" —")[0].split(",")[0]

                    compare_data.append({
                        "Reiseziel": city_short,
                        "Wetter Aktuell": f"{ftemp} °C {get_weather_icon(fcode)}",
                        "Trend (nächste 7T)": f"bis zu {round(max_7_days)} °C",
                        "Koffer-Tipp": tipp
                    })

        # Zeigt das Ergebnis als saubere Pandas-Tabelle ohne Index-Zahlen an
        if compare_data:
            df_compare = pd.DataFrame(compare_data)
            st.dataframe(df_compare, use_container_width=True, hide_index=True)