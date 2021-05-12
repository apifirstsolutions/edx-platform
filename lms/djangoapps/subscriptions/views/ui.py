import mimetypes

from django.http import Http404
from django.template import TemplateDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from bridgekeeper import perms

from common.djangoapps.util.cache import cache_if_anonymous
from common.djangoapps.edxmako.shortcuts import render_to_response
from mako.exceptions import TopLevelLookupException
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from ..models import Bundle
from ..permissions import VIEW_BUNDLE


@ensure_csrf_cookie
@cache_if_anonymous()
def render(request, template, bundle_id):
    
    bundle = Bundle.objects.get(id=bundle_id)

    if not perms[VIEW_BUNDLE].check(request.user, bundle):
        raise Http404()

    try:
        context = {
            "name": bundle.name,
            "description": bundle.description,
            "courses": bundle.course_metadata,
        }
        return render_to_response('subscriptions/' + template, context, content_type='text/html')
    except TopLevelLookupException:
        raise Http404
    except TemplateDoesNotExist:
        raise Http404