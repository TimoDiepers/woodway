"""Tests for scripts/pptx_tools.py.

pptx_tools.py lives outside the nbs package (it is a CLI/editing helper), but
pytest can import it directly because pyproject.toml adds scripts/ to
pythonpath, the same convention test_fetch_data.py uses for fetch_data.

Every test here works against a throwaway deck built fresh in tmp_path (via
python-pptx's own default template) and passes explicit deck_path /
workspace_dir keyword arguments through to the functions under test. Nothing
here ever touches docs/slides/dissvortrag.pptx -- that is the real deck this
tool is meant to edit, and Plan 3's safety rules are explicit that tests must
run against a copy, never the original.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pptx import Presentation

import pptx_tools


def _make_deck(path: Path, n_slides: int = 2) -> Path:
    """Build a minimal, valid .pptx at *path* using python-pptx's own
    default template, with *n_slides* slides added (layout 1, "Title and
    Content"). This is a real, openable deck -- not a stub -- so it is a
    faithful stand-in for dissvortrag.pptx in every test below.
    """
    prs = Presentation()
    layout = prs.slide_layouts[1]
    for i in range(n_slides):
        slide = prs.slides.add_slide(layout)
        if slide.shapes.title is not None:
            slide.shapes.title.text = f"Slide {i}"
    prs.save(str(path))
    return path


# ---------------------------------------------------------------------------
# backup()
# ---------------------------------------------------------------------------


def test_backup_creates_a_readable_copy_with_step_and_timestamp_in_the_name(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx")
    workspace_dir = tmp_path / "workspace"

    result = pptx_tools.backup("mystep", deck_path=deck_path, workspace_dir=workspace_dir)

    assert result.exists()
    assert result.parent == workspace_dir
    assert "mystep" in result.name
    # dissvortrag_pre_<step>_<timestamp>.pptx -- timestamp is digits, not
    # asserting the exact format so this doesn't pin an implementation detail.
    assert re.search(r"\d{4,}", result.name), f"no timestamp-looking digits in {result.name}"

    # readable: opening it must not raise, and it must carry the same content.
    reopened = Presentation(str(result))
    assert len(reopened.slides) == 2


def test_backup_does_not_modify_the_original_deck(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx")
    workspace_dir = tmp_path / "workspace"
    original_bytes = deck_path.read_bytes()

    pptx_tools.backup("mystep", deck_path=deck_path, workspace_dir=workspace_dir)

    assert deck_path.read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# check_not_locked()
# ---------------------------------------------------------------------------


def test_check_not_locked_raises_when_lock_file_exists(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx")
    lock_path = deck_path.parent / f"~${deck_path.name}"
    lock_path.write_text("")

    with pytest.raises(RuntimeError, match=r"(?i)lock|gesperrt|open|geöffnet"):
        pptx_tools.check_not_locked(deck_path=deck_path)


def test_check_not_locked_passes_silently_when_no_lock_file(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx")
    pptx_tools.check_not_locked(deck_path=deck_path)  # must not raise


# ---------------------------------------------------------------------------
# open_deck() / save_deck()
# ---------------------------------------------------------------------------


def test_open_deck_returns_a_presentation_with_expected_slide_count(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=3)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    assert len(prs.slides) == 3


def test_open_deck_refuses_a_locked_deck(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx")
    lock_path = deck_path.parent / f"~${deck_path.name}"
    lock_path.write_text("")

    with pytest.raises(RuntimeError):
        pptx_tools.open_deck(deck_path=deck_path)


def test_save_deck_persists_changes_to_disk(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=1)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    pptx_tools.add_slide(prs, 1)

    pptx_tools.save_deck(prs, deck_path=deck_path)

    reopened = Presentation(str(deck_path))
    assert len(reopened.slides) == 2


def test_save_deck_refuses_a_locked_deck(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx")
    prs = pptx_tools.open_deck(deck_path=deck_path)
    lock_path = deck_path.parent / f"~${deck_path.name}"
    lock_path.write_text("")

    with pytest.raises(RuntimeError):
        pptx_tools.save_deck(prs, deck_path=deck_path)


# ---------------------------------------------------------------------------
# add_slide()
# ---------------------------------------------------------------------------


def test_add_slide_increases_slide_count_by_one(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=2)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    before = len(prs.slides)

    pptx_tools.add_slide(prs, 1)

    assert len(prs.slides) == before + 1


def test_add_slide_accepts_a_layout_index(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)

    slide = pptx_tools.add_slide(prs, 6)  # "Blank" in the default template

    assert slide.slide_layout == prs.slide_layouts[6]


def test_add_slide_accepts_a_layout_name(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)

    slide = pptx_tools.add_slide(prs, "Title Only")

    assert slide.slide_layout.name == "Title Only"


def test_add_slide_raises_on_unknown_layout_name(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)

    with pytest.raises(KeyError):
        pptx_tools.add_slide(prs, "Does Not Exist")


# ---------------------------------------------------------------------------
# set_title() / add_body() / add_latex_line()
# ---------------------------------------------------------------------------


def test_set_title_sets_the_title_placeholder_text(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    slide = pptx_tools.add_slide(prs, 1)

    pptx_tools.set_title(slide, "Ein Titel mit Umlauten: ä ö ü")

    assert slide.shapes.title.text_frame.text == "Ein Titel mit Umlauten: ä ö ü"


def test_add_body_adds_every_line_as_its_own_paragraph(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    slide = pptx_tools.add_slide(prs, 1)

    lines = ["Erste Zeile", "Zweite Zeile", "Dritte Zeile"]
    pptx_tools.add_body(slide, lines)

    all_text = "\n".join(
        p.text for shp in slide.shapes if shp.has_text_frame for p in shp.text_frame.paragraphs
    )
    for line in lines:
        assert line in all_text


def test_add_latex_line_sets_the_formula_as_plain_text_not_omml(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    slide = pptx_tools.add_slide(prs, 6)

    formula = r"m(t) = m_{max}\left(1 - e^{-kt}\right)^{p}"
    shape = pptx_tools.add_latex_line(slide, formula)

    # The formula must appear as ordinary text on the shape...
    assert formula in shape.text_frame.text
    # ...and the shape's XML must contain no OMML markup at all -- setting a
    # formula as OMML is exactly what this function exists to avoid.
    xml = shape._element.xml
    assert "oMath" not in xml, "found OMML markup; add_latex_line must set formulas as text"


def test_add_latex_line_docstring_explains_why_not_omml():
    doc = pptx_tools.add_latex_line.__doc__ or ""
    assert "OMML" in doc
    # the docstring must carry the actual reason, not just the word: this
    # file already broke a save once because of hand-written OMML.
    assert re.search(r"(?i)speicher|save|broke|zerst", doc), (
        "add_latex_line's docstring must explain *why* no OMML, not just assert it"
    )


# ---------------------------------------------------------------------------
# add_picture_slide()
# ---------------------------------------------------------------------------


def test_add_picture_slide_embeds_the_image_and_caption(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    slide = pptx_tools.add_slide(prs, 6)

    # a minimal 1x1 PNG
    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8ffff3f0005fe02fea7d0e0a600000000"
        "49454e44ae426082"
    )
    png_path = tmp_path / "tiny.png"
    png_path.write_bytes(png_bytes)

    pptx_tools.add_picture_slide(slide, png_path, "Bildunterschrift mit ü")

    pictures = [shp for shp in slide.shapes if shp.shape_type == 13]
    assert len(pictures) == 1

    all_text = "\n".join(
        shp.text_frame.text for shp in slide.shapes if shp.has_text_frame
    )
    assert "Bildunterschrift mit ü" in all_text


def test_add_picture_slide_raises_for_a_missing_file(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    slide = pptx_tools.add_slide(prs, 6)

    with pytest.raises(FileNotFoundError):
        pptx_tools.add_picture_slide(slide, tmp_path / "does_not_exist.png", "x")


# ---------------------------------------------------------------------------
# move_slide()
# ---------------------------------------------------------------------------


def test_move_slide_reorders_without_changing_the_slide_count(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    titles = ["A", "B", "C"]
    for t in titles:
        s = pptx_tools.add_slide(prs, 1)
        pptx_tools.set_title(s, t)

    pptx_tools.move_slide(prs, 0, 2)

    assert len(prs.slides) == 3
    new_titles = [s.shapes.title.text_frame.text for s in prs.slides]
    assert new_titles == ["B", "C", "A"]


def test_move_slide_survives_a_save_and_reopen(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=0)
    prs = pptx_tools.open_deck(deck_path=deck_path)
    titles = ["A", "B", "C"]
    for t in titles:
        s = pptx_tools.add_slide(prs, 1)
        pptx_tools.set_title(s, t)
    pptx_tools.move_slide(prs, 0, 2)
    pptx_tools.save_deck(prs, deck_path=deck_path)

    reopened = Presentation(str(deck_path))
    new_titles = [s.shapes.title.text_frame.text for s in reopened.slides]
    assert new_titles == ["B", "C", "A"]


# ---------------------------------------------------------------------------
# verify_deck()
# ---------------------------------------------------------------------------


def test_verify_deck_returns_the_slide_count_of_a_healthy_deck(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=4)
    assert pptx_tools.verify_deck(deck_path) == 4


def test_verify_deck_raises_on_a_deliberately_corrupted_file(tmp_path):
    deck_path = _make_deck(tmp_path / "deck.pptx", n_slides=2)
    # Corrupt it in place: truncate to the first third of the bytes, which
    # breaks the zip/OOXML container structure.
    data = deck_path.read_bytes()
    deck_path.write_bytes(data[: len(data) // 3])

    with pytest.raises(Exception):
        pptx_tools.verify_deck(deck_path)


def test_verify_deck_raises_for_a_nonexistent_file(tmp_path):
    with pytest.raises(Exception):
        pptx_tools.verify_deck(tmp_path / "nope.pptx")
