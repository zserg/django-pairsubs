from django.db import models

class Subs(models.Model):
    movie_name = models.CharField(max_length=100)
    sub_language_id = models.CharField(max_length=3)
    sub_file_name = models.CharField(max_length=100)
    id_movie_imdb = models.CharField(max_length=100)
    id_sub_file = models.CharField(max_length=100)

class SubElement(models.Model):
    num = models.IntegerField()
    start = models.IntegerField()
    end = models.IntegerField()
    text = models.CharField(max_length=220)
    subtitles = models.ForeignKey(Subs, on_delete=models.CASCADE)

class SubPair(models.Model):
    id_movie_imdb = models.CharField(max_length=100, null=True)
    first_lang = models.CharField(max_length=3, null=True)
    second_lang = models.CharField(max_length=3, null=True)
    first_sub = models.ForeignKey(Subs, null=True, related_name='first_sub', on_delete=models.SET_NULL)
    second_sub = models.ForeignKey(Subs, null=True, related_name='second_sub', on_delete=models.SET_NULL)
    first_start = models.IntegerField()
    first_end = models.IntegerField()
    second_start = models.IntegerField()
    second_end = models.IntegerField()


def create_subs(pair):
    subs = []
    #import ipdb; ipdb.set_trace()
    for s in pair.subs:
        s_i = Subs.objects.create(
            movie_name = s.sub_info['MovieName'],
            sub_language_id = s.sub_info['SubLanguageID'],
            sub_file_name   = s.sub_info['SubFileName'],
            id_movie_imdb   = s.sub_info['IDMovieImdb'],
            id_sub_file     = s.sub_info['IDSubtitleFile'],
            )
        subs.append(s_i)

        for e in s.sub:
            SubElement.objects.create(
                num = e.index,
                start = int((e.start.seconds * 1000000 + e.start.microseconds)/1000),
                end = int((e.end.seconds * 1000000 + e.end.microseconds)/1000),
                text = e.content,
                subtitles = s_i
                )


    first_end = subs[0].subelement_set.order_by('num').last().start
    second_end = subs[1].subelement_set.order_by('num').last().start

    sp = SubPair.objects.create(
            id_movie_imdb = subs[0].id_movie_imdb,
            first_lang =subs[0].sub_language_id,
            second_lang =subs[1].sub_language_id,
            first_sub = subs[0],
            second_sub = subs[1],
            first_start = 0,
            first_end = first_end,
            second_start = 0,
            second_end = second_end
            )

    return sp

def get_subtitles(id, offset, length):
    subs_pair = SubPair.objects.get(pk=id)
    subs = []
    #import ipdb; ipdb.set_trace()
    for sub in subs_pair.first_sub, subs_pair.second_sub:
        elements = sub.subelement_set.filter(start__lte=(offset+length),
                                              end__gte=offset).order_by('num')
        subs.append([e.text for e in elements])

    sub_info = {'name':'Name'}
    return {'sub_info': sub_info, 'subs': subs}



