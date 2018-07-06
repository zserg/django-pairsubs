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
                start = e.start.seconds * 1000 + e.start.microseconds,
                end = e.end.seconds * 1000 + e.end.microseconds,
                text = e.content,
                subtitles = s_i
                )

    sp = SubPair.objects.create(
            first_sub = subs[0],
            second_sub = subs[1],
            first_start = 0,
            first_end = 0,
            second_start = 0,
            second_end = 0
            )

    return sp

