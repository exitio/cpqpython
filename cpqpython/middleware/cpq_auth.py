from django.conf import settings
from django.contrib.auth import authenticate, login, logout

from cpqpython import Client

from account.models import User


class CPQAuthMiddleware(object):
    """
    Middleware which inspects the request for a auth header and will login a
    user if they're not already logged in.
    """
    def process_request(self, request):
        current_user = request.user

        user = None

        jsessionid = request.GET.get('sId', None)
        if jsessionid:
            request.session['jsessionid'] = jsessionid
        email = request.GET.get('un', None)

        if not any([jsessionid, email]):
            return

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return
        if user.is_active:
            if not user == current_user:
                logout(request)
            cpq_url = request.session.get(
                'cpq_url', settings.CPQ_SERVER_NAME
            )
            client = Client(
                server_name=cpq_url,
                debug=settings.DEBUG,
                session_id=jsessionid
            )
            resp = client.query('SELECT Id FROM Opportunity', batchsize=1)
            if resp.status_code == 200:
                auth_user = authenticate(
                    username=user.email, password=user.api_key.key
                )
                login(request, auth_user)
