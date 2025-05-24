# Festlegen der anzuzeigenden Festplatte

# HDDDEV="/dev/sda"
# HDDEV="/dev/sdb"
HDDDEV="/dev/nvme0n1"
#HDDDEV="/dev/nvme0n2"
#HDDDEV="/dev/nvme1n1"
#HDDDEV="/dev/nvme1n2"

# Zeitschleife (in ms), die nach Festplattenaktivität geschaut wird

REFRESHTIME=100

# Zeit, die die LED an bleibt

SHOWTIME=0.3


# Verschiebung des Fensters weg vom Rand

SHIFTX=50
SHIFTY=50
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

def get_screen_resolution():
    display = Gdk.Display.get_default()
    if not display:
        print("Kein Display gefunden.")
        return None, None
    # Iteriere über alle Monitore
    for i in range(display.get_n_monitors()):
        monitor = display.get_monitor(i)
        # Prüfen, ob dies der primäre Monitor ist
        if monitor.is_primary():
            geometry = monitor.get_geometry()
            width = geometry.width
            height = geometry.height
            return width, height
    # Wenn kein primärer Monitor gefunden wurde, einfach den ersten zurückgeben
    if display.get_n_monitors() > 0:
        monitor = display.get_monitor(0)
        geometry = monitor.get_geometry()
        width = geometry.width
        height = geometry.height
        return width, height
        
    return None, None


class DiskActivityApplet:


    def __init__(self, device_path=HDDDEV):
        self.position=3
        self.oldposition=self.position
        self.size=16
        self.width, self.height = get_screen_resolution()
        self.LED_Color="green"
        
        self.movx=xpos(self,1)
        self.movy=ypos(self,1)
        
        # Gerät für die Überwachung der Festplattenaktivität
        self.device_path = device_path
        self.last_io = psutil.disk_io_counters(perdisk=True).get(device_path.replace("/dev/", ""), None)
        if not self.last_io:
            print(f"Gerät {device_path} nicht gefunden. Beende...")
            Gtk.main_quit()
            return

        # Initialisiere AppIndicator
        self.indicator = AppIndicator3.Indicator.new(
            "HDD_LED",
            "HDD_LED",
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )

        self.indicator.set_icon_full("HDD-LED", "Zeigt eine virtuelle HDD-LED auf dem Desktop an")
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        # Erstelle ein Zeichenfläche für die LED
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(self.size,self.size)
        self.drawing_area.connect("draw", self.on_draw)
        self.indicator.set_icon_theme_path("/usr/share/icons")
        self.indicator.set_label("", "")

        # Erstelle ein Menü
        menu = Gtk.Menu()
        hide_item = Gtk.MenuItem(label="Verstecken")
        hide_item.connect("activate", self.hide)
        menu.append(hide_item)
        position_item=Gtk.MenuItem(label="Position")
        position_item.connect("activate",self.position_dialog)
        menu.append(position_item)
        dialog_item=Gtk.MenuItem(label="LED-Farbe")
        dialog_item.connect("activate",self.color_dialog)
        menu.append(dialog_item)
        size_item=Gtk.MenuItem(label="Größe")
        size_item.connect("activate",self.size_dialog)
        menu.append(size_item)
        quit_item = Gtk.MenuItem(label="Beenden")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)
        
        menu.show_all()
        self.indicator.set_menu(menu)

        # Container für die Zeichenfläche
        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.add(self.drawing_area)
        self.window.set_default_size(self.size,self.size)

                
        self.window.move(self.movx,self.movy)
        self.window.show_all()
        self.window.stick()
        self.window.set_keep_above(True)
        self.is_hidden = False
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.indicator.set_title("...")

        # Status der LED (aktiv/inaktiv)
        self.active = False
        self.last_activity_time = time.time()

        # Starte Timer für regelmäßige Aktualisierungen (alle 500ms)
        GLib.timeout_add(REFRESHTIME, self.update)

    def on_draw(self, widget, cr):
        # Zeichne einen Kreis (LED)
        match self.LED_Color:
            case "green":
                cr.set_source_rgb(0.0, 0.3, 0.0) if not self.active else cr.set_source_rgb(0, 1, 0)  # Grau (inaktiv) oder Grün (aktiv)
            case "red":
                cr.set_source_rgb(0.3, 0.0, 0.0) if not self.active else cr.set_source_rgb(1, 0, 0)  # Grau (inaktiv) oder Rot (aktiv)
            case "blue":
                cr.set_source_rgb(0.0, 0.0, 0.3) if not self.active else cr.set_source_rgb(0, 0, 1)  # Grau (inaktiv) oder Blau (aktiv)
        cr.arc(self.size/2, self.size/2, self.size/2-2, 0, 2 * PI)  # Kreis mit Radius 6
        cr.fill()

    def update(self):
        # Überwache Festplattenaktivität
        if self.oldposition!=self.position:
            self.window.move(self.movx,self.movy)
            self.window.show_all()
            self.oldposition=self.position
        
        current_io = psutil.disk_io_counters(perdisk=True).get(self.device_path.replace("/dev/", ""), None)
        if not current_io:
            return True

        # Vergleiche Lese-/Schreibzähler mit dem letzten Stand
        if self.last_io:
            read_diff = current_io.read_bytes - self.last_io.read_bytes
            write_diff = current_io.write_bytes - self.last_io.write_bytes
            if read_diff > 0 or write_diff > 0:
                self.active = True
                self.last_activity_time = time.time()
            elif time.time() - self.last_activity_time > SHOWTIME:  # Nach 1 Sekunde Inaktivität
                self.active = False

        self.last_io = current_io

        # Aktualisiere die Zeichenfläche
        self.drawing_area.queue_draw()
        return True  # Fortfahren mit dem Timer

    def quit(self, widget):
        Gtk.main_quit()

    def run(self):
        
        Gtk.main()
    
    def hide(self,widget):
        if self.is_hidden:
            self.window.show_all()
            self.is_hidden=False
            
        else:
            self.window.hide()
            self.is_hidden=True
  
    def color_dialog(self, widget):
        dialog = Gtk.Dialog(title="LED-Farbe", parent=self.window,flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)
        dialog.move(self.width/2,self.height/2)

        dialog.add_button("_ABBRUCH", Gtk.ResponseType.CANCEL)
        dialog.add_button("_OK", Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()

        label = Gtk.Label(label="Bitte LED-Farbe wählen:")
        content_area.pack_start(label, True, True, 0)

        # Radio-Buttons
        radio_group = []
        options = ["LED GRÜN", "LED ROT", "LED BLAU"]
        selected_option=None
        match self.LED_Color:
            case "green":
                nr=0
            case "red":
                nr=1
            case "blue":
                nr=2
        for i, option_text in enumerate(options):
            if i == 0:
                radio_button = Gtk.RadioButton.new_with_label_from_widget(None, option_text)
            else:
                radio_button = Gtk.RadioButton.new_with_label_from_widget(radio_group[0], option_text)
            
            if i==nr:
                radio_button.set_active(True)
            radio_group.append(radio_button)
            content_area.pack_start(radio_button, True, True, 0)


        dialog.show_all()

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            for i, radio_button in enumerate(radio_group):
                if radio_button.get_active():
                    selected_option = options[i]
                    break
            match selected_option:
                case "LED GRÜN":
                    self.LED_Color="green"
                case "LED ROT":
                    self.LED_Color="red"
                case "LED BLAU":
                    self.LED_Color="blue"
            # print(f"Ausgewählte Option: {selected_option}")
        # elif response == Gtk.ResponseType.CANCEL:
            # print("Auswahl abgebrochen.")

        dialog.destroy()
        
    def size_dialog(self, widget):
        dialog = Gtk.Dialog(title="LED-Größe", parent=self.window,flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)
        dialog.move(self.width/2,self.height/2)

        dialog.add_button("_ABBRUCH", Gtk.ResponseType.CANCEL)
        dialog.add_button("_OK", Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()

        label = Gtk.Label(label="Bitte LED-Größe wählen:")
        content_area.pack_start(label, True, True, 0)

        # Radio-Buttons
        radio_group = []
        options = ["8 Pixel", "16 Pixel", "20 Pixel", "24 Pixel", "28 Pixel", "32 Pixel", "40 Pixel", "48 Pixel", "64 Pixel"]
        selected_option=None
        match self.size:
            case 8:
                nr=0
            case 16:
                nr=1
            case 20:
                nr=2
            case 24:
                nr=3
            case 28:
                nr=4
            case 32:
                nr=5
            case 40:
                nr=6
            case 48:
                nr=7
            case 64:
                nr=8
        for i, option_text in enumerate(options):
            if i == 0:
                radio_button = Gtk.RadioButton.new_with_label_from_widget(None, option_text)
            else:
                radio_button = Gtk.RadioButton.new_with_label_from_widget(radio_group[0], option_text)
            
            if i==nr:
                radio_button.set_active(True)
            radio_group.append(radio_button)
            content_area.pack_start(radio_button, True, True, 0)


        dialog.show_all()

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            for i, radio_button in enumerate(radio_group):
                if radio_button.get_active():
                    selected_option = options[i]
                    break
            match selected_option:
                case "8 Pixel":
                    self.size=8
                case "16 Pixel":
                    self.size=16
                case "20 Pixel":
                    self.size=20
                case "24 Pixel":
                    self.size=24
                case "28 Pixel":
                    self.size=28
                case "32 Pixel":
                    self.size=32
                case "40 Pixel":
                    self.size=40
                case "48 Pixel":
                    self.size=48
                case "64 Pixel":
                    self.size=64
                
            match self.position:
                case "7->":
                    self.position=7
                    self.movx=xpos(self,-1)
                    self.movy=ypos(self,-1)
                case "8->":
                    self.position=8
                    self.movx=xpos(self,0)
                    self.movy=ypos(self,-1)
                case "9->":
                    self.position=9
                    self.movx=xpos(self,1)
                    self.movy=ypos(self,-1)
                case "4->":
                    self.position=4
                    self.movx=xpos(self,-1)
                    self.movy=ypos(self,0)
                case "5->":
                    self.position=5
                    self.movx=xpos(self,0)
                    self.movy=ypos(self,0)
                case "6->":
                    self.position=6
                    self.movx=xpos(self,1)
                    self.movy=ypos(self,0)
                case "1->":
                    self.position=1
                    self.movx=xpos(self,-1)
                    self.movy=ypos(self,1)
                case "2->":
                    self.position=2
                    self.movx=xpos(self,0)
                    self.movy=ypos(self,1)
                case "3->":
                    self.position=3
                    self.movx=xpos(self,1)
                    self.movy=xpos(self,1)
        
        self.drawing_area.set_size_request(self.size,self.size)
        self.window.set_default_size(self.size,self.size)
        self.window.move(self.movx,self.movy)

        dialog.destroy()


    def position_dialog(self,widget):
        dialog = Gtk.Dialog(title="Position", parent=self.window,flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)
        dialog.move(self.width/2,self.height/2)
        dialog.add_button("_ABBRUCH", Gtk.ResponseType.CANCEL)
        dialog.add_button("_OK", Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        grid=Gtk.Grid()
        content_area.add(grid)

        label = Gtk.Label(label="Bitte Position (Zehner-Tastenfeld) wählen:")
        content_area.pack_start(label, True, True, 0)

        # Radio-Buttons
        radio_group = []
        options = ["7->", "8->", "9->", "4->", "5->", "6->", "1->", "2->", "3->" ]
        selected_option=None

        row=0
        column=0
        for i, option_text in enumerate(options):
            if i == 0:
                radio_button = Gtk.RadioButton.new_with_label_from_widget(None, option_text)
            else:
                radio_button = Gtk.RadioButton.new_with_label_from_widget(radio_group[0], option_text)
            
            nr=option_text
            grid.attach(radio_button,column,row,1,1)
            radio_group.append(radio_button)
            # content_area.pack_start(radio_button, True, True, 0)
            column+=1
            if column>2:
                column=0
                row+=1
            match i:
                case 0:
                    nr=7
                case 1:
                    nr=8
                case 2:
                    nr=9
                case 3:
                    nr=4
                case 4:
                    nr=5
                case 5:
                    nr=6
                case 6:
                    nr=1
                case 7:
                    nr=2
                case 8:
                    nr=3
                    
            if nr==self.position:
                radio_button.set_active(True)

        dialog.show_all()

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            for i, radio_button in enumerate(radio_group):
                if radio_button.get_active():
                    selected_option = options[i]
                    break
            match selected_option:
                case "7->":
                    self.position=7
                    self.movx=xpos(self,-1)
                    self.movy=ypos(self,-1)
                case "8->":
                    self.position=8
                    self.movx=xpos(self,0)
                    self.movy=ypos(self,-1)
                case "9->":
                    self.position=9
                    self.movx=xpos(self,1)
                    self.movy=ypos(self,-1)
                case "4->":
                    self.position=4
                    self.movx=xpos(self,-1)
                    self.movy=ypos(self,0)
                case "5->":
                    self.position=5
                    self.movx=xpos(self,0)
                    self.movy=ypos(self,0)
                case "6->":
                    self.position=6
                    self.movx=xpos(self,1)
                    self.movy=ypos(self,0)
                case "1->":
                    self.position=1
                    self.movx=xpos(self,-1)
                    self.movy=ypos(self,1)
                case "2->":
                    self.position=2
                    self.movx=xpos(self,0)
                    self.movy=ypos(self,1)
                case "3->":
                    self.position=3
                    self.movx=xpos(self,1)
                    self.movy=xpos(self,1)

        self.window.move(self.movx,self.movy)
                    
        dialog.destroy()

def xpos(self,pos):
    match(pos):
        case -1:
            return (SHIFTX-self.size/2)
        case 0:
            return (self.width/2)
        case 1:
            return(self.width-SHIFTX-self.size/2)

def ypos(self,pos):
    match(pos):
        case -1:
            return (SHIFTY-self.size)
        case 0:
            return (self.height/2)
        case 1:
            return (self.height-SHIFTY-self.size/2)

if __name__ == "__main__":
    # Ersetze "/dev/sda" durch das gewünschte Gerät, z. B. "/dev/nvme0n1"
    applet = DiskActivityApplet(device_path=HDDDEV)
    # applet.set_tooltip_text("dslfkhsdfhsf")
    applet.run()
