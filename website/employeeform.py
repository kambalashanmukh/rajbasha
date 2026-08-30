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
            "mother_tongue",
            "education_qualification",
            "matric_medium",
            "hindi_in_matric",
            "hindi_in_graduation",
            "designation",
            "highest_exam",
            "hindiproficiency",
            "official_work_in_hindi",
            "super_annuation_date",
        ]

        labels = {
            "empcode": "Emp. Code / कर्मचारी कोड",
            "ename": "Name / नाम",

            "mother_tongue": "Mother Tongue / मातृ भाषा",

            "education_qualification":
                "Education Qualifications / शैक्षणिक योग्यताएँ",

            "matric_medium":
                "Medium of examination of Matric or Equivalent / मैट्रिक या समकक्ष परीक्षा का माध्यम",

            "hindi_in_matric":
                "Whether Hindi was one of the subjects in Matric or Equivalent / क्या मैट्रिक या समकक्ष परीक्षा में हिंदी एक विषय था",

            "hindi_in_graduation":
                "Whether Hindi was one of the subjects in Graduation or Equivalent / क्या स्नातक या समकक्ष परीक्षा में हिंदी एक विषय था",

            "designation":
                "Designation / पदनाम",

            "highest_exam":
                "Highest Examination passed under Hindi Teaching Scheme (MHA) / हिंदी शिक्षण योजना (गृह मंत्रालय) के अंतर्गत उत्तीर्ण उच्चतम परीक्षा",

            "hindiproficiency":
                "Possess knowledge of Hindi / हिंदी का ज्ञान",

            "official_work_in_hindi":
                "How much of your official work do you perform in Hindi / आप अपने सरकारी कार्य का कितना भाग हिंदी में करते हैं",

            "super_annuation_date":
                "Date of Retirement / सेवानिवृत्ति की तारीख",
        }

        widgets = {

            "empcode": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "ename": forms.TextInput(
                attrs={"class": "form-control",
                       "style": "text-transform: uppercase;"
                       }
            ),

            "mother_tongue": forms.Select(
                attrs={"class": "form-select"}
            ),

            "education_qualification": forms.TextInput(
                attrs={"class": "form-control",
                       "style": "text-transform: uppercase;"
                       }
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

            "hindiproficiency": forms.Select(
                attrs={"class": "form-select"}
            ),

            "highest_exam": forms.Select(
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

    def clean_ename(self):
        """Name field: reject any digit characters (e.g. "John123", "12345",
        "123 John"), independent of any frontend/JS validation, so a direct
        POST bypassing the browser is still rejected."""
        value = (self.cleaned_data.get("ename") or "").strip()

        if value:
            if any(ch.isdigit() for ch in value):
                raise forms.ValidationError(
                    "Name must not contain numbers."
                )
            if not any(ch.isalpha() for ch in value):
                raise forms.ValidationError(
                    "Name must contain valid alphabetic characters."
                )

        return value.upper()
