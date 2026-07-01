"""
Backend-Logik: Theme-Enums (core/themes.py)

WAS MACHT DIESE DATEI?
Hier definieren wir die Farbwelten (Themes) unserer App. Anstatt Farben hart in den
Code zu schreiben, nutzen wir eine "Enum"-Klasse. Das ist wie eine feste Liste von
vordefinierten Paketen. Jedes Paket hat einen Anzeigenamen und die passenden
Hex-Farbcodes für Hintergrund, Text und Akzente.

Warum Enums?
Das macht den Code extrem robust. Wenn wir eine Farbe ändern wollen, müssen wir sie
nur hier an einer zentralen Stelle anpassen und nicht an 100 Stellen im Frontend.
"""

from enum import Enum


class ThemePalette(Enum):
    """
    Die Klasse 'ThemePalette' speichert unsere Farbwelten.
    Jedes Element (z.B. SUMMER) ist ein Objekt, das die spezifischen Farben enthält.
    """

    # Aufbau: Label für das Menü, Hintergrundfarbe, Sekundärfarbe, Textfarbe, Primärfarbe (Buttons/Akzente)
    SUMMER = ("Gelb (Sommer)", "#fcf9f2", "#f7efdb", "#3d2b1f", "#d97706")
    OCEAN = ("Blau (Ozean)", "#f0f9ff", "#e0f2fe", "#0f172a", "#0284c7")
    NATURE = ("Grün (Natur)", "#f0fdf4", "#dcfce7", "#064e3b", "#16a34a")
    MYSTIC = ("Violett (Mystik)", "#f5f3ff", "#ede9fe", "#2e1065", "#7c3aed")
    BLOSSOM = ("Rosa (Blüte)", "#fff1f2", "#ffe4e6", "#881337", "#e11d48")

    def __init__(self, label, bg, sec_bg, text, primary):
        # Hier werden die Farben beim Erstellen des Objekts den Variablen zugewiesen
        self.label = label  # Name, der im Dropdown-Menü erscheint
        self.bg = bg  # Haupt-Hintergrundfarbe
        self.sec_bg = sec_bg  # Farbe für Boxen/Seitenleisten
        self.text = text  # Textfarbe (für optimale Lesbarkeit)
        self.primary = primary  # Akzentfarbe für Buttons/Diagramme

    @classmethod
    def get_all_labels(cls):
        """
        Hilfsfunktion: Gibt alle Anzeigenamen als Liste zurück.
        Wird im Frontend (app.py) gebraucht, um das Dropdown-Menü zu füllen.
        """
        return [theme.label for theme in cls]

    @classmethod
    def from_label(cls, label):
        """
        Hilfsfunktion: Sucht aus der Liste den passenden Theme-Eintrag zum gewählten Namen.
        Falls der Nutzer etwas auswählt, was es nicht gibt, nehmen wir SUMMER als Sicherheitsnetz.
        """
        for theme in cls:
            if theme.label == label:
                return theme
        return cls.SUMMER  # Sicherheits-Fallback