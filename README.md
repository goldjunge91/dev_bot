




| **Motor**                                                              |                                      |
| ---------------------------------------------------------------------- | ------------------------------------ |
| L-Typ GM3865-520 12V DC Motor mit Encoder                              |                                      |
| ---------------------------------------------------------------------- | ------------------------------------ |
| Motorspannung:                                                         | 12 V                                 |
| Sperrmoment:                                                           | 10 kg*cm                             |
| Nenndrehmoment:                                                        | 4,4 kg*cm                            |
| Drehzahl vor Getriebe:                                                 | 12.0000 U/min                        |
| Drehzahl nach Getriebe:                                                | 300 U/min                            |
| Übersetzungsverhältnis:                                                | 1:40                                 |
| Nennleistung:                                                          | 6 W                                  |
| Sperrstrom:                                                            | 4 A                                  |
| Nennstrom:                                                             | 0,5 A                                |
| Encodertyp:                                                            | AB Phasen-inkremental-Hall-Encoder   |
| Anzahl der Magnetringlinien:                                           | 11 zeilig                            |
| Encoder-Versorgungsspannung:                                           | 3,3 V                                |
| Schnittstellentyp:                                                     | PH2.0-6P                             |
| FUnktion:                                                              | MCU kann Signalimpulse direkt lesen. |
## Beschreibung des Encoder-Ausgangs
Die Phasendifferenz zwischen den beiden Signalen beträgt
100°. Die Drehrichtung des Motors lässt sich anhand der
Reihenfolge der beiden Signale bestimmen. Die aktuelle
Reifenfahrstrecke lässt sich anhand der Anzahl der
Signalimpulse pro Zeiteinheit und des Reifenumfangs berech-
non.
Erkennt man nur die Anzahl der AB-Phasenimpulse pro
Zeiteinheit, lässt sich auch die aktuelle Motordrehzahl
messen.

Nehmen wir als Beispiel einen Motor mit einem
Untersetzungsverhältnis von 1:40. Bei einer Umdrehung gibt
der Motor 11 Impulse pro Phase aus. Bei einem
Untersetzungsverhältnis von 1:40 beträgt die maximale
Leistung der Motorabtriebswelle (40*11*4)=1760 Impulse pro
Umdrehung. Die Phasendifferenz zwischen dem
AB-Zweiphasen-Ausgangsimpulssignal beträgt 100° und
ermöglicht so die Erkennung der Motordrehrichtung.

## Motor Wiring
![Motor Wiring](src/gubot_one/Motor_wiring.png)

| **IMU**                                                               |                                      |
| --------------------------------------------------------------------- | ------------------------------------ |
| ICM-20948 9-Achsen-Bewegungssensormodul (9-DoF)                       |                                      |
| --------------------------------------------------------------------- | ------------------------------------ |
| Versorgungsspannung (VCC):                                            | 1,8 V - 3,6 V                        |
| Messbereich Beschleunigungssensor:                                    | ±2g, ±4g, ±8g, ±16g                  |
| Messbereich Gyroskop:                                                 | ±250, ±500, ±1000, ±2000 dps         |
| Messbereich Magnetometer:                                             | ±4900 µT                             |
| Schnittstelle:                                                        | I2C / SPI                            |
| I2C-Adresse (AD0 LOW):                                                | 0x68                                 |
| I2C-Adresse (AD0 HIGH):                                               | 0x69                                 |
| Auflösung:                                                            | 16-Bit ADCs                          |
| Funktionen:                                                           | DMP, Temperatursensor, Interrupt-Pin |

## Beschreibung des IMU-Moduls
Das ICM-20948 ist ein hocheffizientes 9-Achsen-Bewegungssensormodul, das einen 3-Achsen-Beschleunigungssensor, ein 3-Achsen-Gyroskop und ein 3-Achsen-Magnetometer kombiniert. Dank der integrierten Digitalen Bewegungsverarbeitung (DMP) liefert es präzise Orientierungsdaten wie Quaternionen und Euler-Winkel. 

### Pin-Belegung
*   **VCC/GND**: Spannungsversorgung (1,8V-3,6V) und Masse.
*   **SCL/SDA**: I2C-Schnittstelle (Clock/Data).
*   **NCS**: SPI Chip Select (auf HIGH für I2C-Modus).
*   **AD0**: Adressauswahl für I2C (GND=0x68, VCC=0x69).
*   **INT**: Interrupt-Ausgang für Datenbereitschaft oder Bewegungserkennung.
*   **FSY**: Frame-Synchronisation für externe Triggerung.
*   **ACL/ADA**: Hilfs-I2C-Bus für zusätzliche Sensoren.

> [!IMPORTANT]
> Das Modul ist für 3,3V-Systeme ausgelegt. Bei Verwendung mit 5V-Systemen ist ein Pegelwandler erforderlich.


raspberry pi installation
sudo apt install screen tio


source /opt/ros/humble/setup.bash && source /home/ros/dev_bot/install/setup.bash 
&& ros2 launch gubot_bringup launch_all_real.launch.py launch_lidar:=false launch_camera:=false

ros2 run joy joy_node --ros-args -r __node:=joy_node --param device_id:=0
