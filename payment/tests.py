from django.test import TestCase
from django.urls import reverse


class PaymentServiceChoiceMarkupTests(TestCase):
    def test_checkout_services_has_client_class(self):
        r = self.client.get(reverse('payment:services_for_checkout'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'service-choices-client')
        self.assertContains(r, 'service_choices.css')
        self.assertNotContains(r, "addClass('fs-4 text-success')")
