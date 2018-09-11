from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.views.generic.list import ListView
from celery.result import AsyncResult
import json
import re

from .forms import SubSearchForm
from .forms import AlignFormSet
from .models import PairOfSubs
from .models import get_subtitles
from .models import get_subtitles_for_alignment
from .models import set_alignment_data
from .tasks import download_sub

import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def home(request):
    return HttpResponseRedirect(
        reverse('pairsubs:subpair_show')
        )


@require_http_methods(["GET", "POST"])
def opensubtitles_search(request):
    logger.info(request)

    # import ipdb; ipdb.set_trace()
    status = {}
    if request.method == 'POST':
        form = SubSearchForm(request.POST)
        if form.is_valid():
            imdb_r = re.search(r'\d+', form.cleaned_data['imdb'])
            if imdb_r:
                imdb = imdb_r[0].lstrip('0')
                lang1 = form.cleaned_data['lang1']
                lang2 = form.cleaned_data['lang2']
                sp = PairOfSubs.objects.filter(id_movie_imdb=imdb,
                                               first_lang=lang1,
                                               second_lang=lang2)
                if not sp:  # check if not exists already
                    logger.info('Start download...')
                    result = download_sub.delay(imdb, lang1, lang2)
                    return HttpResponseRedirect(
                        reverse('pairsubs:status')+'?id={}'.format(result.task_id)
                        )
                else:
                    status.update(
                        {'error_message':
                         'Subtitles IMDB {} are already exiist in database'.format(imdb)})

    else:  # GET
        form = SubSearchForm()

    status.update({'form': form})
    return render(request, "pairsubs/search.html", status)


def opensubtitles_download(request):
    return HttpResponse("ToDo")


def subpair_info(request, id):
    subs_pair = PairOfSubs.objects.get(pk=id)
    sub1 = subs_pair.first_sub
    info = {'MovieName': sub1.movie_name,
            'Languages': (subs_pair.first_lang, subs_pair.second_lang),
            'IMDB': sub1.id_movie_imdb,
            'id': id
            }

    return render(request, 'pairsubs/sub_info.html', {'sub_info': info})


def status(request):
    task_id = request.GET.get('id', None)
    return render(request, 'pairsubs/status.html', {'status': task_id})


def subpair_show(request):
    sub_id = request.GET.get('id', None)
    return render(request, 'pairsubs/show.html', {'id': sub_id})


def get_subtitles_data(request):
    # import ipdb; ipdb.set_trace()
    sub_id = request.GET.get('id', None)
    if sub_id:
        sub_id = int(sub_id)

    offset = int(request.GET.get('offset', '0'))
    length = int(request.GET.get('length', '0'))
    subtitles = get_subtitles(sub_id, offset, length)
    return JsonResponse({'data': subtitles})


class SubPairListView(ListView):

    model = PairOfSubs
    paginate_by = 100  # if pagination is desired
    ordering = ['-id']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def check_task(request):
    result = AsyncResult(request.POST['task_id'])
    status = result.status
    result = result.result
    return HttpResponse(
            json.dumps({'status': status,
                        'result': result}
                       ), content_type='application/json')


def subpair_align(request, id):
    if request.method == 'POST':
        # import ipdb; ipdb.set_trace()
        subs = get_subtitles_for_alignment(id)
        formset = AlignFormSet(request.POST, form_kwargs={'subs': subs})
        if formset.is_valid():
            set_alignment_data(id, formset.cleaned_data)
            return HttpResponseRedirect(
                    reverse('pairsubs:subpair_show')+'?id={}'.format(id))
        else:
            status.update({'error_message': 'error'})

    else:  # GET
        subs = get_subtitles_for_alignment(id)
        formset = AlignFormSet(form_kwargs={'subs': subs})

    return render(request,
                  'pairsubs/align.html',
                  {'formset': formset, 'sub_id': id})


def subpair_delete(request, id):
    if request.method == 'DELETE':
        PairOfSubs.objects.filter(pk=id).delete()
    return HttpResponse(json.dumps({'status': 'SUCCESS'}))
