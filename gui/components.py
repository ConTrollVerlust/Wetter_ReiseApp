"""
Backend-Logik: Komponenten-Modul (gui/components.py)

WAS MACHT DIESE DATEI?
Streamlit bietet von sich aus nur einfache Elemente wie Text oder Buttons an. Wenn wir
etwas Komplexeres wollen – wie eine interaktive Bildergalerie, bei der man durchklicken
kann –, müssen wir dem Browser "direktes HTML & JavaScript" schicken.

Diese Datei enthält eine Funktion, die diesen komplexen HTML-Code dynamisch baut und
an Streamlit zurückgibt, damit es im Browser angezeigt werden kann.
"""


def get_gallery_html(mock_images, height=400):
    """
    Erzeugt den HTML- und JavaScript-Code für eine flüssige Bildergalerie.

    Parameters:
    - mock_images: Eine Liste mit den Links (URLs) zu den Bildern.
    - height: Die Höhe der Galerie in Pixeln.
    """

    # 1. HTML-Teil: Wir bauen für jedes Bild einen eigenen <img>-Tag
    img_tags = ""
    for img in mock_images:
        # Die Klasse 'mySlides' brauchen wir später für JavaScript, um Bilder zu verstecken/zeigen.
        img_tags += f'<img class="mySlides" src="{img}" onclick="toggleFullscreen()">'

    # 2. Der gesamte HTML-String, den wir an Streamlit übergeben
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    /* CSS für das Aussehen der Galerie */
    body {{ margin: 0; padding: 0; background-color: transparent; font-family: sans-serif; }}

    /* Der Rahmen der Galerie */
    .slideshow-container {{ position: relative; width: 100%; height: {height}px; margin: auto; overflow: hidden; border-radius: 15px; background: #111; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}

    /* Die Bilder an sich */
    .mySlides {{ display: none; width: 100%; height: 100%; object-fit: cover; cursor: pointer; transition: opacity 0.3s ease-in-out; }}

    /* Die Pfeile (prev/next) zum Durchklicken */
    .prev, .next {{ cursor: pointer; position: absolute; top: 50%; width: auto; padding: 16px; margin-top: -22px; color: white; font-weight: bold; font-size: 24px; border-radius: 0 5px 5px 0; user-select: none; background-color: rgba(0,0,0,0.3); text-decoration: none; border: none; transition: background-color 0.2s; }}
    .next {{ right: 0; border-radius: 5px 0 0 5px; }}
    .prev:hover, .next:hover {{ background-color: rgba(0,0,0,0.8); }}

    /* Ein kleiner Hinweis-Text im Bild */
    .hint {{ position: absolute; bottom: 10px; right: 10px; color: rgba(255,255,255,0.9); font-size: 13px; background: rgba(0,0,0,0.6); padding: 5px 10px; border-radius: 20px; pointer-events: none; }}

    /* Wenn der Nutzer auf Vollbild klickt, wird das Bild zentriert und nicht mehr abgeschnitten */
    :fullscreen .mySlides {{ object-fit: contain; background-color: #000; }}
    :fullscreen .slideshow-container {{ border-radius: 0; height: 100vh; width: 100vw; }}
    </style>
    </head>
    <body>

    <!-- Das Gerüst der Galerie -->
    <div class="slideshow-container" id="gallery">
      {img_tags}
      <a class="prev" onclick="plusSlides(-1)">&#10094;</a>
      <a class="next" onclick="plusSlides(1)">&#10095;</a>
      <div class="hint">Klick für Vollbild ⤢</div>
    </div>

    <!-- JavaScript sorgt für die Logik (Wechseln der Bilder, Vollbild, Tastatur-Steuerung) -->
    <script>
    let slideIndex = 1;
    showSlides(slideIndex);

    // Funktion zum Weiter/Zurück schalten
    function plusSlides(n) {{ showSlides(slideIndex += n); }}

    // Logik: Zeigt nur das aktuelle Bild an, versteckt den Rest
    function showSlides(n) {{
      let i;
      let slides = document.getElementsByClassName("mySlides");
      if (n > slides.length) {{slideIndex = 1}}
      if (n < 1) {{slideIndex = slides.length}}
      for (i = 0; i < slides.length; i++) {{ 
          slides[i].style.display = "none"; 
      }}
      slides[slideIndex-1].style.display = "block";
    }}

    // Vollbild-Funktion nutzen
    function toggleFullscreen() {{
        let elem = document.getElementById("gallery");
        if (!document.fullscreenElement) {{
            elem.requestFullscreen().catch(err => {{ console.log("Fehler beim Vollbild."); }});
        }} else {{
            document.exitFullscreen();
        }}
    }}

    // Tastatur-Steuerung (Pfeiltasten)
    document.addEventListener('keydown', function(event) {{
        if(event.key === 'ArrowLeft') {{ plusSlides(-1); }}
        else if(event.key === 'ArrowRight') {{ plusSlides(1); }}
    }});
    </script>

    </body>
    </html>
    """
    return html_code