from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.views.generic.list import ListView
from celery.result import AsyncResult
import json
import re

from . import pairsubs
from .forms import SubSearchForm
from .models import PairOfSubs
from .models import get_subtitles, create_subs
from .models import get_subtitles_for_alignment
from .tasks import download_sub

def home(request):
    return render(request, "pairsubs/home.html")

@require_http_methods(["GET", "POST"])
def opensubtitles_search(request):
    #import ipdb; ipdb.set_trace()
    status = {}
    if request.method == 'POST':
        form = SubSearchForm(request.POST)
        if form.is_valid():
            imdb_r = re.search('\d+', form.cleaned_data['imdb'])
            if imdb_r:
                imdb = imdb_r[0].lstrip('0')
                lang1 = form.cleaned_data['lang1']
                lang2 = form.cleaned_data['lang2']
                sp = PairOfSubs.objects.filter(id_movie_imdb = imdb,
                                         first_lang = lang1,
                                         second_lang = lang2)
                if not sp: # check if not exists already
                    result = download_sub.delay(imdb, lang1, lang2)
                    print(result.task_id)
                    #import ipdb; ipdb.set_trace()
                    return HttpResponseRedirect(reverse('pairsubs:status')+'?id={}'.format(result.task_id))
                else:
                    status.update({'error_message':
                        "Subtitles IMDB {} are already exiist in database".format(imdb)})

    else: # GET
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
    #import ipdb; ipdb.set_trace()
    sub_id = request.GET.get('id', None)
    if sub_id:
        sub_id = int(sub_id)

    offset = int(request.GET.get('offset', '0'))
    length = int(request.GET.get('length', '0'))
    subtitles = get_subtitles(sub_id, offset, length)
    return JsonResponse({'data':subtitles})


class SubPairListView(ListView):

    model = PairOfSubs
    paginate_by = 100  # if pagination is desired
    #ordering = ['first_sub__movie_name']
    ordering = ['-id']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def check_task(request):
    result = AsyncResult(request.POST['task_id'])
    status = result.status
    result = result.result
    print(status)
    print(result)
    return HttpResponse(json.dumps({
	'status': status,
        'result': result
    }), content_type='application/json')


def subpair_align(request, id):
    subs = get_subtitles_for_alignment(id)
    return render(request, 'pairsubs/align.html', {'id': id, 'subs': subs})




