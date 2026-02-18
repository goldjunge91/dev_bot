import cv2
import socket
import struct
import pickle
import time
import sys

# Konfiguration
# ACHTUNG: Hier steht deine WSL-IP-Adresse (automatisch eingefügt)
WSL_IP = "172.25.12.53"
PORT = 9999
# Standard-Kamera-Index
DEFAULT_CAMERA_INDEX = 5


def main():
    camera_idx = DEFAULT_CAMERA_INDEX
    if len(sys.argv) > 1:
        try:
            camera_idx = int(sys.argv[1])
        except ValueError:
            print(
                f"Ungültiger Kamera-Index: {sys.argv[1]}. Verwende {DEFAULT_CAMERA_INDEX}."
            )

    # UDP Socket erstellen
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000)

    print(
        f"Öffne Kamera {camera_idx} mit DirectShow (Drücke 'q' im Vorschaufenster zum Beenden)..."
    )
    # WICHTIG: cv2.CAP_DSHOW erzwingen, da MSMF oft failt (-2147483638)
    cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)

    # Auflösung setzen (320x240 reicht für Performance)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    if not cap.isOpened():
        print(f"FEHLER: Kamera {camera_idx} konnte nicht geöffnet werden!")
        print("Mögliche Ursachen:")
        print("1. Kamera wird noch von WSL verwendet (usbipd detach nötig!)")
        print("2. Falscher Index (versuche python stream_cam.py 1)")
        print("3. Kamera wird von anderer App (Zoom, Skype) blockiert")
        return

    print(f"Starte Stream an {WSL_IP}:{PORT}...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Fehler beim Lesen des Frames (Kamera disconnected?).")
                time.sleep(1)
                continue

            # Lokale Vorschau anzeigen
            cv2.imshow("Windows Kamera Stream (q zum Beenden)", frame)

            # Beenden mit 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            # Frame als JPEG komprimieren (Qualität 80)
            _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

            # Daten senden
            try:
                client_socket.sendto(buffer.tobytes(), (WSL_IP, PORT))
            except Exception as e:
                pass

            time.sleep(0.03)  # Ca. 30 FPS begrenzen

    except KeyboardInterrupt:
        print("\nStream beendet.")
    finally:
        cap.release()
        client_socket.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
