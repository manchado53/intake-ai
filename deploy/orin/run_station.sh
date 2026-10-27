#!/bin/bash
# (Re)start the station on the Orin (clock in CDT) and show its screen fullscreen on the robot display.
#   ./run_station.sh            keep station.db (an open BEFORE survives a restart)
#   RESET=1 ./run_station.sh    forget all scans first (do this before the demo)
#   MEAL=dinner CAM=2 ./run_station.sh
cd ~/intake
[ -f station.pid ] && kill "$(cat station.pid)" 2>/dev/null; sleep 2
. venv/bin/activate
CAM=${CAM:-$(readlink -f /dev/v4l/by-id/*Orbbec*index0 | sed s,/dev/video,,)}  # Orbbec color, whatever its number
TZ=America/Chicago nohup python station/station.py --source "$CAM" --meal "${MEAL:-lunch}" --port 8080 \
  ${RESET:+--reset} > station.log 2>&1 &
echo $! > station.pid
sleep 8
curl -s -m 5 localhost:8080/state | head -c 160; echo
# snap Firefox/Chromium don't start on this Jetson; kiosk.py is a small WebKit window
if ! pgrep -f "python3 kiosk.py" >/dev/null; then
  DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
    WEBKIT_DISABLE_COMPOSITING_MODE=1 nohup python3 kiosk.py > /tmp/kiosk.log 2>&1 &
fi
