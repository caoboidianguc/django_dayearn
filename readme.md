<!-- cai dat virtualenv -->
pip install virtualenvwrapper-win
<!-- khoi dong virtualenv (dayearn-ten tu chon) -->
py -m venv dayearn
dayearn\Scripts\activate
pip install Django
should run python v12
python3 -m venv venv --prompt=dayearn

pip install "django-phonenumber-field[phonenumbers]"
<!-- https://django-phonenumber-field.readthedocs.io/en/latest/ -->

Mac source ./venv/bin/activate
Win venv\Scripts\activate
win dayearn\Scripts\activate

pip install -r requirements.txt
django-admin startproject



Add to INSTALLED_APPS:
'crispy_forms',
"crispy_bootstrap5",
'phonenumber_field',
'taggit',



CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

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