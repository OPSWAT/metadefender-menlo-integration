# import requests
from tornado.httpclient import AsyncHTTPClient
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
import datetime
import os
import json
import logging
from metadefender_menlo.log_types import SERVICE, TYPE


class MetaDefenderCoreAPI(MetaDefenderAPI):

    def __init__(self, url, apikey):
        self.server_url = url
        self.apikey = apikey
        self.report_url = self.server_url + \
            "/#/public/process/dataId/{data_id}"

    def _get_submit_file_headers(self, filename, metadata):
        metadata_str = json.dumps(metadata) if metadata is not None else ""

        headers = {
            "filename": filename,
            "metadata": metadata_str
        }
        logging.debug("{0} > {1} > {2}Add headers: {0}".format(
            SERVICE.MenloPlugin, TYPE.Iternal, {"headers": headers}))
        return headers

    def check_analysis_complete(self, json_response):
        if ("process_info" in json_response and "progress_percentage" in json_response["process_info"]):
            return json_response["process_info"]["progress_percentage"] == 100
        else:
            print("Unexpected response from MetaDefender: {0}".format(
                json_response))
            return False

    async def retrieve_sanitized_file(self, data_id):
        logging.info(
            "{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {"message":"Retrieve Sanitized file for "%data_id}))
        response, http_status = await self._request_status("sanitized_file", fields={"data_id": data_id})

        return (response, http_status)
