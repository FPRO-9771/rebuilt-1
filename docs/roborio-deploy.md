   # RoboRIO Setup and Deployment Guide - Team 9771 FPRO

This guide covers setting up the roboRIO and deploying Python code for the 2026 season.

## Prerequisites

Before deploying, make sure you have:

1. **Python 3.13 installed** - See `docs/PYTHON_SETUP.md`
2. **Project dependencies installed locally:**
   ```bash
   pip3 install -r requirements.txt --upgrade
   ```
3. **roboRIO imaged with 2026 firmware** - Use NI FRC Game Tools to image with `FRC_roboRIO2_2026_vX.X`

## Connecting to the RoboRIO

You can connect via:

- **USB cable** - Direct connection, most reliable for first-time setup
- **Ethernet** - Direct cable to the roboRIO
- **Radio** - Over WiFi once the radio is configured

Verify connection by pinging the robot:
```bash
ping roboRIO-9771-FRC.local
```

Or use the IP directly (for team 9771):
```bash
ping 10.97.71.2
```

---

## First-Time RoboRIO Setup

The first deploy to a fresh roboRIO requires extra steps to install Python and dependencies.

### Step 1: Download Python for the RoboRIO

```bash
python -m robotpy installer download-python
```

### Step 2: Create the pip cache directory

```bash
mkdir -p ~/wpilib/2026/robotpy/pip_cache
```

### Step 3: Download all project dependencies

```bash
python -m robotpy installer download -r requirements.txt
```

This downloads ARM-compatible packages for the roboRIO architecture.

### Step 4: Install packages on the RoboRIO

```bash
python -m robotpy installer install -r requirements.txt
```

### Step 5: Deploy the code

```bash
python -m robotpy deploy
```

The first deploy takes several minutes as it installs Python on the roboRIO. The robot will reboot after Python installation - wait 30-60 seconds before reconnecting.

---

## Regular Deployment

After the first-time setup, deploying is simple:

```bash
# Full deploy (runs tests first)
python -m robotpy deploy

# Skip tests (faster, use when you know code works)
python -m robotpy deploy --skip-tests
```

---

## Adding New Dependencies

When you add a new package to `requirements.txt`:

```bash
# Install locally
pip3 install -r requirements.txt --upgrade

# Download for roboRIO
python -m robotpy installer download -r requirements.txt

# Install on roboRIO
python -m robotpy installer install -r requirements.txt

# Deploy
python -m robotpy deploy
```

---

## Troubleshooting

### "Robot not found" or can't ping

- Check your network connection (USB/Ethernet/Radio)
- Try the direct IP: `ping 10.97.71.2`
- Make sure the roboRIO is powered on
- Wait 30-60 seconds after a reboot

### "RoboRIO image XXXX is required"

Your local RobotPy version doesn't match the roboRIO image year. Update your local packages:
```bash
pip3 install -r requirements.txt --upgrade
```

### "python314 has not been downloaded yet"

Run:
```bash
python -m robotpy installer download-python
```

### "FileNotFoundError: pip_cache"

Create the cache directory:
```bash
mkdir -p ~/wpilib/2026/robotpy/pip_cache
```

### "No module named 'XXX'" on robot

The package isn't installed on the roboRIO. Download and install it:
```bash
python -m robotpy installer download -r requirements.txt
python -m robotpy installer install -r requirements.txt
python -m robotpy deploy
```

### Robot code red light on Driver Station

Check the Driver Station console or roboRIO logs for the specific error. Common causes:
- Missing module (see above)
- Syntax error in code
- Import error

### Deploy succeeds but can't ping after

The roboRIO reboots after installing Python. Wait 30-60 seconds, then try pinging again. If it still doesn't respond, power cycle the robot.

---

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `python -m robotpy deploy` | Deploy code to robot |
| `python -m robotpy deploy --skip-tests` | Deploy without running tests |
| `python -m robotpy sim` | Run robot code in simulation |
| `python -m robotpy test` | Run tests locally |
| `python -m robotpy installer download-python` | Download Python for roboRIO |
| `python -m robotpy installer download -r requirements.txt` | Download all dependencies |
| `python -m robotpy installer install -r requirements.txt` | Install dependencies on roboRIO |

---

## Getting Help

- Ask Brian (coding mentor)
- [RobotPy Documentation](https://robotpy.readthedocs.io/)
- [WPILib Python Docs](https://docs.wpilib.org/en/stable/docs/software/python/index.html)
