"""
Adds JioSaavn support to the autotagger.
"""

import collections
import re

from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from beets.plugins import BeetsPlugin
from musicapy.saavn_api.api import SaavnAPI


class JioSaavnPlugin(BeetsPlugin):
    data_source = 'JioSaavn'

    def __init__(self):
        super().__init__()

    def album_distance(self, items, album_info, mapping):
        """Returns the album distance.
        """
        dist = Distance()
        if album_info.data_source == 'JioSaavn':
            dist.add('source', self.config['source_weight'].as_number())
        return dist

    jiosaavn = SaavnAPI()
    def get_albums(self, query):
        """Returns a list of AlbumInfo objects for a JioSaavn search query.
        """
        # Strip non-word characters from query. Things like "!" and "-" can
        # cause a query to return no results, even if they match the artist or
        # album title. Use `re.UNICODE` flag to avoid stripping non-english
        # word characters.
        query = re.sub(r'(?u)\W+', ' ', query)
        # Strip medium information from query, Things like "CD1" and "disk 1"
        # can also negate an otherwise positive result.
        query = re.sub(r'(?i)\b(CD|disc)\s*\d+', '', query)
        albums = []
        self._log.debug('Searching JioSaavn for: {}', query)
        try:
            data = self.jiosaavn.search_album(query)
        except:
            self._log.debug('Invalid search query: {}', query)
        for album in data["results"]:
            id = self.jiosaavn.create_identifier(album["perma_url"], 'album')
            album_details = self.jiosaavn.get_album_details(id)
            album_info = self.get_album_info(album_details, type)
            albums.append(album_info)
        return albums

    def candidates(self, items, artist, release, va_likely, extra_tags=None):
        """Returns a list of AlbumInfo objects for beatport search results
        matching release and artist (if not various).
        """
        if va_likely:
            query = release
        else:
            query = f'{release} {artist}'
        try:
            return self.get_albums(query)
        except Exception as e:
            self._log.debug('JioSaavn Search Error: {}'.format(e))
            return []

    def get_album_info(self, item, type):
        """Returns an AlbumInfo object for a JioSaavn album.
        """
        album = item["title"]
        jiosaavn_album_id = item["albumid"]
        perma_url = item["perma_url"]
        artist_id = item["primary_artists_id"]
        year = item["year"]
        if item["release_date"] is not None:
            releasedate = item["release_date"].split("-")
            year = int(releasedate[0])
            month = int(releasedate[1])
            day = int(releasedate[2])
        artists = item["primary_artists"]
        songs = item["songs"]
        tracks = []
        medium_totals = collections.defaultdict(int)
        for i, song in enumerate(songs, start=1):
            track = self._get_track(song)
            track.index = i
            medium_totals[track.medium] += 1
            tracks.append(track)
        for track in tracks:
            track.medium_total = medium_totals[track.medium]
        return AlbumInfo(album=album,
                         album_id=jiosaavn_album_id,
                         jiosaavn_album_id=jiosaavn_album_id,
                         artist=artists,
                         artist_id=artist_id,
                         jiosaavn_artist_id=artist_id,
                         tracks=tracks,
                         albumtype=type,
                         year=year,
                         month=month,
                         day=day,
                         mediums=max(medium_totals.keys()),
                         data_source=self.data_source,
                         jiosaavn_perma_url=perma_url,
                        )

    def _get_track(self, track_data):
        """Convert a JioSaavn song object to a TrackInfo object.
        """
        # Get album information for JioSaavn tracks
        return TrackInfo(
            title=track_data['song'],
            track_id=track_data['id'],
            jiosaavn_track_id=track_data['id'],
            artist=track_data['singers'],
            album=track_data['album'],
            jiosaavn_artist_id=track_data["music_id"],
            length=int(track_data['duration']),
            data_source=self.data_source,
            jiosaavn_perma_url=track_data['perma_url'],
        )
