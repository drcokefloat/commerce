from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listing/<int:listing_id>/", views.listing, name="listing"),
    path("create/", views.create_listing, name="create_listing"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("listing/<int:listing_id>/add_watchlist/", views.add_watchlist, name="add_watchlist"),
    path("listing/<int:listing_id>/remove_watchlist/", views.remove_watchlist, name="remove_watchlist"),
    path("categories/", views.categories, name="categories"),
    path("categories/<int:category_id>/", views.category_listings, name="category_listings"),
]
