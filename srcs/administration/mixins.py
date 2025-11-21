from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
# Make sure to import the Member model to handle the DoesNotExist exception if needed
# form authen.models import Member 

class OrganizerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        # 1. Check if user is logged in
        if not request.user.is_authenticated:
            return redirect("login") # Ensure this matches your login URL name

        # 2. Check if user is an organizer
        if not request.user.is_organizer:
            member_pk = request.user.member.pk
            return redirect("roadmap:career-roadmap", pk=member_pk)

        # 4. If User IS authenticated AND IS an organizer, allow access to the view
        return super().dispatch(request, *args, **kwargs)