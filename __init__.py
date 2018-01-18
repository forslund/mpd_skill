from adapt.intent import IntentBuilder
from mycroft.messagebus.message import Message
from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.log import LOG

import mpd
import time
from fuzzywuzzy.process import extractOne

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


class MPDSkill(MycroftSkill):
    def __init__(self):
        super(MPDSkill, self).__init__('MPDSkill')
        self.volume_is_low = False
        self.playlist = []

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
            LOG.info('Could not connect to server, retrying in 10 sec')
            time.sleep(10)
            self.emitter.emit(Message(self.name + '.connect'))
            return

        self.albums = self.server.list('album')
        self.artists = self.server.list('artist')
        self.genres = self.server.list('genre')

        self.playlist = self.albums + self.artists + self.genres

        self.register_vocabulary(self.name, 'NameKeyword')

    def initialize(self):
        LOG.info('initializing MPD skill')

        self.emitter.on(self.name + '.connect', self._connect)
        self.emitter.emit(Message(self.name + '.connect'))
        self.add_event('mycroft.audio.service.next', self.handle_next)
        self.add_event('mycroft.audio.service.prev', self.handle_prev)
        self.add_event('mycroft.audio.service.pause', self.handle_pause)
        self.add_event('mycroft.audio.service.resume', self.handle_play)

    @intent_file_handler('Play.intent')
    def handle_play_playlist(self, message):
        LOG.info('Handling play request')
        key, confidence = extractOne(message.data.get('music'),
                                     self.playlist)
        if confidence > 50:
            p = key
        else:
            LOG.info('couldn\'t find playlist')
            return
        self.server.clear()
        self.server.stop()
        self.speak("Playing " + str(p))
        time.sleep(3)

        self.server.clear()

        if p in self.genres:
            self.server.searchadd('genre', p)
        elif p in self.artists:
            self.server.searchadd('artist', p)
        else:
            self.server.searchadd('album', p)

        self.server.play()

    def stop(self, message=None):
        LOG.info('Handling stop request')
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
        LOG.info('lowering volume')
        self.server.setvol(10)
        self.volume_is_low = True

    def restore_volume(self, message):
        LOG.info('maybe restoring volume')
        self.volume_is_low = False
        time.sleep(2)
        if not self.volume_is_low:
            LOG.info('restoring volume')
            self.server.setvol(100)

    def handle_currently_playing(self, message):
        current_track = self.server.currentsong()
        if current_track is not None:
            self.server.setvol(10)
            time.sleep(1)
            if 'album' in current_track:
                data = {'current_track': current_track['title'],
                        'artist': current_track['artist']}
                self.speak_dialog('currently_playing', data)


def create_skill():
    return MPDSkill()
