"""
Celery tasks
"""
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import create_subs
from . import pairsubs
import time


@shared_task(bind=True)
def download_sub(self, imdb, lang1, lang2):
    """
    Search & download pair of subs
    from opensubtitles.org and
    create PairOfSubs object in DB
    """
    pair, log = pairsubs.SubPair.download(imdb, lang1, lang2)
    if pair:
        sub_pair = create_subs(pair)
        return "Success", sub_pair.id, log
    else:
        return "Fail", None, log


