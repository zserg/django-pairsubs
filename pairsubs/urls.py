from django.urls import path

from . import views

app_name = 'pairsubs'
urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.SubPairListView.as_view(), name='subpair-list'),
    path('search/', views.opensubtitles_search, name='opensubtitles_search'),
    path('pairinfo/<int:id>/', views.subpair_info, name='subpair_info'),
    path('pairshow/', views.subpair_show, name='subpair_show_random'),
    path('pairshow/<int:id>/', views.subpair_show, name='subpair_show'),

]

