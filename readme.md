

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
az group create --name dayearnGroup --location eastus
    {
  "id": "/subscriptions/d8947932-258a-479d-a0c4-f0ff6b537603/resourceGroups/dayearnGroup",
  "location": "eastus",
  "managedBy": null,
  "name": "dayearnGroup",
  "properties": {
    "provisioningState": "Succeeded"
  },
  "tags": null,
  "type": "Microsoft.Resources/resourceGroups"
    }
    <!-- https://x.com/i/grok/share/RSk9RJv7VJ2s2lVMkTB7NqVy9 -->

az appservice plan create --name dayearnPlan --resource-group dayearnGroup --sku B1 --is-linux
az webapp create --resource-group dayearnGroup --plan dayearnPlan --name quang-dayearn --runtime "PYTHON|3.11"
https://quang-dayearn.azurewebsites.net.

django_dayearn % az webapp deployment user set --user-name jubi --password Dayearn.7818  
https://jubi@quang-dayearn.scm.azurewebsites.net/quang-dayearn.git