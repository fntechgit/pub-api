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
        params['page'] = page
        response = requests.get(endpoint, params=params)
        return response.json()

    async def __get_remaining_items(self, endpoint: str, params: any, last_page: int):
        result = await asyncio.gather(*[self.__get_page(endpoint, params, page) for page in range(2, last_page + 1)])
        ordered_result = sorted(result, key=lambda d: d['current_page'])
        items = []
        for r in ordered_result:
            items += r['data']

        return items

    async def __download_events(self, summit_id: int, access_token: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_events: summit_id {summit_id}')
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
                return data + await self.__get_remaining_items(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_events error')

    async def __download_speakers(self, summit_id: int, access_token: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_speakers: summit_id {summit_id}')
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
                return data + await self.__get_remaining_items(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_speakers error')

    async def __download_summit(self, summit_id: int, access_token: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_summit: summit_id {summit_id}')
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
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_summit_extra_questions: summit_id {summit_id}')
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
                return data + await self.__get_remaining_items(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_summit_extra_questions error')

    async def __download_voteable_presentations(self, summit_id: int, access_token: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_voteable_presentations: summit_id {summit_id}')
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
                return data + await self.__get_remaining_items(endpoint, params, resp['last_page'])

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_voteable_presentations error')

    async def __dump_all_for_summit(self, summit_id: int, access_token: str, target_dir: str):

        logging.getLogger('api') \
            .info(f'FeedsDownloadService __dump_all_for_summit: summit_id {summit_id} saving files to {target_dir}')

        events, speakers, summit, extra_questions, presentations = await asyncio.gather(
            self.__download_events(summit_id, access_token),
            self.__download_speakers(summit_id, access_token),
            self.__download_summit(summit_id, access_token),
            self.__download_summit_extra_questions(summit_id, access_token),
            self.__download_voteable_presentations(summit_id, access_token)
        )

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        with open(f'{target_dir}/events.json', 'w', encoding='utf8') as outfile:
            json.dump(events, outfile, separators=(',', ':'), ensure_ascii=False)

        with open(f'{target_dir}/speakers.json', 'w', encoding='utf8') as outfile:
            json.dump(speakers, outfile, separators=(',', ':'), ensure_ascii=False)

        with open(f'{target_dir}/summit.json', 'w', encoding='utf8') as outfile:
            json.dump(summit, outfile, separators=(',', ':'), ensure_ascii=False)

        with open(f'{target_dir}/extra-questions.json', 'w', encoding='utf8') as outfile:
            json.dump(extra_questions, outfile, separators=(',', ':'), ensure_ascii=False)

        with open(f'{target_dir}/presentations.json', 'w', encoding='utf8') as outfile:
            json.dump(presentations, outfile, separators=(',', ':'), ensure_ascii=False)

    def download(self, summit_id: int, target_dir: str):
        try:
            access_token = self.access_token_service.get_access_token()
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.__dump_all_for_summit(summit_id, access_token, target_dir))
            loop.close()
            logging.getLogger('api').info(f'FeedsDownloadService download finished for summit_id {summit_id}')
        except Exception:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('FeedsDownloadService error')
