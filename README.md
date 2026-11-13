# AMD SFH Renoir 2-in-1 Tablet Fix & Auto-Rotation

> Working AMD Sensor Fusion Hub (`amd_sfh`) driver patches and hardware gravity auto-rotation for AMD Ryzen 4000 (Renoir) 2-in-1 convertible laptops on Linux (tested on Dell Inspiron 7405 2-in-1 + Hyprland / Wayland).

---

##  The Problem

For years, Linux users on AMD Ryzen 4000 Renoir 2-in-1 laptops (Dell Inspiron 7405 2-in-1, HP Envy x360, Lenovo Yoga 6) found that tablet mode and screen auto-rotation were completely non-functional. 

Upstream Linux kernels suffered from multiple compounded bugs:
1. **Memory Corruption & Kernel Panics:** Renoir MP2 uses a 32-bit DMA engine. Upstream drivers requested `DMA_BIT_MASK(64)`, causing DMA buffer allocations above 4GB. The hardware truncated addresses to 32 bits, overwriting random user/process memory and triggering `MCE: hardware memory corruption` faults.
2. **Firmware Timeout:** `intr_disable` defaulted to `true`, preventing Renoir MP2 firmware from acknowledging commands.
3. **Dropped Motion Reports:** In `amd_sfh_client.c`, `cli_data->report_type` was uninitialized, which misrouted 15-byte feature reports into the input report handler. The kernel HID subsystem rejected every report with `-EINVAL` (`Event data for report 1 was too short (15 vs 14)`), freezing accelerometer readings.

This repository provides:
- **A fully patched, DKMS-managed `amd_sfh` kernel driver** resolving all 3 upstream bugs.
- **A Wayland / Hyprland auto-rotation daemon (`auto_rotate.py`)** with real-time screen rotation, 1:1 touch coordinate mapping (`output = "eDP-1"`), and stylus transformation.
- **A systemd user service** ensuring persistence across reboots.

---

##  Tested Hardware
- **Device:** Dell Inspiron 7405 2-in-1 (AMD Ryzen 4500U / 4700U Renoir)
- **OS:** Arch Linux (Kernel 7.2.x / 6.x)
- **Compositor:** Hyprland (0.56.x with Lua configuration)
- **Sensors Detected:** Accelerometer (`accel_3d`), Gyroscope, Magnetometer, ALS

*Should also work on HP Envy x360 (Renoir) and Lenovo Yoga 6 (Renoir) convertible laptops.*

---

##  Quick Install (1-Line Setup)

Clone the repository and run the installer:

```bash
git clone https://github.com/<your-username>/amd-sfh-renoir-fix.git
cd amd-sfh-renoir-fix
chmod +x install.sh
./install.sh
```

The script will:
1. Register and build the patched `amd_sfh` driver via DKMS (automatically survives future kernel updates).
2. Load the driver.
3. Install the auto-rotate daemon to `~/.config/hypr/scripts/auto_rotate.py`.
4. Enable and start `auto-rotate.service` in your user systemd session.

---

##  Hyprland Integration

If using Hyprland with Lua (`hyprland.lua`), ensure `~/.config/hypr/custom/execs.lua` starts the service:

```lua
hl.on("hyprland.start", function ()
    hl.exec_cmd("systemctl --user start auto-rotate.service")
end)
```

The daemon writes directly to `~/.config/hypr/monitors.lua` and applies synchronous touch matrix updates via:
```lua
hl.config({
    input = {
        touchdevice = { transform = <val>, output = "eDP-1" },
        tablet = { transform = <val>, output = "eDP-1" }
    }
})
```

---

##  Verification

1. **Verify DKMS status:**
   ```bash
   dkms status amd_sfh
   # Output: amd_sfh/1.0, <kernel-version>, x86_64: installed
   ```

2. **Watch live gravitational sensor readings:**
   ```bash
   watch -n 0.2 "cat /sys/bus/iio/devices/iio:device*/in_accel_*_raw"
   ```
   *(Rotate or tilt the laptop — the numbers dynamically update!)*

3. **Monitor rotation logs:**
   ```bash
   journalctl --user -u auto-rotate -f
   ```

---

##  Upstream Kernel Submission

The `patches/` directory contains clean, atomic patches formatted for submission to the Linux Kernel Mailing List (`linux-input@vger.kernel.org`):
- `0001-HID-amd_sfh-Fix-32-bit-DMA-mask-truncation-on-Renoir.patch`
- `0002-HID-amd_sfh-Route-HID-reports-using-node_type-in-work-handler.patch`
- `0003-HID-amd_sfh-Enable-interrupts-by-default-for-Renoir-hardware.patch`
- `0004-HID-amd_sfh-Add-DMI-quirk-for-Dell-Inspiron-7405-2-in-1.patch`

---

## 📄 License
GPL-2.0 (matching the Linux Kernel).
