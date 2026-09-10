"""Helpers for editing docs/slides/dissvortrag.pptx safely.

This module exists because hand-editing this deck has broken it before:
hand-written OMML for a formula once made the file refuse to save (see
``add_latex_line`` below), and a defective landmask once shipped straight
to a slide because nobody looked at the rendered image (see the project's
own commit history / spec documents). The functions here encode the safety
rules that grew out of those incidents:

  * ``check_not_locked`` refuses to touch the deck while PowerPoint has it
    open (PowerPoint's own ``~$dissvortrag.pptx`` lock file is the tell --
    if it is there, PowerPoint will silently clobber any change made here
    the next time a human hits save).
  * ``backup`` is meant to be called before every write, so a bad edit can
    always be rolled back.
  * ``add_latex_line`` sets formulas as plain text, never as hand-authored
    OMML XML.
  * ``verify_deck`` reopens the file from disk after a write and returns
    the slide count, so a corrupted save is caught immediately rather than
    discovered the next time someone opens the deck in PowerPoint.

Every function that touches a deck takes an explicit ``deck_path`` (and,
for ``backup``, ``workspace_dir``) keyword argument defaulting to the real
project paths, so callers get sane defaults in normal use while tests can
point every function at a throwaway copy in ``tmp_path`` -- never at the
real presentation.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Iterable

from pptx import Presentation
from pptx.shapes.base import BaseShape
from pptx.slide import Slide
from pptx.util import Emu, Inches, Pt

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DECK_PATH = REPO_ROOT / "docs" / "slides" / "dissvortrag.pptx"
WORKSPACE_DIR = REPO_ROOT / "docs" / "slides" / "workspace"


def _lock_path(deck_path: Path) -> Path:
    """PowerPoint's own lock-file convention: ``~$<name>``."""
    return deck_path.parent / f"~${deck_path.name}"


# ---------------------------------------------------------------------------
# Safety: lock check and backup
# ---------------------------------------------------------------------------


def check_not_locked(*, deck_path: Path = DECK_PATH) -> None:
    """Raise ``RuntimeError`` if ``deck_path`` is currently open in PowerPoint.

    PowerPoint marks an open file with a sibling lock file named
    ``~$<filename>``. If that lock file exists, the deck is open somewhere
    and PowerPoint will overwrite any change made here the next time a
    human saves from the app -- so every write path in this module must
    call this first and stop rather than proceed.
    """
    lock = _lock_path(Path(deck_path))
    if lock.exists():
        raise RuntimeError(
            f"Deck is locked (open in PowerPoint): {lock}. "
            "Close PowerPoint before writing to the deck."
        )


def backup(step: str, *, deck_path: Path = DECK_PATH, workspace_dir: Path = WORKSPACE_DIR) -> Path:
    """Copy ``deck_path`` into ``workspace_dir`` with a timestamped name.

    The name follows ``dissvortrag_pre_<step>_<timestamp>.pptx`` (timestamp
    ``YYYYMMDD_HHMMSS``), matching the convention already used in this
    project's ``docs/slides/workspace/`` directory (which is git-ignored).
    Returns the path to the new copy. Does not check the lock: a backup of
    a currently-open deck is still useful and harmless to make; only writes
    to the primary deck are gated by ``check_not_locked``.
    """
    deck_path = Path(deck_path)
    workspace_dir = Path(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = deck_path.stem
    dest = workspace_dir / f"{stem}_pre_{step}_{timestamp}.pptx"

    dest.write_bytes(deck_path.read_bytes())
    return dest


# ---------------------------------------------------------------------------
# Open / save
# ---------------------------------------------------------------------------


def open_deck(*, deck_path: Path = DECK_PATH) -> Presentation:
    """Open ``deck_path`` for editing. Refuses if the deck is locked."""
    check_not_locked(deck_path=deck_path)
    return Presentation(str(deck_path))


def save_deck(prs: Presentation, *, deck_path: Path = DECK_PATH) -> None:
    """Save ``prs`` to ``deck_path``. Refuses if the deck is locked.

    Callers should ``backup()`` before calling this and ``verify_deck()``
    after, per this project's write protocol.
    """
    check_not_locked(deck_path=deck_path)
    prs.save(str(deck_path))


# ---------------------------------------------------------------------------
# Slide construction
# ---------------------------------------------------------------------------


def add_slide(prs: Presentation, layout_name_or_index):
    """Append a new slide using the given layout and return it.

    ``layout_name_or_index`` may be an ``int`` index into
    ``prs.slide_layouts``, or a ``str`` matched against each layout's
    ``.name``. Raises ``KeyError`` for an unknown layout name.
    """
    if isinstance(layout_name_or_index, int):
        layout = prs.slide_layouts[layout_name_or_index]
    else:
        layout = next(
            (l for l in prs.slide_layouts if l.name == layout_name_or_index), None
        )
        if layout is None:
            known = ", ".join(l.name for l in prs.slide_layouts)
            raise KeyError(
                f"unknown slide layout {layout_name_or_index!r}; known layouts: {known}"
            )
    return prs.slides.add_slide(layout)


def set_title(slide: Slide, text: str) -> None:
    """Set the slide's title placeholder text."""
    title = slide.shapes.title
    if title is None:
        raise ValueError("slide has no title placeholder")
    title.text_frame.text = text


def add_body(slide: Slide, lines: Iterable[str]) -> BaseShape:
    """Add each of ``lines`` as its own paragraph.

    Reuses the slide's body placeholder (the first non-title placeholder)
    if one exists; otherwise adds a plain text box sized to the slide's
    usable content area. Returns the shape holding the text.
    """
    lines = list(lines)
    body = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx != 0:  # idx 0 is conventionally the title
            body = ph
            break

    if body is None:
        prs = slide.part.package.presentation_part.presentation
        left, top = Inches(0.5), Inches(1.5)
        width = prs.slide_width - Inches(1.0)
        height = prs.slide_height - Inches(2.0)
        body = slide.shapes.add_textbox(left, top, width, height)

    tf = body.text_frame
    tf.word_wrap = True
    tf.clear()
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
    return body


def add_picture_slide(slide: Slide, png_path: Path, caption: str | None = None) -> BaseShape:
    """Embed ``png_path`` on ``slide``, centred, with an optional caption
    text box beneath it. Returns the picture shape.

    Raises ``FileNotFoundError`` if ``png_path`` does not exist -- silently
    skipping a missing figure would leave a slide with a hole in it and no
    error to explain why.
    """
    png_path = Path(png_path)
    if not png_path.exists():
        raise FileNotFoundError(f"figure not found: {png_path}")

    prs = slide.part.package.presentation_part.presentation
    slide_width = prs.slide_width
    slide_height = prs.slide_height

    max_width = slide_width - Inches(1.0)
    max_height = slide_height - Inches(2.5)

    picture = slide.shapes.add_picture(str(png_path), Inches(0), Inches(0))
    scale = min(max_width / picture.width, max_height / picture.height, 1.0)
    picture.width = int(picture.width * scale)
    picture.height = int(picture.height * scale)
    picture.left = int((slide_width - picture.width) / 2)
    picture.top = Inches(1.3)

    if caption:
        cap_top = picture.top + picture.height + Inches(0.15)
        cap_box = slide.shapes.add_textbox(
            Inches(0.5), cap_top, slide_width - Inches(1.0), Inches(0.5)
        )
        tf = cap_box.text_frame
        tf.word_wrap = True
        tf.text = caption
        for p in tf.paragraphs:
            p.font.size = Pt(12)
            p.font.italic = True

    return picture


def add_latex_line(
    slide: Slide,
    latex: str,
    *,
    left: Emu | None = None,
    top: Emu | None = None,
    width: Emu | None = None,
    height: Emu | None = None,
    font_size: Pt = Pt(18),
) -> BaseShape:
    """Add ``latex`` to ``slide`` as a plain text box, verbatim.

    Why text and not OMML: PowerPoint formulas are natively stored as OMML
    (Office Math Markup Language) XML, and python-pptx has no builtin
    LaTeX-to-OMML converter. Earlier in this project someone hand-authored
    OMML XML to get a formula onto a slide -- and that hand-written markup
    broke the deck's ability to save at all, costing a repair. Setting the
    LaTeX source as ordinary text avoids the entire OMML code path: the
    file stays valid, python-pptx and PowerPoint agree on how to read it,
    and it can be re-edited by anyone who knows LaTeX, not just someone
    willing to hand-write Office Math Markup. Do not "upgrade" this to emit
    OMML -- see the incident above.
    """
    prs = slide.part.package.presentation_part.presentation
    if left is None:
        left = Inches(0.5)
    if top is None:
        top = Inches(1.5)
    if width is None:
        width = prs.slide_width - Inches(1.0)
    if height is None:
        height = Inches(0.6)

    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.text = latex
    for p in tf.paragraphs:
        p.font.size = font_size
        p.font.name = "Cambria Math"
    return box


# ---------------------------------------------------------------------------
# Reordering
# ---------------------------------------------------------------------------


def move_slide(prs: Presentation, from_idx: int, to_idx: int) -> None:
    """Move the slide at ``from_idx`` to position ``to_idx`` (0-based).

    Used to shuffle a replaced placeholder slide into the backup section
    of the deck rather than deleting it -- this project's rule is that
    nothing gets deleted, only moved out of the way.
    """
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    xml_slides.remove(slides[from_idx])
    xml_slides.insert(to_idx, slides[from_idx])


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify_deck(path: Path) -> int:
    """Reopen the deck at ``path`` from disk and return its slide count.

    Raises if the file cannot be opened as a valid presentation -- callers
    should treat any exception here as "the last write corrupted the file,
    roll back to the most recent backup" per this project's write protocol.
    """
    prs = Presentation(str(path))
    return len(prs.slides)
