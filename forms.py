from django import forms

class SubSearchForm(forms.Form):
    imdb = forms.CharField(label='IMDB', max_length=32)
    lang1 = forms.CharField(label='Lang #1', max_length=3)
    lang2 = forms.CharField(label='Lang #2', max_length=3)
