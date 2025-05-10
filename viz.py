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


def render(state: dict,
           *,
           figsize: tuple[int, int] = (7, 7),
           show_radius: bool = False,
           cmap: str = "terrain",
           link_colour: str = "white",
           save_path: str | None = None) -> None:
    # ------------------------------------------------------------------
    # 1.  Terrain -------------------------------------------------------
    fig, ax = plt.subplots(figsize=figsize)
    alt = state["altitude"].T                 # transpose → (x→col, y→row)
    im = ax.imshow(
        alt,
        origin="lower",
        cmap=cmap,
        extent=[0, state["map_size"][0], 0, state["map_size"][1]],
        alpha=0.6,
    )

    # ------------------------------------------------------------------
    # 2.  Tanks & optional radio radius --------------------------------
    for tank in state["tanks"]:
        x, y = tank["pos"]
        ax.scatter(x, y, s=60, edgecolor="k", facecolor="dodgerblue", zorder=3)
        ax.text(x + 0.8, y + 0.8, str(tank["idx"]), fontsize=8, color="k")
        if show_radius:
            circ = plt.Circle(
                (x, y),
                tank["radius"],
                linestyle=":",
                linewidth=1,
                fill=False,
                alpha=0.4,
                zorder=2,
            )
            ax.add_patch(circ)

    # ------------------------------------------------------------------
    # 3.  Links ---------------------------------------------------------
    for i, j in state["links"]:
        xi, yi = state["tanks"][i]["pos"]
        xj, yj = state["tanks"][j]["pos"]
        ax.plot([xi, xj], [yi, yj], linestyle="--", linewidth=1,
                color=link_colour, zorder=2)

    # ------------------------------------------------------------------
    # 4.  HQ & Targets --------------------------------------------------
    hqx, hqy = state["hq"]
    ax.scatter(hqx, hqy, marker="*", s=140, edgecolor="k",
               facecolor="yellow", zorder=4, label="HQ")

    for tx, ty in state["targets"]:
        ax.scatter(tx, ty, marker="X", s=80, edgecolor="k",
                   facecolor="red", zorder=4)

    # ------------------------------------------------------------------
    # 5.  Final touches -------------------------------------------------
    ax.set_xlim(0, state["map_size"][0])
    ax.set_ylim(0, state["map_size"][1])
    ax.set_aspect("equal")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("Battle‑field overview")
    fig.colorbar(im, ax=ax, label="Altitude")

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
