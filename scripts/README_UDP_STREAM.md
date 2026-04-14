# UDP Camera Streaming & Face Recognition

Diese Dokumentation erklärt, wie ein Kamera-Stream von einem Windows-PC via UDP an das ROS 2 System (Remote PC/WSL) gesendet und dort für die Gesichtserkennung verarbeitet wird.

## 1. Vorbereitung auf Windows
1.  **Abhängigkeiten**: Python und OpenCV müssen installiert sein.
    ```powershell
    pip install opencv-python
    ```
2.  **Konfiguration**: Öffne `windows_streamer.py` und setze die `WSL_IP` auf die IP deines Remote-PCs/WSL (z.B. `172.25.12.53`).
3.  **Stream starten**:
    ```powershell
    python windows_streamer.py
    ```
    *Optionaler Kamera-Index: `python windows_streamer.py 0`*

## 2. Start auf dem Remote-PC (ROS 2)
1.  **Workspace vorbereiten**:
    ```bash
    cd ~/projects/my_new_robot
    source install/setup.bash
    ```
2.  **Launch-File starten**:
    ```bash
    ros2 launch ball_tracker face_tracker_udp.launch.py
    ```

## 3. Visualisierung
Um das Bild mit den Erkennungs-Boxen zu sehen:
1.  **rqt_image_view starten**:
    ```bash
    ros2 run rqt_image_view rqt_image_view
    ```
2.  **Topic wählen**: Wähle in der Dropdown-Liste oben links das Topic **`/image_out`** aus.

## Troubleshooting & Nützliches
*   **Kein Bild in rqt**: Prüfe, ob die IP in `windows_streamer.py` korrekt ist und ob Windows Pakete an den Remote-PC senden darf (Firewall).
*   **rqt zurücksetzen**: Falls die Fenster in rqt falsch angezeigt werden, lösche die Konfiguration:
    ```bash
    rm -rf ~/.config/ros.org
    ```
*   **Installation**: Falls `rqt_image_view` fehlt:
    ```bash
    sudo apt update && sudo apt install ros-humble-rqt-image-view
    ```

---

## 4. Alternate Setup: Robot-to-PC Stream
Falls du die Kamera am Roboter (Raspberry Pi) hast und die Erkennung auf dem PC laufen lassen willst.

### A. Faces registrieren (auf PC oder Roboter)
Gesichter müssen registriert sein, bevor der Tracker sie identifizieren kann.
```bash
ros2 run ball_tracker register_face --ros-args -p person_name:=<dein_name>
```

### B. UDP Sender starten (auf dem Roboter)
Startet den Kamera-Stream zur IP des Remote-PCs.
```bash
ros2 run ball_tracker udp_cam_sender --ros-args -p target_ip:=<PC_IP_ADRESSE>
```

### C. Gesichtserkennung starten (auf dem PC)
Startet den Receiver und den Detector (wie in Sektion 2).
```bash
ros2 launch ball_tracker face_tracker_udp.launch.py
```
