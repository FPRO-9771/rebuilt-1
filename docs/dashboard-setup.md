# Dashboard Setup Guide

How to view live robot telemetry on the driver station laptop.

---

## What Is SmartDashboard / NetworkTables?

NetworkTables is FRC's built-in system for sharing data between the robot and the driver station. Our code publishes values to SmartDashboard (a layer on top of NetworkTables), and a dashboard app on the laptop displays them in real time.

---

## Our Dashboard: Elastic

We use **Elastic Dashboard** — a modern, drag-and-drop dashboard for FRC. It has a clean UI, handles our ASCII table widgets well, and works on all platforms.

### Installing Elastic

#### macOS (development machines)

1. Go to the [Elastic releases page](https://github.com/Gold872/elastic-dashboard/releases/latest)
2. Download the `.dmg` file for macOS
3. Open the `.dmg` and drag Elastic to your Applications folder
4. First launch: right-click → Open (to bypass Gatekeeper)

#### Windows (driver station laptop)

1. Go to the [Elastic releases page](https://github.com/Gold872/elastic-dashboard/releases/latest)
2. Download the `.exe` installer for Windows
3. Run the installer

#### No install needed?

You can also try Elastic in your browser at https://gold872.github.io/elastic_dashboard/ — useful for a quick look, but the installed app is better for real use.

---

## Connecting

### In Simulation

1. Run `python -m robotpy sim` in this project
2. Open Elastic
3. It auto-connects to `localhost` — telemetry keys will appear automatically

### On the Real Robot

1. Connect your laptop to the robot's radio network
2. The robot's address is `10.97.71.2` (Team 9771 → `10.TE.AM.2`)
3. Elastic should auto-discover the robot. If not, set the team number in Elastic settings to `9771`

---

## Match Setup Choosers

Before every match, the drive team must set two dropdowns:

1. **Alliance** -- Red or Blue (must match your actual alliance)
2. **Starting Pose** -- Left, Center, or Right (must match robot placement)

These appear automatically under SmartDashboard when the robot connects. Drag them onto your layout so they're always visible.

**What they control:**

- Which AprilTags the turret auto-tracks (each alliance has its own Hub tags)
- The robot's starting position for odometry and autonomous paths
- Which autonomous routine runs (future)

**Important:** Always verify these are correct after field reset. The dashboard remembers your last selection, which may be wrong for the next match.

For details on how to add new poses or change tag priorities, see [Match Setup Architecture](architecture/match-setup.md).

---

## Viewing Telemetry Keys

Once connected, you'll see keys grouped by prefix:

- **Motors/** -- motor positions and velocities (numbers)
- **Commands/** -- active commands and recent event log (text)
- **Vision/Shooter/** -- Shooter Limelight AprilTag data (text + booleans)
- **Vision/Front/** -- Front Limelight AprilTag data (text + booleans)

### Setting Up a Layout

1. Drag keys from the sidebar onto the main area
2. Right-click a widget to change its display type (e.g., use "Text View" for table strings)
3. Arrange widgets into tabs (e.g., "Motors", "Commands", "Vision")

### Table Widgets (Commands/Recent, Vision/Shooter/Tags, Vision/Front/Tags)

These keys contain multi-line ASCII tables. To display them well:

1. Drag the key onto the dashboard
2. Right-click → change to **Text View**
3. Resize the widget to be wide enough to show full rows (~400px wide)
4. Make it tall enough to show all rows (~150px)

### Saving and Loading Layouts

- **Save:** File → Save Layout (or Ctrl+S / Cmd+S)
- **Load:** File → Load Layout
- Save your layout file in the repo so the whole team can use it

---

## Motor Tuning Workflow

Use the dashboard to find good motor speeds, then save them as constants.

1. Run `python -m robotpy sim`
2. Open Elastic and connect
3. Drag the `Motors/*` keys onto your layout (velocity and position values)
4. Operate the mechanisms using your controller or sim controls
5. Watch the values in real time — note the velocities/positions that work well
6. Add those values to the appropriate file in `constants/`

This is how we discover values like conveyor speed and launcher RPM before hardcoding them.

---

## Camera Streams

Each Limelight's MJPEG video feed is registered with CameraServer automatically at startup. In Elastic:

1. Look for the camera streams in the sidebar under **CameraServer**
2. Drag **Limelight Left** and **Limelight Right** onto your layout
3. Right-click → change to **Camera Stream** widget type
4. Resize to your preferred video size

The streams come from the Limelights at `http://10.97.71.11:5800/stream.mjpg` (left) and `http://10.97.71.12:5800/stream.mjpg` (right). Camera config is defined in `constants/vision.py`.

---

## Alternative Dashboard Apps

These are available but we don't use them day-to-day.

### Shuffleboard

Comes pre-installed with WPILib. Heavier and less actively maintained than Elastic.

- **Windows:** Start menu → WPILib → Shuffleboard
- **macOS:** WPILib VS Code command palette → `WPILib: Start Tool` → Shuffleboard

### Glass

Lightweight viewer included with WPILib. Good for quick spot-checks.

- Open from WPILib VS Code command palette: `WPILib: Start Tool` → Glass
- Navigate to NetworkTables → SmartDashboard to see all keys
