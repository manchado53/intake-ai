"""Fullscreen station page on the robot screen (the snap browsers do not start on this Jetson).

    DISPLAY=:0 python3 kiosk.py [url]      (Esc quits)
"""
import sys

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.0")
from gi.repository import Gdk, Gtk, WebKit2  # noqa: E402

win = Gtk.Window(title="Intake.ai station")
view = WebKit2.WebView()
view.load_uri(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080")
win.add(view)
win.connect("destroy", Gtk.main_quit)
win.connect("key-press-event", lambda w, e: e.keyval == Gdk.KEY_Escape and Gtk.main_quit())
win.fullscreen()
win.show_all()
Gtk.main()
