
````markdown
# qbqmanager

A Python script to better manage qBittorrent queue.

---

## TL;DR

This repository contains a **Python helper script** (`qb-q-helper.py`) to intelligently manage your qBittorrent download queue based on availability, ETA, and size. It also includes a **PowerShell bootstrapper** (`qb-q-helper.ps1`) for Windows to ensure the environment is ready and launch the helper automatically.

---

## Features

- Automatically resumes/pauses torrents based on your custom scoring logic.
- Performs a “warm-up” of incomplete torrents to get accurate ETA and availability.
- Respects qBittorrent settings like max active downloads, ratio limits, and upload pausing.
- Cross-user support: can be integrated into multi-user setups with Fast User Switching.
- Minimal dependencies (Python + `requests`).

---

## Repository Contents

| File | Description |
|------|-------------|
| `qb-q-helper.py` | Main Python script managing qBittorrent queue. |
| `qb-q-helper.ps1` | Windows PowerShell bootstrapper for installing dependencies and launching the Python helper. |
| `README.md` | This file, instructions for setup and usage. |

---

## Windows Setup

### 1. Clone the Repository
```powershell
git clone https://github.com/yourusername/qb-q-helper.git
cd qb-q-helper
````

### 2. Run the Bootstrapper

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\qb-q-helper.ps1"
```

The bootstrapper will:

* Install Scoop if not present.
* Install Python3 if missing.
* Install `requests` Python package.
* Launch the Python helper (`qb-q-helper.py`).

---

### 3. First-Time Python Configuration

On the first run, `qb-q-helper.py` will prompt for your **qBittorrent WebUI port**.
The port is stored in `config.json` for future runs.

---

### 4. Optional: Automatic Startup

To have the helper start automatically at login:

1. Open the Startup folder:

```powershell
shell:startup
```

2. Create a shortcut to the bootstrapper:

* **Target:**

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\full\path\to\qb-q-helper.ps1"
```

* **Optional:** Set the shortcut to **run minimized**.

> ⚠️ Do not commit shortcuts to the repository; paths vary per user.

---

### 5. Optional: Automatic Shortcut Creation Script

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\QB Helper.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$PSScriptRoot\qb-q-helper.ps1`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.Save()
```

Run this once after cloning to create the Startup shortcut automatically.

---

### 6. Notes

* Make sure **Fast User Switching** is enabled if using multiple accounts.
* WebUI authentication for localhost can be bypassed.
* If multiple qBittorrent instances run on the same machine, ensure each uses a **different WebUI port**.
* Errors during Python or pip installation will display in the console.

---

## Linux Setup (Optional)

For Linux users, a simple shell bootstrapper (`qb-q-helper.sh`) can:

* Detect the package manager (`apt`, `dnf`, `pacman`, `zypper`).
* Install Python3 if missing.
* Install `requests` via pip.
* Launch `qb-q-helper.py`.

Usage:

```bash
chmod +x qb-q-helper.sh
./qb-q-helper.sh
```

The Python script handles port configuration and `config.json` just like on Windows.

---

## Cross-Platform Notes

* The **PowerShell** and **shell scripts** are lightweight bootstrappers; all queue management logic is handled by the Python helper.
* The scripts ensure dependencies are installed and launch the Python helper automatically.
* The Python helper maintains persistent configuration in `config.json`.

---

## License

[MIT License](LICENSE)
