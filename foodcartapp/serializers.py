from rest_framework import serializers
from .models import Order, OrderItem, Product

class OrderItemSerializer(serializers.Serializer):
    product = serializers.CharField()
    quantity = serializers.CharField()

    def validate_product(self, value):
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("ID продукта должен быть числом")
        if not Product.objects.filter(id=int_value).exists():
            raise serializers.ValidationError("Такого продукта не существует")
        return int_value

    def validate_quantity(self, value):
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Количество должно быть числом")
        if int_value < 1:
            raise serializers.ValidationError("Количество должно быть больше 0")
        return int_value

class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']

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
