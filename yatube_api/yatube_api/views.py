from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "message": "Welcome to the Yatube API",
        "endpoints": {
            "api-token-auth": "/api/v1/api-token-auth/",
            "posts": "/api/v1/posts/",
            "groups": "/api/v1/groups/",
            "comments": "/api/v1/posts/{post_id}/comments/"
        }
    })