import datetime
from django.contrib.auth import logout
from app.models import UserStatus
from galtwo.models import UserStatus as StatusUser
from django.contrib.auth import get_user_model


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user = UserStatus.objects.get(user=request.user)
            user.last_active=datetime.datetime.now()
            user.save()
            use = StatusUser.objects.get(user=request.user)
            use.last_active=datetime.datetime.now()
            use.save()
                        
        response = self.get_response(request)
        return response
        