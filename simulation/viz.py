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
  **and** show a short "hit" animation.  You can flash either a PNG
  (e.g. an angry‑king emoji) *next to* the eliminated tank or fall back
  to a red X marker.
• Call `viz.hold()` after your loop so the window stays open.

Typical usage
-------------
>>> import viz
>>>
>>> def kill_tank(idx):
...     env.set_tank_destroyed_or_missing(idx)
...     print(f"Tank {idx} destroyed!")
>>>
>>> viz.init_live(
...     click_kill_callback=kill_tank,
...     hit_radius=2.0,
...     hit_image_path="assets/angry_king.png",   # path to PNG
...     hit_image_zoom=0.12,                      # much smaller now
...     hit_image_offset=(2, 2),                  # show 2 units up/right
... )
>>> for step in range(100):
...     viz.render(env.get_state_dict())
>>> viz.hold()
"""

from __future__ import annotations

import math
from typing import Callable, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.offsetbox as ob
import numpy as np

# ---------------------------------------------------------------------
# Global handles & state ------------------------------------------------
# ---------------------------------------------------------------------
_FIG: Optional[plt.Figure] = None
_AX: Optional[plt.Axes] = None
_LATEST_STATE: Optional[dict] = None        # cache of most recent state
_KILL_CB: Optional[Callable[[int], None]] = None  # callback on click
_HIT_RADIUS: float = 2.0                           # hit‑box radius (map units)
_HIT_IMG: Optional[np.ndarray] = None              # loaded PNG
_HIT_IMG_ZOOM: float = 0.12                       # default much smaller
_HIT_IMG_OFFSET: Tuple[float, float] = (2.0, 2.0) # dx,dy in map units

# ---------------------------------------------------------------------
# Internal helper: flashy hit‑marker animation -------------------------
# ---------------------------------------------------------------------

# ─── overwrite the helper used earlier ─────────────────────────────────
def _show_hit_marker(x: float, y: float, duration_ms: int = 500):
    """
    Draw a temporary hit marker for ~duration_ms milliseconds WITHOUT
    blocking the GUI or the sim loop.
    """
    if _AX is None:
        return

    # ── 1. create whichever artist we're using ───────────────────────
    if _HIT_IMG is not None:
        dx, dy  = _HIT_IMG_OFFSET
        img_box = ob.OffsetImage(_HIT_IMG, zoom=_HIT_IMG_ZOOM)
        artist  = ob.AnnotationBbox(img_box,
                                    (x + dx, y + dy),
                                    frameon=False,
                                    zorder=6)
        _AX.add_artist(artist)
    else:                                    # red X fallback
        artist = _AX.scatter(x, y,
                             marker="x", s=250, linewidths=3,
                             color="red", zorder=6)

    _FIG.canvas.draw_idle()                  # show immediately

    # ── 2. schedule its disappearance with a one‑shot Timer ───────────
    def _hide_artist():
        # First just make it invisible (always works) …
        artist.set_visible(False)

        # … then *try* to remove it from the Axes; ignore if unsupported
        try:
            artist.remove()                  # PathCollection works
        except (NotImplementedError, ValueError):
            # AnnotationBbox in some MPL versions lacks .remove()
            if artist in _AX.artists:
                _AX.artists.remove(artist)

        _FIG.canvas.draw_idle()

    t = _FIG.canvas.new_timer(interval=duration_ms)
    t.single_shot = True
    t.add_callback(_hide_artist)
    t.start()


# ---------------------------------------------------------------------
# Internal helper: mouse‑click handler ---------------------------------
# ---------------------------------------------------------------------

def _on_click(event):
    """Called by matplotlib when the user clicks inside the figure."""
    if event.inaxes != _AX or _LATEST_STATE is None:
        return

    mx, my = float(event.xdata), float(event.ydata)

    for tank in _LATEST_STATE["tanks"]:
        tx, ty = tank["pos"]
        if math.hypot(mx - tx, my - ty) <= _HIT_RADIUS:
            if _KILL_CB is not None:
                _KILL_CB(tank["idx"])
            _show_hit_marker(tx, ty)
            break

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
    hit_image_path: Optional[str] = None,
    hit_image_zoom: float = 0.12,
    hit_image_offset: Tuple[float, float] = (2.0, 2.0),
):
    """Prepare the live, non‑blocking visualisation.

    Parameters
    ----------
    hit_image_zoom : float
        How much to scale the PNG (smaller number → smaller image).
    hit_image_offset : (dx, dy)
        Offset in *map units* to place the PNG *next to* the tank centre.
    """
    global _FIG, _AX, _KILL_CB, _HIT_RADIUS, _HIT_IMG, _HIT_IMG_ZOOM, _HIT_IMG_OFFSET

    plt.ion()

    _FIG, _AX = plt.subplots(figsize=figsize)
    _FIG.canvas.manager.set_window_title("Mesh‑Radio Simulation")

    # Axis‑stored visual defaults
    _AX._viz_cmap = cmap
    _AX._viz_link_colour = link_colour
    _AX._viz_show_radius = show_radius

    # Interaction settings
    _KILL_CB = click_kill_callback
    _HIT_RADIUS = float(hit_radius)

    # Load hit marker image if provided
    if hit_image_path is not None:
        try:
            _HIT_IMG = mpimg.imread(hit_image_path)
            _HIT_IMG_ZOOM = hit_image_zoom
            _HIT_IMG_OFFSET = hit_image_offset
        except FileNotFoundError:
            print(f"[viz] Could not find hit image at '{hit_image_path}'. "
                  "Falling back to red X marker.")
            _HIT_IMG = None
    else:
        _HIT_IMG = None

    # Connect click handler
    _FIG.canvas.mpl_connect("button_press_event", _on_click)

    _AX.set_aspect("equal")
    _FIG.show()

    return _FIG, _AX


def render(state: dict):
    """Refresh the live window with the current environment state."""
    global _LATEST_STATE

    if _AX is None:
        raise RuntimeError("viz.init_live() must be called before viz.render()")

    _AX.cla()

    # Terrain
    alt = state["altitude"].T
    _AX.imshow(
        alt,
        origin="lower",
        cmap=_AX._viz_cmap,
        extent=[0, state["map_size"][0], 0, state["map_size"][1]],
        alpha=0.6,
    )

    # Tanks
    for tank in state["tanks"]:
        x, y = tank["pos"]
        _AX.scatter(x, y, s=60, edgecolor="k", facecolor="dodgerblue", zorder=3)
        _AX.text(x + 0.8, y + 0.8, str(tank["idx"]), fontsize=8, color="k")
        if _AX._viz_show_radius:
            circ = plt.Circle((x, y), tank["radius"], linestyle=":", linewidth=1,
                               fill=False, alpha=0.4, zorder=2)
            _AX.add_patch(circ)

    # Links
    for i, j in state["links"]:
        xi, yi = state["tanks"][i]["pos"]
        xj, yj = state["tanks"][j]["pos"]
        _AX.plot([xi, xj], [yi, yj], linestyle="--", linewidth=1,
                 color=_AX._viz_link_colour, zorder=2)

    # HQ & targets
    hqx, hqy = state["hq"]
    _AX.scatter(hqx, hqy, marker="*", s=140, edgecolor="k", facecolor="yellow", zorder=4)
    for tx, ty in state["targets"]:
        _AX.scatter(tx, ty, marker="X", s=80, edgecolor="k", facecolor="red", zorder=4)

    # Axis cosmetics
    _AX.set_xlim(0, state["map_size"][0])
    _AX.set_ylim(0, state["map_size"][1])
    _AX.set_xlabel("X (m)")
    _AX.set_ylabel("Y (m)")
    _AX.set_title("Battle‑field overview")

    _FIG.canvas.draw_idle()
    plt.pause(0.001)

    _LATEST_STATE = state


def hold() -> None:
    """Keep the figure open until the user closes it."""
    plt.ioff()
    if _FIG is not None:
        _FIG.canvas.draw_idle()
    plt.show()
