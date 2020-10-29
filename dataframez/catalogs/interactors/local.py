# Modifications © 2020 Hashmap, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime

from dataframez.catalogs.interactors.interface import Interface
import os
import yaml


class Local(Interface):
    """

    Entries have format:
    asset_name:
      type: ...
      versions: []
    """

    def __init__(self, location: str, name: str, **kwargs):
        super().__init__(**kwargs)

        self.__location = location
        self.__name = name

    def read_asset_configuration(self, entry_name: str, version: int = 1) -> dict:
        self._load_catalog()
        entries = self._catalog.get(entry_name)
        entry = [entry for entry in entries if entry_name['versions']['number'] == version][0]

        if not entry:
            error_message = f'dataframez: when attempting to read from catalog, {entry_name} did not exist. It is possible that version {version} is not ' \
                            f'there, but {entry_name} is.'
            self._logger.error(error_message)
            raise ValueError(error_message)

        return entry['asset_configuration']

    def get_latest_version(self, entry_name: str) -> int:
        return max([version['number'] for version in self.__catalog[entry_name]['versions']])

    def register(self, entry_name: str, **kwargs) -> None:
        self._load_catalog()

        if self._check_if_registered(entry_name=entry_name):
            self._logger.info(f'Entry {entry_name} already exists. Creating a new version of the entry.')
            self._catalog[entry_name]['versions'].append(
                {
                    'number': kwargs.get('version_number'),
                    'asset_configuration': kwargs.get('asset_configuration'),
                    'create_timestamp': datetime.datetime.timestamp(datetime.datetime.utcnow())
                }
            )
        else:
            self.__catalog[entry_name] = {
                'type': kwargs.get('type').lower(),
                'versions': {
                    'number': kwargs.get('version_number'),
                    'asset_configuration': kwargs.get('asset_configuration'),
                    'create_timestamp': datetime.datetime.timestamp(datetime.datetime.utcnow())
                }
            }

    def validate_entry_type(self, entry_name: str, asset_type: str) -> bool:
        if self._check_if_registered(entry_name=entry_name):
            return self.__catalog.get(entry_name)['type'].lower() == asset_type
        return True

    def _load_catalog(self) -> None:
        if not self.__catalog_in_memory:
            with open(os.path.join(self.__location, self.__name), 'r') as stream:
                self.__catalog = yaml.safe_load(stream)
            self.__catalog_in_memory = True