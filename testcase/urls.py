from django.urls import path
from . import views
app_name = 'testcase'
urlpatterns = [
    path('set_testcases/', views.SetTestcases.as_view(), name='submit'),
]