from django.urls import path, re_path
from . import views
from django.contrib.auth.decorators import login_required
from Users.views import profile as user_profile_update
urlpatterns = [
    path('', views.home, name="home"),
    path('user/<str:username>/portfolio', login_required(views.UserPositionListView.as_view()), name='user-positions'),
    path('user/profile', user_profile_update, name='user-profile'),
    path('user/<str:username>/delete_position/<int:pk>/', login_required(views.UserPositionDelete.as_view()), name='delete-position'),
    path('quotes/', views.search_stocks, name="search_stocks"),
    path('quotes/<str:ticker>/', views.searched_stock, name="searched_stock"),
    path('quotes/<str:ticker>/(?P<price>\d+\.\d{2})/$/add_position', views.new_equity_position, name="create_position"),
]
