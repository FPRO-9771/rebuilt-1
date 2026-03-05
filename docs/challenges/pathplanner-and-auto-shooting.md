# PathPlanner and Opportunistic Auto Shooting

We want to level up our autonomous mode. Right now our auto routines use
hand-tuned velocity and duration tuples -- drive forward at 2 m/s for 1
second, etc. That is hard to get right and breaks if the robot slips or
starts in a slightly different spot. We are going to switch to PathPlanner,
which lets us draw paths visually and have the robot follow them accurately.

But the really cool part is what we can do on top of that: **shoot while
driving.** Our turret tracks the Hub independently from the drivetrain. So
while the robot follows a path collecting Fuel, the turret can lock onto the
Hub and fire whenever it has a clear shot -- without stopping.

This doc explains the concepts and gives you the pieces. Your job is to
figure out how to put them together.

---

## Part 1: PathPlanner Basics

### What is PathPlanner?

PathPlanner is two things:

1. **A desktop app** where you drag waypoints on a picture of the field to
   draw paths. You set speed limits, acceleration, and rotation targets.
   Paths get saved as JSON files in `deploy/pathplanner/`.

2. **A Python library** (`pathplannerlib`) that loads those paths and turns
   them into trajectory-following commands. It uses the drivetrain's odometry
   to know where the robot is and correct errors in real time.

### Why is this better than timed driving?

With timed driving (`drive forward at 2 m/s for 1 second`):
- If the robot slips, it does not know and does not correct
- If you start 5 cm off, you end up 5 cm off (or worse)
- Tuning means changing numbers and redeploying over and over

With PathPlanner:
- The robot knows where it is (odometry) and corrects back to the path
- You adjust paths by dragging points in a GUI -- no code changes
- You can see exactly where the robot will go on the field map

### How do you hook it up?

PathPlanner needs to know four things about your robot:

1. **Where am I?** -- A function that returns the robot's current pose
   (x, y, and heading on the field)
2. **Reset my position** -- A function to set the starting pose at the
   beginning of auto
3. **How fast am I going?** -- A function that returns current chassis speeds
4. **How do I drive?** -- A function that takes a `ChassisSpeeds` and makes
   the robot move

All four of these already exist in our swerve drivetrain. You need to find
them and wire them into PathPlanner's `AutoBuilder.configure()` method.

### Things to figure out

- Look at the PathPlanner docs: https://pathplanner.dev/home.html
- Look at `generated/tuner_constants.py` and our drivetrain wrapper. What
  methods give you pose, speeds, and driving?
- PathPlanner needs PID controllers for path correction (x, y, and rotation).
  What are PID controllers? We use them already for the turret -- look at how
  those work.
- What does "should flip path" mean? Think about how blue alliance paths
  relate to red alliance paths on a mirrored field.

---

## Part 2: Opportunistic Auto Shooting

This is the fun part. Instead of stopping to shoot, we want the robot to
fire whenever conditions are right -- even while driving a path.

### The concept

Think of it as two independent systems running at the same time:

```
Path following (drivetrain)          Opportunistic shooting (turret + shooter)
================================     =========================================
Drive to pickup spot                 Is turret locked on target?
Pick up Fuel                           AND shooter wheels at speed?
Drive to next spot                     AND we have Fuel loaded?
Pick up more Fuel                      AND distance is in range?
Drive back toward Hub                    --> YES: Fire!
                                         --> NO:  Keep tracking, wait
```

The drivetrain does not care about the turret. The turret does not care
about the path. They run in parallel.

### WPILib parallel commands

WPILib lets you run commands side by side using `ParallelCommandGroup` or
`ParallelDeadlineGroup`. You have already seen this in our auto docs. The
question is: which one do you want here?

Think about it:
- `ParallelCommandGroup` -- ends when ALL commands finish
- `ParallelDeadlineGroup` -- ends when the FIRST (deadline) command finishes
- `ParallelRaceGroup` -- ends when ANY command finishes

Which one makes sense if the path is the "main" thing and the shooting
should just keep going alongside it?

### The auto-shoot command

You need to design a command that runs in the background and shoots when
ready. Think about:

1. **What subsystems does it need?** It will check the turret, the shooter,
   and the intake. But be careful -- if this command REQUIRES those
   subsystems, nothing else can use them at the same time. Think about
   whether it should require them or just read from them.

2. **What conditions mean "ready to fire"?** List them all out. Think about
   what happens if you fire when one of them is not quite right.

3. **What does "fire" mean mechanically?** Look at how the intake feeds
   Fuel into the shooter. What command triggers that?

4. **Should it fire as fast as possible?** Or should there be a minimum
   time between shots? What if the turret was briefly aligned but is
   actually swinging past the target?

5. **How does it know when to stop?** Does it run forever? Until auto ends?
   Until we are out of Fuel?

### The "locked on" problem

This one is tricky. The turret PD controller will report small error when
the turret is pointed at the target. But "small error" at 2 meters is very
different from "small error" at 6 meters. A turret that is 1 degree off at
2 meters misses by about 3.5 cm. The same 1 degree at 6 meters misses by
10.5 cm.

Should the "locked on" tolerance be the same at all distances? Or should it
get tighter as distance increases? Think about what makes a shot actually
go in.

### Settling time

The turret might swing through the target as it tracks. For one brief
instant the error is zero -- but the turret is still moving. If you fire at
that instant, the ball will not go where you think because the turret was
in motion.

How do you make sure the turret is truly locked on and not just passing
through? Think about what "settled" means. (Hint: it is not just about
position -- velocity matters too.)

---

## Part 3: Putting It Together

Once you have the pieces, the auto routine structure looks like this
(pseudocode):

```
auto routine:
    parallel:
        deadline = path sequence:
            follow path "pickup fuel 1"
            follow path "pickup fuel 2"
            follow path "return to scoring zone"
        alongside:
            auto shoot when ready (runs whole time)
```

### Things to figure out

- Where in our code do auto routines get built? (Check the autonomous docs)
- How does the chooser work with PathPlanner autos vs our current system?
- PathPlanner has its own "auto" builder in the GUI where you can chain
  paths and add event markers. Should we use that, or compose our own
  `SequentialCommandGroup` with PathPlanner paths? What are the tradeoffs?
- How do you test this? Can you simulate it? What would you check?

---

## Where to start

Do not try to build everything at once.

1. **Read the PathPlanner docs** and install the app. Draw a simple path
   on the field and look at the JSON it creates.
2. **Get a single path following working** before worrying about shooting.
   Make the robot drive a square in sim.
3. **Think through the auto-shoot logic on paper.** Write out the conditions
   in plain English before writing any code. Talk about it as a group.
4. **Build the auto-shoot command** and test it separately (not during a
   path -- just while the robot is stationary with the turret tracking).
5. **Combine them** with a parallel group and test in sim.

Take it step by step. Talk through the design decisions before coding.
The hard part here is not the code -- it is deciding WHEN to shoot and
making sure the robot only fires when it will actually score.

Good luck!
