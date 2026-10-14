"""Net light product: darker canopy plus more low clouds (nbs.light)."""

import os
import subprocess
import sys

import numpy as np

from nbs.albedo_grid import alpha_q_product, monthly_product
from nbs.cloud_grid import cloud_q_product
from nbs.light import light_product, monthly_light_product


def test_light_is_albedo_plus_clouds():
    k = "mf_gemaessigt"
    np.testing.assert_allclose(light_product(k, clouds=True), alpha_q_product(k) + cloud_q_product(k))
    np.testing.assert_allclose(monthly_light_product(k, clouds=True).mean(axis=0), light_product(k, clouds=True), atol=1e-9)


def test_clouds_false_is_albedo_only():
    k = "enf_boreal"
    np.testing.assert_array_equal(light_product(k, clouds=False), alpha_q_product(k))
    np.testing.assert_array_equal(monthly_light_product(k, clouds=False), monthly_product(k))


def test_env_switch_in_fresh_process():
    code = ("import numpy as np; from nbs.light import light_product; from nbs.albedo_grid import alpha_q_product;"
            "assert np.array_equal(light_product('mf_boreal'), alpha_q_product('mf_boreal'))")
    subprocess.run([sys.executable, "-c", code], check=True, env={**os.environ, "NBS_CLOUDS": "0"})
