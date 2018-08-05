from django.test import TestCase
from django.test import Client
from django.urls import reverse
from bs4 import BeautifulSoup
from unittest.mock import MagicMock
from unittest.mock import patch
import srt
import random
from datetime import timedelta

from pairsubs import pairsubs
from pairsubs import models

def generate_sub(imdb, lang):
    sub_count = 10
    sub_info = {
        'MovieName':'Name_{}'.format(imdb),
        'SubEncoding':'utf-8',
        'SubFileName':'File_{}'.format(imdb),
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
        self.assertEqual(200, response.status_code)

        soup = BeautifulSoup(response.content, 'html.parser')
        hrefs = [x['href'] for x in soup.find_all('a', href=True)]

        self.assertIn(reverse('pairsubs:opensubtitles_search'), hrefs)
        self.assertIn(reverse('pairsubs:subpair_show'), hrefs)
        self.assertIn(reverse('pairsubs:subpair-list'), hrefs)


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
        p = models.PairOfSubs.objects.get()
        self.assertRedirects(response, reverse('pairsubs:subpair_info', args=(p.pk,)),
                status_code=302, target_status_code=200)


    @patch.object(pairsubs.SubPair, 'download', mock_pair_sub)
    def test_search_form_not_found(self):
        url = reverse('pairsubs:opensubtitles_search')
        response = self.client.post(url, {'imdb':'to_be_not_found', 'lang1':'rus', 'lang2':'eng'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['not_found'], True)

    def test_subpair_show(self):
        pair = mock_pair_sub('to_be_found', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        response = self.client.get(reverse('pairsubs:subpair_show'),
                        {'id':sub_pair.id, 'offset':11000, 'length':30000})
        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.context['subtitles']['subs'][0]), 4)
        self.assertEqual(len(response.context['subtitles']['subs'][1]), 4)

    @patch('pairsubs.models.randrange', return_value=12000)
    def test_subpair_show_random(self, mock_randrange):
        pair = mock_pair_sub('to_be_found', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        response = self.client.get(reverse('pairsubs:subpair_show'))
        self.assertEqual(200, response.status_code)
        #import ipdb; ipdb.set_trace()

        self.assertEqual(len(response.context['subtitles']['subs'][0]), 4)
        self.assertEqual(len(response.context['subtitles']['subs'][1]), 4)

    def test_subpair_list(self):
        pair = mock_pair_sub('1234', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        response = self.client.get(reverse('pairsubs:subpair-list'))
        self.assertEqual(200, response.status_code)
        #import ipdb; ipdb.set_trace()

        self.assertEqual(response.context['object_list'][0].first_sub.movie_name, 'Name_1234')

    def test_search_already_exists(self):
        pair = mock_pair_sub('1234', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        url = reverse('pairsubs:opensubtitles_search')
        response = self.client.post(url, {'imdb':'1234', 'lang1':'rus', 'lang2':'eng'})
        self.assertEqual(response.context['already_exists'], True)

    def test_subpair_info(self):
        pair = mock_pair_sub('to_be_found', 'rus', 'eng')
        sub_pair = models.create_subs(pair)

        response = self.client.get(reverse('pairsubs:subpair_info', args=(sub_pair.id,)))
        self.assertEqual(200, response.status_code)

        self.assertEqual(response.context['sub_info']['MovieName'], 'Name_to_be_found')
        self.assertEqual(response.context['sub_info']['Languages'], ('rus', 'eng'))
        self.assertEqual(response.context['sub_info']['IMDB'], 'to_be_found')
        self.assertEqual(response.context['sub_info']['id'], sub_pair.id)

        soup = BeautifulSoup(response.content, 'html.parser')
        link = soup.findAll('a')
        #import ipdb; ipdb.set_trace()

        hrefs = [x['href'] for x in soup.find_all('a', href=True)]

        self.assertIn(reverse('pairsubs:subpair_show')+'?id={}'.format(sub_pair.id), hrefs)
        self.assertIn(reverse('pairsubs:subpair_show'), hrefs)


    def test_subpair_show_random_empty_base(self):
        response = self.client.get(reverse('pairsubs:subpair_show'))
        self.assertEqual(200, response.status_code)

        self.assertEqual(response.context['subtitles'], None)

