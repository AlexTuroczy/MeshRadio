"""
Lightweight battlefield visualiser
----------------------------------
• Tanks  → blue circles (+ optional dashed radio radius)
• HQ     → yellow star
• Target → red X
• Links  → white dashed lines when tanks can radio each other
• Terrain→ 'terrain' colormap heat‑map
"""

from __future__ import annotations
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------
#  A global figure / axis so we can reuse them every frame
# ---------------------------------------------------------------------
_FIG = None
_AX  = None

def init_live(*, figsize=(7, 7), cmap="terrain", link_colour="white",
              show_radius=False):
    """
    Call once before your simulation loop to switch matplotlib to
    interactive mode and to create the figure we will update in‑place.
    """
    global _FIG, _AX
    plt.ion()                       # interactive / non‑blocking
    _FIG, _AX = plt.subplots(figsize=figsize)
    _FIG.canvas.manager.set_window_title("Mesh‑Radio Simulation")
    # store defaults for later
    _AX._viz_cmap         = cmap
    _AX._viz_link_colour  = link_colour
    _AX._viz_show_radius  = show_radius
    _AX.set_aspect("equal")
    _FIG.show()
    return _FIG, _AX                # handy if you want to tweak styling


def render(state: dict):
    """
    Refresh the live window using the current environment state.
    Must call init_live() beforehand.
    """
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
    _AX.set_xlabel("X (m)")
    _AX.set_ylabel("Y (m)")
    _AX.set_title("Battle‑field overview")

    # ------------------------------------------------------------------
    # 7.  Draw & yield control back to Python
    # ------------------------------------------------------------------
    _FIG.canvas.draw_idle()
    plt.pause(0.001)                # ~1 ms; keeps UI responsive

def hold() -> None:
    """
    Switch back to blocking mode and keep the live window open until the
    user closes it manually.  Call this *after* your simulation loop.
    """
    plt.ioff()          # leave interactive mode
    if _FIG is not None:
        _FIG.canvas.draw_idle()
    plt.show()          # this call is now blocking
