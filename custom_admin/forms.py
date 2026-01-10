from django import forms
from accounts.models import User
from providers.models import ServiceProvider
from services.models import ServiceCategory
from .icon_list import get_icon_choices


class ServiceCategoryForm(forms.ModelForm):
    icon = forms.ChoiceField(
        choices=get_icon_choices(),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'icon-select'}),
        help_text="Select an Iconsax icon that will be displayed in the Flutter app"
    )
    
    class Meta:
        model = ServiceCategory
        fields = ['name', 'slug', 'icon', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProviderApprovalForm(forms.Form):
    verification_status = forms.ChoiceField(
        choices=[('approved', 'Approve'), ('rejected', 'Reject')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    verification_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="Optional notes for the provider"
    )




