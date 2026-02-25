# Debugging Guide - Team 9771 FPRO

This guide covers how to access robot logs, diagnose issues remotely, and debug common problems during development and at competitions.

## SSH into the RoboRIO

You can log into the roboRIO directly from any computer on the robot's network:

```bash
ssh admin@roborio-9771-frc.local
```

Or by IP:

```bash
ssh admin@10.97.71.2
```

No password is needed. The first time you connect, you'll be asked to accept the host key — type `yes`.

Type `exit` when you're done.

---

## Viewing Robot Logs

### On the RoboRIO via SSH

Once connected, you can read the robot program log:

```bash
# View the full log
cat /var/local/natinst/log/FRC_UserProgram.log

# Watch the log live (new lines appear as they're written)
tail -f /var/local/natinst/log/FRC_UserProgram.log
```

### From the Driver Station

The Driver Station console shows `WARNING` and `ERROR` level messages from our logger (see the Logging section in `CLAUDE.md`). These logs are automatically saved on the DS laptop:

- **Windows:** `C:\Users\Public\Documents\FRC\Log Files\`
- **File types:** `.dslog` (data) and `.dsevents` (events/errors)

Open saved logs with the **FRC Log Viewer** (included with FRC Game Tools).

### NetConsole / RioLog (Any Laptop)

The roboRIO broadcasts all console output over the network on UDP port 6666. You can pick this up from any computer on the robot's network — no Driver Station needed.

- **VS Code:** Open the command palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run **"WPILib: Start RioLog"**
- **Terminal:** `nc -u -l 6666`

---

## Useful SSH Commands

Once you're SSH'd into the roboRIO:

| Command | What it does |
|---------|-------------|
| `cat /var/local/natinst/log/FRC_UserProgram.log` | View robot program log |
| `tail -f /var/local/natinst/log/FRC_UserProgram.log` | Watch log live |
| `ps aux` | See what processes are running |
| `df -h` | Check disk space |
| `free -m` | Check memory usage |
| `dmesg` | View kernel/system messages |
| `top` | Live CPU and memory monitor (press `q` to quit) |

---

## Checking NetworkTables Remotely

Our telemetry module publishes data over NetworkTables. You can view this from any computer on the robot's network using:

- **Shuffleboard** — Full dashboard with customizable widgets
- **Glass** — Lightweight viewer for NetworkTables values
- **Elastic** — Web-based dashboard

See `docs/dashboard-setup.md` for how to open these tools.

---

## Common Debugging Scenarios

### Robot code won't start (red light on DS)

1. Check the DS console for the error message
2. SSH in and read the log: `cat /var/local/natinst/log/FRC_UserProgram.log`
3. Common causes: missing module, syntax error, import error

### Communications light is half-green half-red

This means packets are being dropped between the DS and roboRIO. Check:

1. Ethernet cables — re-seat both ends
2. Radio — power cycle or re-image
3. WiFi signal strength — move closer to the robot
4. Robot code — look for blocking calls or tight loops in the main thread

### Robot is slow or unresponsive

SSH in and check resource usage:

```bash
top       # Watch CPU usage (q to quit)
free -m   # Check available memory
df -h     # Check disk space
```

### Need to see what a subsystem is doing

1. Open a dashboard tool (Shuffleboard/Glass/Elastic) and look at the telemetry keys published by the subsystem
2. Temporarily increase logging verbosity by setting `DEBUG["verbose"] = True` in `constants/debug.py` and redeploying

---

## Getting Help

- Ask Brian (coding mentor)
- [RobotPy Documentation](https://robotpy.readthedocs.io/)
- [WPILib Python Docs](https://docs.wpilib.org/en/stable/docs/software/python/index.html)
