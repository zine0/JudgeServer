from django.urls import path
from . import views
app_name = 'judge'
urlpatterns = [
    path('judge_problem/',views.Judge.as_view(), name='judge_problem'),
]