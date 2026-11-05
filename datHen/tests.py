from django.test import TestCase

# Create your tests here.


from datetime import time as _time
from django.contrib.auth import get_user_model as _gum
from django.test import TestCase as _TC
from django.urls import reverse as _rev
from ledger.models import Technician as _Tech


class ScheduleDefaultTechTests(_TC):
    def setUp(self):
        self.user = _gum().objects.create_user(username='staff', password='pw12345!x')
        self.client.force_login(self.user)

    def _tech(self, name):
        return _Tech.objects.create(name=name, phone='+14045551234', owner=self.user,
                                    start_work_at=_time(9), end_work=_time(19))

    def test_quang_is_default_tech(self):
        self._tech('Anna')
        quang = self._tech('Quang')
        r = self.client.get(_rev('datHen:schedule_user'))
        self.assertEqual(r.context['form'].initial.get('technician'), quang)
        self.assertContains(r, f'<option value="{quang.pk}" selected>Quang</option>', html=True)

    def test_no_quang_means_no_default(self):
        self._tech('Anna')
        r = self.client.get(_rev('datHen:schedule_user'))
        self.assertIsNone(r.context['form'].initial.get('technician'))
        self.assertNotContains(r, 'selected>Anna')

    def test_setting_none_restores_no_default(self):
        self._tech('Quang')
        from datHen.views import ScheduleViewUser
        from unittest import mock
        with mock.patch.object(ScheduleViewUser, 'DEFAULT_TECH_NAME', None):
            r = self.client.get(_rev('datHen:schedule_user'))
        self.assertIsNone(r.context['form'].initial.get('technician'))
