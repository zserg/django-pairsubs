from django.test import TestCase
from django.test import Client
from django.urls import reverse
from bs4 import BeautifulSoup
from unittest.mock import MagicMock
from unittest.mock import patch
import srt
from datetime import timedelta

from pairsubs import pairsubs

from pairsubs import models

def generate_sub(name):
    sub_count = 10
    sub_info = {
        'MovieName':'Name_{}'.format(name),
        'SubEncoding':'utf-8',
        'SubFileName':'File_{}'.format(name),
        'SubLanguageID': 'en{}'.format(name[0]),
        'IDMovieImdb': '1234',
        'IDSubtitleFile': 10
    }
    sub = []
    for i in range(sub_count):
        s = srt.Subtitle(
            i+1,
            timedelta(seconds=i*10),
            timedelta(seconds=i*10+5),
            'Subtitle #{}'.format(i)
            )
        sub.append(s)
        sub_s = srt.compose(sub)

    return pairsubs.Subs(sub_s.encode('utf-8'), sub_info)

def mock_pair_sub(imdb, lang1, lang2):
    if imdb == 'to_be_found':
        subs = [generate_sub('one'),
                generate_sub('two')
                ]
        return pairsubs.SubPair(subs)
    else:
        return None


class SubTestCase(TestCase):

    def test_create_models(self):
        pair = mock_pair_sub('to_be_found', 'rus', 'eng')
        sub_pair = models.create_subs(pair)
        self.assertIsInstance(sub_pair, models.SubPair)


class ViewsTestCase(TestCase):

    def SetUp(self):
        self.client = Client()

    @patch.object(pairsubs.SubPair, 'download', mock_pair_sub)
    def test_search_form(self):
        response = self.client.get(reverse('pairsubs:opensubtitles_search'))
        self.assertEqual(200, response.status_code)

        #import ipdb; ipdb.set_trace()
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

        url = reverse('pairsubs:opensubtitles_search')
        response = self.client.post(url, {'imdb':'to_be_found', 'lang1':'rus', 'lang2':'eng'})
        p = models.SubPair.objects.get()
        self.assertRedirects(response, reverse('pairsubs:subpair_info', args=(p.pk,)),
                status_code=302, target_status_code=200)


    @patch.object(pairsubs.SubPair, 'download', mock_pair_sub)
    def test_search_form_not_found(self):
        response = self.client.get(reverse('pairsubs:opensubtitles_search'))
        self.assertEqual(200, response.status_code)

        url = reverse('pairsubs:opensubtitles_search')
        response = self.client.post(url, {'imdb':'not_to_be_found', 'lang1':'rus', 'lang2':'eng'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['not_found'], True)



