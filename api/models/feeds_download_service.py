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

    async def __get_page(self, endpoint: str, params: any, page: int):
        response = requests.get(endpoint, params=params)
        return {'page_number': page, 'page_data': response.json()}

    async def __get_remaining_pages(self, endpoint: str, params: any, last_page: int):
        result = await asyncio.gather(*[self.__get_page(endpoint, params, page) for page in range(2, last_page + 1)])
        ordered_result = sorted(result, key=lambda d: d['page_number'])
        pages = []
        for r in ordered_result:
            pages.append(r['page_data'])
        return pages

    async def __download_events(self, summit_id: int, access_token: str):
        try:
            endpoint = f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/events/published"
            params = {
                "access_token": access_token,
                "per_page": 50,
                "page": 1,
                "expand": 'slides, links, videos, media_uploads, type, track, track.allowed_access_levels, '
                          'location, location.venue, location.floor, speakers, moderator, sponsors, '
                          'current_attendance, groups, rsvp_template, tags',
            }
            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                return data + await self.__get_remaining_pages(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_events error')

    async def __download_speakers(self, summit_id: int, access_token: str):
        try:
            endpoint = f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/speakers/on-schedule"
            params = {
                "access_token": access_token,
                "page": 1,
                "per_page": 30
            }
            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                return data + await self.__get_remaining_pages(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_speakers error')

    async def __download_summit(self, summit_id: int, access_token: str):
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
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_summit error')

    async def __download_summit_extra_questions(self, summit_id: int, access_token: str):
        try:
            endpoint = f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/order-extra-questions"
            params = {
                'access_token': access_token,
                'filter[]': ['class==MainQuestion', 'usage==Ticket'],
                'expand': '*sub_question_rules,*sub_question,*values',
                'order': 'order',
                'page': 1,
                'per_page': 100,
            }
            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                return data + await self.__get_remaining_pages(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_summit_extra_questions error')

    async def __download_voteable_presentations(self, summit_id: int, access_token: str):
        try:
            endpoint = f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/presentations/voteable"
            params = {
                'access_token': access_token,
                'filter': 'published==1',
                'page': 1,
                'per_page': 50,
                'expand': 'slides, links, videos, media_uploads, type, track, track.allowed_access_levels, '
                          'location, location.venue, location.floor, speakers, moderator, sponsors, '
                          'current_attendance, groups, rsvp_template, tags'
            }
            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                return data + await self.__get_remaining_pages(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_voteable_presentations error')

    async def __dump_all_for_summit(self, summit_id: int, access_token: str):

        logging.getLogger('api') \
            .info(f'FeedsDownloadService __dump_all_for_summit: summit_id {summit_id}')

        events, speakers, summit, extra_questions, presentations = await asyncio.gather(
            self.__download_events(summit_id, access_token),
            self.__download_speakers(summit_id, access_token),
            self.__download_summit(summit_id, access_token),
            self.__download_summit_extra_questions(summit_id, access_token),
            self.__download_voteable_presentations(summit_id, access_token)
        )

        show_feeds_dir_path = os.path.join(config('LOCAL_SHOW_FEEDS_DIR_PATH'), summit_id.__str__())

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