import face_recognition
import pickle
import os
import cv2

# Einstellungen
INPUT_DIR = "faces_raw"
OUTPUT_FILE = "encodings.pkl"

known_encodings = []
known_names = []

print("[INFO] Starte Verarbeitung der Gesichter...")

# Gehe durch jeden Unterordner (Person)
for person_name in os.listdir(INPUT_DIR):
    person_dir = os.path.join(INPUT_DIR, person_name)

    if not os.path.isdir(person_dir):
        continue

    # Gehe durch jedes Bild der Person
    for image_name in os.listdir(person_dir):
        image_path = os.path.join(person_dir, image_name)

        # Bild laden
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Gesicht finden und Encoding berechnen
        # 'hog' ist schneller auf CPUs (Pi), 'cnn' ist genauer (braucht GPU)
        boxes = face_recognition.face_locations(rgb_image, model="hog")
        encodings = face_recognition.face_encodings(rgb_image, boxes)

        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(person_name)
            print(f"[+] Gesicht von {person_name} in {image_name} gespeichert.")

# Alles in eine Datei schreiben
print(f"[INFO] Speichere {len(known_encodings)} Encodings in {OUTPUT_FILE}...")
data = {"encodings": known_encodings, "names": known_names}

with open(OUTPUT_FILE, "wb") as f:
    f.write(pickle.dumps(data))

print("[FERTIG] Datei erfolgreich erstellt!")
