# Motor Debugging Guide - Raspberry Pi Pico

## Problem: Motoren bewegen sich nicht nach Firmware Update

### Schnelle Diagnose

#### 1. Test-Script ausführen
```bash
cd /home/ros/projects/my_new_robot/src/diffdrive_arduino
python3 src/diffdrive_arduino/test_firmware.py
```

Das Script testet:
- ✓ Serielle Kommunikation
- ✓ Welche Pins Motoren angeschlossen haben
- ✓ Ob alte oder neue Pin-Konfiguration verwendet wird

---

## Ursachen & Lösungen

### Ursache 1: Hardware noch auf ALTE Pins verdrahtet ⚠️

**Problem:** Die neue Firmware verwendet:
- **LEFT Motor:** GP0, GP4, GP5 (neu)
- **RIGHT Motor:** GP6, GP7, GP8 (unverändert)

Alte Firmware hatte:
- **LEFT Motor:** GP2, GP3, GP4 (alt - hatte PWM-Konflikt!)
- **RIGHT Motor:** GP6, GP7, GP8

**Lösung A - Hardware umverdrahten (EMPFOHLEN):**

Verdrahte den LEFT Motor auf die neuen Pins:
```
TB6612 Pin → Pico GPIO
-----------------------
PWMA      → GP0  (statt GP2)
AIN1      → GP4  (unverändert)
AIN2      → GP5  (statt GP4... warte das passt nicht)
```

Moment, hier ist Verwirrung. Lass mich die Pin-Zuordnung klären:

**NEUE Konfiguration (optimal, keine PWM-Konflikte):**
```
LEFT Motor (TB6612 Motor A):
  PWM  → GP0  (PWMA auf TB6612)
  IN1  → GP4  (AIN1 auf TB6612)  
  IN2  → GP5  (AIN2 auf TB6612)

RIGHT Motor (TB6612 Motor B):
  PWM  → GP6  (PWMB auf TB6612)
  IN1  → GP7  (BIN1 auf TB6612)
  IN2  → GP8  (BIN2 auf TB6612)
```

**ALTE Konfiguration (hatte PWM-Konflikt):**
```
LEFT Motor:
  PWM  → GP2  (PWMA)
  IN1  → GP3  (AIN1) ← Konflikt mit GP2 im gleichen PWM Slice!
  IN2  → GP4  (AIN2)

RIGHT Motor:
  PWM  → GP6  (PWMB)
  IN1  → GP7  (BIN1)
  IN2  → GP8  (BIN2)
```

**Lösung B - Firmware auf ALTE Pins zurücksetzen:**

Wenn du die Hardware NICHT umverdrahten willst:

1. Ersetze `pinout.h` durch `pinout_legacy.h`:
   ```bash
   cd firmware/ROSArduinoBridge
   cp pinout.h pinout_new.h.backup
   cp pinout_legacy.h pinout.h
   ```

2. Neu kompilieren und auf Pico laden

3. ⚠️ **Warnung:** Die alte Konfiguration hat einen PWM-Slice-Konflikt zwischen GP2 und GP3, weshalb der LEFT Motor möglicherweise nicht richtig funktioniert!

---

### Ursache 2: TB6612 STBY Pin nicht verbunden 🔴

Der TB6612 Motor Driver hat einen **STBY (Standby)** Pin der auf **HIGH** sein muss, damit die Motoren laufen!

**Lösung:**
- **Einfach:** Verbinde STBY direkt mit **3.3V** am Pico (immer aktiv)
- **Fortgeschritten:** Verbinde STBY mit einem GPIO (z.B. GP9) und setze ihn in der Firmware auf HIGH

**TB6612 Verdrahtung Checkliste:**
```
TB6612 Pin  → Verbindung
────────────────────────
VCC         → 3.3V (Logik-Spannung)
GND         → GND (gemeinsam mit Pico & Motor Power)
VM          → 6-12V (Motor-Spannung)
STBY        → 3.3V (oder GPIO auf HIGH!)
PWMA        → GP0
AIN1        → GP4
AIN2        → GP5
PWMB        → GP6
BIN1        → GP7
BIN2        → GP8
A01/A02     → LEFT Motor
B01/B02     → RIGHT Motor
```

---

### Ursache 3: Motor-Stromversorgung fehlt 🔋

**Prüfen:**
- VM Pin (6-12V Motor Power) angeschlossen?
- Gemeinsames GND zwischen Pico, TB6612 und Netzteil?
- Netzteil kann genug Strom liefern? (min. 1A pro Motor)

---

### Ursache 4: Encoder-Pin-Konflikt (unwahrscheinlich)

Die Encoder verwenden:
- LEFT: GP22, GP21
- RIGHT: GP11, GP10

Diese sollten NICHT mit Motor-Pins kollidieren.

---

## Debug-Tests

### Test 1: Serielle Kommunikation
```bash
python3 test_firmware.py
```
Sollte "✓ Communication working!" zeigen.

### Test 2: Manuelle Pin-Tests
```bash
python3 debug_pins.py
```

Beobachte, ob Motoren sich bei den Tests drehen.

### Test 3: Motor-Kommandos direkt senden

```bash
# Serial Monitor öffnen (z.B. screen)
screen /dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00 57600

# Befehle eingeben (mit Enter):
o 100 100    # Beide Motoren vorwärts, PWM 100
o 0 0        # Stop
o -100 100   # Links rückwärts, rechts vorwärts
```

---

## Finale Checkliste

- [ ] Serielle Kommunikation funktioniert (test_firmware.py)
- [ ] TB6612 STBY Pin auf 3.3V oder GPIO HIGH
- [ ] VM (Motor Power) 6-12V angeschlossen
- [ ] GND gemeinsam verbunden
- [ ] Hardware auf richtige Pins verdrahtet (neu: GP0,4,5 + GP6,7,8)
- [ ] Motoren können sich frei drehen (nicht blockiert)
- [ ] Motor-Netzteil liefert genug Strom

---

## Empfohlene Vorgehensweise

1. **Test-Script ausführen:** `python3 test_firmware.py`
2. **STBY Pin prüfen:** Ist er auf 3.3V?
3. **Pins umverdrahten** auf GP0,4,5 für LEFT Motor
4. **Nochmal testen:** `python3 debug_pins.py`

Wenn immer noch nichts funktioniert, verwende die alte Pin-Konfiguration (pinout_legacy.h) bis die Hardware umverdrahtet ist.
