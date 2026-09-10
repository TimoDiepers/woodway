"""Rendered formulas for the slides, with a colour code that carries meaning.

Two problems this module solves.

**The formulas were not rendered.** Several slides carried LaTeX *source* as
plain text (``\\dot m_{Stör}(t) = p_{Stör}(T)\\, m(t)`` appearing literally on
the slide). That convention exists because hand-authored OMML once broke the
deck's ability to save at all, so nobody wanted to touch the XML again. Going
through a real LaTeX run and inserting the result as an image avoids the OMML
code path entirely and still gives a properly set formula.

**The symbols were not recognisable across slides.** A viewer who has just
learned that the green curve is the CO2 channel should meet the same green
when the CO2 term appears in an equation. So the colours here are not
decorative: they are the same four the result figures already use.

    ROLE_CARBON  #1b7837   everything on the carbon channel
    ROLE_ALBEDO  #d95f02   everything on the albedo / shortwave channel
    ROLE_RISK    #b2182b   disturbance and its parameters
    ROLE_CLIMATE #252525   the balance and the climate response (the "net")
    ROLE_TIME    #7a7a7a   time and integration variables

``nbs.plots`` uses C_CARBON = #1b7837 and C_ALBEDO = #d95f02 for exactly the
two channels, and C_NET = #252525 for their sum; those constants and these
are deliberately the same values.

Rendering needs a working LaTeX installation (latex + dvipng, both standard
in TeX Live and MacTeX). ``latex_available()`` reports whether one is
present, so a caller on a machine without TeX gets a clear failure rather
than a broken image.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROLE_CARBON = "1B7837"
ROLE_ALBEDO = "D95F02"
ROLE_RISK = "B2182B"
ROLE_CLIMATE = "252525"
ROLE_TIME = "7A7A7A"

ROLE_LABELS_DE: dict[str, str] = {
    ROLE_CARBON: "Kohlenstoff — was der Baum bindet",
    ROLE_ALBEDO: "Albedo und Strahlung — was er zusätzlich absorbiert",
    ROLE_RISK: "Störung — was er wieder verlieren kann",
    ROLE_CLIMATE: "Bilanz und Klimaantwort — das Netto",
    ROLE_TIME: "Zeit",
}

_PREAMBLE = r"""
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{xcolor}
\usepackage{amsmath}
\usepackage{amssymb}
"""


def latex_available() -> bool:
    """True when both ``latex`` and ``dvipng`` are on PATH."""
    return bool(shutil.which("latex")) and bool(shutil.which("dvipng"))


def c(role: str, body: str) -> str:
    r"""Wrap *body* in a colour for *role*: ``c(ROLE_CARBON, "m")``.

    Keeping this a function rather than writing ``\textcolor`` by hand means
    a role's colour is defined in exactly one place, and a typo in a hex
    string cannot silently give one symbol a slightly different green than
    the same symbol on the next slide.
    """
    return rf"\textcolor[HTML]{{{role}}}{{{body}}}"


@dataclass(frozen=True)
class Formula:
    """One rendered formula: its LaTeX (with colour markup) and its slide."""

    key: str
    latex: str
    """Display-math body, without the surrounding $$."""
    caption: str = ""
    """Optional plain-text line under the formula, in the climate colour."""


def render(
    latex: str,
    out_path: str,
    *,
    fontsize: int = 26,
    dpi: int = 400,
    color: str = "#252525",
) -> str:
    """Render one display formula to a transparent PNG and return the path.

    Transparent background so the slide's own paper colour shows through, and
    a tight bounding box so the caller can place the image by its own
    geometry rather than guessing at whitespace.
    """
    if not latex_available():
        raise RuntimeError(
            "LaTeX oder dvipng fehlt — ohne beide kann diese Funktion keine "
            "Formel setzen. Installiere TeX Live bzw. MacTeX."
        )
    directory = os.path.dirname(out_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with matplotlib.rc_context({
        "text.usetex": True,
        "text.latex.preamble": _PREAMBLE,
        "font.family": "serif",
    }):
        fig = plt.figure(figsize=(0.1, 0.1))
        fig.text(0.0, 0.0, f"${latex}$", fontsize=fontsize, color=color)
        fig.savefig(
            out_path, dpi=dpi, transparent=True, bbox_inches="tight",
            pad_inches=0.02,
        )
        plt.close(fig)
    return out_path


__all__ = [
    "Formula",
    "ROLE_ALBEDO",
    "ROLE_CARBON",
    "ROLE_CLIMATE",
    "ROLE_LABELS_DE",
    "ROLE_RISK",
    "ROLE_TIME",
    "c",
    "latex_available",
    "render",
]
