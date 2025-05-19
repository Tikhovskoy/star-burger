from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.utils import timezone

class Restaurant(models.Model):
    name = models.CharField('название', max_length=50)
    address = models.CharField('адрес', max_length=100, blank=True)
    contact_phone = models.CharField('контактный телефон', max_length=50, blank=True)

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name

class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)

class ProductCategory(models.Model):
    name = models.CharField('название', max_length=50)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField('название', max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField('картинка')
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField('описание', max_length=200, blank=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name

class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField('в продаже', default=True, db_index=True)

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"

class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(
                ExpressionWrapper(
                    F('items__price') * F('items__quantity'),
                    output_field=DecimalField()
                )
            )
        )

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Не обработан'),
        ('confirmed', 'Подтверждён'),
        ('assembled', 'Собран'),
        ('delivering', 'В доставке'),
        ('completed', 'Завершён'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Наличные курьеру'),
        ('card', 'Картой онлайн'),
    ]

    firstname = models.CharField('Имя', max_length=50)
    lastname = models.CharField('Фамилия', max_length=50, blank=True)
    phonenumber = PhoneNumberField('Телефон', db_index=True)
    address = models.CharField('Адрес', max_length=200)
    status = models.CharField(
        'Статус', max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField(
        'Время создания',
        auto_now_add=True,
        db_index=True
    )
    called_at = models.DateTimeField(
        'Время звонка менеджера',
        null=True,
        blank=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'Время доставки',
        null=True,
        blank=True,
        db_index=True
    )
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='cash',
        db_index=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ {self.firstname} {self.lastname} ({self.phonenumber})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='заказ', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='товар', related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField('количество', default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField('цена за единицу', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f"{self.product.name} x {self.quantity} по {self.price}"
