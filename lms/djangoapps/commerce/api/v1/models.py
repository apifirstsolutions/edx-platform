""" API v1 models. """


import logging
from itertools import groupby

from babel.numbers import get_currency_symbol

import six
from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from course_modes.models import CourseMode
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
        if 'jwt_token' in kwargs:
            self.jwt_token = kwargs['jwt_token']

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
                return ratings
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
            subcategory = SubCategory.objects.filter(name=subcategory)
            if subcategory:
                subcategory_id =  subcategory.first().id
                return str(subcategory_id)
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
    def discount_info(self):
        course_id = CourseKey.from_string(six.text_type(self.id))

        try:
            url = settings.LMS_ROOT_URL + '/api/discounts/course/' + str(course_id)
            headers={'Authorization': self.jwt_token}
            response = json.loads(requests.get(url=url,headers=headers).text)
            return response
            #return CourseEnrollment.objects.enrollment_counts(course_id)['total']
        except CourseEnrollment.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning(u'Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None 

    @property
    def discount_applicable(self):
        return self.discount_info['discount_applicable'] if self.discount_info else False

    @property
    def web_discount_applicable(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        configured_percentage = DiscountPercentageConfig.objects.filter(course=course_id).order_by('-id')
        if len(configured_percentage) and configured_percentage[0].percentage > 0:
            return True
        return False


    @property
    def web_discounted_price(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        configured_percentage = DiscountPercentageConfig.objects.filter(course=course_id).order_by('-id')
        course_mode_price = self.get_paid_mode_price()
        if len(configured_percentage) and configured_percentage[0].percentage > 0:
            #course_mode_price = self.get_paid_mode_price()
            if course_mode_price:
                return (course_mode_price - ( (configured_percentage[0].percentage/100) * course_mode_price))
            else:
                return 0.0

        return course_mode_price

    @property
    def web_discount_percentage(self):
        course_id = CourseKey.from_string(six.text_type(self.id))
        configured_percentage = DiscountPercentageConfig.objects.filter(course=course_id).order_by('-id')
        course_mode_price = self.get_paid_mode_price()
        if len(configured_percentage) and configured_percentage[0].percentage > 0:
            if course_mode_price:
                return configured_percentage[0].percentage 
            else:
                return 0.0

        return 0.0


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
        course_mode_price = self.get_paid_mode_price()
        if self.discount_info and self.discount_info['discount_applicable']:
            jwt_token = self.discount_info['jwt']
            decoded_jwt = jwt.decode(jwt_token, verify=False)
            discount_percentage = decoded_jwt['discount_percent']
            course_mode_price = self.get_paid_mode_price()
            if course_mode_price:
                return (discount_percentage/100) * course_mode_price
            else:
                return 0.0

        return course_mode_price


    @property
    def discount_percentage(self):
        course_mode_price = self.get_paid_mode_price()
        if self.discount_info and  self.discount_info['discount_applicable']:
            jwt_token = self.discount_info['jwt']
            decoded_jwt = jwt.decode(jwt_token, verify=False)
            discount_percentage = decoded_jwt['discount_percent']
            course_mode_price = self.get_paid_mode_price()
            if course_mode_price:
                return discount_percentage
            else:
                return 0.0
        return 0.0


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
    def iterator(cls,jwt_token=None,filters=None):
        """ Generator that yields all courses. """
        if filters==None:
            course_modes = CourseMode.objects.order_by('course_id')
        else:
            pass
            #course_modes = CourseMode.objects.order_by('ratings')
        JWT_TOKEN = jwt_token
        for course_id, modes in groupby(course_modes, lambda o: o.course_id):
            yield cls(course_id, list(modes),jwt_token=jwt_token)
