# Shooter Targeting Upgrades

Our auto-targeting works! The turret tracks AprilTags, the launcher spins up,
and the hood adjusts -- all from the distance lookup table. But there are two
problems that make our shots miss. This doc explains both problems so we can
fix them.

---

## Problem 1: AprilTag Offset Changes With Distance

### What we have now

Each AprilTag on the Hub has a `tx_offset` in `constants/shooter.py`. This is
a fixed number of degrees that we add to `tx` to correct for the fact that the
tag is not in the center of the target hole. The orchestrator applies it here:

```python
self._last_tx = target.tx + offsets["tx_offset"]
```

### Why it does not work

The tags are on the corners of a square. The target hole is in the center of
that square. The physical distance between a tag and the center is always the
same -- say 0.3 meters. But angles are not fixed. The same 0.3 meters looks
like a big angle up close and a small angle far away.

Think about it this way: hold your hand 0.3 meters to the left of your face.
Now look at your hand -- it is way off to the side. Now imagine that same
0.3 meter gap, but 10 meters away from you. It barely looks like anything.

Here is a picture of the problem:

```
  Close up (2m away)             Far away (5m away)

      tag --> . . . X <-- center      tag --> .X <-- center
             /     /                          /|
            /     /                          / |
           /     /                          /  |
          /     /                          /   |
         /     /                          /    |
    [robot]                              /     |
                                        /      |
    big angle!                     [robot]

                                   small angle!
```

At 2 meters, the 0.3m offset might be ~8.5 degrees.
At 5 meters, the same 0.3m offset is only ~3.4 degrees.

A fixed `tx_offset` can only be right at ONE distance. At every other distance
it will be wrong.

### What we need

The offset in degrees needs to be calculated every cycle, based on how far
away we are. The physical offset (in meters) stays constant -- that is the
number we should store in the constants. Then we convert it to degrees using
the distance we are getting from the Limelight.

### Clues

- There is a trig function that converts an opposite side and an adjacent
  side into an angle. Look it up!
- Python has a `math` module with trig functions. They return radians, not
  degrees. There is a `math.degrees()` function to convert.
- The constants currently store `tx_offset` as degrees. You will want to
  change this to meters. Think about what to name it.
- The change in the orchestrator is small -- just one line needs to do math
  instead of adding a fixed number.
- You can measure the physical offset on the real Hub with a tape measure.

### How to test your fix

- Set a tag's offset to something like 0.3 meters
- Simulate targets at different distances (2m, 3m, 5m)
- The corrected `tx` should get smaller as distance increases
- A fixed offset would stay the same at every distance -- yours should not

---

## Problem 2: The Robot Is Moving, But We Aim Where The Target Is Now

### What we have now

Every cycle, the orchestrator reads `tx` from the Limelight and aims the
turret at where the target is RIGHT NOW. The launcher spins up and the hood
adjusts for the current distance.

### Why it does not work

The ball takes time to fly from the launcher to the Hub. If the robot is
driving sideways while shooting, the ball will miss because we aimed at where
the Hub WAS when we fired, not where it will APPEAR to be when the ball
arrives. (The Hub does not move, but the robot does -- so from the ball's
point of view, the target shifts.)

Think about throwing a ball to a friend who is running. You throw it to where
they WILL be, not where they are now. Same idea, but reversed -- we are the
one running and the target is standing still.

```
  Time 0: We fire               Time 1: Ball arrives

  Hub --> X                      Hub --> X
          |                              |  <-- ball misses!
          |                              |
     [robot]-->                       [robot]-->
     (moving right)                  (moved right, ball went
                                      where Hub USED to be
                                      relative to us)
```

### What we need

We need to "lead" the target. If the robot is moving to the right, the Hub
appears to drift left from our point of view, so we should aim a little to
the left of where the target is now. How much we lead depends on:

1. How fast is the robot moving sideways (relative to the Hub)?
2. How long will the ball be in the air?

### Clues

- The drivetrain knows how fast the robot is moving. Look at how the swerve
  drivetrain reports velocity.
- Ball flight time depends on distance. Farther = longer flight time.
  You could start with a rough estimate (like 0.5 seconds) and tune it.
- "Leading" the target means adding a correction to `tx` before the PD
  controller uses it. This is similar to the tag offset correction -- it is
  another adjustment to `tx`.
- The correction in degrees depends on the robot's sideways speed and the
  distance to the target. Think about what trig you need (similar to
  Problem 1!).
- Start simple. Even a rough lead correction will be better than none.

### How to test

- Drive the robot sideways past the Hub while auto-targeting
- Without the fix: shots trail behind where you want them
- With the fix: shots should land closer to center even while moving
- Try different speeds -- faster driving needs more lead

---

## Where to start

Problem 1 is simpler and does not need any new sensor data. Start there.
Once that is working, move on to Problem 2, which needs velocity data from
the drivetrain.

Both fixes happen in the same place: `commands/shooter_orchestrator.py` in
the `execute()` method, around where `self._last_tx` gets calculated.

Good luck!
