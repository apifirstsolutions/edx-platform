""" API v1 models. """


import logging
from itertools import groupby

from babel.numbers import get_currency_symbol

import six
from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.verify_student.models import VerificationDeadline
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, SubCategory, CourseOverviewImageSet
from student.models import CourseEnrollment
from django.db.models import Avg
from openedx.features.discounts.models import DiscountPercentageConfig, DiscountRestrictionConfig
from django.conf import settings

log = logging.getLogger(__name__)

UNDEFINED = object()
import requests
import json
import jwt
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from django.contrib.auth import get_user_model
User = get_user_model()

from lms.djangoapps.lhub_ecommerce_offer.models import Offer, Coupon
from decimal import Decimal as D
from datetime import datetime
import pytz

utc = pytz.UTC


class Course(object):
    """ Pseudo-course model used to group CourseMode objects. """
    id = None  # pylint: disable=invalid-name
    modes = None
    _deleted_modes = None
    jwt_token = None
    def __init__(self, id, modes, **kwargs):  # pylint: disable=redefined-builtin
        self.id = CourseKey.from_string(six.text_type(id))  # pylint: disable=invalid-name
        self.modes = list(modes)
        self.verification_deadline = UNDEFINED
        if 'verification_deadline' in kwargs:
            self.verification_deadline = kwargs['verification_deadline']
        self._deleted_modes = []


    @property
    def name(self):
        """ Return course name. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseOverview.get_from_id(course_id).display_name
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def difficulty_level(self):
        """ Return course Difficulty Level. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseOverview.get_from_id(course_id).difficulty_level
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def created(self):
        """ Return course Date Created. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseOverview.get_from_id(course_id).created
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def ratings(self):
        """ Return course rating. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            ratings = CourseOverview.get_from_id(course_id).course_reviews.aggregate(Avg('rating'))['rating__avg']
            if ratings:
                return round(ratings,1)
            else:
                return 0.0
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return 0.0



    @property
    def subcategory_id(self):
        """ Return course rating. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            subcategory = CourseOverview.get_from_id(course_id).subcategory
            if subcategory:
                subcategory_id =  subcategory.id
                return str(subcategory_id)
            else:
                return str(0)
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return 0.0


    @property
    def category(self):
        """ Return course category ID. """
        course_id = CourseKey.from_string(six.text_type(self.id))
        try:
            category = CourseOverview.get_from_id(course_id).new_category
            if category:
                category_id =  category.id
                return str(category_id)
            else:
                return str(0)
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return 0.0


    @property
    def comments_count(self):
        """ Return course Difficulty Level. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseOverview.get_from_id(course_id).course_reviews.all().count()
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def enrollments_count(self):
        """ Return course Difficulty Level. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseEnrollment.objects.enrollment_counts(course_id)['total']
        except CourseEnrollment.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None


    @property
    def coupon_applicable(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        current_datetime = str(utc.localize(datetime.now()))
        current_datetime = utc.localize(datetime.strptime(current_datetime[:19], '%Y-%m-%d %H:%M:%S'))
        if len(self.modes) > 0:
            if Coupon.objects.filter(course__pk=course_id).exists():
                coupon = Coupon.objects.filter(course__pk=course_id).first()
                start_date = coupon.start_datetime
                end_date = coupon.end_datetime
                if current_datetime >= start_date and current_datetime < end_date:
                    return True
                else:
                    return False
        return False


    @property
    def discount_applicable(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        current_datetime = str(utc.localize(datetime.now()))
        current_datetime = utc.localize(datetime.strptime(current_datetime[:19], '%Y-%m-%d %H:%M:%S'))
        if len(self.modes) > 0:
            if Offer.objects.filter(course__pk=course_id).exists():
                offer = Offer.objects.filter(course__pk=course_id).order_by('-priority', 'id').first()
                start_date = offer.start_datetime
                end_date = offer.end_datetime
                if end_date:
                    if offer.is_suspended == False and current_datetime >= start_date and current_datetime < end_date:
                        return True
                    else:
                        return False
                else:
                    if offer.is_suspended == False and current_datetime >= start_date:
                        return True
                    else:
                        return False
        return False

    @property
    def discount_type(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        if len(self.modes) > 0:
            if Offer.objects.filter(course__pk=course_id).exists():
                offer = Offer.objects.filter(course__pk=course_id).order_by('-priority', 'id').first()
                if offer.incentive_type == 'Percentage':
                    return "Percentage"
                else:
                    return "Value"


    @property
    def currency(self):
        try:
            currency = self.modes[0].currency.upper()
            symbol = get_currency_symbol(currency)
            return symbol
        except:
            return "S$"

    @property
    def discounted_price(self):
        if len(self.modes) > 0:
            price = float(self.modes[0].min_price)
            course_id = CourseKey.from_string(six.text_type(self.id))
            current_datetime = str(utc.localize(datetime.now()))
            current_datetime = utc.localize(datetime.strptime(current_datetime[:19], '%Y-%m-%d %H:%M:%S'))
            
            if Offer.objects.filter(course__pk=course_id).exists():
                offer = Offer.objects.filter(course__pk=course_id).order_by('-priority', 'id').first()
                start_date = offer.start_datetime
                end_date = offer.end_datetime
                if end_date:
                    if offer.is_suspended == False and current_datetime >= start_date and current_datetime < end_date:
                        incentive_type = offer.incentive_type
                        incentive_value = float(offer.incentive_value)
                        
                        if incentive_type == 'Percentage':
                            discounted_price = price - (price * (incentive_value/100))
                        elif incentive_type == 'Absolute':
                            discounted_price = price - incentive_value

                        return "%.2f" % discounted_price
                    else:
                        return "%.2f" % price
                else:
                    if offer.is_suspended == False and current_datetime >= start_date:
                        incentive_type = offer.incentive_type
                        incentive_value = float(offer.incentive_value)
                        
                        if incentive_type == 'Percentage':
                            discounted_price = price - (price * (incentive_value/100))
                        elif incentive_type == 'Absolute':
                            discounted_price = price - incentive_value

                        return "%.2f" % discounted_price
                    else:
                        return "%.2f" % price 


        course_mode_price = self.get_paid_mode_price()
        return course_mode_price

    @property
    def discounted_price_string(self):
        if len(self.modes) > 0:
            price = float(self.modes[0].min_price)
            course_id = CourseKey.from_string(six.text_type(self.id))
            current_datetime = str(utc.localize(datetime.now()))
            current_datetime = utc.localize(datetime.strptime(current_datetime[:19], '%Y-%m-%d %H:%M:%S'))
            
            if Offer.objects.filter(course__pk=course_id).exists():
                offer = Offer.objects.filter(course__pk=course_id).order_by('-priority', 'id').first()
                start_date = offer.start_datetime
                end_date = offer.end_datetime
                if end_date:
                    if offer.is_suspended == False and current_datetime >= start_date and current_datetime < end_date:
                        incentive_type = offer.incentive_type
                        incentive_value = float(offer.incentive_value)
                        
                        if incentive_type == 'Percentage':
                            discounted_price = price - (price * (incentive_value/100))
                        elif incentive_type == 'Absolute':
                            discounted_price = price - incentive_value

                        return "%.2f" % discounted_price
                    else:
                        return "%.2f" % price
                else:
                    if offer.is_suspended == False and current_datetime >= start_date:
                        incentive_type = offer.incentive_type
                        incentive_value = float(offer.incentive_value)
                        
                        if incentive_type == 'Percentage':
                            discounted_price = price - (price * (incentive_value/100))
                        elif incentive_type == 'Absolute':
                            discounted_price = price - incentive_value

                        return "%.2f" % discounted_price
                    else:
                        return "%.2f" % price 


        course_mode_price = self.get_paid_mode_price()
        return course_mode_price

    @property
    def discount_percentage(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        if len(self.modes) > 0:
            if Offer.objects.filter(course__pk=course_id).exists():
                offer = Offer.objects.filter(course__pk=course_id).order_by('-priority', 'id').first()
                return offer.incentive_value
        return 0.0

    @property
    def discount_percentage_string(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        if len(self.modes) > 0:
            if Offer.objects.filter(course__pk=course_id).exists():
                offer = Offer.objects.filter(course__pk=course_id).order_by('-priority', 'id').first()
                return str("%.2f" % offer.incentive_value)
        return "%.2f" % 0.0


    @property
    def coupon_available(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        if len(self.modes) > 0:
            if Coupon.objects.filter(course__pk=course_id).exists():
                coupon = Coupon.objects.filter(course__pk=course_id).first()
                if coupon:
                    return True
                else:
                    return False
    


    @property
    def coupon_type(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        if len(self.modes) > 0:
            if Coupon.objects.filter(course__pk=course_id).exists():
                coupon = Coupon.objects.filter(course__pk=course_id).first()
                if coupon.incentive_type == 'Percentage':
                    return 'Percentage'
                else:
                    return 'Value'


    @property
    def available_vouchers(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        vouchers = []
        current_datetime = str(utc.localize(datetime.now()))
        current_datetime = utc.localize(datetime.strptime(current_datetime[:19], '%Y-%m-%d %H:%M:%S'))
        if len(self.modes) > 0:
            if Coupon.objects.filter(course__pk=course_id).exists():
                vouchers_data = Coupon.objects.filter(course__pk=course_id).values('name', 'coupon_code', 'incentive_type', 'incentive_value', 'is_exclusive')
                coupons = Coupon.objects.filter(course__pk=course_id)
                for index, coupon in enumerate(coupons):
                    start_date = coupon.start_datetime
                    end_date = coupon.end_datetime

                    if current_datetime >= start_date and current_datetime < end_date:
                            vouchers.append(vouchers_data[index])
                return vouchers
            else:
                return []




    @property
    def sale_type(self):
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            if CourseOverview.get_from_id(course_id).course_sale_type:
                return CourseOverview.get_from_id(course_id).course_sale_type.lower()
            return CourseOverview.get_from_id(course_id).course_sale_type
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None


    @property
    def is_premium(self):
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseOverview.get_from_id(course_id).premium
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None


    @property
    def platform_visibility(self):
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            if CourseOverview.get_from_id(course_id).platform_visibility:
                return CourseOverview.get_from_id(course_id).platform_visibility.lower()
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def image_urls(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        try:
            if CourseOverview.get_from_id(course_id).image_urls:
                return CourseOverview.get_from_id(course_id).image_urls
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def allow_review(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        try:
            return CourseOverview.get_from_id(course_id).allow_review
        except CourseOverview.DoesNotExist:
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    def get_paid_mode_price(self):
        for mode in self.modes:
            if mode.mode_slug != 'honor':
                return mode.min_price
            else:
                continue
        return None


    def get_mode_display_name(self, mode):
        """ Returns display name for the given mode. """
        slug = mode.mode_slug.strip().lower()

        if slug == 'credit':
            return 'Credit'
        if 'professional' in slug:
            return 'Professional Education'
        elif slug == 'verified':
            return 'Verified Certificate'
        elif slug == 'honor':
            return 'Honor Certificate'
        elif slug == 'audit':
            return 'Audit'

        return mode.mode_slug

    @transaction.atomic
    def save(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ Save the CourseMode objects to the database. """

        if self.verification_deadline is not UNDEFINED:
            # Override the verification deadline for the course (not the individual modes)
            # This will delete verification deadlines for the course if self.verification_deadline is null
            VerificationDeadline.set_deadline(self.id, self.verification_deadline, is_explicit=True)

        for mode in self.modes:
            mode.course_id = self.id
            mode.mode_display_name = self.get_mode_display_name(mode)
            mode.save()

        deleted_mode_ids = [mode.id for mode in self._deleted_modes]
        CourseMode.objects.filter(id__in=deleted_mode_ids).delete()
        self._deleted_modes = []

    def update(self, attrs):
        """ Update the model with external data (usually passed via API call). """
        # There are possible downstream effects of settings self.verification_deadline to null,
        # so don't assign it a value here unless it is specifically included in attrs.
        if 'verification_deadline' in attrs:
            self.verification_deadline = attrs.get('verification_deadline')

        existing_modes = {mode.mode_slug: mode for mode in self.modes}
        merged_modes = set()
        merged_mode_keys = set()

        for posted_mode in attrs.get('modes', []):
            merged_mode = existing_modes.get(posted_mode.mode_slug, CourseMode())

            merged_mode.course_id = self.id
            merged_mode.mode_slug = posted_mode.mode_slug
            merged_mode.mode_display_name = posted_mode.mode_slug
            merged_mode.min_price = posted_mode.min_price
            merged_mode.currency = posted_mode.currency
            merged_mode.sku = posted_mode.sku
            merged_mode.bulk_sku = posted_mode.bulk_sku
            merged_mode.expiration_datetime = posted_mode.expiration_datetime
            merged_mode.save()

            merged_modes.add(merged_mode)
            merged_mode_keys.add(merged_mode.mode_slug)

        # Masters degrees are not sold through the eCommerce site.
        # So, Masters course modes are not included in PUT calls to this API,
        # and their omission which would normally cause them to be deleted.
        # We don't want that to happen, but for the time being,
        # we cannot include in Masters modes in the PUT calls from eCommerce.
        # So, here's hack to handle Masters course modes, along with any other
        # modes that end up in that boat.
        MODES_TO_NOT_DELETE = {
            CourseMode.MASTERS,
        }

        modes_to_delete = set(existing_modes.keys()) - merged_mode_keys
        modes_to_delete -= MODES_TO_NOT_DELETE
        self._deleted_modes = [existing_modes[mode] for mode in modes_to_delete]
        self.modes = list(merged_modes)

    @classmethod
    def get(cls, course_id):

        """ Retrieve a single course. """
        try:
            course_id = CourseKey.from_string(six.text_type(course_id))
        except InvalidKeyError:
            log.debug(u'[%s] is not a valid course key.', course_id)
            raise ValueError

        course_modes = CourseMode.objects.filter(course_id=course_id)

        if course_modes:
            verification_deadline = VerificationDeadline.deadline_for_course(course_id)
            return cls(course_id, list(course_modes), verification_deadline=verification_deadline)

        return None

    @classmethod
    def iterator(cls,filters=None):
        """ Generator that yields all courses. """
        if filters==None:
            course_modes = CourseMode.objects.order_by('course_id')
        else:
            pass
            #course_modes = CourseMode.objects.order_by('ratings')
        for course_id, modes in groupby(course_modes, lambda o: o.course_id):
            yield cls(course_id, list(modes))



class WebCourse(Course):

    @property
    def start_date(self):
        """ Return course Date Created. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            courseoverview = CourseOverview.get_from_id(course_id)
            if courseoverview.advertised_start:
                start_date = courseoverview.advertised_start.strftime("%b") + " " + str(courseoverview.advertised_start.day) +", " + str(courseoverview.advertised_start.year)
            else:
                start_date = courseoverview.start.strftime("%b") + " " + str(courseoverview.start.day) + ", " + str(courseoverview.start.year)
            return start_date


        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def organization(self):
        """ Return course Date Created. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseOverview.get_from_id(course_id).display_org_with_default
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def course_number(self):
        """ Return course Date Created. """
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            return CourseOverview.get_from_id(course_id).display_number_with_default
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

