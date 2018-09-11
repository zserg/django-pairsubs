from django import forms
from django.forms import BaseFormSet
from django.forms import formset_factory


class SubSearchForm(forms.Form):
    w = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rus'})
    imdb = forms.CharField(
         label='IMDb link',
         widget=forms.TextInput(
           attrs={'class': 'form-control',
                  'placeholder':
                  'https://www.imdb.com/title/tt0583539/?ref_=ttep_ep4'}),
    )
    lang1 = forms.CharField(
         label='First language',
         max_length=3,
         widget=forms.TextInput(
           attrs={'class': 'form-control',
                  'placeholder': 'rus'}),
    )

    lang2 = forms.CharField(
         label='Second language',
         max_length=3,
         widget=forms.TextInput(
           attrs={'class': 'form-control',
                  'placeholder': 'eng'}),
    )


class AlignForm(forms.Form):
    def __init__(self, subs, index,  *args, **kwargs):
        super(AlignForm, self).__init__(*args, **kwargs)
        self.fields['subs_choice'] = forms.ChoiceField(choices=subs[index],
                                                       widget=forms.RadioSelect)


class BaseAlignFormSet(BaseFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['index'] = index
        return kwargs


AlignFormSet = formset_factory(AlignForm, formset=BaseAlignFormSet, extra=4)
