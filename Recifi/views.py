from django.http import HttpResponse
from rest_framework.views import APIView


class SuccessView(APIView):
    """
    API view to check the status of the services.

    Methods:
        get: Returns a simple HTTP response indicating the services are up and running.
    """

    def get(self, request):
        return HttpResponse(
            "HOWDY - looks like the services are up and running fine. \m/"
        )
