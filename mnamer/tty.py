"""Provides an interface for handling user input and printing output."""

import traceback
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from teletype import codes
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import style_format, style_input, style_print

from mnamer.const import SYSTEM
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerEditException,
    MnamerException,
    MnamerSkipException,
)
from mnamer.language import Language
from mnamer.metadata import Metadata, MetadataEpisode
from mnamer.setting_store import SettingStore
from mnamer.types import MessageType
from mnamer.utils import format_dict, format_exception, format_iter

no_style: bool = False
verbose: bool = False


def _chars() -> dict[str, str]:
    if no_style:
        chars = codes.CHARS_ASCII
    else:
        chars = codes.CHARS_DEFAULT
        chars["arrow"] = style_format(chars["arrow"], "magenta")
    return chars


def _abort_helpers() -> tuple[
    ChoiceHelper[MnamerSkipException], ChoiceHelper[MnamerAbortException]
]:
    if no_style:
        style = None
        skip_mnemonic = "[s]"
        quit_mnemonic = "[q]"
    else:
        style = "dark"
        skip_mnemonic = "s"
        quit_mnemonic = "q"
    return (
        ChoiceHelper(MnamerSkipException(), "skip", style, skip_mnemonic),
        ChoiceHelper(MnamerAbortException(), "quit", style, quit_mnemonic),
    )


def _edit_helper() -> ChoiceHelper[MnamerEditException]:
    if no_style:
        return ChoiceHelper(MnamerEditException(), "enter name", None, "[e]")
    return ChoiceHelper(MnamerEditException(), "enter name", "dark", "e")


def _manual_entry(metadata: Metadata) -> Metadata:
    """Prompts for a title typed by hand, returning a copy which uses it."""
    field = "series" if isinstance(metadata, MetadataEpisode) else "name"
    current = getattr(metadata, field, None) or ""
    value = style_input(f"name [{current}]: ").strip()
    if not value:
        return metadata
    updated = deepcopy(metadata)
    setattr(updated, field, value)
    return updated


def _msg_format(body: Any) -> str:
    converter_map: dict[type, Callable[[Any], str]] = {
        dict: format_dict,
        list: format_iter,
        tuple: format_iter,
        set: format_iter,
        MnamerException: format_exception,
    }
    converter: Callable[[Any], str] = converter_map.get(type(body), str)
    return converter(body)


def configure(settings: SettingStore):
    """Sets class variables using a settings instance."""
    global verbose, no_style
    verbose = settings.verbose
    no_style = settings.no_style


def msg(
    body: Any,
    message_type: MessageType = MessageType.INFO,
    debug: bool = False,
):
    if debug and not verbose:
        return
    if no_style:
        print(_msg_format(body))
    else:
        style_print(_msg_format(body), style=message_type.value)


def error(body: Any):
    msg(body, message_type=MessageType.ERROR, debug=False)


def metadata_prompt(matches: list[Metadata]) -> Metadata:  # pragma: no cover
    """Prompts user to choose a match from a list of matches."""
    msg("select match")
    selector = SelectOne([*matches, _edit_helper(), *_abort_helpers()], **_chars())
    choice = selector.prompt()
    if isinstance(choice, MnamerEditException):
        return _manual_entry(matches[0])
    if isinstance(choice, MnamerAbortException | MnamerSkipException):
        raise choice
    return choice


def metadata_guess(metadata: Metadata) -> Metadata:  # pragma: no cover
    """Prompts user to confirm a single match."""
    label = str(metadata)
    if no_style:
        label += " (best guess)"
    else:
        label += style_format(" (best guess)", "blue")
    option = ChoiceHelper(metadata, label)
    selector = SelectOne([option, _edit_helper(), *_abort_helpers()], **_chars())
    choice = selector.prompt()
    if isinstance(choice, MnamerEditException):
        return _manual_entry(metadata)
    if isinstance(choice, MnamerAbortException | MnamerSkipException):
        raise choice
    else:
        return choice


def subtitle_prompt() -> Language:
    msg("select language")
    choices = [ChoiceHelper(language, language.name) for language in Language.all()]
    selector = SelectOne([*choices, *_abort_helpers()], **_chars())
    choice = selector.prompt()
    if isinstance(choice, MnamerAbortException | MnamerSkipException):
        raise choice
    else:
        return choice


def crash_report():  # pragma: no cover
    s = f"""
============================== CRASH REPORT BEGIN ==============================

--------------------------------- environment ----------------------------------

{_msg_format(SYSTEM)}

--------------------------------- stack trace ----------------------------------

{traceback.format_exc()}
=============================== CRASH REPORT END ===============================

Dang, it looks like mnamer crashed! Please consider filling an issue at
https://github.com/jkwill87/mnamer/issues along with this report.
"""
    print(s)
    raise SystemExit(1)
