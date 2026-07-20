PORT=/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00

# 1) ARM/DISARM im Wechsel (5×)
for i in {1..5}; do
  printf "ARM\n" > "$PORT"; sleep 1
  printf "DISARM\n" > "$PORT"; sleep 1
done

# 2) UP 200 / DN 200 im Wechsel (5×)
for i in {1..5}; do
  printf "UP 200\n" > "$PORT"; sleep 0.5
  printf "DN 200\n" > "$PORT"; sleep 0.5
done

# 3) NF / NB im Wechsel (5×)
for i in {1..5}; do
  printf "NF\n" > "$PORT"; sleep 0.5
  printf "NB\n" > "$PORT"; sleep 0.5
done

# 4) 2–3× TEST_SHOT
for i in {1..3}; do
  printf "TEST_SHOT\n" > "$PORT"; sleep 1
done

# Abschließend sicherstellen:
printf "DISARM\n" > "$PORT"
