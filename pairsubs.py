import xmlrpc.client
import base64
import zlib
import srt
from bs4 import UnicodeDammit
import textwrap
import itertools
from datetime import timedelta
import random
import os
import json
import codecs


COLUMN_WIDTH = 40

#: Directory in which to store PaiSubs cache.
APP_DIR = '{}/.pairsubs'.format(os.path.expanduser('~'))

#: File in which to store details aboud downloaded subtitles
CACHE_DB = '{}/cache.json'.format(APP_DIR)


class Opensubtitles:
    '''
    Class for opensuntitles.org access
    '''

    user_agent = "TemporaryUserAgent"

    def __init__(self):
        '''Init xml-rpc proxy'''

        self.proxy = xmlrpc.client.ServerProxy(
                "https://api.opensubtitles.org/xml-rpc")

    def logout(self):
        ''' Logout from api.opensubtitles.org.'''

        try:
            self.proxy.LogOut(self.token)
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))

    def login(self):
        ''' Login into api.opensubtitles.org.'''

        try:
            login = self.proxy.LogIn("", "", "en", "TemporaryUserAgent")
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            self.token = login['token']

    def _select_sub_(self, subtitles):
        ''' Select subtitles that have maximal downloads count'''
        rate = 0
        top_sub = None

        for sub in subtitles:
            if int(sub['SubDownloadsCnt']) >= rate:
                rate = int(sub['SubDownloadsCnt'])
                top_sub = sub
        return top_sub

    def search_sub(self, imdbid, lang):
        '''
        Search the subtitles in Opensubtitles database
        by IMBD id and a language.
        Return dict as described in
        http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
        Args:
            imdbid (int): Movie's IMDB id
            lang (str): Language of subtitles in ISO639 format (3-letter)
        Returns:
            sub (dict): subtitles info in Opensubtitles API format
        '''
        try:
            result = self.proxy.SearchSubtitles(
                    self.token,
                    [{'imdbid': str(imdbid), 'sublanguageid': lang}],
                    [100])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            return self._select_sub_(result['data'])

    def download_sub(self, sub):
        '''
        Download subtitles from subtitles.org.
        Args:
            sub (dict): subtitles info in Opensubtitles API format
        Return:
            data_bytes (bytes): downloaded subtitles
        '''
        try:
            result = self.proxy.DownloadSubtitles(self.token,
                                                  [sub['IDSubtitleFile']])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            data_zipped = base64.b64decode(result['data'][0]['data'])
            data_bytes = zlib.decompress(data_zipped, 15+32)
            return data_bytes


class Subs:
    '''
    Base class for subtitles
    '''

    def __init__(self, sub_data, sub_info):
        '''
        Args:
            sub_info (:obj:`dict`): subtitles information
            sub (:obj:`list` of :obj:`Subtitle`): subtitles in SRT format
        '''
        self.sub_info = {}
        self.sub_info['SubLanguageID'] = sub_info.get('SubLanguageID', None)
        self.sub_info['SubFileName'] = sub_info.get('SubFileName', None)
        self.sub_info['SubEncoding'] = sub_info.get('SubEncoding', None)
        self.sub_info['MovieName'] = sub_info.get('MovieName', None)
        self.sub_info['IDMovieImdb'] = sub_info.get('IDMovieImdb', None)
        self.sub_info['IDSubtitleFile'] = sub_info.get('IDSubtitleFile', None)

        # Decode bytes to Unicode string
        data_decoded = self.sub_decode(sub_data, self.sub_info['SubEncoding'])

        # Parse bytes into a list of Subtitles objects
        self.sub = self._parse_subtitles_(data_decoded)

    def __repr__(self):
        return "Subs: [{}] [{}] [{}]".format(self.sub_info['MovieName'],
                                             self.sub_info['IDMovieImdb'],
                                             self.sub_info['SubLanguageID'])

    @staticmethod
    def sub_decode(data, encoding):
        '''
        Args:
            sub_data (bytes): subtitles in SRT format
            encoding: (str): encoding
        '''
        if encoding:
            if data.startswith(codecs.BOM_UTF8):
                enc = 'utf-8-sig'
            else:
                enc = encoding
            return data.decode(enc)
        else:
            return UnicodeDammit(data).unicode_markup

    def save(self, name=None):
        data = srt.compose(self.sub)
        file_name = name if name else self.sub_info['SubFileName']
        with open(file_name, 'wb') as f:
            f.write(data)

    # @classmethod
    # def read(cls, name, encoding=None,
    #          lang=None, movie_name=None, imdbid=None):

    #     subs_args = {'encoding': encoding, 'lang': lang,
    #                  'movie_name': movie_name, 'imdbid': imdbid}
    #     with open(name, 'rb') as f:
    #         data = f.read()

    #     return cls(data, **subs_args)


    def get_subs(self, start, end):
        '''
        Return list of <str> from subtitles
        whose timedelta is between start and stop.
        Args:
            start (timedelta): start time of subtitles
            end (timedelta): end time of subtitles
        Returns:
            :obj:`list` of :obj:`Subtitles`
        '''
        subs = []
        for s in self.sub:
            if s.start >= start and s.start <= end:
                subs.append(s)
        return subs

    # def set_encoding(self, encoding):
    #     self.sub_info['SubEncoding'] = encoding
    #     data = self.sub_b.decode(self.sub_info['SubEncoding'])
    #     self.sub = self._parse_subtitles_(data)
    #     self._fix_subtitles_()

    def _parse_subtitles_(self, data):
        try:
            sub = list(srt.parse(data))
            return sub
        except ValueError as e:
            print("Subtitles parsing failed: {}".format(e))
            return []


class SubPair:
    ''' Pair of subtitles'''

    def __init__(self, subs):
        '''
        Args:
            subs: list of <Subs> objects
        '''
        #self._cache_init_()
        self.subs = subs
        self.offset = 0  # offset in seconds betwen subtitles in a pair
        self.coeff = 1  # difference in duration between subtitles in a pair
        # import ipdb; ipdb.set_trace()
        # self._append_to_cache_()

    def __repr__(self):
        return "{}, {}".format(self.subs[0].__repr__(),
                               self.subs[1].__repr__())

    @classmethod
    def download(cls, imdbid, lang1, lang2, enc1=None, enc2=None):
        osub = Opensubtitles()
        osub.login()

        subs = []
        for lang, enc in [(lang1, enc1), (lang2, enc2)]:
            sub = osub.search_sub(imdbid, lang)
            if sub:
                print("Downloading {} ...".format(lang))
                sub_b = osub.download_sub(sub)
                # import ipdb; ipdb.set_trace()
                s = Subs(sub_b, sub)
                subs.append(s)
            else:
                print("Subtitles #{} isn't found".format(imdbid))
                osub.logout()
                return None

        osub.logout()
        return cls(subs)

    def get_parallel_subs(self, start, length):
        '''
        Args:
            start (float): 0-100 percenrage of full length from the begin
            lenght (int): duration in seconds
        Returns:
            :obj:`tuple` of :obj:`list' of :obj:`Subtitles`
        '''
        start_td = self.subs[0].sub[-1].end * start/100
        end_td = start_td + timedelta(seconds=length)

        par_subs = []
        first = True
        for s in self.subs:
            if first:
                subs = s.get_subs(start_td, end_td)
            else:
                start_td_mod = (start_td +
                                timedelta(seconds=self.offset))/self.coeff
                end_td_mod = (end_td +
                              timedelta(seconds=self.offset))/self.coeff
                subs = s.get_subs(start_td_mod, end_td_mod)
            par_subs.append(subs)
            first = False

        return par_subs

    def print_pair(self, offset=0, count=1,
                   hide_left=None, hide_right=None, srt=False):

        par_subs = self.get_parallel_subs(offset, count)
        data = []
        for subs in par_subs:
            line = ""
            for sub in subs:
                line = "\n\n".join((line, sub.content))
            res = []
            for l in line.splitlines(keepends=True):
                res += textwrap.wrap(l, COLUMN_WIDTH)
            data.append(res)

        out = itertools.zip_longest(*data,  fillvalue="")

        for s in out:
            s = list(s)
            if hide_left:
                s[0] = len(s[0])*" "

            if hide_right:
                s[1] = len(s[1])*" "

            print("{}  |  {}".format(s[0]+(COLUMN_WIDTH-len(s[0]))*" ", s[1]))

    def print_pair_random(self, count=1):
        offset = random.random() * 100
        self.print_pair(offset, count)

    def print_start_and_end(self, count=4):
        data = []
        for sub in self.subs:
            lines = srt.compose(sub.sub[:count])
            res = []
            for l in lines.splitlines():
                res += textwrap.wrap(l, COLUMN_WIDTH)
            data.append(res)

        out = itertools.zip_longest(*data,  fillvalue="")

        for s in out:
            print("{}  |  {}".format(s[0]+(COLUMN_WIDTH-len(s[0]))*" ", s[1]))

        print("----------------------------------------------------")
        data = []
        for sub in self.subs:
            lines = srt.compose(sub.sub[-count:], reindex=False)
            res = []
            for l in lines.splitlines():
                res += textwrap.wrap(l, COLUMN_WIDTH)
            data.append(res)

        out = itertools.zip_longest(*data,  fillvalue="")

        for s in out:
            print("{}  |  {}".format(s[0]+(COLUMN_WIDTH-len(s[0]))*" ", s[1]))

    def align_subs(self, left_start, right_start, left_end, right_end):
        l1 = self.subs[0].sub[left_start-1].start.seconds
        l2 = self.subs[0].sub[left_end-1].start.seconds

        r1 = self.subs[1].sub[right_start-1].start.seconds
        r2 = self.subs[1].sub[right_end-1].start.seconds

        offset = l1 - r1
        coeff = (l2 - l1) / (r2 - r1)
        self.set_params(offset, coeff)

    def save_subs(self):
        for sub in self.subs:
            sub.save()

    def _cache_init_(self):
        '''
        Init cache
        '''
        # verify that the application directory (~/.pairsubs) exists,
        #   else create it
        if not os.path.exists(APP_DIR):
            os.makedirs(APP_DIR)

        # If the cache db doesn't exist we create it.
        # Otherwise we only open for reading
        if not os.path.isfile(CACHE_DB):
            with open(CACHE_DB, 'a'):
                os.utime(CACHE_DB, None)

        self.cache_db = {}

        # We know from above that this file exists so we open it
        #   for reading only.
        with open(CACHE_DB, 'r') as f:
            try:
                self.cache_db = json.load(f)
            except ValueError:
                pass

    def set_params(self, offset, coeff):
        self.offset = offset
        self.coeff = coeff
        if self._is_in_cache_():
            self.cache_db[self._get_key_()]['offset'] = self.offset
            self.cache_db[self._get_key_()]['coeff'] = self.coeff
            self._cache_write_()

    def _get_key_(self):
        return '_'.join([
                self.subs[0].sub_info['IDSubtitleFile'],
                self.subs[1].sub_info['IDSubtitleFile']
                ])

    def _get_value_(self):
        return {'offset': self.offset,
                'coeff': self.coeff,
                'subs': [
                    self.subs[0].sub_info,
                    self.subs[1].sub_info
                    ]}

    def _cache_write_(self):
        with open(CACHE_DB, 'w') as f:
            f.write(json.dumps(self.cache_db))

    def _append_to_cache_(self):
        # load offset and coeff from cache if exists
        if self._is_in_cache_():
            key = self._get_key_()
            self.offset = self.cache_db[key]['offset']
            self.coeff = self.cache_db[key]['coeff']
        # store info in cache if doesn't exists
        if not self._is_in_cache_():
            key = self._get_key_()
            value = self._get_value_()
            self.cache_db[key] = value
            self._cache_write_()

    def _is_in_cache_(self):
        key = self._get_key_()
        return key in self.cache_db


def learn(pair, length):
    while True:
        offset = random.random() * 100
        pair.print_pair(offset, length, hide_right=True)
        input("Press Enter...")
        pair.print_pair(offset, length, hide_right=False)
        input("Press Enter...")


if __name__ == '__main__':

    s = SubPair.download(1492032, "rus", "eng")
    learn(s, 20)
