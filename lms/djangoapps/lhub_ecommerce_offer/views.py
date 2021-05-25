from logging import info
import logging
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Offer, Coupon
from datetime import datetime
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Ecommerce_Offer(APIView):

    def post(self, request):
        ecommerce_data = request.data

        # If Offer already exists
        # Update it
        if Offer.objects.filter(associated_ecommerce_offer_id = ecommerce_data['associated_ecommerce_offer_id']).exists():
            ecommerce_offer = Offer.objects.filter(associated_ecommerce_offer_id = ecommerce_data['associated_ecommerce_offer_id'])
            start_datetime_str = ecommerce_data['start_datetime']
            start_datetime = datetime.strptime(start_datetime_str[:19], '%Y-%m-%d %H:%M:%S')

            if ecommerce_data['end_datetime'] != "None":
                end_datetime_str = ecommerce_data['end_datetime']
                end_datetime = datetime.strptime(end_datetime_str[:19], '%Y-%m-%d %H:%M:%S')
            else:
                end_datetime = None

            ecommerce_offer.update(
                associated_ecommerce_offer_id = ecommerce_data['associated_ecommerce_offer_id'],
                start_datetime = start_datetime,
                end_datetime = end_datetime,
                priority = ecommerce_data['priority'],
                incentive_type = ecommerce_data['incentive_type'],
                incentive_value = ecommerce_data['incentive_value'],
                condition_type = ecommerce_data['condition_type'],
                condition_value = ecommerce_data['condition_value'],
                is_exclusive = ecommerce_data['is_exclusive'],
                is_suspended = ecommerce_data['is_suspended'],
            )


            for course in ecommerce_offer[0].course.all():
                # Condition 01: course is present in Offer courses
                # and also in the api courses
                if str(course.id) in ecommerce_data['courses_id']:
                    # do nothing
                    pass

                # Condition 02: course is present in offer courses
                # but not in the api courses
                elif str(course.id) not in ecommerce_data['courses_id']:
                    # remove the course from Offer courses
                    course.offer_set.remove(ecommerce_offer[0])
 
            # Condition 03: course is not present in offer courses
            # but present in the api courses
            for course in ecommerce_data['courses_id']:
                if course not in str(ecommerce_offer[0].course.all()):
                    # add course in the Offer courses
                    ecommerce_offer[0].course.add(CourseOverview.get_from_id(course))    


        # Else if Offer does not exist
        # Create it
        else: 
            start_datetime_str = ecommerce_data['start_datetime']
            start_datetime = datetime.strptime(start_datetime_str[:19], '%Y-%m-%d %H:%M:%S')

            if ecommerce_data['end_datetime'] != "None":
                end_datetime_str = ecommerce_data['end_datetime']
                end_datetime = datetime.strptime(end_datetime_str[:19], '%Y-%m-%d %H:%M:%S')
            else:
                end_datetime = None

            ecommerce_offer = Offer(
                associated_ecommerce_offer_id = ecommerce_data['associated_ecommerce_offer_id'],
                start_datetime = start_datetime,
                end_datetime = end_datetime,
                priority = ecommerce_data['priority'],
                incentive_type = ecommerce_data['incentive_type'],
                incentive_value = ecommerce_data['incentive_value'],
                condition_type = ecommerce_data['condition_type'],
                condition_value = ecommerce_data['condition_value'],
                is_exclusive = ecommerce_data['is_exclusive'],
                is_suspended = ecommerce_data['is_suspended'],
            )   

            ecommerce_offer.save()  

            for course_id in ecommerce_data['courses_id']:
                ecommerce_offer.course.add(CourseOverview.get_from_id(course_id))

        
        return Response({'status': 'Succes'}, status=status.HTTP_200_OK)


    def delete(self, *args, **kwargs):
        
        offer_id = self.kwargs.get('offer_id')
        try:
            offer = Offer.objects.get(associated_ecommerce_offer_id=offer_id)
        except Offer.DoesNotExist:
            return Response({'status': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        offer.delete()

        return Response({'status': 'Succes'}, status=status.HTTP_200_OK)



class Ecommerce_Coupon(APIView):

    def post(self, request):
        ecommerce_data = request.data

        # If Coupon already exists
        # Update it
        if Coupon.objects.filter(associated_ecommerce_coupon_id = ecommerce_data['associated_ecommerce_coupon_id']).exists():
            ecommerce_coupon = Coupon.objects.filter(associated_ecommerce_coupon_id = ecommerce_data['associated_ecommerce_coupon_id'])
            start_datetime_str = ecommerce_data['start_datetime']
            start_datetime = datetime.strptime(start_datetime_str[:19], '%Y-%m-%d %H:%M:%S')

            end_datetime_str = ecommerce_data['end_datetime']
            end_datetime = datetime.strptime(end_datetime_str[:19], '%Y-%m-%d %H:%M:%S')

            coupon_code = ecommerce_data['coupon_code']
            coupon_code = coupon_code.upper()

            ecommerce_coupon.update(
                associated_ecommerce_coupon_id = ecommerce_data['associated_ecommerce_coupon_id'],
                name = ecommerce_data['name'],
                coupon_code = coupon_code,
                start_datetime = start_datetime,
                end_datetime = end_datetime,
                incentive_type = ecommerce_data['incentive_type'],
                incentive_value = ecommerce_data['incentive_value'],
                usage = ecommerce_data['usage'],
                is_exclusive = ecommerce_data['is_exclusive'],
            )

            for course in ecommerce_coupon[0].course.all():
                # Condition 01: course is present in coupon courses
                # and also in the api courses
                if str(course.id) in ecommerce_data['courses_id']:
                    # do nothing
                    pass

                # Condition 02: course is present in coupon courses
                # but not in the api courses
                elif str(course.id) not in ecommerce_data['courses_id']:
                    # remove the course from coupon courses
                    course.coupon_set.remove(ecommerce_coupon[0])
 
            # Condition 03: course is not present in coupon courses
            # but present in the api courses
            for course in ecommerce_data['courses_id']:
                if course not in str(ecommerce_coupon[0].course.all()):
                    # add course in the coupon courses
                    ecommerce_coupon[0].course.add(CourseOverview.get_from_id(course))    


        # Else if Offer does not exist
        # Create it
        else: 
            start_datetime_str = ecommerce_data['start_datetime']
            start_datetime = datetime.strptime(start_datetime_str[:19], '%Y-%m-%d %H:%M:%S')

            end_datetime_str = ecommerce_data['end_datetime']
            end_datetime = datetime.strptime(end_datetime_str[:19], '%Y-%m-%d %H:%M:%S')

            coupon_code = ecommerce_data['coupon_code']
            coupon_code = coupon_code.upper()


            ecommerce_coupon = Coupon(
                associated_ecommerce_coupon_id = ecommerce_data['associated_ecommerce_coupon_id'],
                name = ecommerce_data['name'],
                coupon_code = coupon_code,
                start_datetime = start_datetime,
                end_datetime = end_datetime,
                incentive_type = ecommerce_data['incentive_type'],
                incentive_value = ecommerce_data['incentive_value'],
                usage = ecommerce_data['usage'],
                is_exclusive = ecommerce_data['is_exclusive'],
            )   

            ecommerce_coupon.save()  

            for course_id in ecommerce_data['courses_id']:
                ecommerce_coupon.course.add(CourseOverview.get_from_id(course_id))

        
        return Response({'status': 'Succes'}, status=status.HTTP_200_OK)


    def delete(self, *args, **kwargs):
        
        coupon_id = self.kwargs.get('coupon_id')
        try:
            coupon = Coupon.objects.get(associated_ecommerce_coupon_id=coupon_id)
        except Coupon.DoesNotExist:
            return Response({'status': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        coupon.delete()

        return Response({'status': 'Succes'}, status=status.HTTP_200_OK)


