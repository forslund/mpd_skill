import sys
from os.path import dirname, abspath
sys.path.append(abspath(dirname(__file__)))

from mycroft.skills.media import MediaSkill
from adapt.intent import IntentBuilder
from mycroft.messagebus.message import Message

import mpd

import time
from os.path import dirname

from mycroft.util.log import getLogger
logger = getLogger(__name__)

__author__ = 'forslund'

class MPDReconnectable(mpd.MPDClient):
    def __init__(self):
        super(MPDReconnectable, self).__init__()

    def connect(self, uri, port=6600):
        self.uri = uri
        self.port = port
        return super(MPDReconnectable, self).connect(uri, port)

    def searchadd(self, *args):
        try:
            return super(MPDReconnectable, self).searchadd(*args)
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).searchadd(*args)

    def list(self, *args):
        try:
            return super(MPDReconnectable, self).list(*args)
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).list(*args)

    def pause(self, PAUSE):
        try:
            return super(MPDReconnectable, self).pause(PAUSE)
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).pause(PAUSE)

    def stop(self):
        try:
            return super(MPDReconnectable, self).stop()
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).stop()

    def play(self):
        try:
            return super(MPDReconnectable, self).play()
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).play()

    def currentsong(self):
        try:
            return super(MPDReconnectable, self).currentsong()
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).currentsong()

    def next(self):
        try:
            return super(MPDReconnectable, self).next()
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).next()

    def previous(self):
        try:
            return super(MPDReconnectable, self).previous()
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).previous()

    def clear(self):
        try:
            return super(MPDReconnectable, self).clear()
        except:
            super(MPDReconnectable, self).connect(self.uri, self.port)
            return super(MPDReconnectable, self).clear()

class MPDSkill(MediaSkill):
    def __init__(self):
        super(MPDSkill, self).__init__('MPDSkill')
        self.volume_is_low = False

    def _connect(self, message):
        if self.config:
            url = self.config.get('mpd_url', 'localhost')
            port = self.config.get('mpd_port', 6600)
        else:
            url = 'localhost'
            port = 6600
        try:
            self.server = MPDReconnectable()
            self.server.connect(url, port)
        except:
            logger.info('Could not connect to server, retrying in 10 sec')
            time.sleep(10)
            self.emitter.emit(Message(self.name + '.connect'))
            return

        self.albums = self.server.list('album')
        self.artists = self.server.list('artist')
        self.genres = self.server.list('genre')

        self.playlist = self.albums + self.artists + self.genres

        self.register_vocabulary(self.name, 'NameKeyword')
        for p in self.playlist:
            logger.debug("Playlist: " + p)
            self.register_vocabulary(p, 'PlaylistKeyword' + self.name)
        intent = IntentBuilder('PlayPlaylistIntent' + self.name)\
            .require('PlayKeyword')\
            .require('PlaylistKeyword' + self.name)\
            .build()
        self.register_intent(intent, self.handle_play_playlist)
        intent = IntentBuilder('PlayFromIntent' + self.name)\
            .require('PlayKeyword')\
            .require('PlaylistKeyword')\
            .require('NameKeyword')\
            .build()
        self.register_intent(intent, self.handle_play_playlist)

    def initialize(self):
        logger.info('initializing MPD skill')
        super(MPDSkill, self).initialize()
        self.load_data_files(dirname(__file__))

        self.emitter.on(self.name + '.connect', self._connect)
        self.emitter.emit(Message(self.name + '.connect'))

    def play(self, tracks):
        self.server.clear()
        if tracks in self.genres:
            self.server.searchadd('genre', tracks)
        elif tracks in self.artists:
            self.server.searchadd('artist', tracks)
        else:
            self.server.searchadd('album', tracks)
        self.server.play()

    def handle_play_playlist(self, message):
        logger.info('Handling play request')
        p = message.metadata.get('PlaylistKeyword' + self.name)
        self.before_play()
        self.speak("Playing " + str(p))
        time.sleep(3)
        self.play(p)

    def stop(self, message=None):
        logger.info('Handling stop request')
        self.server.clear()
        self.server.stop()

    def handle_next(self, message):
        self.server.next()

    def handle_prev(self, message):
        self.server.previous()

    def handle_pause(self, message):
        self.server.pause(1)

    def handle_play(self, message):
        """Resume playback if paused"""
        self.server.pause(0)

    def lower_volume(self, message):
        logger.info('lowering volume')
        #self.mopidy.lower_volume()
        self.volume_is_low = True

    def restore_volume(self, message):
        logger.info('maybe restoring volume')
        self.volume_is_low = False
        time.sleep(2)
        if not self.volume_is_low:
            logger.info('restoring volume')
            #self.mopidy.restore_volume()

    def handle_currently_playing(self, message):
        current_track = self.server.currentsong()
        if current_track is not None:
            #self.mopidy.lower_volume()
            time.sleep(1)
            if 'album' in current_track:
                data = {'current_track': current_track['title'],
                        'artist': current_track['artist']}
                self.speak_dialog('currently_playing', data)


def create_skill():
    return MPDSkill()
