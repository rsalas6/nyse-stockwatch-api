from django.urls import path

from . import views

urlpatterns = [
    path("", views.company_list_create, name="company-list-create"),
    path("<uuid:pk>/", views.company_detail, name="company-detail"),
    path(
        "external/<str:symbol>/",
        views.get_company_info,
        name="company-info",
    ),
    path(
        "validate-token/",
        views.validate_token,
        name="validate-token",
    ),
]
