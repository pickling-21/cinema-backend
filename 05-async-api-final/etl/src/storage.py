import abc
import json
from datetime import datetime
from typing import Any, Dict

from loguru import logger


class BaseStorage(abc.ABC):
    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]:
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save_state(self, state: Dict[str, Any]) -> None:
        with open(self.file_path, "w") as file:
            json.dump(state, file)

    def retrieve_state(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Json not valid. {self.file_path}")
            return {}
        except FileNotFoundError:
            self.save_state({})
            return {}


class StateManager:
    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        current_state = self.storage.retrieve_state()
        current_state[key] = value
        self.storage.save_state(current_state)

    def get_state(self, key: str) -> Any:
        current_state = self.storage.retrieve_state()
        return current_state.get(key, str(datetime.min))
