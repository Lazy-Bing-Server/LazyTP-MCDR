from enum import Enum
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.utils import Serializable
from typing import List, Dict, Optional
from threading import RLock

from location_marker.entry import storage, Location
from lazytp.constants import global_server, CONFIG_PATH


config_access_lock = RLock()


class Dimension(Enum):
    overworld = 0
    the_nether = -1
    the_end = 1

    @property
    def prefix(self):
        return f'!!{self.name}' if not self.name.startswith('the_') else f'!!{self.name[4:]}'

    @classmethod
    def get(cls, prefix: str) -> 'Dimension':
        dic = {}
        for item in cls:
            dic[item.prefix] = item
        return dic[prefix]


class Coordinate(Serializable):
    x: float = 0
    y: float = 64
    z: float = 64
    dim: Dimension

    @classmethod
    def gen(cls, x: float, y: float, z: float):
        return cls.deserialize({'x': x, 'y': y, 'z': z})

    @property
    def text(self):
        return f'{self.x} {self.y} {self.z}'


class DefaultWaypoints(Serializable):
    overworld: Coordinate = Coordinate.gen(0, 64, 0)
    the_nether: Coordinate = Coordinate.gen(0, 64, 0)
    the_end: Coordinate = Coordinate.gen(0, 64, 100)


class EzTeleportLocations(Serializable):
    location_name: str
    alias: str

    def ensure_existance(self):
        return storage.get(self.location_name) is not None


class Config(Serializable):
    we_unstuck: bool = True
    default_waypoints: DefaultWaypoints = DefaultWaypoints.get_default()
    ez_teleport_destnations: List[EzTeleportLocations] = []

    def save(self):
        with config_access_lock:
            global_server.save_config_simple(self, CONFIG_PATH, in_data_folder=False)

    @classmethod
    def load(cls):
        with config_access_lock:
            return global_server.load_config_simple(
                CONFIG_PATH, default_config=cls.get_default().serialize(), in_data_folder=False, target_class=cls
            )

    def add_wp(self, alias: str, name: str):
        with config_access_lock:
            if name in self.name_map.keys():
                raise LocationAlreadyExist(f'Location {name}')
            if alias in self.alias_map.keys():
                raise LocationAlreadyExist(f'Alias {alias}')
            if storage.get(name) is not None:
                self.ez_teleport_destnations.append(EzTeleportLocations(location_name=name, alias=alias))
                global_server.logger.info(f'Added location: {alias} -> {name}')
            else:
                LocationNotFound(name)
        self.save()

    def rm_wp(self, alias: str):
        with config_access_lock:
            if alias not in self.alias_map.keys():
                raise LocationNotFound(f'Alias {alias}')
            self.ez_teleport_destnations.remove(self.alias_map[alias])
            global_server.logger.info(f'Removed location: {alias}')
        self.save()

    @new_thread('LazyTeleport_Config')
    def remove_invalid(self):
        to_remove = self.query_invalid().get_return_value(block=True)
        num = len(to_remove)
        with config_access_lock:
            for loc in to_remove:
                self.ez_teleport_destnations.remove(loc)
        self.save()
        return num

    @new_thread('LazyTeleport_Config')
    def query_invalid(self):
        with config_access_lock:
            invalid = []
            for loc in self.ez_teleport_destnations.copy():
                if not loc.ensure_existance():
                    invalid.append(loc)
            if len(invalid) != 0:
                invalid_text = ''
                for loc in invalid:
                    invalid_text += f' {loc.alias}[{loc.location_name}]'
                global_server.logger.info(f'{len(invalid)} invalid eztp location detected:{invalid_text}')
            return invalid

    @new_thread('LazyTeleport_Config')
    def __build_map(self, name: bool):
        ret = {}
        for loc in self.ez_teleport_destnations:
            if name:
                ret[loc.location_name] = loc
            else:
                ret[loc.alias] = loc
        return ret

    @property
    def name_map(self) -> Dict[str, EzTeleportLocations]:
        return self.__build_map(True).get_return_value(block=True)

    @property
    def alias_map(self) -> Dict[str, EzTeleportLocations]:
        return self.__build_map(False).get_return_value(block=True)

    def get_location(self, alias: str) -> Optional[Location]:
        with config_access_lock:
            return storage.get(self.alias_map.get(alias).location_name)


config = Config.load()


class LocationAlreadyExist(Exception):
    def __init__(self, loc: str):
        self.text = f'{loc} already exists'


class LocationNotFound(Exception):
    def __init__(self, loc: str):
        self.text = f'{loc} not found'
