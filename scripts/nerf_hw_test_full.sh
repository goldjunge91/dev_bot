#!/usr/bin/env bash
# Nerf hardware test script (full)
# Adjust PORT if needed
PORT="/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00"
SERIAL_LOG="nerf_serial.log"

set -euo pipefail

if [ ! -e "$PORT" ]; then
  echo "ERROR: serial port $PORT does not exist"
  exit 2
fi

echo "Logging serial output to $SERIAL_LOG (background)"
# Log serial output in background
cat "$PORT" |& tee "$SERIAL_LOG" &
SERIAL_PID=$!

echo "Starting test sequence (will send commands to $PORT)."

echo "== ARM/DISARM x5 =="
for i in {1..5}; do
  printf "ARM\n" > "$PORT"
  sleep 1
  printf "DISARM\n" > "$PORT"
  sleep 1
done

sleep 1

echo "== UP 200 / DN 200 x5 =="
for i in {1..5}; do
  printf "UP 200\n" > "$PORT"
  sleep 0.6
  printf "DN 200\n" > "$PORT"
  sleep 0.6
done

sleep 1

echo "== NF / NB x5 =="
for i in {1..5}; do
  printf "NF\n" > "$PORT"
  sleep 0.5
  printf "NB\n" > "$PORT"
  sleep 0.5
done

sleep 1

echo "== TEST_SHOT x3 =="
for i in {1..3}; do
  printf "TEST_SHOT\n" > "$PORT"
  sleep 1.5
done

# Ensure DISARM at end
printf "DISARM\n" > "$PORT"

echo "Test sequence complete. Waiting 1s and then stopping serial log."
sleep 1
kill "$SERIAL_PID" 2>/dev/null || true

echo "Logs: $SERIAL_LOG"
exit 0
