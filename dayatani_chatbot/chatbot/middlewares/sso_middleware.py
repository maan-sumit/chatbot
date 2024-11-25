import os
import requests
from django.contrib.auth import get_user_model
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import authenticate

User = get_user_model()

class SSOAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin'):
            sso_token = request.META.get('HTTP_AUTHORIZATION')
            
            if sso_token:
                try:
                    SSO_API_URL = os.getenv('SSO_API_URL')
                    response = requests.get(SSO_API_URL, headers={
                        'Accept-Language': 'en',
                        'Authorization': sso_token
                    })

                    if response.status_code == 200:
                        user_data = (response.json()).get('user')  # Assuming the API returns user data
                        #request.sso_user = user_data["user"]  # Attach the SSO user data to the request
                        sso_id = user_data['id']
                        mobile_number = user_data['phone']
                        user, created = User.objects.get_or_create(sso_uid=sso_id)
                        if created:
                            user.set_unusable_password()  # Set an unusable password for SSO users
                            user.mobile_number = mobile_number
                            user.save()
                        request.user = user  # Set the user in the request
                except requests.exceptions.RequestException:
                    print("some exception occured")
        response = self.get_response(request)
        return response            
            
        
