# Phase 3: Wie sieht der Roboter aus? (URDF & XACRO)

Wenn du willst, dass eine Software deinen Roboter berechnet oder simuliert, musst du ihr erklären, wie er aussieht. Wo ist der Arm? Wie schwer ist der Rumpf? Wo ist das Rad befestigt?

Dafür gibt es **URDF** (Unified Robot Description Format) Dateien. Diese sind in **XML** geschrieben.
Dein Roboter nutzt `xacro` (XML Macros). Das ist einfach URDF, aber man kann Variablen und include-Befehle benutzen, um es aufzuräumen.

## 1. Syntax-Crashkurs: XML lesen

XML ist wie ein Stammbaum oder Schachtel-Aufbau. Es besteht aus "Tags" (Etiketten) in spitzen Klammern `< >`.
Jeder Tag, der geöffnet wird `<name>`, muss auch wieder geschlossen werden `</name>`. Alles dazwischen gehört zu dieser Schachtel.

**Das Grundgerüst:**
```xml
<robot name="mein_roboter">
    <!-- Hier ist der Inhalt des Roboters -->
</robot>
```
Alles, was zwischen `<!--` und `-->` steht, ist nur ein **Kommentar** für Menschen. Der Computer ignoriert das.

**Kurzschreibweise:**
Wenn eine Schachtel keinen Inhalt hat, sondern nur Eigenschaften, kann man sie mit `/>` am Ende direkt wieder schließen (spart Platz):
```xml
<xacro:include filename="camera.xacro" />
```

## 2. Deine `robot.urdf.xacro` im Detail

Schauen wir uns deine Datei `robot.urdf.xacro` an:

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro"  name="robot">

    <xacro:arg name="use_ros2_control" default="true"/>
    <xacro:arg name="sim_mode" default="false"/>

    <xacro:include filename="robot_core.xacro" />
    <xacro:include filename="camera.xacro" />
    <xacro:include filename="nerf_launcher.xacro" />

</robot>
```

**Was tut das?**
Das ist die Hauptdatei deines Roboters. Statt hier tausende Zeilen Code für jede einzelne Schraube reinzuschreiben, ist sie extrem aufgeräumt. Sie sagt einfach: "Hey, mein Roboter besteht aus den Dateien `robot_core.xacro` (Rahmen+Räder), `camera.xacro` und `nerf_launcher.xacro`." 

**Wie liest man es?**
- `<xacro:arg name="..." default="..."/>`: Hier definierst du Argumente (Variablen). Zum Beispiel sagst du, dass standardmäßig `use_ros2_control` auf `true` (Wahr) gesetzt ist.
- `<xacro:include filename="..." />`: Das ist wie Lego zusammenstecken. Er nimmt den kompletten Code aus der benannten Datei und klebt ihn unsichtbar an genau diese Stelle.

## 3. Links und Joints (Die eigentliche Geometrie)
Wenn du in die Datei `robot_core.xacro` schaust, wirst du die echten Roboter-Vokabeln finden:
- **`link`**: Ein festes, hartes Teil (Knochen, Räder, Kameragehäuse).
- **`joint`**: Ein Gelenk, das zwei Links verbindet (ein Motor, ein Scharnier oder auch einfach eine feste Klebe-Verbindung).

So sieht ein typisches Rad in URDF aus:
```xml
<link name="rechtes_rad">
    <visual> ... Aussehen ... </visual>
    <collision> ... Wo eckt es an? ... </collision>
</link>

<joint name="rad_gelenk" type="continuous">
    <parent link="chassis"/>
    <child link="rechtes_rad"/>
</joint>
```
*Deutsch:* "Es gibt ein Rad. Es hängt über ein Endlos-Gelenk (`continuous`) am Chassis."

> [!TIP]
> **Dein Lern-Check:**
> Schau einmal in eine Codedatei wie `robot_core.xacro` oder `nerf_launcher.xacro`. Kannst du ein Gelenk (`<joint>`) finden und herauslesen, welche zwei Teile (`parent` und `child`) es miteinander verbindet?
