from datetime import datetime, timedelta
from .abstract_pub_service import AbstractPubService
from supabase import create_client, Client
import logging
from ..utils import config
import traceback


class SupaBasePubService(AbstractPubService):
    supabase: Client = None

    def __init__(self):
        url: str = config("SUPABASE.URL")
        key: str = config("SUPABASE.KEY")

        try:
            self.supabase = create_client(url, key)
        except:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('SUPABASE connection error')

    def __del__(self):
        if self.supabase is not None:
            self.supabase = None

    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        try:
            result = self.supabase \
                .table("summit_entity_updates").insert(
                {"summit_id": summit_id, "entity_id": entity_id, "entity_type": entity_type, "entity_operator": op, "created_at": created_at}).execute()
            if len(result.data) > 0:
                return result.data[0]
            return None
        except:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('SUPABASE error')

    def purge_entity_updates(self, hours_from_backward: int):
        try:
            date_time_from_backward = \
                round((datetime.today() - timedelta(hours=hours_from_backward)).timestamp() * 1000)

            result = self.supabase.table("summit_entity_updates").delete().lte("created_at", date_time_from_backward).execute()

            return len(result.data)
        except:
            logging.getLogger('api').error(traceback.format_exc())
            return 0
