from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    slide_count = forms.CharField(max_length=2)
    file  = forms.FileField()