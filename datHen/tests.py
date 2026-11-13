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


from datetime import date, time, timedelta
from django.urls import reverse
from ledger.models import Khach, Service, KhachVisit
from datHen.forms import DatHenForm
from datHen.hours import schedule_time_bounds, WEEKDAY_OPEN, format_ampm


def _next_weekday(start=None):
    d = start or date.today()
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _next_saturday(start=None):
    d = start or date.today()
    while d.weekday() != 5:
        d += timedelta(days=1)
    return d


class ServiceChoiceMarkupTests(_TC):
    """Every service-selection page gets the scoped size class."""

    def setUp(self):
        self.user = _gum().objects.create_user(username='staff', password='pw12345!x')
        self.tech = _Tech.objects.create(
            name='Quang', phone='+14045551234', owner=self.user,
            start_work_at=_time(9, 30), end_work=_time(18, 30),
        )
        self.service = Service.objects.create(
            service='Regular Pedicure', price=30, owner=self.user,
            category=Service.Category.pedi,
        )
        self.client.force_login(self.user)

    def _session(self, **keys):
        session = self.client.session
        for k, v in keys.items():
            session[k] = v
        session.save()

    def test_new_client_service_choice_has_client_class(self):
        self._session(id=str(self.tech.pk), date=str(date.today()))
        r = self.client.get(_rev('datHen:service_choice'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'service-choices-client')
        self.assertContains(r, 'service_choices.css')
        self.assertNotContains(r, "addClass('fs-4 text-success')")

    def test_existing_client_service_choice_has_client_class(self):
        khach = Khach.objects.create(
            full_name='LINH', phone='+14045550000',
            technician=self.tech, day_comes=date.today(), time_at=_time(10, 0),
        )
        self._session(client_id=khach.pk, tech_id=self.tech.pk, date=str(date.today()))
        r = self.client.get(_rev('datHen:service_choice_exist'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'service-choices-client')
        self.assertContains(r, 'service_choices.css')

    def test_schedule_user_has_staff_class_and_time_limits(self):
        r = self.client.get(_rev('datHen:schedule_user'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'service-choices-staff')
        self.assertContains(r, 'service_choices.css')
        self.assertContains(r, 'min="09:30"')
        self.assertContains(r, 'max="19:30"')
        self.assertContains(r, 'updateScheduleTimeBounds')

    def test_visit_detail_has_staff_class(self):
        khach = Khach.objects.create(
            full_name='LINH', phone='+14045550000',
            technician=self.tech, day_comes=date.today(), time_at=_time(10, 0),
        )
        visit = KhachVisit.objects.create(
            client=khach, technician=self.tech,
            day_comes=date.today(), time_at=_time(10, 0),
        )
        visit.services.add(self.service)
        r = self.client.get(_rev('datHen:visit_detail', kwargs={'pk': visit.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'service-choices-staff')
        self.assertContains(r, 'service_choices.css')
        # Already-chosen services are checked on load so the CSS can turn them green.
        self.assertContains(r, f'value="{self.service.pk}"')
        self.assertRegex(r.content.decode(), r'checked[^>]*value="%s"|value="%s"[^>]*checked' % (self.service.pk, self.service.pk))


class ServiceChoiceCssTests(_TC):
    def test_css_turns_checked_items_green(self):
        from pathlib import Path
        from django.conf import settings
        css = (Path(settings.BASE_DIR) / 'ledger/static/css/service_choices.css').read_text()
        self.assertIn('#198754', css)
        self.assertIn('input:checked', css)
        self.assertIn('accent-color: #198754', css)
        self.assertIn('service-choices-client', css)
        self.assertIn('service-choices-staff', css)
        self.assertIn('1.5rem', css)
        self.assertIn('1.75rem', css)
        self.assertIn('margin-top: 3px', css)


class ScheduleTimeLimitTests(_TC):
    """Staff schedule times stay inside working hours plus 1 hour.

    10:00 AM is inside the window; 10:00 PM is not, so a 10pm/10am
    mix-up cannot be saved.
    """

    def setUp(self):
        self.user = _gum().objects.create_user(username='staff', password='pw12345!x')
        self.tech = _Tech.objects.create(
            name='Quang', phone='+14045551234', owner=self.user,
            start_work_at=_time(9, 30), end_work=_time(18, 30),
        )
        self.service = Service.objects.create(
            service='Regular Pedicure', price=30, owner=self.user,
            category=Service.Category.pedi,
        )

    def _data(self, day, at):
        return {
            'technician': self.tech.pk,
            'services': [self.service.pk],
            'full_name': 'Linh Test',
            'phone': '+14045550011',
            'day_comes': day.isoformat(),
            'time_at': at.strftime('%H:%M'),
            'status': Khach.Status.online,
        }

    def test_weekday_bounds_are_open_to_close_plus_one_hour(self):
        lo, hi = schedule_time_bounds(_next_weekday())
        self.assertEqual(lo, WEEKDAY_OPEN)
        self.assertEqual(lo, time(9, 30))
        self.assertEqual(hi, time(19, 30))  # 6:30 PM + 1 hour

    def test_saturday_bounds_close_plus_one_hour(self):
        lo, hi = schedule_time_bounds(_next_saturday())
        self.assertEqual(lo, time(9, 30))
        self.assertEqual(hi, time(19, 0))  # 6:00 PM + 1 hour

    def test_ten_am_is_accepted(self):
        form = DatHenForm(data=self._data(_next_weekday(), time(10, 0)))
        self.assertTrue(form.is_valid(), form.errors)

    def test_ten_pm_is_rejected(self):
        form = DatHenForm(data=self._data(_next_weekday(), time(22, 0)))
        self.assertFalse(form.is_valid())
        self.assertIn('time_at', form.errors)
        self.assertTrue(
            any('7:30 PM' in e or 'working hours' in e for e in form.errors['time_at'])
        )

    def test_weekday_edge_times(self):
        day = _next_weekday()
        self.assertTrue(DatHenForm(data=self._data(day, time(9, 30))).is_valid())
        self.assertTrue(DatHenForm(data=self._data(day, time(19, 30))).is_valid())
        self.assertFalse(DatHenForm(data=self._data(day, time(9, 29))).is_valid())
        self.assertFalse(DatHenForm(data=self._data(day, time(19, 31))).is_valid())

    def test_saturday_730pm_rejected_but_7pm_ok(self):
        day = _next_saturday()
        self.assertTrue(DatHenForm(data=self._data(day, time(10, 0))).is_valid())
        self.assertTrue(DatHenForm(data=self._data(day, time(19, 0))).is_valid())
        self.assertFalse(DatHenForm(data=self._data(day, time(19, 30))).is_valid())
        self.assertFalse(DatHenForm(data=self._data(day, time(22, 0))).is_valid())
