"""
The application interface to roles which checks whether any user trying to change
authorization has authorization to do so, which infers authorization via role hierarchy
(GlobalStaff is superset of auths of course instructor, ...), which consults the config
to decide whether to check course creator role, and other such functions.
"""

import logging
from ccx_keys.locator import CCXBlockUsageLocator, CCXLocator
from django.conf import settings
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.locator import LibraryLocator

from common.djangoapps.student.roles import (
    CourseBetaTesterRole,
    CourseCreatorRole,
    CourseInstructorRole,
    CourseRole,
    CourseStaffRole,
    GlobalStaff,
    LibraryUserRole,
    OrgInstructorRole,
    OrgLibraryUserRole,
    OrgStaffRole
)
from cms.djangoapps.course_creators.views import add_user_with_status_unrequested, get_course_creator_status

# Studio permissions:
STUDIO_EDIT_ROLES = 8
STUDIO_VIEW_USERS = 4
STUDIO_EDIT_CONTENT = 2
STUDIO_VIEW_CONTENT = 1
STUDIO_NO_PERMISSIONS = 0
# In addition to the above, one is always allowed to "demote" oneself to a lower role within a course, or remove oneself

def is_ccx_course(course_key):
    """
    Check whether the course locator maps to a CCX course; this is important
    because we don't allow access to CCX courses in Studio.
    """
    return isinstance(course_key, CCXLocator) or isinstance(course_key, CCXBlockUsageLocator)


def user_has_role(user, role):
    """
    Check whether this user has access to this role (either direct or implied)
    :param user:
    :param role: an AccessRole
    """
    if not user.is_active:
        return False
    # do cheapest check first even tho it's not the direct one
    if GlobalStaff().has_user(user):
        return True
    # CourseCreator is odd b/c it can be disabled via config
    if isinstance(role, CourseCreatorRole):
        # completely shut down course creation setting
        if settings.FEATURES.get('DISABLE_COURSE_CREATION', False):
            return False
        # wide open course creation setting
        if not settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
            return True

    if role.has_user(user):
        return True
    # if not, then check inferred permissions
    if (isinstance(role, (CourseStaffRole, CourseBetaTesterRole)) and
            CourseInstructorRole(role.course_key).has_user(user)):
        return True
    return False


def get_user_permissions(user, course_key, org=None):
    """
    Get the bitmask of permissions that this user has in the given course context.
    Can also set course_key=None and pass in an org to get the user's
    permissions for that organization as a whole.
    """
    if org is None:
        org = course_key.org
        course_key = course_key.for_branch(None)
    else:
        assert course_key is None
    # No one has studio permissions for CCX courses
    if is_ccx_course(course_key):
        return STUDIO_NO_PERMISSIONS
    all_perms = STUDIO_EDIT_ROLES | STUDIO_VIEW_USERS | STUDIO_EDIT_CONTENT | STUDIO_VIEW_CONTENT
    # global staff, org instructors, and course instructors have all permissions:
    if GlobalStaff().has_user(user) or OrgInstructorRole(org=org).has_user(user) or (_get_course_creator_status(user) == 'granted' and OrgInstructorRole(org=org).has_same_organization(user)):
        return all_perms
    if course_key and user_has_role(user, CourseInstructorRole(course_key)):
        return all_perms
    # Staff have all permissions except EDIT_ROLES:
    if OrgStaffRole(org=org).has_user(user) or (course_key and user_has_role(user, CourseStaffRole(course_key))):

        return STUDIO_VIEW_USERS | STUDIO_EDIT_CONTENT | STUDIO_VIEW_CONTENT
    # Otherwise, for libraries, users can view only:
    if course_key and isinstance(course_key, LibraryLocator):
        if OrgLibraryUserRole(org=org).has_user(user) or user_has_role(user, LibraryUserRole(course_key)):
            return STUDIO_VIEW_USERS | STUDIO_VIEW_CONTENT

    return STUDIO_NO_PERMISSIONS


def has_studio_write_access(user, course_key):
    """
    Return True if user has studio write access to the given course.
    Note that the CMS permissions model is with respect to courses.
    There is a super-admin permissions if user.is_staff is set.
    Also, since we're unifying the user database between LMS and CAS,
    I'm presuming that the course instructor (formally known as admin)
    will not be in both INSTRUCTOR and STAFF groups, so we have to cascade our
    queries here as INSTRUCTOR has all the rights that STAFF do.

    :param user:
    :param course_key: a CourseKey
    """
    return bool(STUDIO_EDIT_CONTENT & get_user_permissions(user, course_key))


def has_course_author_access(user, course_key):
    """
    Old name for has_studio_write_access
    """
    return has_studio_write_access(user, course_key)


def has_studio_read_access(user, course_key):
    """
    Return True iff user is allowed to view this course/library in studio.
    Will also return True if user has write access in studio (has_course_author_access)

    There is currently no such thing as read-only course access in studio, but
    there is read-only access to content libraries.
    """
    return bool(STUDIO_VIEW_CONTENT & get_user_permissions(user, course_key))


def add_users(caller, role, *users):
    """
    The caller requests adding the given users to the role. Checks that the caller
    has sufficient authority.

    :param caller: a user
    :param role: an AccessRole
    """
    _check_caller_authority(caller, role)
    role.add_users(*users)


def remove_users(caller, role, *users):
    """
    The caller requests removing the given users from the role. Checks that the caller
    has sufficient authority.

    :param caller: a user
    :param role: an AccessRole
    """
    # can always remove self (at this layer)
    if not(len(users) == 1 and caller == users[0]):
        _check_caller_authority(caller, role)
    role.remove_users(*users)


def _check_caller_authority(caller, role):
    """
    Internal function to check whether the caller has authority to manipulate this role
    :param caller: a user
    :param role: an AccessRole
    """
    if not (caller.is_authenticated and caller.is_active):
        raise PermissionDenied
    # superuser
    if GlobalStaff().has_user(caller):
        return

    if isinstance(role, (GlobalStaff, CourseCreatorRole)):
        raise PermissionDenied
    elif isinstance(role, CourseRole):  # instructors can change the roles w/in their course
        if not user_has_role(caller, CourseInstructorRole(role.course_key)):
            raise PermissionDenied


def _get_course_creator_status(user):
    """
    Helper method for returning the course creator status for a particular user,
    taking into account the values of DISABLE_COURSE_CREATION and ENABLE_CREATOR_GROUP.

    If the user passed in has not previously visited the index page, it will be
    added with status 'unrequested' if the course creator group is in use.
    """

    if user.is_staff:
        course_creator_status = 'granted'
    elif settings.FEATURES.get('DISABLE_COURSE_CREATION', False):
        course_creator_status = 'disallowed_for_this_site'
    elif settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
        course_creator_status = get_course_creator_status(user)
        if course_creator_status is None:
            # User not grandfathered in as an existing user, has not previously visited the dashboard page.
            # Add the user to the course creator admin table with status 'unrequested'.
            add_user_with_status_unrequested(user)
            course_creator_status = get_course_creator_status(user)
    else:
        course_creator_status = 'granted'

    return course_creator_status

