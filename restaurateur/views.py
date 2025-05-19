from collections import defaultdict
import requests
from geopy.distance import distance
from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.db.models import Prefetch
from django.conf import settings

from foodcartapp.models import Product, Restaurant, Order, OrderItem, RestaurantMenuItem

YANDEX_GEOCODER_API_KEY = getattr(settings, "YANDEX_GEOCODER_API_KEY", None)
YANDEX_GEOCODER_URL = 'https://geocode-maps.yandex.ru/1.x/'

def fetch_coordinates(api_key, address):
    """Вернуть координаты (lat, lon) или None, если не удалось"""
    params = {
        'apikey': api_key,
        'geocode': address,
        'format': 'json'
    }
    try:
        response = requests.get(YANDEX_GEOCODER_URL, params=params, timeout=2)
        response.raise_for_status()
        places = response.json()['response']['GeoObjectCollection']['featureMember']
        if not places:
            return None
        lon, lat = map(float, places[0]['GeoObject']['Point']['pos'].split())
        return lat, lon
    except Exception:
        return None

def get_distance_km(from_coords, to_coords):
    if from_coords is None or to_coords is None:
        return None
    try:
        return distance(from_coords, to_coords).km
    except Exception:
        return None


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = (
        Order.objects.with_total_price()
        .exclude(status='completed')
        .prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        )
        .order_by('-id')
    )

    menu_items = RestaurantMenuItem.objects.filter(availability=True).select_related('restaurant', 'product')
    product_to_restaurants = defaultdict(set)
    for item in menu_items:
        product_to_restaurants[item.product_id].add(item.restaurant)

    address_coords_cache = {}

    orders_with_available_restaurants = []
    for order in orders:
        order_product_ids = [item.product_id for item in order.items.all()]
        restaurant_sets = [product_to_restaurants.get(pid, set()) for pid in order_product_ids]
        if restaurant_sets:
            available_restaurants = set.intersection(*restaurant_sets)
        else:
            available_restaurants = set()

        delivery_address = order.address
        if delivery_address in address_coords_cache:
            order_coords = address_coords_cache[delivery_address]
        else:
            order_coords = fetch_coordinates(YANDEX_GEOCODER_API_KEY, delivery_address)
            address_coords_cache[delivery_address] = order_coords

        restaurant_distances = []
        for restaurant in available_restaurants:
            rest_address = restaurant.address
            if rest_address in address_coords_cache:
                rest_coords = address_coords_cache[rest_address]
            else:
                rest_coords = fetch_coordinates(YANDEX_GEOCODER_API_KEY, rest_address)
                address_coords_cache[rest_address] = rest_coords

            dist = get_distance_km(order_coords, rest_coords)
            restaurant_distances.append((restaurant, dist))

        sorted_restaurants = sorted(
            restaurant_distances,
            key=lambda r: r[1] if r[1] is not None else 1e9
        )

        orders_with_available_restaurants.append(
            {
                'order': order,
                'restaurants': sorted_restaurants,
            }
        )

    return render(request, template_name='order_items.html', context={
        'orders_with_available_restaurants': orders_with_available_restaurants,
    })
