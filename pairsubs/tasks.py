"""
Celery tasks
"""
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.contrib import rdb
from .models import create_subs
from . import pairsubs
import time

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task(bind=True)
def download_sub(self, imdb, lang1, lang2):
    """
    Search & download pair of subs
    from opensubtitles.org and
    create PairOfSubs object in DB
    """
    logger.info('tasks: download_sub')
    pair, log = pairsubs.SubPair.download(imdb, lang1, lang2)
    if pair:
        sub_pair = create_subs(pair)
        return "Success", sub_pair.id, log
    else:
        return "Fail", None, log


