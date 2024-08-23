from django import forms
from .models import UploadedPPT
from django.db import connection

class UploadPPTForm(forms.ModelForm):
    class Meta:
        model = UploadedPPT
        fields = ['file']
        
        
# forms.py

class TableSelectionForm(forms.Form):
    tables = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        label="Select Tables to Download",
    )

    def __init__(self, *args, **kwargs):
        super(TableSelectionForm, self).__init__(*args, **kwargs)
        self.fields['tables'].choices = self.get_table_choices()

    def get_table_choices(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = [row[0] for row in cursor.fetchall()]
        return [(table, table) for table in table_names]
