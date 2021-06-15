from rest_framework.response import Response
from lms.djangoapps.courseware.courses import get_course_info_section_module
from lms.djangoapps.mobile_api.course_info.views import apply_wrappers_to_content, CourseHandoutsList
from lms.djangoapps.mobile_api.decorators import mobile_course_access, mobile_view


@mobile_view()
class LHUBCourseHandoutsList(CourseHandoutsList):
    """
    **Use Case**

        Get the HTML for course handouts.

    **Example Request**

        GET /api/mobile/v1/course_info/{course_id}/lhub/handouts

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with the following value.

        * handouts_html: The HTML for course handouts.
    """

    @mobile_course_access()
    def list(self, request, course, *args, **kwargs):
        course_handouts_module = get_course_info_section_module(request, request.user, course, 'handouts')
        if course_handouts_module:
            if course_handouts_module.data == "<ol></ol>":
                handouts_html = None
            else:
                handouts_html = apply_wrappers_to_content(course_handouts_module.data, course_handouts_module, request)
            return Response(
                status=200,
                data={
                    "message": "",
                    "status": True,
                    "status_code": 200,
                    "result": {
                        'handouts_html': handouts_html
                    }
                }
            )
        else:
            # course_handouts_module could be None if there are no handouts
            return Response(
                status=200,
                data={
                    "message": "",
                    "status": True,
                    "status_code": 200,
                    "result": {
                        'handouts_html': None
                    }
                }
            )
