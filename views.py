from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from . import pairsubs
from .forms import SubSearchForm
from .models import create_subs, SubPair

def index(request):
    return HttpResponse("Hello, world! You are at the Pairsubs index!")

@require_http_methods(["GET", "POST"])
def opensubtitles_search(request):
    subtitles_not_found = False

    if request.method == 'POST':
        #import ipdb; ipdb.set_trace()
        found = True
        form = SubSearchForm(request.POST)
        if form.is_valid():
            imdb = form.cleaned_data['imdb']
            lang1 = form.cleaned_data['lang1']
            lang2 = form.cleaned_data['lang2']
            pair = download_sub(imdb, lang1, lang2)
            if pair:
                sub_pair = create_subs(pair)
                #import ipdb; ipdb.set_trace()
                return HttpResponseRedirect(reverse('pairsubs:subpair_info', args=(sub_pair.id,)))
            else:
                subtitles_not_found = True

    else: # GET
        form = SubSearchForm()

    return render(request, "pairsubs/search.html", {'form': form,
                                                    'not_found': subtitles_not_found})


def opensubtitles_download(request):
    return HttpResponse("ToDo")

def subpair_info(request, id):
    subs_pair = SubPair.objects.get(pk=id)
    sub1 = subs_pair.first_sub
    sub2 = subs_pair.second_sub
    elements = sub1.subelement_set.all()
    return HttpResponse(elements)

def subpair_show(request, id):
    return HttpResponse(id)


def download_sub(imdb, lang1, lang2):
    pair = pairsubs.SubPair.download(imdb, lang1, lang2)
    return pair



