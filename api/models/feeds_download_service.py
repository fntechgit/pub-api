import asyncio
import json
import logging
import os
import time
import traceback
from datetime import datetime

import requests

from django_injector import inject

from .abstract_feeds_download_service import AbstractFeedsDownloadService
from .tasks_cache_wrapper import TaskStatus, TasksCacheWrapper, dump_if_task_still_active, download_if_task_still_active
from ..security.access_token_service import AccessTokenService
from ..utils import config


class FeedsDownloadService(AbstractFeedsDownloadService):

    @inject
    def __init__(self, access_token_service: AccessTokenService):
        super().__init__()
        self.access_token_service = access_token_service

    @dump_if_task_still_active
    def __build_json_file(self, data: any, path: str, summit_id: int, task_id: str):
        with open(path, 'w', encoding='utf8') as outfile:
            json.dump(data, outfile, separators=(',', ':'), ensure_ascii=False)

    @dump_if_task_still_active
    def __build_index(self, collection: any, path: str, summit_id: int, task_id: str):
        with open(path, 'w', encoding='utf8') as outfile:
            collection_idx = {}
            ix = 0
            for item in collection:
                collection_idx[item['id']] = ix
                ix = ix + 1
            json.dump(collection_idx, outfile, separators=(',', ':'), ensure_ascii=False)

    @download_if_task_still_active
    async def __get_page(self, endpoint: str, params: any, page: int, summit_id: int, task_id: str):
        params['page'] = page
        response = requests.get(endpoint, params=params)
        return response.json()

    async def __get_remaining_items(self, endpoint: str, params: any, last_page: int, summit_id: int, task_id: str):
        result = await asyncio.gather(*[self.__get_page(endpoint, params, page, summit_id=summit_id, task_id=task_id)
                                        for page in range(2, last_page + 1)])
        filtered_result = filter(None, result)
        ordered_result = sorted(filtered_result, key=lambda d: d['current_page'])
        items = []
        for r in ordered_result:
            items += r['data']

        return items

    @download_if_task_still_active
    async def __download_events(self, summit_id: int, access_token: str, task_id: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_events: summit_id {summit_id}')
        try:
            endpoint = f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/events/published"
            params = {
                "access_token": access_token,
                "per_page": config('CONTENT_SNAPSHOT_DOWNLOAD_PAGE_SIZE', 50),
                "page": 1,
                "expand": 'slides, links, videos, media_uploads, type, track, track.subtracks, '
                          'track.allowed_access_levels, location, location.venue, location.floor, speakers, moderator, '
                          'sponsors, current_attendance, groups, rsvp_template, tags',
                "relations": 'speakers.badge_features, speakers.affiliations, speakers.languages, '
                             'speakers.other_presentation_links, speakers.areas_of_expertise, '
                             'speakers.travel_preferences, speakers.organizational_roles, '
                             'speakers.all_presentations, speakers.all_moderated_presentations'
            }
            start = time.time()

            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                data = data + await self.__get_remaining_items(
                    endpoint, params, resp['last_page'], summit_id=summit_id, task_id=task_id)

            end = time.time()

            logging.getLogger('api') \
                .info(f'FeedsDownloadService __download_events: execution time: {end - start} seconds')

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_events error')

    @download_if_task_still_active
    async def __download_speakers(self, summit_id: int, access_token: str, task_id: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_speakers: summit_id {summit_id}')
        try:
            endpoint = f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/speakers/on-schedule"
            params = {
                "access_token": access_token,
                "page": 1,
                "per_page": config('CONTENT_SNAPSHOT_DOWNLOAD_PAGE_SIZE', 50),
                "relations": 'badge_features,affiliations,languages,other_presentation_links,areas_of_expertise,'
                             'travel_preferences,organizational_roles,all_presentations,all_moderated_presentations',
            }
            start = time.time()

            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                data = data + await self.__get_remaining_items(
                    endpoint, params, resp['last_page'], summit_id=summit_id, task_id=task_id)

            end = time.time()

            logging.getLogger('api') \
                .info(f'FeedsDownloadService __download_speakers: execution time: {end - start} seconds')

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_speakers error')

    @download_if_task_still_active
    async def __download_summit(self, summit_id: int, access_token: str, task_id: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_summit: summit_id {summit_id}')
        try:
            response = requests.get(
                f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}",
                params={
                    "access_token": access_token,
                    "t": datetime.now(),
                    "expand": 'event_types,tracks,tracks.subtracks, track_groups,presentation_levels,locations.rooms,locations.floors,'
                              'order_extra_questions.values,schedule_settings,schedule_settings.filters,'
                              'schedule_settings.pre_filters',
                }
            )
            return response.json()
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_summit error')

    @download_if_task_still_active
    async def __download_summit_extra_questions(self, summit_id: int, access_token: str, task_id: str):
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
                'per_page': config('CONTENT_SNAPSHOT_DOWNLOAD_PAGE_SIZE', 50),
            }
            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                data = data + await self.__get_remaining_items(
                    endpoint, params, resp['last_page'], summit_id=summit_id, task_id=task_id)

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_summit_extra_questions error')

    @download_if_task_still_active
    async def __download_voteable_presentations(self, summit_id: int, access_token: str, task_id: str):
        logging.getLogger('api') \
            .info(f'FeedsDownloadService __download_voteable_presentations: summit_id {summit_id}')
        try:
            endpoint = f"{config('SUMMIT_API_BASE_URL', None)}/api/v1/summits/{summit_id}/presentations/voteable"
            params = {
                'access_token': access_token,
                'filter': 'published==1',
                'page': 1,
                'per_page': config('CONTENT_SNAPSHOT_DOWNLOAD_PAGE_SIZE', 50),
                'expand': 'slides, links, videos, media_uploads, type, track, track.allowed_access_levels, '
                          'location, location.venue, location.floor, speakers, moderator, sponsors, '
                          'current_attendance, groups, rsvp_template, tags'
            }

            response = requests.get(endpoint, params=params)
            resp = response.json()
            data = resp['data']
            if resp['current_page'] < resp['last_page']:
                data = data + await self.__get_remaining_items(
                    endpoint, params, resp['last_page'], summit_id=summit_id, task_id=task_id)

            return data
        except Exception as ex:
            logging.getLogger('api').error(ex)
            raise Exception('__download_voteable_presentations error')

    async def __dump_all_for_summit(self, summit_id: int, access_token: str, target_dir: str, task_id: str):

        logging.getLogger('api') \
            .info(f'FeedsDownloadService __dump_all_for_summit: summit_id {summit_id} saving files to {target_dir}')

        start = time.time()

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        events, speakers, summit, extra_questions, presentations = await asyncio.gather(
            self.__download_events(summit_id=summit_id, access_token=access_token, task_id=task_id),
            self.__download_speakers(summit_id=summit_id, access_token=access_token, task_id=task_id),
            self.__download_summit(summit_id=summit_id, access_token=access_token, task_id=task_id),
            self.__download_summit_extra_questions(summit_id=summit_id, access_token=access_token, task_id=task_id),
            self.__download_voteable_presentations(summit_id=summit_id, access_token=access_token, task_id=task_id)
        )

        end = time.time()

        logging.getLogger('api') \
            .info(f'FeedsDownloadService __dump_all_for_summit: execution time: {end - start} seconds')

        self.__build_json_file(events, f'{target_dir}/events.json', summit_id=summit_id, task_id=task_id)

        self.__build_index(events, f'{target_dir}/events.idx.json', summit_id=summit_id, task_id=task_id)

        self.__build_json_file(speakers, f'{target_dir}/speakers.json', summit_id=summit_id, task_id=task_id)

        self.__build_index(speakers, f'{target_dir}/speakers.idx.json', summit_id=summit_id, task_id=task_id)

        self.__build_json_file(summit, f'{target_dir}/summit.json', summit_id=summit_id, task_id=task_id)

        self.__build_json_file(
            extra_questions, f'{target_dir}/extra-questions.json', summit_id=summit_id, task_id=task_id)

        self.__build_index(
            extra_questions, f'{target_dir}/extra-questions.idx.json', summit_id=summit_id, task_id=task_id)

        self.__build_json_file(presentations, f'{target_dir}/presentations.json', summit_id=summit_id, task_id=task_id)

        self.__build_index(presentations, f'{target_dir}/presentations.idx.json', summit_id=summit_id, task_id=task_id)

        if task_id != "0":
            TasksCacheWrapper.update_task_status(summit_id, task_id, TaskStatus.DOWNLOADED)

    def download(self, summit_id: int, target_dir: str, task_id: str):
        try:
            access_token = self.access_token_service.get_access_token()
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.__dump_all_for_summit(summit_id, access_token, target_dir, task_id))
            loop.close()
            logging.getLogger('api').info(f'FeedsDownloadService download finished for summit_id {summit_id}')
        except Exception as ex:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('FeedsDownloadService error')
