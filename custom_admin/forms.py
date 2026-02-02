from django import forms
from accounts.models import User
from providers.models import ServiceProvider
from services.models import ServiceCategory
from .icon_list import get_icon_choices
from .models import EmailSettings


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


class EmailSettingsForm(forms.ModelForm):
    smtp_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter App Password (or leave blank to keep existing)',
            'autocomplete': 'new-password',
        }),
        help_text='For Gmail: use an App Password (Google Account → Security → 2-Step Verification → App passwords). Required when enabling email; leave blank only when updating other fields.',
    )

    class Meta:
        model = EmailSettings
        fields = [
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'from_email', 'use_tls', 'is_active',
        ]
        widgets = {
            'smtp_host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. smtp.gmail.com'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '587'}),
            'smtp_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'from_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'noreply@yourdomain.com'}),
            'use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        data = super().clean()
        is_active = data.get('is_active')
        password = data.get('smtp_password')
        instance = self.instance
        has_existing_password = instance and instance.pk and getattr(instance, 'smtp_password', None)
        if is_active and not password and not has_existing_password:
            self.add_error('smtp_password', 'SMTP password is required when enabling email. For Gmail, use an App Password.')
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        password = self.cleaned_data.get('smtp_password')
        if not password and obj.pk:
            # Keep existing password when field left blank
            existing = EmailSettings.objects.filter(pk=obj.pk).first()
            if existing and existing.smtp_password:
                obj.smtp_password = existing.smtp_password
        if commit:
            obj.save()
        return obj




