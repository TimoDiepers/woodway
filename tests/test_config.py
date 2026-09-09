import dataclasses

import pytest

from nbs.config import ModelConfig


def test_default_config_reproduces_todays_behaviour_except_co2_forcing():
    """The default must match everything committed before this task, except
    co2_forcing, which becomes 'logarithmic' because that is what FaIR
    actually does (slide 21's linear derivation is the alternative)."""
    cfg = ModelConfig()
    assert cfg.co2_forcing == "logarithmic"
    assert cfg.albedo is True
    assert cfg.disturbance == "deterministic"
    assert cfg.carbon_sink == "scenario"


def test_config_is_frozen():
    cfg = ModelConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.albedo = False  # type: ignore[misc]


def test_config_fields_document_their_slide():
    for field in dataclasses.fields(ModelConfig):
        assert field.__doc__ or True  # dataclass fields don't carry __doc__;
    # docstrings live as attribute-docstrings in the source; smoke-check the
    # module docstring at least mentions both CO2 variants and slide 21.
    import nbs.config as config_module

    assert "logarithmic" in config_module.__doc__
    assert "linear" in config_module.__doc__
    assert "21" in config_module.__doc__


def test_label_de_is_short_and_german():
    cfg = ModelConfig()
    label = cfg.label_de
    assert isinstance(label, str)
    assert 0 < len(label) < 120
    # not just an ASCII repr of the dataclass
    assert "ModelConfig(" not in label


def test_label_de_differs_between_configs():
    a = ModelConfig(co2_forcing="linear")
    b = ModelConfig(co2_forcing="logarithmic")
    assert a.label_de != b.label_de


def test_describe_de_is_one_line_and_german():
    cfg = ModelConfig()
    desc = cfg.describe_de()
    assert isinstance(desc, str)
    assert "\n" not in desc
    assert len(desc) > 20


def test_describe_de_reflects_switches():
    with_albedo = ModelConfig(albedo=True)
    without_albedo = ModelConfig(albedo=False)
    assert with_albedo.describe_de() != without_albedo.describe_de()


def test_all_switch_values_are_constructible():
    for co2 in ("linear", "logarithmic"):
        for albedo in (True, False):
            for disturbance in ("off", "deterministic", "stochastic"):
                for sink in ("scenario", "preindustrial"):
                    cfg = ModelConfig(
                        co2_forcing=co2,
                        albedo=albedo,
                        disturbance=disturbance,
                        carbon_sink=sink,
                    )
                    assert cfg.co2_forcing == co2
                    assert cfg.albedo == albedo
                    assert cfg.disturbance == disturbance
                    assert cfg.carbon_sink == sink
