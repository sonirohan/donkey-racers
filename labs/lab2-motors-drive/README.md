# Lab 2: The Drive to Succeed!

- [Introduction](#introduction)
- [Part I: Assembling the Car](#part-i-assembling-the-car)
- [Part II: Controlling the Car](#part-ii-controlling-the-car)
- [Conclusion](#conclusion)
- [Final Note](#final-note)

---

## Introduction

Welcome to your second lab! Hopefully you're reading this after attending lecture, since that knowledge is crucial here. Refresher resources live at [Donkey Racers Plans](#).

In our second lecture, we taught you about the I2C protocol, pulse-width modulation, and making the motor work. With this background, you now have the context required to start putting your car together! By the end of this lab, you'll have a strong theoretical and practical understanding of what makes your car tick (in addition to SCL, of course).

Please remember, we encourage you to seek help from all possible sources. While you should always try to figure out difficulties yourself first, you shouldn't be struggling unnecessarily with these labs. Remember, you have the entire Internet, ChatGPT and its brethren, and two leads dedicated to your success! Don't hesitate to reach out for help or advice.

> **AI usage:** ChatGPT and similar tools are fine for debugging and understanding errors. Make sure you can explain every line you submit — see `CONTRIBUTING.md`.

---

## Part I: Assembling the Car

Recall the circuit diagram we provided. In this part, you'll actually build your car and run a preliminary script to send PWM signals to the motors.

1. Connect your Raspberry Pi to power via the USB-C port.
2. Connect each of the I2C cables on the Raspberry Pi to the appropriate pins on the PCA board. **Do not mess up the connections!**
3. Connect the LiPo battery to the thick red-and-black cables attached to the ESC. Red to red, black to black!
4. Connect the 3-pin connectors from the ESC and servo to the PCA board. Keep track of which channel connects to which motor!
5. SSH into the Raspberry Pi.
6. Write a Python script that makes the car's motor and servo operate under various combinations of ESC and servo PWM values. The more rigorous your stress test, the better.
7. Before starting the script, make sure the car is elevated with its wheels free to spin so it doesn't drive away. Start the script and watch your car respond!

> **Watch out for:** when trying to run the motor, make sure the switch on the car is on. If the motor isn't powered, it doesn't matter how good your code is — the car won't move. Easy to overlook, so double-check every time.

### Check-offs

1. Take a picture of your setup and upload it to your team's submission folder.
2. Upload your motor testing script to your team's submission folder.
3. Create a short doc (Google Doc, text file, whatever) explaining what your motor testing script does.
4. Take a video of your car responding to the motor script. Send it in Discord (not the submission folder).

**Congratulations! You've completed Part I.**

### Extra Credit: Making the car go backwards! (+1 point)

The car is in forward mode by default. In forward mode, PWM pulses between 1–1.5ms have no effect — reversing direction suddenly can stress the motor, so a specific protocol is required to switch direction.

**Entering Backward Mode:**
1. Send a neutral pulse.
2. Send a pulse between 1–1.5ms.
3. Send another neutral pulse.

Now a pulse between 1–1.5ms will move the car backward. A pulse between 1.5–2ms will have no effect.

**Entering Forward Mode:**
1. Send a neutral pulse.
2. Send a pulse between 1.5–2ms.
3. Send another neutral pulse.

Now a pulse between 1.5–2ms will move the car forward.

To earn this point, show the wheels spinning in both directions in response to your motor testing script.

---

## Part II: Controlling the Car

1. Contact a lead so we can give you specific instructions on assembling your car properly (right now your wheels can spin and turn, but the car itself isn't fully put together).
2. Once assembled, SSH into the Raspberry Pi and run:
   ```
   donkey createcar --template=cv_control --path ~/my_cv_car
   donkey createcar --path ~/my_dl_car
   ```
3. These commands create two new directories in your home directory. `cd` into one of them (doesn't matter which, as long as you're consistent).
4. Edit the `myconfig` file in that directory:
   - Uncomment `DRIVE_TRAIN_TYPE = "PWM_STEERING_THROTTLE"`.
   - Uncomment every line in `PWM_STEERING_THROTTLE = { … }`.
   - Specify the pins for steering and throttle: `PCA9685.1:40.<APPROPRIATE_CHANNEL_NUMBER>`.
   - Pick one of two equivalent options:
     - Keep PWM steering scale and PWM throttle scale at 1.0, but scale the PWM values into the appropriate ranges, **or**
     - Specify pulse times in microseconds (not milliseconds) and calculate the PWM steering/throttle scale accordingly.
5. Run `python3 manage.py drive`.
6. In a browser, go to `http://<your_donkeycar_name>.local:8887/` to access the DonkeyCar UI. You should be able to control the car with the virtual joystick — you won't be able to reverse yet, but it should turn left and right.

> **Watch out for:**
> - `./donkeycar/donkeycar/parts/actuator.py` has useful context in the `PulseController`, `PWMSteering`, and `PWMThrottle` classes. Not required reading, but recommended.
> - If `manage.py` throws `"Attempt to start pin (12) that is already started"` (or similar), run:
>   ```
>   python3 -c "from adafruit_pca9685 import PCA9685; import board, busio; i2c=busio.I2C(board.SCL, board.SDA); pca=PCA9685(i2c); pca.frequency=60; pca.channels[12].duty_cycle=0; pca.deinit()"
>   ```
>   (swap `12` for whichever pin number is in your error)

### Check-offs

1. Screenshot the DonkeyCar UI in your browser and upload it to your team's submission folder.
2. Take a video of someone on your team driving 10 laps around the track without going off course. Using your phone's browser for the joystick tends to be more intuitive than a laptop, but either works. Upload to Discord (not the submission folder) — make sure the joystick and the car are visible in the same frame.

**Congratulations! You've completed Part II.**

### Extra Credit: Using the Actual Joystick! (+1.5 points)

If you don't want to use the UI, try the physical joystick included in the car kit. We won't give step-by-step instructions for this one — if you're up for a challenge, give it a shot!

---

## Conclusion

Congratulations! You've completed this lab and brought great honor and glory to your team and to Donkey Racers as a whole. Message both leads so we can schedule a time to go over your work, ask a few final questions to check understanding, and award the points you've earned. Once again — congratulations, we couldn't be prouder of you!

---

## Final Note

Next up is Lab 3, where you'll build both a computer vision autopilot and a deep learning autopilot — getting your car driving itself around the track for the first time. After that, Winter Quarter brings ROS, computer networking, and more advanced deep learning (PyTorch, Reinforcement Learning). The ROS lab needs a working car; the networking lab only needs the Raspberry Pi and a local device; the RL lab is Colab-only, no car required. All of it builds toward your capstone in Spring.

---

## Where This Goes

The PWM/motor control code you wrote in Part I is the direct ancestor of `motor_node` in the capstone — the node that takes a `/cmd_vel` command and turns it into real wheel motion. The manual drive setup in Part II is what Lab 3's autopilot replaces with a trained model.
