import xmlrpc.client
import http.client
import base64
import zlib
import srt
from bs4 import UnicodeDammit
import textwrap
import itertools
from datetime import timedelta
from urllib.parse import urlparse
import random
import os
import json
import codecs
import re



COLUMN_WIDTH = 40
OPENSUBTUTLES_MAX_RETRY = 3


#: Directory in which to store PaiSubs cache.
APP_DIR = '{}/.pairsubs'.format(os.path.expanduser('~'))

FILES_DIR = os.path.join(APP_DIR, 'files')

#: File in which to store details aboud downloaded subtitles
CACHE_DB = '{}/cache.json'.format(APP_DIR)

# Opensubtitles API retry count
MAX_RETRY = 3

def retry(func):
    def wrapper(*args, **kwargs):
        for _ in range(MAX_RETRY):
            try:
                res = func(*args, **kwargs)
            except xmlrpc.client.ProtocolError:
                print("Exception")
                pass
            else:
                return res
    return wrapper

class ProxiedTransport(xmlrpc.client.Transport):

    def set_proxy(self, host, port=None, headers=None):
        self.proxy = host, port
        self.proxy_headers = headers

    def make_connection(self, host):
        connection = http.client.HTTPConnection(*self.proxy)
        connection.set_tunnel(host, headers=self.proxy_headers)
        self._connection = host, connection
        return connection


class Opensubtitles:
    '''
    Class for opensuntitles.org access
    '''

    user_agent = "TemporaryUserAgent"

    def __init__(self):
        '''Init xml-rpc proxy'''
        #import ipdb; ipdb.set_trace()
        proxy_url = os.environ.get('http_proxy','')
        if proxy_url:
            parsed = urlparse(proxy_url).netloc
            transport = ProxiedTransport()
            transport.set_proxy(parsed)
            self.proxy = xmlrpc.client.ServerProxy(
                    "https://api.opensubtitles.org/xml-rpc", transport=transport)
        else:
            self.proxy = xmlrpc.client.ServerProxy(
                    "https://api.opensubtitles.org/xml-rpc")

    def logout(self):
        ''' Logout from api.opensubtitles.org.'''

        try:
            self.proxy.LogOut(self.token)
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))

    @retry
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

    @retry
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
        imdb = re.search('\d+', imdbid)[0]
        try:
            result = self.proxy.SearchSubtitles(
                    self.token,
                    [{'imdbid': str(imdb), 'sublanguageid': lang}],
                    [100])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            return self._select_sub_(result['data'])

    @retry
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

    def __init__(self, sub_data, sub_info, decode=True):
        '''
        Args:
            sub_data (bytes): subtitles in SRT format
            sub_ingo (:obj:`dict`): subtitles information
        '''
        self.sub_info = {}
        self.sub_info['SubLanguageID'] = sub_info.get('SubLanguageID', None)
        self.sub_info['SubFileName'] = sub_info.get('SubFileName', None)
        self.sub_info['SubEncoding'] = sub_info.get('SubEncoding', None)
        self.sub_info['MovieName'] = sub_info.get('MovieName', None)
        self.sub_info['IDMovieImdb'] = sub_info.get('IDMovieImdb', None)
        self.sub_info['IDSubtitleFile'] = sub_info.get('IDSubtitleFile', None)

        # Decode bytes to Unicode string
        if decode:
            data_decoded = self.sub_decode(sub_data, self.sub_info['SubEncoding'])
        else:
            data_decoded = sub_data


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
        #import ipdb; ipdb.set_trace()
        if encoding:
            if data.startswith(codecs.BOM_UTF8):
                enc = 'utf-8-sig'
            else:
                enc = encoding
            return data.decode(enc, errors='replace')
        else:
            return UnicodeDammit(data).unicode_markup

    def save(self, name=None):
        data = srt.compose(self.sub)
        file_name = name if name else self.sub_info['SubFileName']
        with open(os.path.join(FILES_DIR,file_name), 'w') as f:
            f.write(data)

    @classmethod
    def read(cls, sub_info):
        #import ipdb; ipdb.set_trace()
        name = os.path.join(FILES_DIR,sub_info['SubFileName'])
        with open(name, 'r') as f:
            data = f.read()
        return cls(data, sub_info, decode=False)


    def get_subs(self, start, end):
        '''
        Return list of <str> from subtitles
        whose timedelta is between start and stop.
        Args:
            start (float): start time of subtitles
            end (float): end time of subtitles
        Returns:
            :obj:`list` of :obj:`Subtitles`
        '''
        subs = []
        for s in self.sub:
            if (s.start >= self.seconds_to_timedelta(start) and
                s.start <= self.seconds_to_timedelta(end)):
                subs.append(s)
        return subs

    def _parse_subtitles_(self, data):
        try:
            sub = list(srt.parse(data))
            return sub
        except ValueError as e:
            print("Subtitles parsing failed: {}".format(e))
            return []

    def seconds_to_timedelta(self, seconds):
        s = int(seconds)
        ms = seconds - s
        return timedelta(seconds=s,  milliseconds=ms)


class SubPair:
    ''' Pair of subtitles'''

    def __init__(self, subs):
        '''
        Args:
            subs: list of <Subs> objects
        '''
        self.subs = subs
        self.first_start = 0
        self.first_end = subs[0].sub[-1].start.total_seconds()
        self.second_start = 0
        self.second_end = subs[0].sub[-1].start.total_seconds()

    def __repr__(self):
        return "[{}, {}]".format(self.subs[0].__repr__(),
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
                #import ipdb; ipdb.set_trace()
                s = Subs(sub_b, sub)
                if s.sub:
                    subs.append(s)
                else:
                    print("Failed the subtitles parsing")
                    return None
            else:
                print("Subtitles #{} isn't found".format(imdbid))
                osub.logout()
                return None

        osub.logout()
        return cls(subs)

    @classmethod
    def read(cls, info):
        subs = []
        #import ipdb; ipdb.set_trace()
        for sub in info['subs']:
            s = Subs.read(sub)
            subs.append(s)
        return cls(subs)

    def get_parallel_subs(self, start, length):
        '''
        Args:
            start (float): 0-100 percenrage of full length from the begin
            lenght (int): duration in seconds
        Returns:
            :obj:`tuple` of :obj:`list' of :obj:`Subtitles`
        '''
        first_len = self.first_end - self.first_start
        second_len = self.second_end - self.second_start
        coeff = first_len/second_len
        offset = first_len * start / 100

        f_start = self.first_start + offset
        f_end = f_start + length

        s_start = self.second_start + offset/coeff
        s_end = s_start + length/coeff

        par_subs = []
        for s, params in zip(self.subs, [(f_start, f_end), (s_start, s_end)]):
            subs = s.get_subs(*params)
            par_subs.append(subs)

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

    def print_pair_random(self, count=30):
        offset = random.random() * 100
        self.print_pair(offset, count)

    def print_for_align(self, count=4):
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
        self.first_start = self.subs[0].sub[left_start-1].start.total_seconds()
        self.first_end = self.subs[0].sub[left_end-1].start.total_seconds()

        self.second_start = self.subs[1].sub[right_start-1].start.total_seconds()
        self.second_end = self.subs[1].sub[right_end-1].start.total_seconds()

    def save_subs(self):
        for sub in self.subs:
            sub.save()

    def get_id(self):
        return '_'.join([
                self.subs[0].sub_info['IDSubtitleFile'],
                self.subs[1].sub_info['IDSubtitleFile']
                ])

    def get_data(self):
        return {'first_start': self.first_start,
                'first_end': self.first_end,
                'second_start': self.second_start,
                'second_end': self.second_end,
                'subs': [
                    self.subs[0].sub_info,
                    self.subs[1].sub_info
                    ]}

    def learn(self, length):
        while True:
            offset = random.random() * 100
            self.print_pair(offset, length, hide_right=True)
            print()
            data = input("Press 'Enter' (or 'q' + 'Enter' to quit)")
            if data:
                break
            print()
            self.print_pair(offset, length, hide_right=False)
            data = input("Press 'Enter' (or 'q' + 'Enter' to quit) ")
            if data:
                break
            print()


class SubDb():

    def __init__(self):
        self.data = self.load_data()
        self.cache = {}

    def load_data(self):
        '''
        Init cache
        '''
        # verify that the application directory (~/.pairsubs) exists,
        #   else create it
        #import ipdb; ipdb.set_trace()
        if not os.path.exists(APP_DIR):
            os.makedirs(APP_DIR)

        if not os.path.exists(FILES_DIR):
            os.makedirs(FILES_DIR)

        # If the cache db doesn't exist we create it.
        # Otherwise we only open for reading
        if not os.path.isfile(CACHE_DB):
            with open(CACHE_DB, 'a'):
                os.utime(CACHE_DB, None)

        data = {}

        # We know from above that this file exists so we open it
        #   for reading only.
        with open(CACHE_DB, 'r') as f:
            try:
                data = json.load(f)
            except ValueError:
                pass
        return data

    def is_in_db(self, sub_pair):
        sub_id = sub_pair.get_id()
        return sub_id in self.data

    def add_subpair(self, sub_pair):
        if not self.is_in_db(sub_pair):
            sub_id = sub_pair.get_id()
            sub_data = sub_pair.get_data()
            self.data[sub_id] = sub_data

    def download(self, imdbid, lang1, lang2):
        sub_pair = SubPair.download(imdbid, lang1, lang2)
        #import ipdb; ipdb.set_trace()
        if sub_pair:
            self.add_subpair(sub_pair)
            self.add_to_cache(sub_pair)
            self.write_db()
            sub_pair.save_subs()
            return sub_pair.get_id()

    def write_db(self):

        # update db data with the alignment data from cache
        keys = ('first_start', 'first_end',
                'second_start', 'second_end')
        for sub_id in self.cache:
            for k in keys:
                self.data[sub_id][k] = getattr(self.cache[sub_id], k)

        with open(CACHE_DB, 'w') as f:
            f.write(json.dumps(self.data))

    def add_to_cache(self, sub_pair):
        sub_id = sub_pair.get_id()
        if not sub_id in self.cache:
            self.cache[sub_id] = sub_pair

    def read_subpair(self, sub_id):
        if not sub_id in self.cache:
            sub_info = self.data[sub_id]
            sub_pair = SubPair.read(sub_info)
            self.add_to_cache(sub_pair)

    def print_list(self):
        for sp in self.data.items():
            print('{}: {} [{}-{}]'.format(
                sp[0], # sub_id
                sp[1]['subs'][0]['MovieName'],
                sp[1]['subs'][0]['SubLanguageID'],
                sp[1]['subs'][1]['SubLanguageID']))

    def learn(self, sub_id=None):
        if not sub_id: # get random sub
            sub_id = random.choice(list(self.data.keys()))

        if not sub_id in self.cache:
            self.read_subpair(sub_id)
        self.cache[sub_id].learn(20)

        return self.cache[sub_id]

    def delete(self, sub_id):

        #remove subtitles files
        for s in self.data[sub_id]['subs']:
            filename = os.path.join(FILES_DIR, s['SubFileName'])
            try:
                os.remove(filename)
            except FileNotFoundError:
                print('File {} is not found'.format(filename))

        del self.data[sub_id]

        try:
            del self.cache[sub_id]
        except KeyError:
            pass

    def print_for_align(self, sub_id, count=4):
        if not sub_id in self.cache:
            self.read_subpair(sub_id)
        self.cache[sub_id].print_for_align(count)
        return self.cache[sub_id]

    def align_subs(self, sub_id, left_start, right_start, left_end, right_end):
        if not sub_id in self.cache:
            self.read_subpair(sub_id)
        self.cache[sub_id].align_subs(left_start, right_start, left_end, right_end)
        self.write_db()
        return self.cache[sub_id]

if __name__ == '__main__':

    s = SubPair.download("5015956", "rus", "eng")
    learn(s, 20)
