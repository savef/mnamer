import datetime as dt
import sys
from pathlib import Path

import pytest

from mnamer.metadata import MetadataEpisode, MetadataMovie
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MediaType

pytestmark = pytest.mark.local


def test_parse__media__movie():
    target = Target(Path("ninja turtles (1990).mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.MOVIE


def test_parse__media__episode():
    target = Target(Path("ninja turtles s01e01.mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.EPISODE


def test_parse__quality():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.quality == "1080p dolby digital"


def test_parse__group():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.group == "RARGB"


def test_parse__container():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert target.metadata.container == ".mp4"


def test_parse__date():
    file_path = Path("the.colbert.show.2010.10.01.avi")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.date == dt.date(2010, 10, 1)


def test_parse__episode():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.episode == 4


def test_parse__season():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.season == 1


def test_parse__series():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.series == "Ninja Turtles"


def test_parse__year():
    file_path = Path("the.goonies.1985")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.year == 1985


def testparse__name():
    file_path = Path("the.goonies.1985")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.name == "The Goonies"


@pytest.mark.parametrize("media", MediaType)
def test_media__override(media: MediaType):
    target = Target(Path(), SettingStore(media=media))
    assert target.metadata.to_media_type() == media


def test_directory__movie():
    movie_path = Path("/some/movie/path").absolute()
    target = Target(
        Path(), SettingStore(media=MediaType.MOVIE, movie_directory=movie_path)
    )
    assert target.directory == movie_path


def test_directory__episode():
    episode_path = Path("/some/episode/path").absolute()
    target = Target(
        Path(),
        SettingStore(media=MediaType.EPISODE, episode_directory=episode_path),
    )
    assert target.directory == episode_path


def test_ambiguous_subtitle_language():
    target = Target(
        Path("Subs/Nancy.Drew.S01E01.WEBRip.x264-ION10.srt"), SettingStore()
    )
    assert target.metadata.language is None


def test_destination__simple():
    pass  # TODO


def test_destination__relative_directory_lowered():
    """Every part of a relative configured directory receives --lower."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("Movies/{name[0]}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("movies/n/ninja turtles (1990).mkv").resolve()


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_preserves_literal_parts():
    """Literal parts of an absolute configured directory survive --lower."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("/Media Library/Movies"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("/Media Library/Movies/ninja turtles (1990).mkv")


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_transforms_template_parts():
    """Template parts within an absolute configured directory are transformed."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("/Media Library/{name[0]}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("/Media Library/n/ninja turtles (1990).mkv")


def test_destination__format_template_directory_components_transformed():
    """Directory components emitted by the format template are post-processed."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_format="{name}/{name} ({year}).{extension}",
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert (
        target.destination == Path("ninja turtles/ninja turtles (1990).mkv").resolve()
    )


def test_destination__relative_directory_scene():
    """--scene applies to literal and templated parts of a relative directory."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        scene=True,
        movie_directory=Path("Movie Library/{name}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert (
        target.destination
        == Path("movie.library/ninja.turtles/ninja.turtles.1990.mkv").resolve()
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_scene_preserves_literal_parts():
    """Literal parts of an absolute configured directory survive --scene."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        scene=True,
        movie_directory=Path("/Media Library/Movies"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("/Media Library/Movies/ninja.turtles.1990.mkv")


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_scene_transforms_template_parts():
    """Template parts within an absolute configured directory survive --scene."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        scene=True,
        movie_directory=Path("/Media Library/{name}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path(
        "/Media Library/ninja.turtles/ninja.turtles.1990.mkv"
    )


def test_destination__parent_directory_navigation_preserved():
    """A `..` segment in a relative directory survives sanitization."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("../Movies"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("../movies/ninja turtles (1990).mkv").resolve()


def test_destination__same_directory_matches_source(tmp_path, monkeypatch):
    """`--movie_directory=.` resolves to the source path so the no-op is skippable."""
    tmp = tmp_path.resolve()
    monkeypatch.chdir(tmp)
    source = tmp / "Ninja Turtles (1990).mkv"
    source.touch()
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        movie_directory=Path("."),
    )
    target = Target(source, settings)
    assert target.destination == target.source


def test_destination__no_rename_preserves_source_filename():
    """--no-rename keeps the source filename verbatim but still builds directories."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        no_rename=True,
        scene=True,
        movie_directory=Path("Movie Library/{name}"),
    )
    target = Target(Path("The.Film.2009.1080p-GROUP.mkv"), settings)
    assert (
        target.destination
        == Path("movie.library/the.film/The.Film.2009.1080p-GROUP.mkv").resolve()
    )


def test_destination__decade_directory():
    """{decade} groups a film into its decade beneath the configured directory."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        movie_directory=Path("Movies"),
        movie_format="{decade}/{name} ({year}).{extension}",
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("Movies/1990s/Ninja Turtles (1990).mkv").resolve()


def test_destination__empty_leading_field_stays_relative():
    """An empty {decade} must not make the template an absolute path."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        movie_directory=Path("Movies"),
        movie_format="{decade}/{name}.{extension}",
    )
    target = Target(Path("some unmatched film.mkv"), settings)
    assert target.destination == Path("Movies/Some Unmatched Film.mkv").resolve()


def test_destination__colon_becomes_dash():
    """Colons are invalid on many filesystems, so they dash rather than vanish."""
    settings = SettingStore(batch=True, media=MediaType.MOVIE)
    target = Target(Path("wake up dead man 2025.mkv"), settings)
    target.metadata.name = "Wake Up Dead Man: A Knives Out Mystery"
    assert (
        target.destination.name == "Wake Up Dead Man - A Knives Out Mystery (2025).mkv"
    )


def test_query():
    pass  # TODO


def test_relocate():
    pass  # TODO
