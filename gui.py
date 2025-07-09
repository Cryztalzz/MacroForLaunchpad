import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from Main import LaunchpadMK2
import threading
import time
import rtmidi
import pystray
from PIL import Image, ImageDraw
import sys

class LaunchpadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Launchpad MK2 Controller")
        
        window_width = 1200
        window_height = 900

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)

        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.setup_tray_icon()
        print("Initializing LaunchpadMK2...")
        self.launchpad = LaunchpadMK2()
        print("LaunchpadMK2 initialized")
        
        self.current_mode = tk.StringVar(value="macro")
        self.selected_button = None
        self.button_refs = {}
        self.highlighted_button = None
        
        self.setup_gui()
        self.load_configs()

        # Thread untuk polling MIDI Launchpad
        self.running = True
        print("Starting MIDI polling thread...")
        self.poll_thread = threading.Thread(target=self.poll_launchpad, daemon=True)
        self.poll_thread.start()
        print("MIDI polling thread started")

    def setup_tray_icon(self):
        try:
            icon_path = os.path.join('assets', 'apiunggun1.png')
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
            else:
                image = Image.new('RGB', (64, 64), color='black')
                dc = ImageDraw.Draw(image)
                dc.rectangle([16, 16, 48, 48], fill='green')
                image.save(icon_path)
        except Exception as e:
            print(f"Error loading icon: {e}")
            image = Image.new('RGB', (64, 64), color='black')
            dc = ImageDraw.Draw(image)
            dc.rectangle([16, 16, 48, 48], fill='green')
        
# Buat menu untuk tray icon
        menu = (
            pystray.MenuItem('Tampilkan', self.show_window),
            pystray.MenuItem('Keluar', self.quit_application)
        )
# Buat tray icon
        self.icon = pystray.Icon("launchpad", image, "Launchpad MK2 Controller", menu)
# Bind event minimize
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        
# Start tray icon di thread yang lain
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self):
        self.root.deiconify()
        self.root.state('normal')
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        self.root.withdraw()
        self.icon.notify('Aplikasi masih berjalan di background', 'Launchpad MK2 Controller')
        if not self.icon.visible:
            self.icon.visible = True

    def quit_application(self):
        print("Closing application...")
        self.running = False
        if hasattr(self, 'launchpad'):
            print("Closing MIDI ports...")
            self.launchpad.midi_in.closePort()
            self.launchpad.midi_out.closePort()
            print("MIDI ports closed")
        self.icon.stop()
        self.root.destroy()
        print("Application closed")

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        mode_frame = ttk.LabelFrame(main_frame, text="Mode", padding="5")
        mode_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Radiobutton(mode_frame, text="Macro Mode", variable=self.current_mode, value="macro", command=self.switch_mode).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(mode_frame, text="Streamdeck Mode", variable=self.current_mode, value="streamdeck", command=self.switch_mode).grid(row=0, column=1, padx=5)

# Canvas untuk grid Launchpad
        self.canvas = tk.Canvas(main_frame, width=650, height=650, bg="#222")
        self.canvas.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.draw_launchpad_canvas()
        self.canvas.bind('<Button-1>', self.canvas_click)

# Label info tombol terakhir
        self.last_button_var = tk.StringVar()
        self.last_button_var.set("Tombol terakhir: -")
        self.last_button_label = ttk.Label(main_frame, textvariable=self.last_button_var, font=("Arial", 11, "bold"))
        self.last_button_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0,10))

# Panel konfigurasi
        config_frame = ttk.LabelFrame(main_frame, text="Konfigurasi", padding="5")
        config_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
# Nama Action
        ttk.Label(config_frame, text="Nama Aksi:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.action_name = ttk.Entry(config_frame)
        self.action_name.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
# Tipe Action
        ttk.Label(config_frame, text="Tipe Aksi:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.action_type = ttk.Combobox(config_frame, values=["Keyboard", "Mouse", "Custom"])
        self.action_type.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        self.action_type.bind('<<ComboboxSelected>>', self.on_action_type_change)
        
# Parameter
        ttk.Label(config_frame, text="Parameter:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.action_param = ttk.Entry(config_frame)
        self.action_param.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
# Label bantuan parameter
        self.param_help_var = tk.StringVar()
        self.param_help = ttk.Label(config_frame, textvariable=self.param_help_var, wraplength=200)
        self.param_help.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
# Tombol Action
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Simpan", command=self.save_config).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Hapus", command=self.delete_config).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Test", command=self.test_action).grid(row=0, column=2, padx=5)
        
# Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Siap")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E))

    def draw_launchpad_canvas(self):
        self.button_refs.clear()
        pad = 15
        size = 44
        circle = 28
        offset = 35
        offset_y = 60
# Top row (lingkaran)
        for x in range(8):
            cx = offset + x * (size + pad) + size // 2
            cy = offset - size // 2 - pad + offset_y
            oval = self.canvas.create_oval(cx - circle//2, cy - circle//2, cx + circle//2, cy + circle//2, fill="#444", outline="#888", width=2)
            self.button_refs[(x, -1)] = oval
            self.canvas.create_text(cx, cy, text=self.get_top_label(x), fill="white", font=("Arial", 10, "bold"))
# Main grid (kotak)
        for y in range(8):
            for x in range(8):
                x1 = offset + x * (size + pad)
                y1 = offset + y * (size + pad) + offset_y
                rect = self.canvas.create_rectangle(x1, y1, x1 + size, y1 + size, fill="#eee", outline="#888", width=2)
                self.button_refs[(x, y)] = rect
# Right column (lingkaran)
        for y in range(8):
            cx = offset + 8 * (size + pad) + size // 2 + pad
            cy = offset + y * (size + pad) + size // 2 + offset_y
            oval = self.canvas.create_oval(cx - circle//2, cy - circle//2, cx + circle//2, cy + circle//2, fill="#444", outline="#888", width=2)
            self.button_refs[(8, y)] = oval
            self.canvas.create_text(cx, cy, text=self.get_right_label(y), fill="white", font=("Arial", 10, "bold"))
        self.update_button_colors()

    def get_top_label(self, x):
        labels = ["◀", "▲", "▼", "▶", "Session", "User1", "User2", "Mixer"]
        return labels[x] if x < len(labels) else ""

    def get_right_label(self, y):
        labels = ["Volume", "Pan", "Send A", "Send B", "Stop", "Mute", "Solo", "Record Arm"]
        return labels[y] if y < len(labels) else ""

    def canvas_click(self, event):
        for key, shape in self.button_refs.items():
            coords = self.canvas.coords(shape)
            if len(coords) == 4:
                x1, y1, x2, y2 = coords
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self.button_click(*key)
                    break

    def update_button_colors(self):
        # Main grid
        for (x, y), shape in self.button_refs.items():
            if y == 6 and x == 8:
                self.canvas.itemconfig(shape, fill="#0f0")
                continue
            elif y == 7 and x == 8:
                self.canvas.itemconfig(shape, fill="#f00")
                continue

            mapped = False
            if self.current_mode.get() == "macro":
                mapped = (x, y) in self.launchpad.macro_config
            else:
                mapped = (x, y) in self.launchpad.streamdeck_config
            if mapped:
                if self.current_mode.get() == "macro":
                    self.canvas.itemconfig(shape, fill="#0f0")
                else:
                    self.canvas.itemconfig(shape, fill="#f00")
            else:
                if (x, y) == self.highlighted_button:
                    self.canvas.itemconfig(shape, fill="#ff0")
                elif y == -1 or x == 8:
                    self.canvas.itemconfig(shape, fill="#444")
                else:
                    self.canvas.itemconfig(shape, fill="#eee")

    def save_configs(self):
        # Konversi key tuple ke string
        macro_config_str = {f"{k[0]},{k[1]}": v for k, v in self.launchpad.macro_config.items()}
        streamdeck_config_str = {f"{k[0]},{k[1]}": v for k, v in self.launchpad.streamdeck_config.items()}
        try:
            macro_config_path = os.path.join(self.launchpad.config_dir, 'macro_config.json')
            streamdeck_config_path = os.path.join(self.launchpad.config_dir, 'streamdeck_config.json')
            
            with open(macro_config_path, 'w') as f:
                json.dump(macro_config_str, f, indent=4)
            with open(streamdeck_config_path, 'w') as f:
                json.dump(streamdeck_config_str, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan konfigurasi: {str(e)}")

    def load_configs(self):
        try:
            macro_config_path = os.path.join(self.launchpad.config_dir, 'macro_config.json')
            streamdeck_config_path = os.path.join(self.launchpad.config_dir, 'streamdeck_config.json')
            
            if os.path.exists(macro_config_path):
                with open(macro_config_path, 'r') as f:
                    data = json.load(f)
                    self.launchpad.macro_config = {tuple(map(int, k.split(','))): v for k, v in data.items()}
            if os.path.exists(streamdeck_config_path):
                with open(streamdeck_config_path, 'r') as f:
                    data = json.load(f)
                    self.launchpad.streamdeck_config = {tuple(map(int, k.split(','))): v for k, v in data.items()}
            self.update_button_colors()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat konfigurasi: {str(e)}")

    def save_config(self):
        if not self.selected_button:
            messagebox.showwarning("Peringatan", "Pilih tombol terlebih dahulu!")
            return
        config = {
            "name": self.action_name.get(),
            "type": self.action_type.get(),
            "param": self.action_param.get()
        }
        if self.current_mode.get() == "macro":
            self.launchpad.macro_config[self.selected_button] = config
        else:
            self.launchpad.streamdeck_config[self.selected_button] = config
        self.launchpad.save_configs()
        self.update_button_colors()
        self.status_var.set(f"Konfigurasi disimpan untuk tombol {self.selected_button}")

    def delete_config(self):
        if not self.selected_button:
            messagebox.showwarning("Peringatan", "Pilih tombol terlebih dahulu!")
            return
        if self.current_mode.get() == "macro":
            if self.selected_button in self.launchpad.macro_config:
                del self.launchpad.macro_config[self.selected_button]
        else:
            if self.selected_button in self.launchpad.streamdeck_config:
                del self.launchpad.streamdeck_config[self.selected_button]
        self.launchpad.save_configs()
        self.update_button_colors()
        self.clear_inputs()
        self.status_var.set(f"Konfigurasi dihapus untuk tombol {self.selected_button}")

    def button_click(self, x, y):
        print(f"\n=== Button Click: x={x}, y={y} ===")
        if y == 6 and x == 8:  # Tombol Solo
            print("Mengaktifkan mode Macro")
            self.current_mode.set("macro")
            self.switch_mode()
            return
        elif y == 7 and x == 8:  # Tombol Record Arm
            print("Mengaktifkan mode Streamdeck")
            self.current_mode.set("streamdeck")
            self.switch_mode()
            return

        self.selected_button = (x, y)
        self.update_button_colors()
        self.highlight_button_gui((x, y))
        self.highlight_button_launchpad((x, y))
        
        if self.current_mode.get() == "macro":
            if (x, y) in self.launchpad.macro_config:
                print(f"Menjalankan macro untuk tombol ({x}, {y})")
                self.launchpad.execute_macro(self.launchpad.macro_config[(x, y)])
        else:
            if (x, y) in self.launchpad.streamdeck_config:
                print(f"Menjalankan streamdeck action untuk tombol ({x}, {y})")
                self.launchpad.execute_streamdeck_action(self.launchpad.streamdeck_config[(x, y)])

        if self.current_mode.get() == "macro":
            config = self.launchpad.macro_config.get((x, y), {})
        else:
            config = self.launchpad.streamdeck_config.get((x, y), {})
        self.action_name.delete(0, tk.END)
        self.action_name.insert(0, config.get("name", ""))
        self.action_type.set(config.get("type", ""))
        self.action_param.delete(0, tk.END)
        self.action_param.insert(0, config.get("param", ""))
        self.last_button_var.set(f"Tombol terakhir: {(x, y)}")

    def switch_mode(self):
        self.clear_inputs()
        self.update_button_colors()
        self.launchpad.switch_mode(self.current_mode.get())
        self.status_var.set(f"Mode diubah ke {self.current_mode.get()}")

    def clear_inputs(self):
        self.action_name.delete(0, tk.END)
        self.action_type.set("")
        self.action_param.delete(0, tk.END)
        self.selected_button = None

    def test_action(self):
        if not self.selected_button:
            messagebox.showwarning("Peringatan", "Pilih tombol terlebih dahulu!")
            return
        if self.current_mode.get() == "macro":
            if self.selected_button in self.launchpad.macro_config:
                self.launchpad.execute_macro(self.launchpad.macro_config[self.selected_button])
        else:
            if self.selected_button in self.launchpad.streamdeck_config:
                self.launchpad.execute_streamdeck_action(self.launchpad.streamdeck_config[self.selected_button])

    def note_to_xy(self, note):
        # Untuk grid utama (note 11-88, kelipatan 10 + 1..8)
        if 11 <= note <= 88 and note % 10 != 0 and note % 10 <= 8:
            x = (note % 10) - 1
            y = (note // 10) - 1
            y = 7 - y  # flip vertikal agar sesuai GUI
            return (x, y)
        # Top row (note 104-111)
        if 104 <= note <= 111:
            return (note - 104, -1)
        # Right column (note 19, 29, ..., 89)
        if note % 10 == 9 and 19 <= note <= 89:
            y = (note // 10) - 1
            y = 7 - y  # flip vertikal agar sesuai GUI
            return (8, y)
        # Top row (note 91-98)
        if 91 <= note <= 98:
            return (note - 91, -1)
        # Top row (note 81-88)
        if 81 <= note <= 88:
            return (note - 81, -1)
        return None

    def xy_to_note(self, x, y):
        # Main grid
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

    def poll_launchpad(self):
        print("MIDI polling thread started")
        while self.running:
            try:
                note = self.launchpad.get_midi_message()
                if note is not None:
                    btn = self.note_to_xy(note)
                    if btn is not None:
                        print(f"Button pressed: {btn}")
                        self.root.after(0, self.highlight_button_gui, btn)
                        self.root.after(0, self.highlight_button_launchpad, btn)
                        self.root.after(0, self.button_click, *btn)
            except Exception as e:
                print(f"Error in poll_launchpad: {str(e)}")
                import traceback
                traceback.print_exc()
            time.sleep(0.01)

    def highlight_button_gui(self, btn):
        self.highlighted_button = btn
        self.update_button_colors()
        mapped = False
        if self.current_mode.get() == "macro":
            mapped = btn in self.launchpad.macro_config
        else:
            mapped = btn in self.launchpad.streamdeck_config
        if not mapped:
            shape = self.button_refs.get(btn)
            if shape:
                self.canvas.itemconfig(shape, fill="#ff0")
        self.last_button_var.set(f"Tombol terakhir: {btn}")
        self.root.after(150, self.clear_highlight)

    def clear_highlight(self):
        self.highlighted_button = None
        self.update_button_colors()

    def highlight_button_launchpad(self, btn):
        if hasattr(self, 'last_highlighted_lp') and self.last_highlighted_lp:
            x, y = self.last_highlighted_lp
            mapped = False
            if self.current_mode.get() == "macro":
                mapped = (x, y) in self.launchpad.macro_config
            else:
                mapped = (x, y) in self.launchpad.streamdeck_config
            note = self.xy_to_note(x, y)
            if note is not None:
                if mapped:
                    self.launchpad.midi_out.sendMessage(rtmidi.MidiMessage.noteOn(0, note, 0x3C))
                else:
                    self.launchpad.midi_out.sendMessage(rtmidi.MidiMessage.noteOn(0, note, 0x0))
        self.last_highlighted_lp = btn
        x, y = btn
        mapped = False
        if self.current_mode.get() == "macro":
            mapped = (x, y) in self.launchpad.macro_config
        else:
            mapped = (x, y) in self.launchpad.streamdeck_config
        note = self.xy_to_note(x, y)
        if note is not None:
            if mapped:
                self.launchpad.midi_out.sendMessage(rtmidi.MidiMessage.noteOn(0, note, 0x3C))
            else:
                self.launchpad.midi_out.sendMessage(rtmidi.MidiMessage.noteOn(0, note, 0x7C))
            if not mapped:
                self.root.after(150, lambda: self.clear_highlight_launchpad(btn))

    def clear_highlight_launchpad(self, btn):
        x, y = btn
        mapped = False
        if self.current_mode.get() == "macro":
            mapped = (x, y) in self.launchpad.macro_config
        else:
            mapped = (x, y) in self.launchpad.streamdeck_config
        note = self.xy_to_note(x, y)
        if note is not None:
            if mapped:
                self.launchpad.midi_out.sendMessage(rtmidi.MidiMessage.noteOn(0, note, 0x3C))
            else:
                self.launchpad.midi_out.sendMessage(rtmidi.MidiMessage.noteOn(0, note, 0x0))

    def on_close(self):
        self.hide_window()
        return "break"

    def on_canvas_resize(self, event):
        self.draw_launchpad_canvas()

    def on_action_type_change(self, event=None):
        action_type = self.action_type.get()
        if action_type == "Keyboard":
            self.param_help_var.set("Format: 'key1+key2' untuk kombinasi tombol\nContoh: 'ctrl+c', 'alt+tab', 'shift+a'")
        elif action_type == "Mouse":
            self.param_help_var.set("Format:\n- 'click' untuk klik kiri\n- 'rightclick' untuk klik kanan\n- 'doubleclick' untuk klik ganda\n- 'x,y' untuk pindah kursor\n- 'x,y,click' untuk pindah dan klik")
        elif action_type == "Custom":
            self.param_help_var.set("Masukkan perintah yang akan dijalankan")
        else:
            self.param_help_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = LaunchpadGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop() 