import asyncio
import json
import logging
import os
import traceback
from datetime import datetime

import requests

from django_injector import inject

from .abstract_feeds_download_service import AbstractFeedsDownloadService
from ..security.access_token_service import AccessTokenService
from ..utils import config


class FeedsDownloadService(AbstractFeedsDownloadService):

    @inject
    def __init__(self, access_token_service: AccessTokenService):
        super().__init__()
        self.access_token_service = access_token_service

    async def __downloadEvents(self, summit_id: int, access_token: str, page=1, results=[]):
        try:
            response = requests.get(
                f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/events/published",
                params={
                    "access_token": access_token,
                    "per_page": 50,
                    "page": 1,
                    "expand": 'slides, links, videos, media_uploads, type, track, track.allowed_access_levels, '
                              'location, location.venue, location.floor, speakers, moderator, sponsors, '
                              'current_attendance, groups, rsvp_template, tags',
                }
            )
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                return await self.__downloadEvents(summit_id, access_token, page + 1, results + data)

            return results + data
        except Exception:
            logging.getLogger('api').error(traceback.format_exc())

    async def __downloadSpeakers(self, summit_id: int, access_token: str, page=1, results=[]):
        try:
            response = requests.get(
                f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/speakers/on-schedule",
                params={
                    "access_token": access_token,
                    "per_page": 30,
                    "page": page
                }
            )
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                return await self.__downloadSpeakers(summit_id, access_token, page + 1, results + data)

            return results + data
        except Exception:
            logging.getLogger('api').error(traceback.format_exc())

    async def __downloadSummit(self, summit_id: int, access_token: str):
        try:
            response = requests.get(
                f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}",
                params={
                    "access_token": access_token,
                    "t": datetime.now(),
                    "expand": 'event_types,tracks,track_groups,presentation_levels,locations.rooms,locations.floors,'
                              'order_extra_questions.values,schedule_settings,schedule_settings.filters,'
                              'schedule_settings.pre_filters',
                }
            )
            return response.json()
        except Exception:
            logging.getLogger('api').error(traceback.format_exc())

    async def __downloadSummitExtraQuestions(self, summit_id: int, access_token: str):
        try:
            response = requests.get(
                f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/order-extra-questions",
                params={
                    'access_token': access_token,
                    'filter[]': ['class==MainQuestion', 'usage==Ticket'],
                    'expand': '*sub_question_rules,*sub_question,*values',
                    'order': 'order',
                    'page': 1,
                    'per_page': 100,
                }
            )
            return response.json()
        except Exception:
            logging.getLogger('api').error(traceback.format_exc())

    async def __downloadVoteablePresentations(self, summit_id: int, access_token: str, page=1, results=[]):
        try:
            response = requests.get(
                f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/presentations/voteable",
                params={
                    'access_token': access_token,
                    'filter': 'published==1',
                    'page': page,
                    'per_page': 50,
                    'expand': 'slides, links, videos, media_uploads, type, track, track.allowed_access_levels, '
                              'location, location.venue, location.floor, speakers, moderator, sponsors, '
                              'current_attendance, groups, rsvp_template, tags'
                }
            )
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                return await self.__downloadVoteablePresentations(summit_id, access_token, page + 1, results + data)

            return results + data
        except Exception:
            logging.getLogger('api').error(traceback.format_exc())

    async def __dump_all_for_summit(self, summit_id: int, access_token: str):

        logging.getLogger('api') \
            .info(f'FeedsDownloadService __dump_all_for_summit: summit_id {summit_id}')

        events, speakers, summit, extra_questions, presentations = await asyncio.gather(
            self.__downloadEvents(summit_id, access_token),
            self.__downloadSpeakers(summit_id, access_token),
            self.__downloadSummit(summit_id, access_token),
            self.__downloadSummitExtraQuestions(summit_id, access_token),
            self.__downloadVoteablePresentations(summit_id, access_token)
        )

        show_feeds_dir_path = config('LOCAL_SHOW_FEEDS_DIR_PATH')

        if not os.path.exists(show_feeds_dir_path):
            os.makedirs(show_feeds_dir_path)

        with open(f'{show_feeds_dir_path}/events.json', 'w') as outfile:
            json.dump(events, outfile)

        with open(f'{show_feeds_dir_path}/speakers.json', 'w') as outfile:
            json.dump(speakers, outfile)

        with open(f'{show_feeds_dir_path}/summit.json', 'w') as outfile:
            json.dump(summit, outfile)

        with open(f'{show_feeds_dir_path}/extra_questions.json', 'w') as outfile:
            json.dump(extra_questions, outfile)

        with open(f'{show_feeds_dir_path}/presentations.json', 'w') as outfile:
            json.dump(presentations, outfile)

    def download(self, summit_id: int):
        try:
            access_token = self.access_token_service.get_access_token()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.__dump_all_for_summit(summit_id, access_token))
            loop.close()
            logging.getLogger('api').info(f'FeedsDownloadService download finished for summit_id {summit_id}')
        except Exception:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('FeedsDownloadService error')
