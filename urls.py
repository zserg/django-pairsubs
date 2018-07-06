from django.urls import path

from . import views

app_name = 'pairsubs'
urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.opensubtitles_search, name='opensubtitles_search'),
    #path('download/', views.opensubtitles_download, name='opensubtitles_download'),
    path('pairinfo/<int:id>/', views.subpair_info, name='subpair_info'),
    path('pairshow/<int:id>/', views.subpair_show, name='subpair_show'),

]

