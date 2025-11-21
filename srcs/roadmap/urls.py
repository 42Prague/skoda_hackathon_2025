from django.urls import path
from . import views
from .views import *

app_name = "roadmap"

urlpatterns = [
	path("member/<int:pk>/chat/", views.chat_ai, name="chat_ai"),
    path("<int:pk>/", views.member_dashboard, name="career-roadmap"),
	path("member/update/", MemberSelfUpdateView.as_view(), name="member-self-update"),
]