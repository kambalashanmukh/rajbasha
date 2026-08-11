from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):

    super_annuation_date = forms.DateField(
        label="Superannuation Date",
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date"
            }
        )
    )

    class Meta:
        model = Employee

        fields = [
            "empcode",
            "ename",
            "hname",

            "mother_tongue",
            "education_qualification",
            "matric_medium",
            "hindi_in_matric",
            "hindi_in_graduation",

            "designation",
            "highest_exam",
            "hindiproficiency",
            "official_work_in_hindi",

            "typing",
            "gazet",
            "stenographer",
            "olic_affiliate",
        ]

        labels = {
            "empcode": "Empcode",
            "ename": "Name in English",
            "hname": "Name in Hindi",
            "designation": "Designation",
            "typing": "Typing",
            "hindiproficiency": "Hindi Proficiency",
            "gazet": "Gazet",
            "stenographer": "Stenographer",
            "highest_exam": "Highest Hindi Exam Passed",
            "olic_affiliate": "OLIC Affiliate",
            "mother_tongue": "Mother Tongue",

            "education_qualification": "Educational Qualification",

            "matric_medium": "Medium of Examination of Matric or Equivalent",

            "hindi_in_matric": "Whether Hindi was one of the subjects in Matric",

            "hindi_in_graduation": "Whether Hindi was one of the subjects in Graduation",

            "official_work_in_hindi": "How much of your official work do you perform in Hindi",
        }

        widgets = {

            "empcode": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "ename": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "hname": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "mother_tongue": forms.Select(
                attrs={"class": "form-select"}
            ),

            "education_qualification": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "matric_medium": forms.Select(
                attrs={"class": "form-select"}
            ),

            "hindi_in_matric": forms.Select(
                attrs={"class": "form-select"}
            ),

            "hindi_in_graduation": forms.Select(
                attrs={"class": "form-select"}
            ),

            "official_work_in_hindi": forms.Select(
                attrs={"class": "form-select"}
            ),
            
            # Dropdowns (choices come automatically from model)
            "designation": forms.Select(
                attrs={"class": "form-select"}
            ),

            "typing": forms.Select(
                attrs={"class": "form-select"}
            ),

            "hindiproficiency": forms.Select(
                attrs={"class": "form-select"}
            ),

            "gazet": forms.Select(
                attrs={"class": "form-select"}
            ),

            "stenographer": forms.Select(
                attrs={"class": "form-select"}
            ),

            "highest_exam": forms.Select(
                attrs={"class": "form-select"}
            ),

            "olic_affiliate": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # decrypt superannuation date
        if self.instance and self.instance.pk:

            decrypted_date = self.instance.get_super_annuation_date()

            if decrypted_date:
                self.fields["super_annuation_date"].initial = decrypted_date
