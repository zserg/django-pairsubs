from django.urls import path

from . import views

app_name = 'pairsubs'
urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.opensubtitles_search, name='opensubtitles_search'),
    path('result/', views.opensubtitles_search, name='search_result'),
    path('download/', views.opensubtitles_download, name='opensubtitles_download'),
    path('subpairs/<int:id>/', views.subpair_info, name='subpair_info'),

]

