from django.test import TestCase
from django.test import Client
from django.urls import reverse
from bs4 import BeautifulSoup
from unittest.mock import MagicMock
from unittest.mock import patch
import srt
import random
import json
from datetime import timedelta

from pairsubs import pairsubs
from pairsubs import models


def generate_sub(imdb, lang):
    sub_count = 10
    sub_info = {
        'MovieName': 'Name_{}'.format(imdb),
        'SubEncoding': 'utf-8',
        'SubFileName': 'File_{}'.format(imdb),
        'SubLanguageID': lang,
        'IDMovieImdb': imdb,
        'IDSubtitleFile': 10
    }
    sub = []
    for i in range(sub_count):
        s = srt.Subtitle(
            i+1,
            timedelta(seconds=i*10, milliseconds=100),
            timedelta(seconds=i*10+5, milliseconds=800),
            'Subtitle #{}'.format(i)
            )
        sub.append(s)
        sub_s = srt.compose(sub)

    return pairsubs.Subs(sub_s.encode('utf-8'), sub_info)


def mock_pair_sub(imdb, lang1, lang2):
    if imdb == 'to_be_not_found':
        return None
    else:
        subs = [generate_sub(imdb, lang1),
                generate_sub(imdb, lang2)
                ]
        return pairsubs.SubPair(subs)


class SubTestCase(TestCase):

    def test_create_models(self):
        pair = mock_pair_sub('12345', 'rus', 'eng')
        sub_pair = models.create_subs(pair)
        self.assertIsInstance(sub_pair, models.PairOfSubs)
        self.assertEqual(sub_pair.first_start, 0)
        self.assertEqual(sub_pair.first_end, 90100)
        self.assertEqual(sub_pair.second_start, 0)
        self.assertEqual(sub_pair.second_end, 90100)
        self.assertEqual(sub_pair.id_movie_imdb, '12345')
        self.assertEqual(sub_pair.first_lang, 'rus')
        self.assertEqual(sub_pair.second_lang, 'eng')


class ViewsTestCase(TestCase):

    def SetUp(self):
        self.client = Client()

    def test_home(self):
        response = self.client.get(reverse('pairsubs:home'))
        self.assertRedirects(response, reverse('pairsubs:subpair_show'))

    @patch.object(pairsubs.SubPair, 'download', mock_pair_sub)
    def test_search_form(self):
        response = self.client.get(reverse('pairsubs:opensubtitles_search'))
        self.assertEqual(200, response.status_code)

        # import ipdb; ipdb.set_trace()
        soup = BeautifulSoup(response.content, 'html.parser')
        search_form = soup.find('form', {
            'name': 'search_subs',
            'action': reverse('pairsubs:opensubtitles_search')
            })
        self.assertIsNotNone(search_form)

        imdb_input = soup.find('input', {'id': 'id_imdb'})
        self.assertIsNotNone(imdb_input)

        lang1_input = soup.find('input', {'id': 'id_lang1'})
        self.assertIsNotNone(lang1_input)
        lang2_input = soup.find('input', {'id': 'id_lang2'})
        self.assertIsNotNone(lang2_input)

    def test_subpair_show(self):
        pair = mock_pair_sub('to_be_found', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        response = self.client.get(
            reverse('pairsubs:subpair_show'),
            {'id': sub_pair.id, 'offset': 11000, 'length': 30000}
            )
        self.assertEqual(200, response.status_code)

        self.assertIsNotNone(response.context['id'])

    def test_subpair_list(self):
        pair = mock_pair_sub('1234', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        response = self.client.get(reverse('pairsubs:subpair-list'))
        self.assertEqual(200, response.status_code)

        self.assertEqual(response.context['object_list'][0].first_sub.movie_name, 'Name_1234')

    def test_search_already_exists(self):
        pair = mock_pair_sub('1234', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        url = reverse('pairsubs:opensubtitles_search')
        response = self.client.post(url, {'imdb':'1234', 'lang1':'rus', 'lang2':'eng'})
        self.assertIsNotNone(response.context['error_message'])

    @patch('pairsubs.models.randrange', return_value=10)
    def test_get_subtitles_data(self, mock_randrange):
        pair = mock_pair_sub('to_be_found', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        response = self.client.get(reverse('pairsubs:get_subtitles_data'))
        self.assertEqual(200, response.status_code)

        text = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(text['data'])
        self.assertIsNotNone(text['data']['sub_info'])
        self.assertIsNotNone(text['data']['subs'])
        self.assertEqual(len(text['data']['subs'][0]), 2)


