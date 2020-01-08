from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.util.log import LOG

import mpd
import time
from fuzzywuzzy.process import extractOne


class MPDReconnectable(mpd.MPDClient):
    def __init__(self):
        super().__init__()

    def connect(self, uri, port=6600):
        self.__uri = uri
        self.__port = port
        return super().connect(uri, port)

    def searchadd(self, *args):
        try:
            return super().searchadd(*args)
        except Exception:
            super().connect(self.__uri, self.__port)
            return super().searchadd(*args)

    def list(self, *args):
        try:
            return super().list(*args)
        except Exception:
            super().connect(self.__uri, self.__port)
            return super().list(*args)

    def pause(self, PAUSE):
        try:
            return super().pause(PAUSE)
        except Exception:
            super().connect(self.__uri, self.__port)
            return super().pause(PAUSE)

    def stop(self):
        try:
            return super().stop()
        except Exception:
            super().connect(self.__uri, self.__port)
            return super(MPDReconnectable, self).stop()

    def play(self):
        try:
            return super().play()
        except Exception:
            super().connect(self.__uri, self.__port)
            return super().play()

    def currentsong(self):
        try:
            return super(MPDReconnectable, self).currentsong()
        except Exception:
            super().connect(self.__uri, self.__port)
            return super().currentsong()

    def next(self):
        try:
            return super(MPDReconnectable, self).next()
        except Exception:
            super(MPDReconnectable, self).connect(self.__uri, self.__port)
            return super(MPDReconnectable, self).next()

    def previous(self):
        try:
            return super(MPDReconnectable, self).previous()
        except Exception:
            super(MPDReconnectable, self).connect(self.__uri, self.__port)
            return super(MPDReconnectable, self).previous()

    def clear(self):
        try:
            return super(MPDReconnectable, self).clear()
        except Exception:
            super(MPDReconnectable, self).connect(self.__uri, self.__port)
            return super(MPDReconnectable, self).clear()


class MPDSkill(CommonPlaySkill):
    def __init__(self):
        super(MPDSkill, self).__init__('MPDSkill')
        self.server = None
        self.volume_is_low = False
        self.playlist = []
        self.albums = []
        self.artists = []
        self.genres = []

    def _connect(self):
        self.log.info("TRYING TO CONNECT")
        url = self.settings.get('mpd_url', 'localhost')
        port = self.settings.get('mpd_port', 6600)

        try:
            self.server = MPDReconnectable()
            self.server.connect(url, port)
        except Exception:
            LOG.debug('Could not connect to server, retrying in 10 sec')
            return False

        self.log.info('Fetching albums and stuff!!!')
        self.albums = self.server.list('album')
        self.artists = self.server.list('artist')
        self.genres = self.server.list('genre')

        self.playlist = self.albums + self.artists + self.genres

        self.register_vocabulary(self.name, 'NameKeyword')
        return True

    def repeating_check(self, message):
        if not self.server:
            self._connect()

    def initialize(self):
        LOG.info('initializing MPD skill')

        self.add_event('mycroft.audio.service.next', self.handle_next)
        self.add_event('mycroft.audio.service.prev', self.handle_prev)
        self.add_event('mycroft.audio.service.pause', self.handle_pause)
        self.add_event('mycroft.audio.service.resume', self.handle_play)

        self.schedule_repeating_event(self.repeating_check, None, 30,
                                      name='mpd_check')

    def CPS_match_query_phrase(self, phrase):
        if self.playlist:
            key, confidence = extractOne(phrase, self.playlist)
            if confidence < 50:
                LOG.info('couldn\'t find playlist')
                return None
            elif confidence > 90:
                confidence = CPSMatchLevel.EXACT
            elif confidence > 70:
                confidence = CPSMatchLevel.MULTI_KEY
            elif confidence > 60:
                confidence = CPSMatchLevel.TITLE
            else:
                confidence = CPSMatchLevel.CATEGORY
            return phrase, confidence, {'playlist': key}

    def CPS_start(self, phrase, data):
        LOG.info('Handling play request')
        p = data['playlist']
        self.server.clear()
        self.server.stop()
        self.speak("Playing " + str(p))
        time.sleep(3)

        if p in self.genres:
            self.server.searchadd('genre', p)
        elif p in self.artists:
            self.server.searchadd('artist', p)
        else:
            self.server.searchadd('album', p)

        self.server.play()

    def stop(self, message=None):
        LOG.info('Handling stop request')
        if self.server:
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

    def shutdown(self):
        self.cancel_scheduled_event('mpd_check')


def create_skill():
    return MPDSkill()
