# Phase 1: Das "Big Picture" (Die Vogelperspektive)

Willkommen beim ersten Schritt! Bevor wir uns in Quellcode vergraben, müssen wir die "Sprache von ROS 2" und die Ordnung in deinem Projekt verstehen.

## 1. Die ROS 2 Grundbegriffe
Stell dir ROS 2 wie eine Firma vor. In dieser Firma gibt es verschiedene Abteilungen, und sie müssen miteinander kommunizieren.

- **Node (Knoten):** Das ist ein einzelner Arbeiter (ein kleines Programm) in deiner Firma. Ein Node macht normalerweise nur *eine* Sache: z.B. die Kamera auslesen, oder die Motor-Geschwindigkeit berechnen. Du hast viele Nodes, die gleichzeitig laufen.
- **Topic (Thema):** Das ist wie ein schwarzes Brett oder ein Newsletter. Ein Node kann Informationen "veröffentlichen" (**Publisher**), z.B. "Hier ist das aktuelle Kamera-Bild". Andere Nodes können diesen Newsletter abonnieren (**Subscriber**), um das Bild zu empfangen. Die Nodes kennen sich dabei nicht einmal gegenseitig!
- **Message (Nachricht):** Das Datenpaket, das über ein Topic verschickt wird (z.B. ein Text, eine Zahl oder ein Bild).

*Zusammenfassung:* Dein Roboter ist einfach eine Gruppe von Nodes (kleinen Programmen), die über Topics (Newsletter) miteinander reden.

## 2. Die Ordnerstruktur deines Roboters
Dein aktuelles Projekt liegt im Ordner `src` (Source/Quelle). Darin gibt es verschiedene "Packages" (Pakete), z.B. `gubot_one` und `nerf_launch_system`. Jedes Paket hat einen bestimmten Zweck.

Hier ist, was die Standard-Ordner in einem ROS 2 Paket normalerweise bedeuten:

*   **`launch/`**: Hier liegen die Start-Knöpfe. Da ein Roboter aus vielen Nodes besteht, wollen wir nicht jeden einzeln im Terminal starten. Launch-Dateien starten viele Nodes auf einmal.
*   **`description/`** oder **`urdf/`**: Das "Aussehen" des Roboters. Hier steht, wo die Räder sind, wie lang der Arm ist und wo Sensoren montiert sind.
*   **`config/`**: Dateien für Einstellungen (oft `.yaml`). Hier stehen Dinge drin wie "Maximale Geschwindigkeit = 5 m/s", damit man sie ändern kann, ohne den Code neu zu kompilieren.
*   **`hardware/`**: Wenn dein Code direkt mit echten Platinen (wie Arduino) oder Motoren redet, liegt das meistens hier.
*   **`firmware/`**: Das ist oft C++ Code, der *nicht* auf dem Hauptcomputer läuft, sondern direkt auf die kleinen Microcontroller (z.B. Arduino / RP2040) hochgeladen wird.

---
> [!TIP]
> **Dein Lern-Check:**
> 1. Was ist ein Node?
> 2. Wo würdest du nachsehen, wenn du das 3D-Modell des Roboters ändern willst?
> 
> *Wenn du das verstanden hast, bist du bereit für Phase 2: Die Launch-Dateien!*
