import face_recognition
import pickle
import os
import cv2

# Einstellungen
INPUT_DIR = "faces_raw"
# Ausgabepfad – kompatibel mit detect_face Node (Parameter: encodings_path)
OUTPUT_FILE = os.path.expanduser("~/.ros/face_detector/encodings.pkl")

known_encodings = []
known_names = []
skipped = 0

print("[INFO] Starte Verarbeitung der Gesichter...")
print(f"[INFO] Eingabe: {os.path.abspath(INPUT_DIR)}")
print(f"[INFO] Ausgabe: {OUTPUT_FILE}")

# Gehe durch jeden Unterordner (Person)
for person_name in sorted(os.listdir(INPUT_DIR)):
    person_dir = os.path.join(INPUT_DIR, person_name)

    if not os.path.isdir(person_dir):
        continue

    print(f"\n[INFO] Verarbeite Person: {person_name}")

    # Gehe durch jedes Bild der Person
    for image_name in sorted(os.listdir(person_dir)):
        image_path = os.path.join(person_dir, image_name)

        # Bild laden
        image = cv2.imread(image_path)
        if image is None:
            print(f"  [WARN] Konnte Bild nicht laden: {image_name} – übersprungen.")
            skipped += 1
            continue

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Gesicht finden und Encoding berechnen
        # Versuche zuerst CNN (genauer), Fallback auf HOG + Upsampling
        try:
            # Upsample 2x hilft bei kleinen Gesichtern
            boxes = face_recognition.face_locations(
                rgb_image, model="cnn", number_of_times_to_upsample=1
            )
        except Exception:
            # Fallback: HOG mit 2x Upsampling (langsamer aber genauer als Standard)
            boxes = face_recognition.face_locations(
                rgb_image, model="hog", number_of_times_to_upsample=2
            )

        encodings = face_recognition.face_encodings(rgb_image, boxes)

        if not encodings:
            print(f"  [WARN] Kein Gesicht gefunden in: {image_name} – übersprungen.")
            skipped += 1
            continue

        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(person_name)
            print(f"  [+] {person_name} / {image_name} → Encoding gespeichert.")

# Ausgabeverzeichnis erstellen falls nötig
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Alles in eine Datei schreiben
print(f"\n[INFO] Speichere {len(known_encodings)} Encodings in {OUTPUT_FILE}...")
data = {"encodings": known_encodings, "names": known_names}

with open(OUTPUT_FILE, "wb") as f:
    f.write(pickle.dumps(data))

print("[FERTIG] Datei erfolgreich erstellt!")
print(f"  Encodings gespeichert : {len(known_encodings)}")
print(f"  Bilder übersprungen   : {skipped}")
print(f"  Personen              : {sorted(set(known_names))}")
