from datetime import time as _time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ledger.models import Service, Technician


class StaffServiceChoiceMarkupTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='staff', password='pw12345!x')
        self.client.force_login(self.user)
        Technician.objects.create(
            name='Quang', phone='+14045551234', owner=self.user,
            start_work_at=_time(9, 30), end_work=_time(18, 30),
        )
        Service.objects.create(
            service='Regular Pedicure', price=30, owner=self.user,
            category=Service.Category.pedi,
        )

    def test_walkin_has_staff_class(self):
        r = self.client.get(reverse('ledger:walkin'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'service-choices-staff')
        self.assertContains(r, 'service_choices.css')
        self.assertNotContains(r, "addClass('fs-4 text-success')")
        self.assertNotContains(r, 'Selected services turn green')

    def test_all_employee_picker_has_staff_class(self):
        r = self.client.get(reverse('ledger:all_employee'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'service-choices-staff')
        self.assertContains(r, 'id="service-picker-list"')
        self.assertContains(r, 'service_choices.css')
