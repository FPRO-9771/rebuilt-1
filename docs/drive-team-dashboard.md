# Drive Team Dashboard Guide

How to set up Elastic Dashboard for competition matches. Two tabs: **Pre-Match** (before the match starts) and **Driving** (during the match).

For general dashboard install and connection instructions, see [Dashboard Setup](dashboard-setup.md).

---

## Tab 1: Pre-Match

This tab is for the queue and on the field before the match starts. Set it up once and save the layout.

### Widgets to add

| Widget | SmartDashboard Key | Widget Type | Notes |
|--------|--------------------|-------------|-------|
| Alliance chooser | `Alliance` | Dropdown (default) | Select Red or Blue |
| Starting Pose chooser | `Starting Pose` | Dropdown (default) | Select Left, Center, or Right |
| Alliance color check | `Match/Is Red Alliance` | **Boolean Box** | Big confirmation indicator |

### Setting up the alliance color check

This is the most important widget -- it confirms that the alliance chooser is set correctly.

1. Drag `Match/Is Red Alliance` onto the tab
2. Right-click the widget and change it to **Boolean Box**
3. In widget properties, set **True color** to red and **False color** to blue
4. Make it BIG -- you need to see it from across the pit

### Why this matters

The alliance chooser defaults to Red. If you forget to change it when you're on Blue, the turret will auto-aim at the wrong Hub. The big color box makes it obvious if something is wrong.

### Pre-match checklist

1. Check the big color box -- does it match your actual alliance?
2. Check the Starting Pose dropdown -- does it match where the robot is placed?
3. Double-check after field reset -- the dashboard remembers the last match's settings

---

## Tab 2: Driving

This tab is what the operator watches during the match. Keep it simple -- only the things you need to make decisions.

### Widgets to add

| Widget | SmartDashboard Key | Widget Type | What it tells you |
|--------|--------------------|-------------|-------------------|
| Shooter camera | CameraServer / Limelight Shooter | **Camera Stream** | What the shooter Limelight sees |
| Driver camera | CameraServer / Limelight Front | **Camera Stream** | Front-facing view (not plugged in yet) |
| On Target | `AutoAim/OnTarget` | **Boolean Box** | Green = turret is locked on the Hub |
| Launcher At Speed | `Motors/Launcher At Speed` | **Boolean Box** | Green = flywheel is up to speed |
| Intake Running | `Motors/Intake Running` | **Boolean Box** | Green = intake spinner is active |
| Feeder Running | `Motors/Feeder Running` | **Boolean Box** | Green = feed system is pushing Fuel |
| Turret Clear | `Motors/Turret Clear` | **Boolean Box** | Green = turret free to move, Red = at a soft limit |

### Setting up camera streams

1. Look under **CameraServer** in the sidebar
2. Drag each Limelight stream onto the tab
3. Right-click and change to **Camera Stream**
4. Resize so you can see them clearly but they don't take up the whole screen

### Setting up the boolean indicators

For each boolean widget (On Target, Intake Running, Feeder Running):

1. Drag the key onto the tab
2. Right-click and change to **Boolean Box**
3. Set **True color** to green and **False color** to dark gray (or red if you prefer)
4. Keep them small -- they just need to be visible at a glance

### Suggested layout

```
+-------------------+-------------------+
|                   |                   |
|  Shooter Camera   |  Driver Camera    |
|                   |                   |
+-------------------+-------------------+
| On Target | Intake Running | Feeder  |
|  (green)  |    (green)     | Running |
+-------------------+-------------------+
```

---

## Saving Your Layout

Once both tabs are set up:

1. File -> Save Layout (Ctrl+S / Cmd+S)
2. Save the `.json` file somewhere you can find it (desktop or in the repo)
3. On match day, File -> Load Layout to restore everything

You only need to do this once. After that, just load the layout and set the alliance/pose before each match.
