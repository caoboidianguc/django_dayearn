

pip install "django-phonenumber-field[phonenumbers]"
<!-- https://django-phonenumber-field.readthedocs.io/en/latest/ -->


pip install -r requirements.txt
django-admin startproject


SPY_TEMPLATE_PACK = "bootstrap5"

PHONENUMBER_DB_FORMAT = 'NATIONAL'
PHONENUMBER_DEFAULT_REGION = 'US'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'hoadambutxinh@gmail.com'
EMAIL_HOST_PASSWORD = 'seztdjfrcdbcykvp'


Add to TEMPLATE_CONTEXT_PROCESSORS:
"django.template.context_processors.request"

<!-- for PostgreSQL specific model fields -->

<!-- Bad
<a href="/language/category/product/{{product.pk}}">Link</a>

<-- Good -->
<!-- <a href="{{product.get_absolute_url}}">Link</a> -->

<!-- https://django-taggit.readthedocs.io/en/latest/ -->

pip install bleach

start database: psql -U postgres
psql -U postgres -d dayearn_db
