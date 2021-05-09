import mimetypes

from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.safestring import mark_safe

from common.djangoapps.util.cache import cache_if_anonymous
from common.djangoapps.edxmako.shortcuts import render_to_response
from mako.exceptions import TopLevelLookupException
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from ..models import Bundle

@ensure_csrf_cookie
@cache_if_anonymous()
def render(request, template, bundle_id):
    # Guess content type from file extension
    # content_type, __ = mimetypes.guess_type(template)

    bundle = Bundle.objects.get(id=bundle_id)

    try:
        context = {
            "name": bundle.name,
            "description": bundle.description,
            "courses": bundle.course_metadata,
        }
        result = render_to_response('subscriptions/' + template, context, content_type='text/html')
        return result

    except TopLevelLookupException:
        raise Http404
    except TemplateDoesNotExist:
        raise Http404