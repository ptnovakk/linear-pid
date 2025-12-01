#!/usr/bin/env python3
"""
Linear PID – Full Interactive Tuning
Live sliders for: Setpoint, Kp, Ki, Kd
Perfect simulation → real hardware bridge
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.patches import Circle, Rectangle
from matplotlib.animation import FuncAnimation

# ========================== INITIAL STATE ==========================
L = 0.5
g = 9.81
dt = 0.02

x = -0.22
v = 0.0
integral = 0.0
prev_error = 0.0

# runtime history for small inset plot
t = 0.0
history_t = []
history_sp = []
history_pos = []
history_window = 12.0  # seconds to display in the inset

# Default values (will be overridden by sliders)
setpoint = 0.10
Kp = 22.0
Ki = 1.2
Kd = 4.5

# ========================== FIGURE ==========================
fig = plt.figure(figsize=(12, 9), facecolor='black')
fig.suptitle('Linear PID – Live Tuning Dashboard', fontsize=20, color='white', y=0.96)

# Main animation area
ax_main = plt.axes([0.05, 0.35, 0.90, 0.55])
ax_main.set_xlim(-0.3, 0.3)
ax_main.set_ylim(-0.25, 0.45)
ax_main.set_aspect('equal', adjustable='box')
ax_main.set_adjustable('box')
ax_main.axis('off')
ax_main.set_facecolor('none')

# Create a subtle vertical gradient background (black at bottom -> dark green at top)
g_h = 256
grad = np.ones((g_h, 1, 3))
top = np.array([6/255, 30/255, 12/255])  # dark green
bot = np.array([0, 0, 0])               # black
for i in range(g_h):
    t = i / (g_h - 1)
    grad[i, 0, :] = bot * (1 - t) + top * t
ax_main.imshow(grad, aspect='auto', extent=( -0.3, 0.3, -0.25, 0.45 ), zorder=-10)

# Rail: we'll draw a glowing core + bright rod
rail_glow_outer, = ax_main.plot([], [], color='#AAFF66', lw=36, alpha=0.06, solid_capstyle='round', zorder=2)
rail_glow_mid,   = ax_main.plot([], [], color='#A7FF33', lw=22, alpha=0.18, solid_capstyle='round', zorder=3)
rail, = ax_main.plot([], [], color='#7CFF00', lw=8, solid_capstyle='round', zorder=5)

# Ball: use patches to draw shaded red sphere + rim/highlight
# Use the data transform (transData) so Circle radii are in data units
ball_shadow = Circle((0, 0), 0.042, color=(0, 0, 0, 0.35), zorder=6, transform=ax_main.transData)
ball_main = Circle((0, 0), 0.036, color='#c92b2b', ec='#5b0000', lw=2, zorder=8, transform=ax_main.transData)
ball_highlight = Circle((0, 0), 0.012, color=(1, 1, 1, 0.6), zorder=9, transform=ax_main.transData)
ax_main.add_patch(ball_shadow)
ax_main.add_patch(ball_main)
ax_main.add_patch(ball_highlight)

# ----------------------- inset real-time plot (see-through) -----------------------
# Top-right inset showing setpoint and position over time
ax_plot = plt.axes([0.62, 0.64, 0.34, 0.27], facecolor=(0, 0, 0, 0.12), zorder=7)
ax_plot.set_xlim(0, history_window)
ax_plot.set_ylim(-0.30, 0.30)
ax_plot.set_title('Setpoint and Position (recent)', fontsize=11, color='white')
ax_plot.tick_params(colors='white', which='both')
for sp in ax_plot.spines.values():
    sp.set_color((0.6, 1.0, 0.4, 0.18))

plot_color = '#AAFF33'
line_sp, = ax_plot.plot([], [], lw=2.25, linestyle='--', color=plot_color, alpha=0.5, label='setpoint')
line_pos, = ax_plot.plot([], [], lw=2.5, linestyle='-', color=plot_color, alpha=0.5, label='position')
ax_plot.legend(loc='upper right', fontsize=9, framealpha=0.12, facecolor=(0,0,0,0.0), edgecolor=(0,1,0,0.06), labelcolor='white')

# Live info text
info = ax_main.text(0.02, 0.92, "", transform=ax_main.transAxes,
                    fontsize=16, color='white', fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor='#0b1b0b', alpha=0.6))

# ========================== SLIDERS ==========================
slider_color = '#3f7f00'   # darker lime/olive for sliders — darker than the bright rail
slider_bg    = '#071006'   # very dark greenish background for slider track

# Setpoint slider
ax_sp = plt.axes([0.20, 0.22, 0.60, 0.04], facecolor=slider_bg)
s_sp = Slider(ax_sp, 'Setpoint (m)', -0.23, 0.23, valinit=setpoint, valstep=0.01, color=slider_color)
s_sp.valtext.set_color('white')

# Kp slider
ax_kp = plt.axes([0.20, 0.16, 0.60, 0.04], facecolor=slider_bg)
s_kp = Slider(ax_kp, 'Kp', 0.0, 100.0, valinit=Kp, valstep=0.5, color=slider_color)
s_kp.valtext.set_color('white')

# Ki slider
ax_ki = plt.axes([0.20, 0.10, 0.60, 0.04], facecolor=slider_bg)
s_ki = Slider(ax_ki, 'Ki', 0.0, 10.0, valinit=Ki, valstep=0.1, color=slider_color)
s_ki.valtext.set_color('white')

# Kd slider
ax_kd = plt.axes([0.20, 0.04, 0.60, 0.04], facecolor=slider_bg)
s_kd = Slider(ax_kd, 'Kd', 0.0, 20.0, valinit=Kd, valstep=0.2, color=slider_color)
s_kd.valtext.set_color('white')

# add a subtle 3D texture to the slider axes: a light top stripe and inner shadow
def style_slider_axis(ax):
    # darker base
    ax.set_facecolor('none')
    bb = ax.get_position()
    # draw on the axes a small faux-gradient using an image
    grad_h = 32
    # darker textured gradient for the slider background
    g = np.ones((grad_h, 1, 3)) * np.array([6/255, 12/255, 6/255])
    for i in range(grad_h):
        t = i/(grad_h-1)
        # subtle brighter stripe on top and darker bottom
        g[i, 0, :] = (np.array([10/255, 36/255, 14/255]) * (1 - t) + np.array([4/255, 10/255, 4/255]) * t)
    ax.imshow(g, aspect='auto', extent=(0, 1, 0, 1), transform=ax.transAxes, zorder=0)
    # soft top highlight
    ax.add_patch(Rectangle((0, 0.7), 1, 0.3, transform=ax.transAxes, color=(1,1,1,0.02), zorder=2))

for a in (ax_sp, ax_kp, ax_ki, ax_kd):
    style_slider_axis(a)

# ========================== LINK SLIDERS TO VARIABLES ==========================
def update_params():
    global setpoint, Kp, Ki, Kd
    setpoint = s_sp.val
    Kp = s_kp.val
    Ki = s_ki.val
    Kd = s_kd.val

s_sp.on_changed(lambda val: update_params())
s_kp.on_changed(lambda val: update_params())
s_ki.on_changed(lambda val: update_params())
s_kd.on_changed(lambda val: update_params())

# ========================== ANIMATION ==========================
def animate(frame):
    global x, v, integral, prev_error, t, history_t, history_sp, history_pos

    error = setpoint - x
    integral += error * dt
    derivative = (error - prev_error) / dt
    output = Kp * error + Ki * integral + Kd * derivative
    prev_error = error

    angle_deg = np.clip(output, -38, 38)
    theta = np.radians(angle_deg)

    a = g * np.sin(theta)
    v += a * dt
    x += v * dt
    x = np.clip(x, -L/2, L/2)

    # time / history
    t += dt
    history_t.append(t)
    history_sp.append(setpoint)
    history_pos.append(x)
    # keep only last window seconds
    start_t = t - history_window
    if start_t < 0:
        start_t = 0.0
    rx = np.linspace(-L/2, L/2, 500)
    ry = rx * np.tan(theta) + 0.09
    # glowing rails behind the main rod
    rail_glow_outer.set_data(rx, ry)
    rail_glow_mid.set_data(rx, ry)
    rail.set_data(rx, ry)

    # ball position (on the tilted rail)
    by = x * np.tan(theta) + 0.09
    # update patch positions for a shaded sphere with shadow/highlight
    ball_shadow.center = (x, by - 0.010)
    ball_main.center = (x, by)
    # offset highlight slightly toward the upper-left for a light source
    ball_highlight.center = (x - 0.01, by + 0.01)

    # update inset plot data (slice for visible window)
    # find first index where time >= start_t
    if history_t:
        idx_start = 0
        for i, tt in enumerate(history_t):
            if tt >= start_t:
                idx_start = i
                break
        xs = history_t[idx_start:]
        line_sp.set_data(xs, history_sp[idx_start:])
        line_pos.set_data(xs, history_pos[idx_start:])
        ax_plot.set_xlim(start_t, start_t + history_window)

    # Live info
    info.set_text(
        f"Setpoint : {setpoint:+.3f} m\n"
        f"Position : {x:+.3f} m\n"
        f"Tilt     : {angle_deg:+.1f}°\n"
        f"Kp={Kp:5.1f} │ Ki={Ki:4.2f} │ Kd={Kd:4.1f}"
    )

    return rail_glow_outer, rail_glow_mid, rail, ball_shadow, ball_main, ball_highlight, line_sp, line_pos

ani = FuncAnimation(fig, animate, interval=int(dt*1000), cache_frame_data=False)

# Fullscreen on Pi
mng = plt.get_current_fig_manager()
mng.full_screen_toggle()

plt.show()