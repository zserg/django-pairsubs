from django.urls import path

from . import views

app_name = 'pairsubs'
urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.SubPairListView.as_view(), name='subpair-list'),
    path('search/', views.opensubtitles_search, name='opensubtitles_search'),
    path('status/', views.status, name='status'),
    path('status/check/', views.check_task, name='check-task'),
    path('pairinfo/<int:id>/', views.subpair_info, name='subpair_info'),
    path('pairshow/', views.subpair_show, name='subpair_show'),
    path('pairshow/get_data/', views.get_subtitles_data, name='get_subtitles_data'),

]

