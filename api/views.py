from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class APIRootView(APIView):
    """
    Root API endpoint providing information about available API versions and endpoints
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        Return information about available API versions
        """
        return Response(
            {
                "message": "NetEOC API",
                "version": "1.0",
                "available_versions": {
                    "v1": "/api/v1/",
                },
                "documentation": "/api-auth/",
                "endpoints": {
                    "v1": {
                        "user_profile": "/api/v1/user-profile/",
                    }
                },
            }
        )


class APIv1RootView(APIView):
    """
    API v1 root endpoint providing information about v1 endpoints
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        Return information about v1 API endpoints
        """
        return Response(
            {
                "version": "v1",
                "endpoints": {
                    "user_profile": {
                        "base_url": "/api/v1/user-profile/",
                        "endpoints": {
                            "user_roster": "/api/v1/user-profile/user/{user_id}/roster/",
                        },
                    }
                },
            }
        )
