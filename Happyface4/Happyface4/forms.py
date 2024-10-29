from django import forms


class DateTimeForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "style": "min-width:120px;",
            }
        )
    )
    time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                "class": "form-control",
                "id": "time-input",
                "type": "time",
                "style": "min-width:80px;",
            }
        )
    )
