"""
Video Streaming Probe
"""
import time
from datetime import datetime
from vlc import Instance, EventType, MediaStats, State, bytes_to_str, libvlc_get_version


class VideoStreamingProbe(object):
    """
    Video Streaming Probe Class
    """

    global video_buffering_events, start_sys_time

    def __init__(self, vlc_instance_params=[], db_conn=None):
        self.vlc_instance = Instance(vlc_instance_params)
        self.player = None
        self.current_time = None
        self.stats_results = []
        self.start_time = time.time()
        self.db = None
        if (db_conn):
            self.db = db_conn.admin.video_probing


    def __get_media_from_instance(self, movie_url):
        media = None
        try:
            media = self.vlc_instance.media_new(movie_url)
        except (AttributeError, NameError) as e:
            raise Exception('%s: %s (LibVLC %s)' % (e.__class__.__name__, e,
                                                    libvlc_get_version()))
        return media


    def __pos_callback(video_streaming_probe, event):
        global video_buffering_events
        event_time = time.time()
        video_buffering_events.append((event_time, event.u.new_cache.real))


    def __mspf(self):
        """Milliseconds per frame"""
        return int(1000 // (self.player.get_fps() or 25))


    def __get_stats(self):
        """Print information about the media"""
        media = self.player.get_media()
        media_stats = MediaStats()
        media.get_stats(media_stats)
        stats_record = {}
        stats_record['state'] = self.player.get_state()
        stats_record['current_time'] = self.player.get_time()
        stats_record['sys_time'] = time.time()
        stats_record['media'] = media
        stats_record['media_stats'] = media_stats

        stats_record['video_size'] = str(self.player.video_get_size(0))
        stats_record['input_bitrate'] = media_stats.input_bitrate

        #print('Video size: %s' % str(self.player.video_get_size(0)))  # num=0
        #print('Input Bitrate: %s' % str(float(media_stats.input_bitrate)*8000))

        return stats_record


    def __parse_final_results(self):
        playback_timeline, buffering_timeline = self.__get_final_results()
        self.__print_final_results(playback_timeline, buffering_timeline)

    def __get_final_results(self):
        global video_buffering_events, start_sys_time
        playback_timeline = []
        buffering_timeline = []
        start_sys_time = self.stats_results[0]['sys_time']

        for record in self.stats_results:
            playback_timeline.append((record['current_time'],
                                      int((record['sys_time'] - start_sys_time) * 1000)))

        for event in video_buffering_events:
            buf_time = datetime.fromtimestamp(float(event[0])).strftime('%Y-%m-%d %H:%M:%S.%f')
            buf_perc = event[1]
            elap_time = max(0, event[0] - start_sys_time)
            buffering_timeline.append((event[0], buf_perc, elap_time))

        return playback_timeline, buffering_timeline

    def __print_final_results(self, playback_timeline, buffering_timeline):
        for record in playback_timeline:
            print(";".join((str(x) for x in record)))
        for record in buffering_timeline:
            print(";".join((str(x) for x in record)))


    def start_probing(self, movie_url, timeout_secs, logger):
        global video_buffering_events, start_sys_time
        video_buffering_events = []
        start_sys_time = []

        is_successfully_executed = True

        start = time.time()

        media = self.__get_media_from_instance(movie_url)
        media_list = self.vlc_instance.media_list_new([movie_url])
        self.player = self.vlc_instance.media_player_new()
        self.player.set_media(media)

        list_player = self.vlc_instance.media_list_player_new()

        event_manager = self.player.event_manager()
        event_manager.event_attach(EventType.MediaPlayerBuffering, self.__pos_callback)

        list_player.set_media_player(self.player)
        list_player.set_media_list(media_list)

        list_player.next()
        self.player.play()

        while True:
            time.sleep(1)
            stats_record = self.__get_stats()
            self.stats_results.append(stats_record)
            if (stats_record['state'] == State.Ended):
                self.__parse_final_results()
                logger.info("\t\tVideo finished gracefully")
                break
            elif (stats_record['state'] == State.Error):
                is_successfully_executed = False
                logger.info("\t\tVLC Error raised")
                break
            if time.time() - start > timeout_secs:
                is_successfully_executed = False
                logger.info("\t\tTimer Expired")
                break

        return [video_buffering_events, start_sys_time, not is_successfully_executed, self.stats_results]


if __name__ == '__main__':
    VideoStreamingProbe(vlc_instance_params=["--sub-source=marq",
                                             "--vout=none",
                                             "--network-caching=5000",
                                             "--file-caching=0",
                                             "--disc-caching=0",
                                             "--sout-mux-caching=1500"]).start_probing('https://www.youtube.com/watch?v=Pcg5dj_ArCg', 10000, None)
