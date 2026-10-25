from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@require_POST
@login_required
def custom_logout(request):
    logout(request)
    return redirect('accounts:login')
