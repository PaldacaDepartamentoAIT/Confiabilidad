from django.http import HttpRequest, HttpResponse
from django.urls import path
from django.views.decorators.http import require_POST

from apps.accounts.models import User


@require_POST
def rename_user(request: HttpRequest, pk: int) -> HttpResponse:
    user = User.objects.get(pk=pk)
    user.name = request.POST["name"]
    user.save()
    return HttpResponse(status=204)


urlpatterns = [path("rename/<int:pk>/", rename_user)]
