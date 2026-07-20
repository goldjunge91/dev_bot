# Kamera Kalibrierung (ROS 2)

Um die Warnungen (`Unable to open camera calibration file`) zu beheben und die Präzision des Roboters (z.B. beim Zielen) zu erhöhen, können wir die Kamera kalibrieren.

ROS 2 bietet dafür ein eigenes Tool (`camera_calibration`), das die Linsenverzerrung (Fisheye-Effekt etc.) misst und eine Konfigurationsdatei erstellt.

## Vorbereitung

1. **Schachbrett (Checkerboard) drucken:**
   Du benötigst ein Schachbrett-Muster auf einem festen, ebenen Untergrund (Karton/Klemmbrett).
   - Downloade z.B. dieses A4 Schachbrett: [ROS Checkerboard (8x6)](https://raw.githubusercontent.com/opencv/opencv/master/doc/pattern.png)
   - **Wichtig:** Messe mit einem Lineal die Kantenlänge eines einzelnen schwarzen Quadrats in Metern (z.B. `0.025` für 2,5 cm).
   - Beachte: Ein "8x6" Schachbrett hat 8x6 *innere* Ecken (also 9x7 Quadrate).

2. **Pakete installieren (auf dem PC):**

   ```bash
   sudo apt update
   sudo apt install ros-humble-camera-calibration
   ```

## Durchführung

Da die Bildübertragung über Tailscale nun funktioniert, können wir die Kalibrierung bequem **auf deinem PC** durchführen, während der Roboter das Bild sendet.

1. **Roboter starten:**
   Starte den Roboter wie gewohnt auf dem Pi (MJPG ist für die flüssige Übertragung hier am besten):

   ```bash
   ./src/gubot_utils/scripts/start_robot.sh --face
   ```

2. **Kalibrierung auf dem PC starten:**
   Öffne ein Terminal auf deinem **PC** und führe folgenden Befehl aus.
   *(Passe `--size` an die Anzahl der inneren Ecken deines Bretts an, und `--square` an die gemessene Kantenlänge eines Quadrats in Metern!)*

   ```bash
   # WICHTIG: Die Kamera muss bereits Bilder senden, bevor dieses Tool gestartet wird!
   ros2 run camera_calibration cameracalibrator \
     --size 8x6 \
     --square 0.025 \
     --ros-args \
     -r image:=/camera/image_raw \
     -r camera:=/camera
   ```

3. **Das Schachbrett bewegen:**
   Es öffnet sich ein Fenster mit dem Kamerabild. Halte das Schachbrett vor die Kamera.
   - Bewege es nach Links, Rechts, Oben, Unten (`X`, `Y`).
   - Bewege es nah an die Kamera und weit weg (`Size`).
   - Kippe das Brett in alle Richtungen (`Skew`).
   - Die Balken am rechten Bildschirmrand füllen sich grün, sobald du genug Variationen gesammelt hast.

4. **Speichern:**
   - Sobald die Balken grün sind, wird der **"CALIBRATE"** Knopf klickbar. Klicke ihn (das Fenster friert kurz ein, während er rechnet).
   - Klicke danach auf **"SAVE"**.
   - Klicke auf **"COMMIT"**.

Dadurch wird die Datei automatisch nach `~/.ros/camera_info/real_cam.yaml` (bzw. auf dem PC) gespeichert.

## Datei auf den Roboter übertragen

Da der PC die Kalibrierung berechnet hat, liegt die Datei nun auf deinem PC. Wir müssen sie auf den Roboter kopieren, da dort der Kameratreiber läuft:

```bash
# Auf dem PC ausführen (Passe USER und IP deines Pi's an)
scp ~/.ros/camera_info/real_cam.yaml ros@ros2pi:~/.ros/camera_info/
```

*(Alternativ über VS Code Remote rüberkopieren).*

Beim nächsten Start des Roboters findet der Treiber die Datei automatisch und die Warnungen sind verschwunden!
