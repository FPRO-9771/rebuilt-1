# Dashboard Setup Guide

How to view live robot telemetry on the driver station laptop.

---

## What Is SmartDashboard / NetworkTables?

NetworkTables is FRC's built-in system for sharing data between the robot and the driver station. Our code publishes values to SmartDashboard (a layer on top of NetworkTables), and a dashboard app on the laptop displays them in real time.

---

## Opening Shuffleboard

Shuffleboard comes pre-installed with WPILib. To open it:

- **Windows:** Start menu → WPILib → Shuffleboard
- **macOS:** Open WPILib VS Code, then from the command palette: `WPILib: Start Tool` → Shuffleboard

---

## Connecting

### In Simulation

When you run `python -m robotpy sim`, Shuffleboard auto-connects to `localhost`. Just open Shuffleboard and the keys will appear.

### On the Real Robot

1. Connect your laptop to the robot's radio network
2. The robot's address is `10.97.71.2` (Team 9771 → `10.TE.AM.2`)
3. Shuffleboard should auto-discover the robot. If not, set the team number in Shuffleboard preferences to `9771`

---

## Viewing Telemetry Keys

Once connected, you'll see keys auto-populate in the left sidebar grouped by prefix:

- **Motors/** — motor positions and velocities (numbers)
- **Commands/** — active commands and recent event log (text)
- **Vision/** — AprilTag target data (text + booleans)

### Setting Up a Layout

1. Drag keys from the sidebar onto the main area
2. Right-click a widget to change its type (e.g., use "Text View" for the table strings)
3. Arrange widgets into tabs (e.g., "Motors", "Commands", "Vision")

### Table Widgets (Commands/Recent, Vision/Tags)

These keys contain multi-line ASCII tables. To display them well:

1. Drag the key onto the dashboard
2. Right-click → "Show as..." → **Text View**
3. Resize the widget to be wide enough to show full rows (~400px wide)
4. Make it tall enough to show all rows (~150px)

### Saving and Loading Layouts

- **Save:** File → Save Layout (or Ctrl+S)
- **Load:** File → Load Layout
- Save your layout file in the repo so the whole team can use it

---

## Alternative Dashboard Apps

### Glass

Lightweight viewer included with WPILib. Good for quick checks.

- Open from WPILib VS Code command palette: `WPILib: Start Tool` → Glass
- Navigate to NetworkTables → SmartDashboard to see all keys

### Elastic

Modern alternative with a cleaner UI. Download from [GitHub](https://github.com/Gold872/elastic-dashboard).

- Supports drag-and-drop layout like Shuffleboard
- Better text widget rendering for our ASCII tables
