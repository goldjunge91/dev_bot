# Übersicht der Launch-Dateien und Skripte (Face Tracking)

Dieses Dokument beschreibt die Struktur und die einzelnen Komponenten für das Face Tracking.

## 1. [face_tracker.launch.py](file:///home/ros/projects/my_new_robot/src/face_tracker/launch/face_tracker.launch.py)

**Das Herzstück (Software-Logik)**

* **Zweck:** Startet alle Analyse-Nodes für das Face Tracking.
* **Komponenten:**
  * `detect_face`: Gesichtserkennung im Kamerabild.
  * `follow_face`: Berechnet Fahrbefehle basierend auf der Gesichtsposition.
  * `fire_at_face`: Löst den Schuss-Service aus, wenn das Ziel gelockt ist.
* **Besonderheit:** Enthält **keinen Kamera-Treiber**. Erwartet Bilder auf dem Topic `/camera/image_raw`.
* **Wann nutzen:** Wird automatisch vom Roboter-Haupt-Launcher (`launch_all_real.launch.py`) eingebunden.

---

## 2. [face_tracker_sim.launch.py](file:///home/ros/projects/my_new_robot/src/face_tracker/launch/face_tracker_sim.launch.py)

**Simulations-Modus (Gazebo)**

* **Zweck:** Konfiguriert das Tracking für die virtuelle Welt.

---

## 3. [face_tracker_udp.launch.py](file:///home/ros/projects/my_new_robot/src/face_tracker/launch/face_tracker_udp.launch.py)

**Remote-Betrieb (UDP)**

* **Zweck:** Empfängt Video-Daten per Netzwerk für externes Processing.

---

## 4. [detect_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_face.py)

**Gesichtserkennung**

* **Zweck:** Sucht Gesichter im Bild und vergleicht sie mit bekannten Profilen.

---

## 5. [follow_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/follow_face.py)

**Bewegungssteuerung**

* **Zweck:** Berechnet die Fahrbefehle (`cmd_vel`), um ein Gesicht zu verfolgen.

---

## 6. [fire_at_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fire_at_face.py)

**Schuss-Logik**

* **Zweck:** Prüft ob das Ziel exakt zentriert ist und löst den Nerf-Schuss aus.

---

## 7. [register_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/register_face.py)

**Gesichter anlernen**

* **Zweck:** Werkzeug zum Aufnehmen und Speichern neuer Gesichter.

---

## 8. [udp_cam_sender.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/udp_cam_sender.py) & [udp_cam_receiver.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/udp_cam_receiver.py)

**Video-Streaming**

* **Zweck:** Überträgt das Kamerabild live per UDP an einen anderen PC (Offloading).

---

## 9. [fake_face_publisher.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fake_face_publisher.py)

**Test-Werkzeug**

* **Zweck:** Simuliert Gesichtserkennungen zum Testen der Mechanik ohne Kamera.

---

## 10. [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py)

**Bildverarbeitung**

* **Zweck:** Gemeinsame Bibliothek für Gesichtserkennungs-Algorithmen.
