from django.http import JsonResponse
# for ping on uptime robot so my free tier service doesnt sleep!


def health(request):
    return JsonResponse({"status": "ok"})
