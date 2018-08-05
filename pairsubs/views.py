from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.views.generic.list import ListView

from . import pairsubs
from .forms import SubSearchForm
from .models import PairOfSubs
from .models import get_subtitles, create_subs

def home(request):
    return render(request, "pairsubs/home.html")

@require_http_methods(["GET", "POST"])
def opensubtitles_search(request):
    #import ipdb; ipdb.set_trace()
    status = {
            'not_found': False,
            'already_exists': False
            }

    if request.method == 'POST':
        #import ipdb; ipdb.set_trace()
        form = SubSearchForm(request.POST)
        if form.is_valid():
            imdb = form.cleaned_data['imdb']
            lang1 = form.cleaned_data['lang1']
            lang2 = form.cleaned_data['lang2']
            sp = PairOfSubs.objects.filter(id_movie_imdb = imdb,
                                     first_lang = lang1,
                                     second_lang = lang2)
            if not sp: # check if not exists already
                pair = download_sub(imdb, lang1, lang2)
                if pair:
                    sub_pair = create_subs(pair)
                    return HttpResponseRedirect(reverse('pairsubs:subpair_info', args=(sub_pair.id,)))
                else:
                    status['not_found'] = True
            else:
                status['already_exists'] = True

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

def subpair_show(request):
    #import ipdb; ipdb.set_trace()
    sub_id = request.GET.get('id', None)
    if sub_id:
        sub_id = int(sub_id)

    offset = int(request.GET.get('offset', '0'))
    length = int(request.GET.get('length', '0'))
    subtitles = get_subtitles(sub_id, offset, length)

    return render(request, 'pairsubs/show.html', {'subtitles': subtitles})


def download_sub(imdb, lang1, lang2):
    pair = pairsubs.SubPair.download(imdb, lang1, lang2)
    return pair


class SubPairListView(ListView):

    model = PairOfSubs
    paginate_by = 100  # if pagination is desired
    ordering = ['first_sub__movie_name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
