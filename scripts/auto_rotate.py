#!/usr/bin/env python3
import time
import os
import subprocess

# Orientations mapping:
# normal (laptop on table, Y ~ -9) -> transform 0
# bottom-up (inverted landscape, Y ~ +9) -> transform 2
# right-up (portrait, X ~ +9) -> transform 1
# left-up (inverted portrait, X ~ -9) -> transform 3

def rotate(transform):
    monitors_file = os.path.expanduser("~/.config/hypr/monitors.lua")
    content = f"""
hl.monitor({{
    output = "eDP-1",
    mode = "1920x1080@60",
    position = "0x0",
    scale = 1,
    transform = {transform}
}})

hl.config({{
    input = {{
        touchdevice = {{
            transform = {transform},
            output = "eDP-1"
        }},
        tablet = {{
            transform = {transform},
            output = "eDP-1"
        }}
    }},
    device = {{
        {{
            name = "04f31234:00-04f3:2a84",
            transform = {transform},
            output = "eDP-1"
        }},
        {{
            name = "04f31234:00-04f3:2a84-stylus",
            transform = {transform},
            output = "eDP-1"
        }}
    }}
}})
"""
    with open(monitors_file, "w") as f:
        f.write(content)

    hypr_dir = f"/run/user/{os.getuid()}/hypr"
    if os.path.exists(hypr_dir):
        sockets = sorted(os.listdir(hypr_dir), key=lambda s: os.path.getmtime(os.path.join(hypr_dir, s)), reverse=True)
        if sockets:
            os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = sockets[0]

    eval_cmd = (
        f'hl.config({{ '
        f'input = {{ touchdevice = {{ transform = {transform}, output = "eDP-1" }}, tablet = {{ transform = {transform}, output = "eDP-1" }} }}, '
        f'device = {{ '
        f'{{ name = "04f31234:00-04f3:2a84", transform = {transform}, output = "eDP-1" }}, '
        f'{{ name = "04f31234:00-04f3:2a84-stylus", transform = {transform}, output = "eDP-1" }} '
        f'}} }})'
    )
    subprocess.run(["hyprctl", "eval", eval_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["hyprctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def find_accel_dir():
    base = '/sys/bus/iio/devices'
    if not os.path.exists(base):
        return None
    for dev in sorted(os.listdir(base)):
        name_path = os.path.join(base, dev, 'name')
        if os.path.exists(name_path):
            try:
                name = open(name_path).read().strip()
                if 'accel' in name:
                    return os.path.join(base, dev)
            except:
                pass
    return None

def read_accel(dev_dir):
    try:
        x = int(open(os.path.join(dev_dir, 'in_accel_x_raw')).read().strip())
        y = int(open(os.path.join(dev_dir, 'in_accel_y_raw')).read().strip())
        z = int(open(os.path.join(dev_dir, 'in_accel_z_raw')).read().strip())
        return x, y, z
    except:
        return None

def main():
    current_transform = 0
    stable_count = 0
    candidate_transform = 0

    dev_dir = None
    initialized = False
    while True:
        if not dev_dir or not os.path.exists(dev_dir):
            dev_dir = find_accel_dir()
            if not dev_dir:
                time.sleep(1)
                continue
            print(f"Auto-rotate daemon active, monitoring {dev_dir}", flush=True)

        accel = read_accel(dev_dir)
        if accel:
            x, y, z = accel
            # Threshold of 4 m/s^2 for dominant axis
            if abs(x) > abs(y) and abs(x) > 4:
                detected = 1 if x > 0 else 3
            elif abs(y) > abs(x) and abs(y) > 4:
                detected = 2 if y > 0 else 0
            else:
                detected = current_transform

            if not initialized:
                current_transform = detected
                candidate_transform = detected
                rotate(current_transform)
                initialized = True
                print(f"Initial orientation applied: transform={current_transform}", flush=True)

            if detected != current_transform:
                if detected == candidate_transform:
                    stable_count += 1
                    # 2 consecutive samples (400ms) to confirm intentional tilt
                    if stable_count >= 2:
                        current_transform = detected
                        print(f"Orientation change detected -> transform={current_transform} (X={x}, Y={y}, Z={z})", flush=True)
                        rotate(current_transform)
                        stable_count = 0
                else:
                    candidate_transform = detected
                    stable_count = 1
            else:
                stable_count = 0

        time.sleep(0.2)

if __name__ == "__main__":
    main()
