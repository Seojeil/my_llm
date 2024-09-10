from stock import views
from django.urls import path

app_name = 'stock'
urlpatterns = [
    path('article/', views.article, name='article'),
]