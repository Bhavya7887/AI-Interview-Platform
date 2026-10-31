from django import forms
from .models import Interview

class InterviewSetupForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ["role", "level", "number_of_questions", "seconds_per_question", "job_description", "resume_file"]
        widgets = {
            "role": forms.TextInput(attrs={"placeholder": "e.g. Python Developer", "class": "form-control"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "number_of_questions": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 15}),
            "seconds_per_question": forms.NumberInput(attrs={"class": "form-control", "min": 30, "max": 300}),
            "job_description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Paste an optional job description"}),
            "resume_file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.docx"}),
        }

    def clean_role(self):
        role = self.cleaned_data["role"].strip()
        if not role:
            raise forms.ValidationError("Please enter a target role.")
        return role

    def clean_number_of_questions(self):
        value = self.cleaned_data["number_of_questions"]
        if not 1 <= value <= 15:
            raise forms.ValidationError("Choose between 1 and 15 questions.")
        return value

    def clean_seconds_per_question(self):
        value = self.cleaned_data["seconds_per_question"]
        if not 30 <= value <= 300:
            raise forms.ValidationError("Choose between 30 and 300 seconds.")
        return value

    def clean_resume_file(self):
        file = self.cleaned_data.get("resume_file")
        if not file:
            return file
        allowed = (".pdf", ".docx")
        if not file.name.lower().endswith(allowed):
            raise forms.ValidationError("Upload a PDF or DOCX resume.")
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Resume must be 5 MB or smaller.")
        return file
