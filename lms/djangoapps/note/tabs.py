#from lms.djangoapps.note.config.waffle import use_bootstrap_flag_enabled
from django.utils.translation import ugettext_noop
from lms.djangoapps.courseware.tabs import CourseTab
from django.conf import settings


class NoteTab(CourseTab):
    """
    The representation of the course teams view type.
    """
    type = "note"
    name = "note"
    title = ugettext_noop("Note")
    view_name = "note_list"
    is_default = True
    tab_id = "note"
    is_hideable = True

    @classmethod
    def is_enabled(cls, course, user=None):
        return settings.FEATURES.get('IS_NOTE_TAB_ENABLED', False)

    @property
    def uses_bootstrap(self):
        """
        Returns true if this tab is rendered with Bootstrap.
        """
        return use_bootstrap_flag_enabled()
