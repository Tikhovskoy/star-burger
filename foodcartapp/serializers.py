from rest_framework import serializers
from .models import Order, OrderItem, Product
from phonenumber_field.phonenumber import to_python
from phonenumber_field.validators import validate_international_phonenumber
from django.core.exceptions import ValidationError
from django.db import transaction

class OrderItemReadSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price']

class OrderItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        error_messages={
            'required': 'ID продукта обязательно.',
            'does_not_exist': 'Такого продукта не существует.',
            'invalid': 'ID продукта должен быть числом.',
        }
    )
    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={
            'required': 'Количество обязательно.',
            'invalid': 'Количество должно быть числом.',
            'min_value': 'Количество должно быть больше 0.',
        }
    )

class OrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(required=True, allow_blank=False)
    lastname  = serializers.CharField(required=True, allow_blank=True)
    phonenumber = serializers.CharField(required=True, allow_blank=False)
    address   = serializers.CharField(required=True, allow_blank=False)
    products  = OrderItemWriteSerializer(many=True, write_only=True)
    items     = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'items', 'products']

    def validate_firstname(self, value):
        if not value.strip():
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    def validate_lastname(self, value):
        if value is None:
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    def validate_phonenumber(self, value):
        if not value.strip():
            raise serializers.ValidationError("Это поле не может быть пустым.")
        try:
            ph = to_python(value)
            validate_international_phonenumber(ph)
        except ValidationError:
            raise serializers.ValidationError("Введен некорректный номер телефона.")
        return value

    def validate_address(self, value):
        if not value.strip():
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    def validate_products(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                'Ожидался список, но получено "{}".'.format(type(value).__name__)
            )
        if not value:
            raise serializers.ValidationError("Этот список не может быть пустым.")
        return value

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            items = [
                OrderItem(
                    order=order,
                    product=prod['product'],
                    quantity=prod['quantity'],
                    price=prod['product'].price
                )
                for prod in products_data
            ]
            OrderItem.objects.bulk_create(items)
        return order
