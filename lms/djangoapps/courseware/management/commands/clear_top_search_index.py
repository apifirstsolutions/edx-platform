"""
Dump the course_ids available to the lms.

Output is UTF-8 encoded by default.
"""


from textwrap import dedent

from django.core.management.base import BaseCommand

from search.search_engine_base import SearchEngine
import logging
log = logging.getLogger(__name__)
class Command(BaseCommand):
    help = dedent(__doc__).strip()

    def handle(self, *args, **options):
        try:
            search_engine = SearchEngine.get_search_engine(index="home_search")
            search_result = search_engine.search(size=2000)
            vault = []
            for x in search_result['results']:
                log.info("Invoking for Purge id "+str(x['_id']))
                vault.append(x['_id'])
            search_engine.remove('home', vault)
            log.info("Cleared Indexing of Top Search Successful !!")
        except Exception as ex:
            log.error("ERROR While trying to purge Indexing of Top Search"+ str(ex))
