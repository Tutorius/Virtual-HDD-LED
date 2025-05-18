# Name of harddisk to show

# HDDDEV="/dev/sda"
# HDDEV="/dev/sdb"

HDDDEV="/dev/nvme0n1"

#HDDDEV="/dev/nvme0n2"
#HDDDEV="/dev/nvme1n1"
#HDDDEV="/dev/nvme1n2"

# schedule-time to look for activity in ms

REFRESHTIME=100

# On-time for LED after an activity

SHOWTIME=0.3

# Size of LED-area

SIZEX=16
SIZEY=16

# Position of LED-area on screen

MOVX = 1900
MOVY = 1040

# PI

PI=3.1415926

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3, GLib, Gdk
import psutil
import time
import os
import cairo

class DiskActivityApplet:
    def __init__(self, device_path=HDDDEV):
        # Device for scan of HDD-activity
        self.device_path = device_path
        self.last_io = psutil.disk_io_counters(perdisk=True).get(device_path.replace("/dev/", ""), None)
        if not self.last_io:
            print(f"Device {device_path} not found. Canceling...")
            Gtk.main_quit()
            return

        # Initialize AppIndicator
        self.indicator = AppIndicator3.Indicator.new(
            "disk-activity-applet",
            "drive-harddisk",
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Create drawing-are for LED
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(SIZEX, SIZEY)
        self.drawing_area.connect("draw", self.on_draw)
        self.indicator.set_icon_theme_path("/usr/share/icons")
        self.indicator.set_label("", "")

        # Create a menu
        menu = Gtk.Menu()
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)
        menu.show_all()
        self.indicator.set_menu(menu)

        # Container for drawing-area
        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.add(self.drawing_area)
        self.window.set_default_size(SIZEX, SIZEY)
        self.window.move(MOVX,MOVY)
        self.window.show_all()
        self.window.stick()
        self.window.set_keep_above(True)
        # self.window.set_skip_taskbar_hint(True)
        # self.window.set_skip_pager_hint(True)
        self.indicator.set_title("...")

        # Status der LED (aktiv/inaktiv)
        self.active = False
        self.last_activity_time = time.time()

        # Start Timer
        GLib.timeout_add(REFRESHTIME, self.update)

    def on_draw(self, widget, cr):
        # Draw a circle (LED)
        cr.set_source_rgb(0.2, 0.3, 0.2) if not self.active else cr.set_source_rgb(0, 1, 0)  # Grey (inactive) oder Green (active)
        cr.arc(SIZEX/2, SIZEY/2, SIZEX/2-2, 0, 2 * PI)  # Circle with Radius calculated of SIZEX
        cr.fill()

    def update(self):
        # Scan HDD-activity
        current_io = psutil.disk_io_counters(perdisk=True).get(self.device_path.replace("/dev/", ""), None)
        if not current_io:
            return True

        # Compare reading with last value
        if self.last_io:
            read_diff = current_io.read_bytes - self.last_io.read_bytes
            write_diff = current_io.write_bytes - self.last_io.write_bytes
            if read_diff > 0 or write_diff > 0:
                self.active = True
                self.last_activity_time = time.time()
            elif time.time() - self.last_activity_time > SHOWTIME:  # Nach 1 Sekunde Inaktivität
                self.active = False

        self.last_io = current_io

        # Refresh Drawing-area
        self.drawing_area.queue_draw()
        return True  # rerun timer

    def quit(self, widget):
        Gtk.main_quit()

    def run(self):
        Gtk.main()
    
        
        

if __name__ == "__main__":
    applet = DiskActivityApplet(device_path=HDDDEV)
    applet.run()
