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


from datHen.views import assign_overlap_lanes, _annotate_visit_lanes, _tech_column_width_rem


class AssignOverlapLanesTests(_TC):
    """Pure lane packing: overlapping ranges sit side by side, not on top."""

    def test_empty(self):
        self.assertEqual(assign_overlap_lanes([]), [])

    def test_single_uses_full_width(self):
        self.assertEqual(assign_overlap_lanes([(10, 11)]), [(0, 1)])

    def test_same_start_and_end_get_separate_lanes(self):
        # Walk-ins checked in at the same time (identical 15-min visual blocks)
        result = assign_overlap_lanes([(10 * 60, 10 * 60 + 15)] * 3)
        lanes = sorted(lane for lane, count in result)
        self.assertEqual(lanes, [0, 1, 2])
        self.assertTrue(all(count == 3 for _lane, count in result))

    def test_partial_overlap_splits_two_ways(self):
        # 10:00-11:00 and 10:30-11:30
        result = assign_overlap_lanes([(10 * 60, 11 * 60), (10 * 60 + 30, 11 * 60 + 30)])
        self.assertEqual({lane for lane, _count in result}, {0, 1})
        self.assertTrue(all(count == 2 for _lane, count in result))

    def test_touching_endpoints_can_share_a_lane(self):
        # One ends at 11:00, the next starts at 11:00 — no overlap
        result = assign_overlap_lanes([(10 * 60, 11 * 60), (11 * 60, 12 * 60)])
        self.assertEqual(result, [(0, 1), (0, 1)])

    def test_non_overlapping_clusters_stay_independent(self):
        # Two morning walk-ins, then one afternoon appointment
        result = assign_overlap_lanes([
            (10 * 60, 10 * 60 + 15),
            (10 * 60, 10 * 60 + 15),
            (14 * 60, 15 * 60),
        ])
        self.assertEqual(result[0][1], 2)
        self.assertEqual(result[1][1], 2)
        self.assertNotEqual(result[0][0], result[1][0])
        self.assertEqual(result[2], (0, 1))

    def test_chain_reuses_a_free_lane(self):
        # A 10-12, B 10-11, C 11-12: C can sit in B's lane, so only 2 columns
        result = assign_overlap_lanes([
            (10 * 60, 12 * 60),
            (10 * 60, 11 * 60),
            (11 * 60, 12 * 60),
        ])
        self.assertTrue(all(count == 2 for _lane, count in result))
        self.assertEqual(result[1][0], result[2][0])
        self.assertNotEqual(result[0][0], result[1][0])

    def test_reversed_interval_is_normalized(self):
        result = assign_overlap_lanes([(11, 10), (10, 11)])
        self.assertEqual({lane for lane, count in result}, {0, 1})
        self.assertTrue(all(count == 2 for _lane, count in result))

    def test_column_widens_when_four_or_more_lanes(self):
        self.assertEqual(_tech_column_width_rem(1), 15)
        self.assertEqual(_tech_column_width_rem(3), 15)
        self.assertEqual(_tech_column_width_rem(4), 20)
        self.assertEqual(_tech_column_width_rem(5), 25)


class DatHenOverlapViewTests(_TC):
    """The schedule board renders overlapping cards with different left offsets."""

    def setUp(self):
        self.user = _gum().objects.create_user(username='staff', password='pw12345!x')
        self.tech = _Tech.objects.create(
            name='Quang', phone='+14045551234', owner=self.user,
            start_work_at=_time(9, 30), end_work=_time(18, 30),
        )
        self.hour_service = Service.objects.create(
            service='Gel Pedicure', price=45, owner=self.user,
            category=Service.Category.pedi,
            time_perform=timedelta(minutes=60),
        )
        self.day = date.today()
        self.client.force_login(self.user)

    def _client(self, name, phone, at, status=KhachVisit.Status.anyone):
        khach = Khach.objects.create(
            full_name=name, phone=phone,
            technician=self.tech, day_comes=self.day, time_at=at,
        )
        visit = KhachVisit.objects.create(
            client=khach, technician=self.tech,
            day_comes=self.day, time_at=at, status=status,
        )
        return visit

    def test_annotate_same_time_walkins_get_three_lanes(self):
        visits = [
            self._client('Mai', '+14045550101', time(10, 0)),
            self._client('Linh', '+14045550102', time(10, 0)),
            self._client('Hoa', '+14045550103', time(10, 0)),
        ]
        self.assertEqual(_annotate_visit_lanes(visits), 3)
        self.assertEqual(sorted(v.lane_index for v in visits), [0, 1, 2])
        self.assertTrue(all(v.lane_count == 3 for v in visits))
        lefts = sorted(v.left_pct for v in visits)
        expected = sorted((i / 3) * 100.0 for i in range(3))
        self.assertEqual(lefts, expected)
        self.assertTrue(all(abs(v.width_pct - (100.0 / 3)) < 1e-9 for v in visits))

    def test_board_shows_all_same_time_walkins_side_by_side(self):
        self._client('Mai', '+14045550101', time(10, 0))
        self._client('Linh', '+14045550102', time(10, 0))
        self._client('Hoa', '+14045550103', time(10, 0))
        r = self.client.get(_rev('datHen:listHen'), {'date': self.day.isoformat()})
        self.assertEqual(r.status_code, 200)
        for name in ('Mai', 'Linh', 'Hoa'):
            self.assertContains(r, name)
        html = r.content.decode()
        # Three walk-in cards share a cluster of 3 lanes
        self.assertEqual(html.count('data-lanes="3"'), 3)
        self.assertIn('data-lane="0"', html)
        self.assertIn('data-lane="1"', html)
        self.assertIn('data-lane="2"', html)
        self.assertIn('is-overlap', html)
        self.assertIn('left: calc(', html)
        self.assertIn('width: calc(', html)

    def test_board_splits_overlapping_scheduled_appointments(self):
        first = self._client('Trang', '+14045550201', time(11, 0), status=KhachVisit.Status.phone)
        first.services.add(self.hour_service)
        second = self._client('Ngoc', '+14045550202', time(11, 30), status=KhachVisit.Status.phone)
        second.services.add(self.hour_service)
        r = self.client.get(_rev('datHen:listHen'), {'date': self.day.isoformat()})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Trang')
        self.assertContains(r, 'Ngoc')
        html = r.content.decode()
        self.assertEqual(html.count('data-lanes="2"'), 2)
        self.assertIn('data-lane="0"', html)
        self.assertIn('data-lane="1"', html)
