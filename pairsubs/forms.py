from django import forms

class SubSearchForm(forms.Form):
    w = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rus'})
    imdb = forms.CharField(
         label='IMDb link',
         widget = forms.TextInput(
           attrs={'class': 'form-control',
                  'placeholder': 'https://www.imdb.com/title/tt0583539/?ref_=ttep_ep4'}),
	)
    lang1 = forms.CharField(
     	 label='First language',
         max_length=3,
         widget = forms.TextInput(
           attrs={'class': 'form-control',
                  'placeholder': 'rus'}),
	)

    lang2 = forms.CharField(
     	 label='Second language',
         max_length=3,
         widget = forms.TextInput(
           attrs={'class': 'form-control',
                  'placeholder': 'eng'}),
	)
