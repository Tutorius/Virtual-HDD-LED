# Virtual-HDD-LED
This is a work in progress, a short Python-script able to display a HDD-LED on a Gnome/Mate-Desktop

I have searched the internet to find a solution for this. On windows i had such a thing (years ago, am not using windows anymore).
You have a Laptop, and it does not have a HDD-LED. So you start something, and with AN SSD, you can't even hear the HDD working, you are totaly inaware if your started tool works or does not.

I have found a tool that can be used to let other LEDS blink when HDD works, it should work with CAPS-Lock-LED, Scroll-Lock. But it only works with Scroll-Lock, and most notebooks don't have this LED equipped.

I thought about an applet that stays in the notification-area or (will be much better) an applet that can be put wherever you like.

I am new to paython-programming, so i used "GROK" as A.I. to help me. I am absolutely no freind of ELon Musk, but i must admit, Grok gives the best results on programming-questions, vompared to Gemini or Chat-GPT.

Grok gave me a python-sourcetext. Its an applet that sits in the notification-area, but it has a window somewhere on the desktop. 
I added things to make it allways visible (despite you hide all) on every screen.

The python-scrips needs to be changed in source to alter HDD, timings, sizes.

Parameters (at top of Script)

HDDDEV="/dev/sda" -> choose your device here. There are other entries with a # at the beginning, you can write a # at start of the actual line and uncomment an other.

REFRESHTIME = 100 -> Time in ms, speed of scanning the harddisk

SHOWTIME = 0.3 -> Time the LED is "burning" after a harddisk-activity

SIZEX = 16 -> Size of the HDD_LED-area in pixels
SIZEY = 16

MOVX = 1900 -> Position of the LED in pixels, this is for a Full-HD-Screen
MOVY = 1040

You can start the script by calling

python 3 disk_activity_applet.py

in a terminal, or create a starter for it containng this command

Be free to work on this, perhaps you manage to get rid of the window and change the icon inside the applet.
dddv
