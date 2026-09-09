"""Model-complexity switches for the single-tree physics chain.

A final review found the CO2 channel deviating 26-40% from a direct FaIR run
over the study period. The cause is not a coding bug but a genuine modelling
choice left implicit: ``green_carbon`` (``nbs.response``) returns the
*scenario-conditioned* marginal airborne fraction under ssp245, while
``A_CO2_W_M2_PER_KG`` is the *present-day linear* radiative efficiency --
but FaIR's own CO2 forcing is logarithmic, and the ssp245 background rises
from about 424 ppm in 2025 to about 624 ppm by 2149.

Rather than picking one formulation, both are made computable and
comparable through the ``co2_forcing`` switch below, so the difference
becomes a documented sensitivity rather than a hidden bias. Three further
model choices -- the albedo channel, the disturbance regime, and which
airborne-fraction curve represents the carbon sink -- get the same
treatment.

``"linear"`` is what the talk's slide 21 derives (a constant radiative
efficiency). ``"logarithmic"`` closely approximates what FaIR actually
computes internally (marginal forcing against the rising background
concentration) -- see ``nbs.forcing.phi_co2_background`` for the size of
that approximation. The default
below is ``"logarithmic"`` because it is the scenario-consistent choice; every
other switch defaults to what was already committed before this module
existed, so that ``ModelConfig()`` reproduces today's behaviour except for
this one field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Co2Forcing = Literal["linear", "logarithmic"]
Disturbance = Literal["off", "deterministic", "stochastic"]
CarbonSink = Literal["scenario", "preindustrial"]


@dataclass(frozen=True)
class ModelConfig:
    """One point in the four-switch space of model-complexity choices.

    Every field isolates one physical claim so its contribution to Delta-T
    can be shown as a sensitivity on its own slide (see ``nbs.variants``).
    """

    co2_forcing: Co2Forcing = "logarithmic"
    """Which CO2 radiative-forcing law to use.

    ``"linear"``: constant radiative efficiency ``A_CO2_W_M2_PER_KG``, the
    form slide 21 derives from a first-order Taylor expansion of the
    logarithmic law around today's concentration. ``"logarithmic"``: the
    marginal forcing evaluated against the actual rising ssp245 background
    (``nbs.forcing.phi_co2_background``), a close standard approximation of
    what FaIR itself computes (FaIR's default ``meinshausen2020`` forcing
    law, not the fixed Myhre et al. coefficient this uses -- see
    ``nbs.forcing.phi_co2_background`` for the size of the gap between them).
    This is the switch the 26-40% CO2-channel deviation traces back to.
    """

    albedo: bool = True
    """Whether the albedo channel phi_alpha (slide 22) contributes at all.

    ``False`` sets phi_albedo identically to zero, isolating the pure carbon
    accounting from the darkening-canopy effect that makes boreal
    afforestation a net-warming intervention for its first few decades
    (slide 14's "light bulb that never goes out").
    """

    disturbance: Disturbance = "deterministic"
    """How stand-loss risk (fire, storm, pests -- slide on the shrinking
    sink) enters the trajectory.

    ``"off"``: no disturbance at all (a species with its disturbance
    probability zeroed). ``"deterministic"``: today's committed behaviour, an
    expected-value drain applied continuously. ``"stochastic"``: discrete
    Monte-Carlo disturbance events; in the single-tree path this is one
    seeded realisation rather than the full 1000-member ensemble.
    """

    carbon_sink: CarbonSink = "scenario"
    """Which airborne-fraction curve g_C represents the carbon sink (slide 13).

    ``"scenario"``: today's committed behaviour, the marginal airborne
    fraction of a pulse superimposed on the full ssp245 background
    (``nbs.response.green_carbon``) -- sink saturation under a warming,
    rising-CO2 world is included. ``"preindustrial"``: the textbook Joos et
    al. (2013) four-box impulse response for a pulse against a flat,
    pre-industrial-style background (``nbs.response.green_carbon_preindustrial``),
    which is more optimistic about how much of the pulse leaves the
    atmosphere because it does not see the saturating sinks of a
    high-CO2 world.
    """

    @property
    def label_de(self) -> str:
        """Short German label for figure legends."""
        co2 = "log" if self.co2_forcing == "logarithmic" else "lin"
        albedo = "+Albedo" if self.albedo else "-Albedo"
        dist = {
            "off": "-Störung",
            "deterministic": "Störung(E)",
            "stochastic": "Störung(MC)",
        }[self.disturbance]
        sink = "Sättigung" if self.carbon_sink == "scenario" else "vorind."
        return f"{co2}, {albedo}, {dist}, {sink}"

    def describe_de(self) -> str:
        """One-line German description of this configuration, for slides."""
        co2 = (
            "logarithmischer CO2-Antrieb gegen die Hintergrundkonzentration"
            if self.co2_forcing == "logarithmic"
            else "linearer CO2-Antrieb mit konstanter Strahlungseffizienz"
        )
        albedo = "mit Albedo-Kanal" if self.albedo else "ohne Albedo-Kanal"
        dist = {
            "off": "ohne Störung",
            "deterministic": "mit Störung (Erwartungswert)",
            "stochastic": "mit Störung (stochastisch)",
        }[self.disturbance]
        sink = (
            "szenario-konditionierte Senke (mit Sättigung)"
            if self.carbon_sink == "scenario"
            else "vorindustrielle Senke (Lehrbuchkurve)"
        )
        return f"{co2}, {albedo}, {dist}, {sink}."
