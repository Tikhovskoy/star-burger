from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from django.core.validators import MinLengthValidator

from .models import Order, OrderItem, Product


class OrderItemReadSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "product_name", "quantity", "price"]


class OrderItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        error_messages={
            "required": "ID продукта обязательно.",
            "does_not_exist": "Такого продукта не существует.",
            "invalid": "ID продукта должен быть числом.",
        },
    )
    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "Количество обязательно.",
            "invalid": "Количество должно быть числом.",
            "min_value": "Количество должно быть больше 0.",
        },
    )


class OrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(allow_blank=False)
    lastname = serializers.CharField(allow_blank=False)
    phonenumber = PhoneNumberField(allow_blank=False)
    address = serializers.CharField(allow_blank=False)
    products = OrderItemWriteSerializer(
        many=True,
        write_only=True,
        validators=[
            MinLengthValidator(1, message="Список продуктов не может быть пустым.")
        ],
    )
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "firstname",
            "lastname",
            "phonenumber",
            "address",
            "items",
            "products",
        ]

    def create(self, validated_data):
        products_data = validated_data.pop("products")
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            items = [
                OrderItem(
                    order=order,
                    product=prod["product"],
                    quantity=prod["quantity"],
                    price=prod["product"].price,
                )
                for prod in products_data
            ]
            OrderItem.objects.bulk_create(items)
        return order
