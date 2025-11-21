from django.shortcuts import render
from django.views import generic, View
from .models import *
from .forms import *
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, reverse, render, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, Http404
from django.shortcuts import redirect

from django.contrib.auth import login
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('administration:member-list')
        return super(LandingPageView, self).dispatch(request, *args, **kwargs)

class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        username = form.cleaned_data['username']
        user = User.objects.get(username=username)
        current_site = get_current_site(self.request)
        subject = 'Activate your Tracer account'
        message = render_to_string('registration/email_activation.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        user.email_user(subject, message)

        messages.info(self.request, ('Please confirm your email to complete registration.'))

        return super(SignupView, self).form_valid(form)

    def get_success_url(self):
        return reverse("login")

class ActivateAccount(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.email_confirmed = True
            user.save()
            login(request, user, backend='authen.backends.EmailBackend')
            return redirect('administration:member-list')
        else:
            messages.warning(request, ('The confirmation link was invalid, possibly because it has already been used.'))
            return redirect('login')