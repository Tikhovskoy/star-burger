from django.urls import path

from .views import OrderView, banners_list_api, product_list_api
from .views import trigger_error 

app_name = "foodcartapp"

urlpatterns = [
    path("products/", product_list_api),
    path("banners/", banners_list_api),
    path("order/", OrderView.as_view()),
    path('test-rollbar/', trigger_error),
]
