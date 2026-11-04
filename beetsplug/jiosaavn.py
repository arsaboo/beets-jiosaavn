"""Adds JioSaavn support to the autotagger."""

from __future__ import annotations

import collections
import re
import time
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar, Literal

import requests
from beets import config
from beets.autotag import AlbumInfo, TrackInfo
from beets.dbcore import types
from beets.importer.tasks import REIMPORT_FRESH_FIELDS_ITEM
from beets.metadata_plugins import IDResponse, SearchApiMetadataSourcePlugin
from musicapy.saavn_api.api import SaavnAPI
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from beets.library import Item
    from beets.metadata_plugins import QueryType, SearchParams

# JioSaavn release URLs look like
# https://www.jiosaavn.com/album/<slug>/<token> and
# https://www.jiosaavn.com/song/<slug>/<token>.
ALBUM_URL_RE = re.compile(r'jiosaavn\.com/album/')
SONG_URL_RE = re.compile(r'jiosaavn\.com/song/')

# Flexible attributes that a reimport should refresh instead of preserving.
FRESH_FIELDS = [
    'jiosaavn_album_id',
    'jiosaavn_artist_id',
    'jiosaavn_track_id',
    'jiosaavn_starring',
    'jiosaavn_perma_url',
    'jiosaavn_updated',
]


def extend_reimport_fresh_fields_item() -> None:
    """Mark the JioSaavn fields as fresh for reimports.

    Flexible attributes are preserved by default, which would leave ids and the
    ``jiosaavn_updated`` timestamp stale across reimports.
    """
    REIMPORT_FRESH_FIELDS_ITEM.extend(
        field for field in FRESH_FIELDS if field not in REIMPORT_FRESH_FIELDS_ITEM
    )


def to_int(value: Any) -> int | None:
    """Parse JioSaavn's stringly-typed numbers (year, duration, ...)."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


class JioSaavnSearchHit(IDResponse):
    """A JioSaavn search hit.

    Carries the release ``type`` alongside the id because JioSaavn's album
    detail endpoint does not report whether a release is an album, a single or
    an EP, while its search endpoint does.
    """

    type: str | None


class JioSaavnPlugin(SearchApiMetadataSourcePlugin[JioSaavnSearchHit]):
    """Autotagger metadata source backed by the JioSaavn web API.

    ``search_limit`` and ``data_source_mismatch_penalty`` are provided, with
    defaults, by :py:class:`~beets.metadata_plugins.MetadataSourcePlugin`.
    """

    item_types: ClassVar[dict[str, types.Type]] = {
        'jiosaavn_album_id': types.INTEGER,
        'jiosaavn_artist_id': types.INTEGER,
        'jiosaavn_track_id': types.STRING,
        'jiosaavn_starring': types.STRING,
        'jiosaavn_perma_url': types.STRING,
        'jiosaavn_updated': types.DATE,
        'cover_art_url': types.STRING,
    }

    def __init__(self) -> None:
        super().__init__()
        extend_reimport_fresh_fields_item()
        self.jiosaavn = SaavnAPI()

    # --------------------------------- search --------------------------------- #

    def get_search_query_with_filters(
        self,
        query_type: QueryType,
        items: Sequence[Item],
        artist: str,
        name: str,
        va_likely: bool,
    ) -> tuple[str, dict[str, str]]:
        """Build the free-text query for a JioSaavn album or track search.

        JioSaavn's search endpoints take a single free-text term and no
        structured filters. The artist is dropped for likely various-artists
        releases, which are mostly soundtracks that the album artist field
        would otherwise hide.
        """
        query = name if va_likely else f'{name} {artist}'
        # Strip non-word characters from query. Things like "!" and "-" can
        # cause a query to return no results, even if they match the artist or
        # album title. Use the `re.UNICODE` flag to avoid stripping non-English
        # word characters.
        query = re.sub(r'(?u)\W+', ' ', query)
        # Strip medium information from query. Things like "CD1" and "disk 1"
        # can also negate an otherwise positive result.
        query = re.sub(r'(?i)\b(CD|disc)\s*\d+', '', query)
        return query.strip(), {}

    def get_search_response(self, params: SearchParams) -> Sequence[JioSaavnSearchHit]:
        """Search JioSaavn and return the hits that carry release ids.

        The perma URL serves as the id: unlike the bare ``id`` field of a
        search hit it says whether the hit is an album or a song, and both
        detail lookups accept it.
        """
        search = (
            self.jiosaavn.search_album
            if params.query_type == 'album'
            else self.jiosaavn.search_song
        )
        data = search(params.query, limit=params.limit) or {}
        hits = data.get('results') or []
        # The endpoint accepts `limit` but ignores it, so cap the hits here:
        # every hit costs at least one further request, and an album hit
        # resolves the details of each of its tracks.
        return [
            {'id': hit['perma_url'], 'type': hit.get('type')}
            for hit in hits[: params.limit]
            if hit.get('perma_url')
        ]

    def candidates(
        self,
        items: Sequence[Item],
        artist: str,
        album: str,
        va_likely: bool,
    ) -> Iterable[AlbumInfo]:
        """Return the album candidates matching `album` and `artist`.

        Extends the base implementation to pass the release type from the
        search hit down to :py:meth:`get_album_info`, which the album detail
        endpoint cannot supply itself.
        """
        hits = self._get_candidates('album', items, artist, album, va_likely)
        for hit in hits:
            album_info = self._album_for_url(hit['id'], hit.get('type'))
            if album_info:
                yield album_info

    # ------------------------------ by id ------------------------------ #

    def album_for_id(self, album_id: str) -> AlbumInfo | None:
        """Fetch an album by its JioSaavn album URL."""
        if not ALBUM_URL_RE.search(album_id):
            return None
        return self._album_for_url(album_id)

    def track_for_id(self, track_id: str) -> TrackInfo | None:
        """Fetch a track by its JioSaavn song URL."""
        if not SONG_URL_RE.search(track_id):
            return None
        try:
            details = self._get_details(track_id, 'song')
            if details is None:
                return None
            # Some API responses wrap the song in a `songs` list.
            song = (details.get('songs') or [details])[0]
            return self._get_track(song)
        except Exception as e:
            if config['raise_on_error'].get(bool):
                raise
            self._log.debug('Could not resolve track {}: {}', track_id, e)
            return None

    # ------------------------------ payloads ------------------------------ #

    def get_album_info(
        self, item: dict[str, Any], albumtype: str = 'album'
    ) -> AlbumInfo:
        """Build an AlbumInfo object from JioSaavn album details."""
        album = item['title'].replace('&quot;', '"')
        jiosaavn_album_id = item['albumid']
        perma_url = item['perma_url']
        artist_id = item['primary_artists_id']
        artists = item['primary_artists']
        cover_art_url = None
        label = None
        year = to_int(item.get('year'))
        month = day = None

        url = item['image'].replace('150x150', '500x500')
        if self.is_valid_image_url(url):
            cover_art_url = url

        songs = item.get('songs') or []
        if songs and isinstance(songs[0], dict):
            label = songs[0].get('label')

        if released := item.get('release_date'):
            parts = released.split('-')
            year = to_int(parts[0]) or year
            month = to_int(parts[1]) if len(parts) > 1 else None
            day = to_int(parts[2]) if len(parts) > 2 else None

        tracks = []
        medium_totals: dict[int | None, int] = collections.defaultdict(int)
        for i, song in enumerate(songs, start=1):
            if not isinstance(song, dict):
                self._log.debug(
                    'Skipping unexpected song entry from JioSaavn API '
                    '(expected dict, got {}): {}',
                    type(song).__name__,
                    song,
                )
                continue
            track = self._get_track(song)
            track.index = i
            medium_totals[track.medium] += 1
            tracks.append(track)
        for track in tracks:
            track.medium_total = medium_totals[track.medium]

        return AlbumInfo(
            album=album,
            album_id=jiosaavn_album_id,
            jiosaavn_album_id=jiosaavn_album_id,
            artist=artists,
            artist_id=artist_id,
            jiosaavn_artist_id=artist_id,
            tracks=tracks,
            albumtype=albumtype,
            year=year,
            month=month,
            day=day,
            mediums=max(medium_totals, default=None),
            data_source=self.data_source,
            jiosaavn_perma_url=perma_url,
            data_url=perma_url,
            cover_art_url=cover_art_url,
            label=label,
        )

    def _get_track(self, track_data: dict[str, Any]) -> TrackInfo:
        """Convert a JioSaavn song object to a TrackInfo object."""
        duration = track_data.get('duration') or (
            track_data.get('more_info') or {}
        ).get('duration')
        # Instrumentals carry no singers, in which case the composer is the
        # best available artist.
        artist = track_data.get('singers') or track_data.get('music')
        perma_url = track_data['perma_url']
        return TrackInfo(
            title=track_data['song'].replace('&quot;', '"'),
            track_id=track_data['id'],
            jiosaavn_track_id=track_data['id'],
            artist=artist,
            album=track_data['album'].replace('&quot;', '"'),
            jiosaavn_artist_id=track_data.get('music_id'),
            length=to_int(duration),
            data_source=self.data_source,
            jiosaavn_perma_url=perma_url,
            jiosaavn_starring=track_data.get('starring') or None,
            data_url=perma_url,
            jiosaavn_updated=time.time(),
        )

    def _album_for_url(
        self, url: str, albumtype: str | None = None
    ) -> AlbumInfo | None:
        """Resolve an album URL to an AlbumInfo object.

        `albumtype` comes from a search hit; an id lookup has no release type
        to report, so it falls back to "album".
        """
        try:
            details = self._get_details(url, 'album')
            if details is None:
                return None
            return self.get_album_info(details, albumtype or 'album')
        except Exception as e:
            if config['raise_on_error'].get(bool):
                raise
            self._log.debug('Could not resolve album {}: {}', url, e)
            return None

    def _get_details(
        self, url: str, kind: Literal['album', 'song']
    ) -> dict[str, Any] | None:
        """Fetch the details payload MusicAPy serves for a JioSaavn URL.

        Returns ``None`` when MusicAPy reports no data (it answers ``False`` for
        a non-2xx response); the calling lookups handle the exceptions MusicAPy
        raises for network, decoding and payload problems, so that one dead link
        does not cost the other candidates.
        """
        get_details = (
            self.jiosaavn.get_album_details
            if kind == 'album'
            else self.jiosaavn.get_song_details
        )
        details = get_details(self.jiosaavn.create_identifier(url, kind))
        if not isinstance(details, dict):
            self._log.debug('No {} details for {}', kind, url)
            return None
        return details

    # ------------------------------- helpers ------------------------------- #

    def is_valid_image_url(self, url: str) -> bool:
        """Check that `url` really serves an image before offering it as art."""
        try:
            response = requests.get(url, timeout=10)
            Image.open(BytesIO(response.content))
        except Exception as e:
            self._log.debug('Invalid image URL {}: {}', url, e)
            return False
        return True
