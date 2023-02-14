import logging
import traceback

from django_extensions.management.jobs import DailyJob

from api.models import AbstractPubService
from api.utils import FileLock, config, inject


class Job(DailyJob):
    help = "Pub API Entities Updates Purge Job"
    code = 'api.jobs.supabase_maintenance_scheduled_job'  # an unique code

    @inject
    def execute(self, service: AbstractPubService):
        try:
            with FileLock(self.__class__, False):
                res = service.purge_entity_updates(int(config("SUMMIT_ENTITIES_UPDATE_PURGE_HOURS_FROM_BACKWARD")))
                logging.getLogger('api').info(f'cron supabase_maintenance_scheduled_job: {res} records deleted')
        except:
            logging.getLogger('api').error(traceback.format_exc())
