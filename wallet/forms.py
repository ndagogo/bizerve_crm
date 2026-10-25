from django import forms
from .models import WithdrawalRequest, WithdrawalMethod, Wallet

class WithdrawalRequestForm(forms.ModelForm):
    class Meta:
        model = WithdrawalRequest
        fields = ['withdrawal_method', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0',
                'class': 'form-control'
            }),
            'withdrawal_method': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show active withdrawal methods
        self.fields['withdrawal_method'].queryset = WithdrawalMethod.objects.filter(is_active=True)
        
        # Add dynamic fields based on selected method
        self.fields['bank_name'] = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['account_number'] = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['account_name'] = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['paypal_email'] = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
        self.fields['crypto_wallet'] = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['mobile_number'] = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        wallet, _ = Wallet.objects.get_or_create(user=self.user)

        if amount > wallet.balance:
            raise forms.ValidationError("Insufficient balance for this withdrawal.")

        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        withdrawal_method = cleaned_data.get('withdrawal_method')
        amount = cleaned_data.get('amount')
        
        if withdrawal_method and amount:
            # Check minimum amount
            if amount < withdrawal_method.minimum_amount:
                raise forms.ValidationError(
                    f"Minimum withdrawal amount is ${withdrawal_method.minimum_amount}"
                )
            
            # Check maximum amount
            if withdrawal_method.maximum_amount and amount > withdrawal_method.maximum_amount:
                raise forms.ValidationError(
                    f"Maximum withdrawal amount is ${withdrawal_method.maximum_amount}"
                )
            
            # Validate method-specific fields
            method_type = withdrawal_method.withdrawal_type
            if method_type == 'bank':
                if not cleaned_data.get('bank_name') or not cleaned_data.get('account_number'):
                    raise forms.ValidationError("Bank name and account number are required for bank transfers.")
            elif method_type == 'paypal':
                if not cleaned_data.get('paypal_email'):
                    raise forms.ValidationError("PayPal email is required.")
            elif method_type == 'crypto':
                if not cleaned_data.get('crypto_wallet'):
                    raise forms.ValidationError("Cryptocurrency wallet address is required.")
            elif method_type == 'mobile_money':
                if not cleaned_data.get('mobile_number'):
                    raise forms.ValidationError("Mobile number is required.")
        
        return cleaned_data

class WithdrawalMethodForm(forms.ModelForm):
    class Meta:
        model = WithdrawalMethod
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'fee_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'fee_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'minimum_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'maximum_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }