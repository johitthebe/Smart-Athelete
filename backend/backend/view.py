from django.http import HttpResponse

def home(request):
    return HttpResponse("Smart Athlete backend is running")
