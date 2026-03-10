# Phase 4: Das "Gehirn" (C++ und Python Nodes)

Ein "Node" ist die kleine Software-Fabrik, die Berechnungen anstellt, Sensoren liest oder Motoren steuert. ROS 2 Nodes können in C++ oder Python geschrieben werden. In deinem Projekt hast du beides!

Gehen wir beides kurz anhand echter Dateien durch.

## 1. Ein Python Node (`gubot_one/scripts/nerf_joy.py`)

Python ist sehr gut lesbar. Schauen wir uns dein `NerfJoy` Programm an, welches Tastendrücke vom Xbox-Controller in Nerf-Launcher-Befehle übersetzt.

**Der Konstruktor (`__init__`) - Die Setup-Phase**
Jede Node-Klasse erbt von `rclpy.node.Node`. Beim Erstellen der Klasse (im `__init__`) richten wir Verbindungen zur Außenwelt ein.

```python
class NerfJoy(Node):
    def __init__(self):
        super().__init__("nerf_joy") # Benennt den Node

        # Subscriber: "Zuhörer"
        self.subscription = self.create_subscription(Joy, "joy", self.joy_callback, 10)

        # Publisher: "Sprecher"
        self.pub_shooter = self.create_publisher(Float64MultiArray, "/shooter_controller/commands", 10)

        # Timer: Ein Metronom
        self.create_timer(0.05, self.loop)
```
- **Subscriber:** Dein Node sagt: "Ich will Nachrichten vom Topic `joy` (vom Datentyp `Joy`) lesen. Jedes mal, wenn eine neue hereinkommt, ruf bitte meine eigene Funktion `self.joy_callback` auf." (Die Zahl `10` ist der Zwischenspeicher).
- **Publisher:** Dein Node sagt: "Ich werde ab und zu dem Rest der Welt etwas auf dem Topic `/shooter_controller/commands` zurufen."
- **Timer:** "Ruf alle 0.05 Sekunden endlos meine Funktion `self.loop` auf."

**Der Callback - Die Reaktion**
Ein Callback ist eine Funktion, die von alleine aufgerufen wird, wenn ein Ereignis passiert.
```python
    def joy_callback(self, msg):
        # Hier landet die Joystick-Eingabe (Variablen wie msg.axes, msg.buttons)
        if msg.buttons[0] == 1:  # "A" Knopf wurde gedrückt
            self.publish_shooter(5.0)  # Schiebe Wert in deinen eigenen Publisher!
```

## 2. Ein C++ Node

C++ ist etwas strenger als Python. Man muss jeden Typ genau deklarieren, erhält dafür aber massive Geschwindigkeitsvorteile.

**Namespaces (Namensräume `::`)**
Du wirst überall Doppelpunkte sehen. Das ist, um sich sauber zu strukturieren.
`std::string` heißt: "Hol mir Bauplan `string` aus dem Ordner/Namespace `std` (Standard Library)".
`rclcpp::Node` heißt: "Hol mir Bauplan `Node` aus dem Namespace `rclcpp` (ROS Client Library C++)".

**Pointer und Speicher (`->`)**
In C++ reicht man bei komplexen Objekten oft nicht das Objekt selbst durch die Gegend (das wäre schwerfällig), sondern man gibt einen kleinen Zettel weiter, auf dem steht: *"Das Objekt findest du bei der Speicheradresse `0x1A42`"*. Das nennt man **Pointer**.

Wenn du den Pointer `mein_node_pointer` hältst und eine Funktion *in* dem eigentlichen Objekt aufrufen willst, nimmst du statt einem Punkt `.` den Pfeil `->`.
```cpp
// Python:
logger = self.get_logger()
logger.info("Hallo!")

// C++ mit Pointern:
RCLCPP_INFO(this->get_logger(), "Hallo!"); 
```
`this->get_logger()` bedeutet: "Geh zu `this` (mir selbst), folge dem Pointer und ruf in mir drinnen `get_logger()` auf."

**Das Node-Grundgerüst in C++**
```cpp
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class MinimalPublisher : public rclcpp::Node
{
public:
  MinimalPublisher() : Node("minimal_publisher") // Konstruktor
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("topic", 10);
  }

private:
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
};
```
Der große Unterschied zu Python, der verwirren kann, ist `create_publisher<std_msgs::msg::String>`.
Die spitzen Klammern `< >` (Templates in C++) sind eine Möglichkeit in C++ zu sagen: "Erstelle mir einen Publisher, *und zwar speziell für diesen einen Datentyp*!". 
In Python brauchst du die Spitzen klammern nicht, du packst den Typ einfach als normalen Parameter in die Klammer. In C++ ist das strikter getrennt.

> [!TIP]
> **Dein Lern-Check:**
> Öffne in deinem Kopf eine neue Python Datei. Wenn du mit `self.create_timer(1.0, self.sage_hallo)` einen Timer einrichtest, was musst du dann in der Klasse noch zwingend definieren, damit das funktioniert?
> *(Eine Funktion namens sage_hallo()!)*
