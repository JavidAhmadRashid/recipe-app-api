from django.contrib import admin
from django.urls import path, include # Import include to include other URL configurations

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    # other paths...
]
