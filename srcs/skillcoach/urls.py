"""
URL configuration for skillcoach project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import admin
from django.urls import path, include
from authen.views import LandingPageView, SignupView, ActivateAccount
from authen.decorators import already_logged
# from administration.decorators import already_logged
from authen.forms import EmailAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LandingPageView.as_view(), name='landing-page'),
    path('administration/', include('administration.urls', namespace="administration")),
    path('roadmap/', include('roadmap.urls', namespace="roadmap")),
    path('login/', LoginView.as_view(
        redirect_authenticated_user=True,
        authentication_form=EmailAuthenticationForm  # <--- Add this line
    ), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', already_logged(SignupView.as_view()), name='signup'),
    path('activation/<uidb64>/<token>/', already_logged(ActivateAccount.as_view()), name='activate'),
    path('reset-password/', already_logged(PasswordResetView.as_view()), name='reset-password'),
    path('password-reset-done/', already_logged(PasswordResetDoneView.as_view()), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', already_logged(PasswordResetConfirmView.as_view()), name='password_reset_confirm'),
    path('password-reset-complete/', already_logged(PasswordResetCompleteView.as_view()), name='password_reset_complete'),
    path('logout/', LogoutView.as_view(), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
