from rest_framework import serializers
from .models import Order, OrderItem, Product
from phonenumber_field.phonenumber import to_python
from phonenumber_field.validators import validate_international_phonenumber
from django.core.exceptions import ValidationError

class OrderItemReadSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity']

class OrderItemWriteSerializer(serializers.Serializer):
    product = serializers.CharField()
    quantity = serializers.CharField()

    def validate_product(self, value):
        if value in [None, '']:
            raise serializers.ValidationError("ID продукта должен быть числом")
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("ID продукта должен быть числом")
        if not Product.objects.filter(id=int_value).exists():
            raise serializers.ValidationError("Такого продукта не существует")
        return int_value

    def validate_quantity(self, value):
        if value in [None, '']:
            raise serializers.ValidationError("Количество должно быть числом")
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Количество должно быть числом")
        if int_value < 1:
            raise serializers.ValidationError("Количество должно быть больше 0")
        return int_value

class OrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(required=True, allow_blank=False)
    lastname = serializers.CharField(required=True, allow_blank=True)
    phonenumber = serializers.CharField(required=True, allow_blank=False)
    address = serializers.CharField(required=True, allow_blank=False)
    products = OrderItemWriteSerializer(many=True, write_only=True)
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'items', 'products']

    def validate_firstname(self, value):
        if value is None or not isinstance(value, str) or not value.strip():
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    def validate_lastname(self, value):
        if value is None:
            raise serializers.ValidationError("Это поле не может быть пустым.")
        if not isinstance(value, str):
            raise serializers.ValidationError("Not a valid string.")
        return value

    def validate_phonenumber(self, value):
        if value is None or not isinstance(value, str) or not value.strip():
            raise serializers.ValidationError("Это поле не может быть пустым.")
        try:
            ph = to_python(value)
            validate_international_phonenumber(ph)
        except ValidationError:
            raise serializers.ValidationError("Введен некорректный номер телефона.")
        return value

    def validate_address(self, value):
        if value is None or not isinstance(value, str) or not value.strip():
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    def validate_products(self, value):
        if value is None:
            raise serializers.ValidationError("Это поле не может быть пустым.")
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Ожидался list со значениями, но был получен \"{}\".".format(type(value).__name__)
            )
        if not value:
            raise serializers.ValidationError("Этот список не может быть пустым.")
        return value

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        items = [
            OrderItem(
                order=order,
                product=Product.objects.get(pk=prod['product']),
                quantity=prod['quantity']
            ) for prod in products_data
        ]
        OrderItem.objects.bulk_create(items)
        return order
