import random
from django.core.mail import send_mail
from django.shortcuts import render, reverse, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from authen.models import *
from .forms import *
from .mixins import *
from django.db.models import Q
import random
from django.utils.text import slugify
import pandas as pd
from django.shortcuts import redirect
from django.contrib import messages
from django.views import View

class MemberImportView(OrganizerAndLoginRequiredMixin, View):
    template_name = "administration/member_import.html"

    def get(self, request):
        return render(request, self.template_name, {"form": MemberImportForm()})

    def post(self, request):
        form = MemberImportForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        # ---- READ FILE INTO A DATAFRAME ----
        uploaded_file = request.FILES["file"]

        # Detect file type
        filename = uploaded_file.name.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
        else:
            messages.error(request, "Invalid file type. Upload CSV or Excel.")
            return redirect("administration:member-import")
        # ------------------------------------

        created_count = 0

        for _, row in df.iterrows():
            email = row.get('email')
            username_val = str(row.get('personal_number', '')).strip()

            if not email or User.objects.filter(email=email).exists():
                continue
            if not username_val or User.objects.filter(username=username_val).exists():
                continue

            try:
                user = User.objects.create_user(
                    username=username_val,
                    email=email,
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', ''),
                    password=f"pass{random.randint(1000,9999)}",
                    is_organizer=False,
                )
            except Exception:
                continue

            Member.objects.create(
                user=user,
                organisation=request.user.account,
                target_role=row.get('target_role', ''),
            )

            send_mail(
                subject="Tracer: You are invited to be a member",
                message=(
                    "You were added as a member of a team. "
                    "Please reset your password with your email and login to start your work."
                ),
                from_email="noreply@mg.mytrac-api.xyz",
                recipient_list=[user.email],
            )

            created_count += 1

        messages.success(request, f"{created_count} members successfully imported.")
        return redirect("administration:member-list")


class MemberListView(OrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "administration/member_list.html"
    context_object_name = "members"

    def get_queryset(self):
        user = self.request.user
        user = User.objects.filter(member__organisation=user.account)
        return user


class MemberCreateView(OrganizerAndLoginRequiredMixin, generic.CreateView):
    template_name = "administration/member_create.html"
    form_class = MemberModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse("administration:member-list")

    def form_valid(self, form):
        # --- Create related User ---
        user = User(
            username=form.cleaned_data['username'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            email=form.cleaned_data['email'],
            is_organizer=False,
        )

        # Random password
        user.set_password(f"{random.randint(100000, 999999)}")
        user.save()

        # --- Create Member ---
        member = form.save(commit=False)
        member.user = user
        member.organisation = self.request.user.account
        member.save()

        # --- Send email ---
        send_mail(
            subject="Tracer: You are invited to be a member",
            message=(
                "You were added as a member of a team. "
                "Please reset your password with your email and login to start your work."
            ),
            from_email="noreply@mg.mytrac-api.xyz",
            recipient_list=[user.email],
        )

        return super().form_valid(form)

class MemberDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "administration/member_detail.html"
    context_object_name = "member"

    def get_queryset(self):
        user = self.request.user
        user = User.objects.filter(member__organisation=user.account)
        return user

class MemberUpdateView(OrganizerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "administration/member_update.html"
    form_class = MemberModelForm
    context_object_name = "member"

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({"request": self.request})
        return kwargs

    def get_context_data(self, **kwargs):
        user = User.objects.get(pk=self.kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["user"] = user
        return context

    def get_initial(self):

        initial = super().get_initial()
        user = User.objects.get(pk=self.kwargs["pk"])
        member = user.member

    # Load USER fields
        initial["username"] = user.username
        initial["email"] = user.email
        initial["target_role"] = member.target_role

        return initial

    def form_valid(self, form):
        # 1. Get the current User object based on the PK from the URL
        usr = User.objects.get(pk=self.kwargs["pk"])
        member = usr.member
        
        changed_member = False
        changed_user = False

        # --- STEP 2: Update User Fields (e.g., role, email, username) ---
        
        # NOTE: You need to know which fields on the User model are in MemberModelForm
        # Example fields commonly included in the MemberModelForm that belong to User:
        
        # 2a. Update User Role (if applicable and if 'role' is in the form)
        for field in ["username", "email"]:
            if field in form.cleaned_data:
                new_value = form.cleaned_data[field]
                if getattr(usr, field) != new_value:
                    setattr(usr, field, new_value)
                    changed_user = True

            
        # 2b. Update User Email (if applicable)
        new_value = form.cleaned_data.get("target_role")
        if new_value and getattr(member, "target_role") != new_value:
            setattr(member, "target_role", new_value)
            changed_member = True

        # --- STEP 4: Save the objects if anything changed ---
        
        if changed_user:
            usr.save()

        if changed_member:
            member.save()

        # Call the parent form_valid to handle redirects/messages. 
        # We ensure a valid HTTP response is returned.
        return super().form_valid(form)


    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(member__organisation=user.account)

    def get_success_url(self):
        return reverse("administration:member-list")

class MemberDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "administration/member_delete.html"
    context_object_name = "member"

    def get_success_url(self):
        return reverse("administration:member-list")

    def get_queryset(self):
        user = self.request.user
        user = User.objects.filter(member__organisation=user.account)
        return user

