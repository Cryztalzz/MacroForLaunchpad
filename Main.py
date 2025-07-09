import rtmidi
import time
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF
import json
import os
import subprocess
import threading
import keyboard
import pyautogui
import re

class LaunchpadMK2:
    def __init__(self):
        self.midi_in = rtmidi.RtMidiIn()
        self.midi_out = rtmidi.RtMidiOut()
        self.setup_midi()
        self.macro_config = {}
        self.streamdeck_config = {}
        self.current_mode = "macro"  # Default mode
        
        self.config_dir = os.path.join(os.getenv('APPDATA'), 'Launchpad-Macro')
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        self.load_configs()
        self.last_press_time = {}
        self.highlight_duration = 150
        print("LaunchpadMK2 initialized")

    def setup_midi(self):
        print("Mencari Launchpad MK2...")
        input_found = False
        output_found = False

# Cari port input
        for i in range(self.midi_in.getPortCount()):
            port_name = self.midi_in.getPortName(i)
            print(f"Port input {i}: {port_name}")
            if "Launchpad MK2" in port_name:
                try:
                    self.midi_in.openPort(i)
                    print("Launchpad MK2 ditemukan di port input!")
                    input_found = True
                    break
                except Exception as e:
                    print(f"Error membuka port input: {str(e)}")

# Cari port output
        for i in range(self.midi_out.getPortCount()):
            port_name = self.midi_out.getPortName(i)
            print(f"Port output {i}: {port_name}")
            if "Launchpad MK2" in port_name:
                try:
                    self.midi_out.openPort(i)
                    print("Launchpad MK2 ditemukan di port output!")
                    output_found = True
                    break
                except Exception as e:
                    print(f"Error membuka port output: {str(e)}")

        if not input_found:
            print("Peringatan: Launchpad MK2 tidak ditemukan di port input!")
        if not output_found:
            print("Peringatan: Launchpad MK2 tidak ditemukan di port output!")

    def load_configs(self):
        try:
            macro_config_path = os.path.join(self.config_dir, 'macro_config.json')
            streamdeck_config_path = os.path.join(self.config_dir, 'streamdeck_config.json')
            
            if os.path.exists(macro_config_path):
                with open(macro_config_path, 'r') as f:
                    data = json.load(f)
                    self.macro_config = {tuple(map(int, k.split(','))): v for k, v in data.items()}
            if os.path.exists(streamdeck_config_path):
                with open(streamdeck_config_path, 'r') as f:
                    data = json.load(f)
                    self.streamdeck_config = {tuple(map(int, k.split(','))): v for k, v in data.items()}
        except Exception as e:
            print(f"Error loading configs: {str(e)}")

    def save_configs(self):
        macro_config_str = {f"{k[0]},{k[1]}": v for k, v in self.macro_config.items()}
        streamdeck_config_str = {f"{k[0]},{k[1]}": v for k, v in self.streamdeck_config.items()}
        try:
            macro_config_path = os.path.join(self.config_dir, 'macro_config.json')
            streamdeck_config_path = os.path.join(self.config_dir, 'streamdeck_config.json')
            
            with open(macro_config_path, 'w') as f:
                json.dump(macro_config_str, f, indent=4)
            with open(streamdeck_config_path, 'w') as f:
                json.dump(streamdeck_config_str, f, indent=4)
        except Exception as e:
            print(f"Error saving configs: {str(e)}")

# Mengatur warna tombol pada koordinat
    def set_button_color(self, x, y, r, g, b):
        note = self.xy_to_note(x, y)
        if note is not None:
            print(f"Mengatur warna untuk note {note} dengan RGB: {r},{g},{b}")
            velocity = r * 16 + g * 4 + b
            self.midi_out.sendMessage(rtmidi.MidiMessage.noteOn(0, note, velocity))

    def xy_to_note(self, x, y):
        # Grid utama
        if 0 <= x <= 7 and 0 <= y <= 7:
            y_flip = 7 - y
            return (y_flip + 1) * 10 + (x + 1)
        # Top row
        if y == -1 and 0 <= x <= 7:
            return 104 + x
        # Right column
        if x == 8 and 0 <= y <= 7:
            y_flip = 7 - y
            return 19 + y_flip * 10
        return None

    def handle_button_press(self, x, y):
        print(f"Tombol ditekan di koordinat: x={x}, y={y}")
        current_time = time.time() * 1000  # Konversi ke milidetik
        self.last_press_time[(x, y)] = current_time

# Cek jika tombol yang ditekan adalah tombol mode
        if y == 6 and x == 8:  # Tombol Solo (Macro Mode)
            self.switch_mode("macro")
            return
        elif y == 7 and x == 8:  # Tombol Record Arm (Streamdeck Mode)
            self.switch_mode("streamdeck")
            return

# Menangani tekanan tombol berdasarkan mode yang aktif
        if self.current_mode == "macro":
            print(f"Mode aktif: macro")
            if (x, y) in self.macro_config:
                print(f"Macro ditemukan untuk koordinat ({x},{y})")
                self.execute_macro(self.macro_config[(x, y)])
                self.set_button_color(x, y, 0, 3, 0)
            else:
                print(f"Tidak ada macro yang dikonfigurasi untuk koordinat ({x},{y})")
                self.set_button_color(x, y, 3, 3, 0)
        else:  # streamdeck mode
            print(f"Mode aktif: streamdeck")
            if (x, y) in self.streamdeck_config:
                print(f"Streamdeck action ditemukan untuk koordinat ({x},{y})")
                self.execute_streamdeck_action(self.streamdeck_config[(x, y)])
                self.set_button_color(x, y, 3, 0, 0)
            else:
                print(f"Tidak ada streamdeck action yang dikonfigurasi untuk koordinat ({x},{y})")
                self.set_button_color(x, y, 3, 3, 0)

# Set timer untuk mengembalikan warna setelah highlight_duration
        def reset_color():
            time.sleep(self.highlight_duration / 1000)  # Konversi ke detik
            if (x, y) in self.last_press_time and current_time == self.last_press_time[(x, y)]:
                if self.current_mode == "macro":
                    if (x, y) in self.macro_config:
                        self.set_button_color(x, y, 0, 3, 0)
                    else:
                        self.set_button_color(x, y, 0, 0, 0)
                else:
                    if (x, y) in self.streamdeck_config:
                        self.set_button_color(x, y, 3, 0, 0)
                    else:
                        self.set_button_color(x, y, 0, 0, 0)

        threading.Thread(target=reset_color, daemon=True).start()
    def execute_macro(self, macro_data):
        print("EKSEKUSI MACRO:", macro_data)
        action_type = macro_data.get("type", "")
        param = macro_data.get("param", "")
        
        if action_type == "Keyboard":
            # Format: "key1+key2+key3" atau "key1,key2,key3"
            if "+" in param:
                keys = param.split("+")
                keyboard.press_and_release("+".join(keys))
            elif "," in param:
                keys = param.split(",")
                for key in keys:
                    keyboard.press_and_release(key.strip())
            else:
                keyboard.press_and_release(param)
                
        elif action_type == "Mouse":
            # Format: "click" atau "x,y" atau "x,y,click"
            parts = param.split(",")
            if len(parts) == 1:
                if parts[0].lower() == "click":
                    pyautogui.click()
                elif parts[0].lower() == "rightclick":
                    pyautogui.rightClick()
                elif parts[0].lower() == "doubleclick":
                    pyautogui.doubleClick()
            elif len(parts) == 2:
                x, y = map(int, parts)
                pyautogui.moveTo(x, y)
            elif len(parts) == 3:
                x, y = map(int, parts[:2])
                action = parts[2].lower()
                pyautogui.moveTo(x, y)
                if action == "click":
                    pyautogui.click()
                elif action == "rightclick":
                    pyautogui.rightClick()
                elif action == "doubleclick":
                    pyautogui.doubleClick()
                    
        elif action_type == "Custom":
            subprocess.Popen(param, shell=True)
        else:
            subprocess.Popen(param, shell=True)

# Menjalankan action streamdeck yang telah dikonfigurasi
    def execute_streamdeck_action(self, action_data):
        try:
            action_type = action_data.get("type", "")
            param = action_data.get("param", "")
            
            if action_type == "Keyboard":
                # Format: "key1+key2+key3" atau "key1,key2,key3"
                if "+" in param:
                    keys = param.split("+")
                    keyboard.press_and_release("+".join(keys))
                elif "," in param:
                    keys = param.split(",")
                    for key in keys:
                        keyboard.press_and_release(key.strip())
                else:
                    keyboard.press_and_release(param)
                    
            elif action_type == "Mouse":
                # Format: "click" atau "x,y" atau "x,y,click"
                parts = param.split(",")
                if len(parts) == 1:
                    if parts[0].lower() == "click":
                        pyautogui.click()
                    elif parts[0].lower() == "rightclick":
                        pyautogui.rightClick()
                    elif parts[0].lower() == "doubleclick":
                        pyautogui.doubleClick()
                elif len(parts) == 2:
                    x, y = map(int, parts)
                    pyautogui.moveTo(x, y)
                elif len(parts) == 3:
                    x, y = map(int, parts[:2])
                    action = parts[2].lower()
                    pyautogui.moveTo(x, y)
                    if action == "click":
                        pyautogui.click()
                    elif action == "rightclick":
                        pyautogui.rightClick()
                    elif action == "doubleclick":
                        pyautogui.doubleClick()
                        
            elif action_type == "Custom":
                subprocess.Popen(param, shell=True)
                
        except Exception as e:
            print(f"Error executing streamdeck action: {str(e)}")
            print(f"Action data: {action_data}")

# Beralih antara mode makro dan streamdeck
    def switch_mode(self, mode):
        if mode in ["macro", "streamdeck"]:
            self.current_mode = mode
            self.update_display()

# Set warna permanen untuk tombol mode
    def update_display(self):
        self.set_button_color(8, 6, 0, 3, 0)
        self.set_button_color(8, 7, 3, 0, 0)

# Update warna tombol yang dikonfigurasi
        if self.current_mode == "macro":
            for (x, y), _ in self.macro_config.items():
                self.set_button_color(x, y, 0, 3, 0)
        else:
            for (x, y), _ in self.streamdeck_config.items():
                self.set_button_color(x, y, 3, 0, 0)

    def note_to_xy(self, note):
        print(f"Mengkonversi note {note} ke koordinat")
        if 11 <= note <= 88 and note % 10 != 0 and note % 10 <= 8:
            x = (note % 10) - 1
            y = (note // 10) - 1
            y = 7 - y
            print(f"Konversi grid: x={x}, y={y}")
            return (x, y)
        if 104 <= note <= 111:
            print(f"Konversi top row: x={note - 104}, y=-1")
            return (note - 104, -1)
        if note % 10 == 9 and 19 <= note <= 89:
            y = (note // 10) - 1
            y = 7 - y
            print(f"Konversi right column: x=8, y={y}")
            return (8, y)
        if 91 <= note <= 98:
            print(f"Konversi bottom row: x={note - 91}, y=-1")
            return (note - 91, -1)
        if 81 <= note <= 88:
            print(f"Konversi bottom row: x={note - 81}, y=-1")
            return (note - 81, -1)
        print(f"Note {note} tidak valid")
        return None

    def get_midi_message(self):
        try:
            msg = self.midi_in.getMessage()
            if msg:
                print(f"Raw MIDI message: {msg}")
                if msg.isNoteOn():
                    note = msg.getNoteNumber()
                    velocity = msg.getVelocity()
                    print(f"Note On: {note}, Velocity: {velocity}")
                    if velocity > 0:
                        return note
            return None
        except Exception as e:
            print(f"Error getting MIDI message: {str(e)}")
            return None

# Loop utama untuk menangani input
    def run(self):
        print("Memulai loop utama...")
        try:
            while True:
                note = self.get_midi_message()
                if note is not None:
                    btn = self.note_to_xy(note)
                    if btn is not None:
                        self.handle_button_press(*btn)
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("Program dihentikan oleh user")
        finally:
            print("Menutup port MIDI...")
            self.midi_in.closePort()
            self.midi_out.closePort()
            print("Port MIDI ditutup")

if __name__ == "__main__":
    launchpad = LaunchpadMK2()
    launchpad.run()
