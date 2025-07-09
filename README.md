# Launchpad-Macro

> **Note: This project is still under development. Features and documentation may change at any time.**

## Description
Launchpad-Macro is an application to turn your Launchpad MK2 device into a multifunctional macro pad for Windows. With this app, every button on the Launchpad can be configured to run keyboard macros, mouse actions, or launch specific applications, similar to a Stream Deck.

This application provides a graphical user interface (GUI) based on Tkinter to make it easy to configure macros and actions for each button.

## Main Features
- Automatic detection of Launchpad MK2 via MIDI
- Macro Mode (keyboard shortcuts, mouse actions, custom commands)
- Streamdeck Mode (special actions, can be extended)
- Button configuration via drag & click GUI
- Save and load macro/streamdeck configurations
- Tray icon for quick access
- Automatic installer for Windows

## Screenshot

## Installation
### Prerequisites
- Windows 10/11
- Launchpad MK2
- Python 3.10+ (venv recommended)

### Manual Installation
1. Clone this repo and navigate to the project folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python gui.py
   ```

### Build/Installer Installation
1. Run `create_installer.bat` as Administrator.
2. Follow the on-screen instructions to create the executable and shortcuts.

## Dependencies
- rtmidi
- python-rtmidi
- keyboard
- pyautogui
- pystray
- Pillow
- pywin32
- winshell
- pyinstaller (for build)

## Example Macro Configuration
File `macro_config.json`:
```json
{
    "0,7": {
        "name": "notepad",
        "type": "Custom",
        "param": "notepad.exe"
    },
    "0,0": {
        "name": "Riot",
        "type": "Custom",
        "param": "\"C:\\Riot Games\\Riot Client\\RiotClientServices.exe\""
    },
}
```

## Contribution
Pull requests and feedback are very welcome! This project is still under development.

## License
Copyright (c) 2025 Alz

---

> This project is still under development. Use with caution and back up your configuration regularly. 