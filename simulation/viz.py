"""
Lightweight battlefield visualiser
----------------------------------
• Tanks   → blue circles (optionally surrounded by a dashed radio‑radius)
• HQ      → yellow star
• Targets → red X marks
• Links   → white dashed lines when two tanks can hear each other
• Terrain → coloured height‑map ("terrain" colormap by default)

Extras
------
• Runs in *interactive* (non‑blocking) mode so your simulation loop keeps
  executing while the figure is visible.
• Click on a tank to trigger any user‑supplied callback (e.g. destroy it)
  **and** show a short "hit" animation at the tank’s last position.
• Call `viz.hold()` after your loop so the window stays open.

Typical usage
-------------
>>> import viz
>>>
>>> def kill_tank(idx):
...     env.set_tank_destroyed_or_missing(idx)
...     print(f"Tank {idx} destroyed!")
>>>
>>> viz.init_live(click_kill_callback=kill_tank, hit_radius=2.0)
>>> for step in range(100):
...     ...  # your simulation logic
...     viz.render(env.get_state_dict())
>>> viz.hold()
"""

from __future__ import annotations

import math
from typing import Callable, Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
import numpy as np

# ---------------------------------------------------------------------
# Global handles & state ------------------------------------------------
# ---------------------------------------------------------------------
_FIG: Optional[plt.Figure] = None
_AX: Optional[plt.Axes] = None
_LATEST_STATE: Optional[dict] = None        # cache of most recent state
_KILL_CB: Optional[Callable[[int], None]] = None  # callback on click
_HIT_RADIUS: float = 2.0                    # hit‑box radius in map units

# ---------------------------------------------------------------------
# Internal helper: flashy hit‑marker animation -------------------------
# ---------------------------------------------------------------------

def _show_hit_marker(x: float, y: float, duration: float = 0.25):
    """Draw a big red X for *duration* seconds, then remove it."""
    if _AX is None:
        return
    marker = _AX.scatter(
        x,
        y,
        marker="x",
        s=350,
        linewidths=3,
        color="red",
        zorder=6,
    )
    _FIG.canvas.draw_idle()
    plt.pause(duration)
    marker.remove()
    _FIG.canvas.draw_idle()

# ---------------------------------------------------------------------
# Internal helper: mouse‑click handler ---------------------------------
# ---------------------------------------------------------------------

def _on_click(event):
    """Called by matplotlib when the user clicks inside the figure."""
    global _LATEST_STATE, _KILL_CB, _HIT_RADIUS

    # Only proceed if click happened inside our axes and we have state
    if event.inaxes != _AX or _LATEST_STATE is None:
        return

    # Mouse position in data (map) coordinates
    mx, my = float(event.xdata), float(event.ydata)

    # Search for a tank centre within hit radius
    for tank in _LATEST_STATE["tanks"]:
        tx, ty = tank["pos"]
        if math.hypot(mx - tx, my - ty) <= _HIT_RADIUS:
            # 1) trigger user callback first (if any)
            if _KILL_CB is not None:
                _KILL_CB(tank["idx"])
            # 2) show fun hit marker
            _show_hit_marker(tx, ty)
            break  # stop after first hit

# ---------------------------------------------------------------------
# Public API -----------------------------------------------------------
# ---------------------------------------------------------------------

def init_live(
    *,
    figsize=(7, 7),
    cmap: str = "terrain",
    link_colour: str = "white",
    show_radius: bool = False,
    click_kill_callback: Optional[Callable[[int], None]] = None,
    hit_radius: float = 2.0,
):
    """Prepare the live, non‑blocking visualisation."""
    global _FIG, _AX, _KILL_CB, _HIT_RADIUS

    plt.ion()

    _FIG, _AX = plt.subplots(figsize=figsize)
    _FIG.canvas.manager.set_window_title("Mesh‑Radio Simulation")

    # Store visual defaults directly on the axis
    _AX._viz_cmap = cmap
    _AX._viz_link_colour = link_colour
    _AX._viz_show_radius = show_radius

    _KILL_CB = click_kill_callback
    _HIT_RADIUS = float(hit_radius)

    _FIG.canvas.mpl_connect("button_press_event", _on_click)

    _AX.set_aspect("equal")
    _FIG.show()

    return _FIG, _AX


def render(state: dict):
    """Refresh the live window with the current environment *state* dict."""
    global _FIG, _AX, _LATEST_STATE

    if _AX is None:
        raise RuntimeError("viz.init_live() must be called before viz.render()")

    # ------------------------------------------------------------------
    # 1.  Clear previous frame
    # ------------------------------------------------------------------
    _AX.cla()

    # ------------------------------------------------------------------
    # 2.  Terrain
    # ------------------------------------------------------------------
    alt = state["altitude"].T
    _AX.imshow(
        alt,
        origin="lower",
        cmap=_AX._viz_cmap,
        extent=[0, state["map_size"][0], 0, state["map_size"][1]],
        alpha=0.6,
    )

    # ------------------------------------------------------------------
    # 3.  Tanks & optional radio radius
    # ------------------------------------------------------------------
    for tank in state["tanks"]:
        x, y = tank["pos"]
        _AX.scatter(x, y, s=60, edgecolor="k", facecolor="dodgerblue", zorder=3)
        _AX.text(x + 0.8, y + 0.8, str(tank["idx"]), fontsize=8, color="k")
        if _AX._viz_show_radius:
            circ = plt.Circle(
                (x, y),
                tank["radius"],
                linestyle=":",
                linewidth=1,
                fill=False,
                alpha=0.4,
                zorder=2,
            )
            _AX.add_patch(circ)

    # ------------------------------------------------------------------
    # 4.  Links
    # ------------------------------------------------------------------
    for i, j in state["links"]:
        xi, yi = state["tanks"][i]["pos"]
        xj, yj = state["tanks"][j]["pos"]
        _AX.plot([xi, xj], [yi, yj], linestyle="--", linewidth=1,
                 color=_AX._viz_link_colour, zorder=2)

    # ------------------------------------------------------------------
    # 5.  HQ & Targets
    # ------------------------------------------------------------------
    hqx, hqy = state["hq"]
    _AX.scatter(hqx, hqy, marker="*", s=140, edgecolor="k",
                facecolor="yellow", zorder=4)

    for tx, ty in state["targets"]:
        _AX.scatter(tx, ty, marker="X", s=80, edgecolor="k",
                    facecolor="red", zorder=4)

    # ------------------------------------------------------------------
    # 6.  Axis cosmetics
    # ------------------------------------------------------------------
    _AX.set_xlim(0, state["map_size"][0])
    _AX.set_ylim(0, state["map_size"][1])
    _AX.set_xlabel("X (m)")
    _AX.set_ylabel("Y (m)")
    _AX.set_title("Battle‑field overview")

    # ------------------------------------------------------------------
    # 7.  Draw & yield control back to simulation
    # ------------------------------------------------------------------
    _FIG.canvas.draw_idle()
    plt.pause(0.001)

    # cache latest state for click handler
    _LATEST_STATE = state


def hold() -> None:
    """Block program exit and keep the figure open until the user closes it."""
    plt.ioff()
    if _FIG is not None:
        _FIG.canvas.draw_idle()
    plt.show()
