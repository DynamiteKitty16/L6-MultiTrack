from django import forms
from .models import AttendanceRecord

class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['date', 'type']
        weights = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }