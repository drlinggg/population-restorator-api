"""Configs are defined here"""

from __future__ import annotations

import os
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

import yaml

from app.models import FertilityInterval

from .logging import LoggingLevel


@dataclass
class AppConfig:
    # todo desc
    host: str
    port: int
    debug: bool
    name: str

    def __post_init__(self):
        self.name = f"population-restorator-api 0.0.1"


@dataclass
class WorkingDirConfig:
    divide_working_db_path: str
    forecast_working_dir_path: str


@dataclass
class RedisQueueConfig:
    # todo desc
    host: str
    port: str
    db: int
    queue_name: str


@dataclass
class ApiConfig:
    """defaut api config"""

    host: str
    port: int
    api_key: str | None
    const_request_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class DBConfig:
    # todo desc
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int


@dataclass
class FileLogger:
    # todo desc
    filename: str
    level: LoggingLevel


@dataclass
class LoggingConfig:
    level: LoggingLevel
    files: list[FileLogger] = field(default_factory=list)

    def __post_init__(self):
        if len(self.files) > 0 and isinstance(self.files[0], dict):
            self.files = [FileLogger(**f) for f in self.files]


@dataclass
class PopulationRestoratorConfig:
    working_dirs: WorkingDirConfig
    fertility_interval: FertilityInterval


@dataclass
class PopulationRestoratorApiConfig:
    app: AppConfig
    population_restorator: PopulationRestoratorConfig
    redis_queue: RedisQueueConfig
    logging: LoggingConfig
    urban_api: ApiConfig
    socdemo_api: ApiConfig
    saving_api: ApiConfig

    def to_order_dict(self) -> OrderedDict:
        """OrderDict transformer."""

        def to_ordered_dict_recursive(obj) -> OrderedDict:
            """Recursive OrderDict transformer."""

            if isinstance(obj, (dict, OrderedDict)):
                return OrderedDict((k, to_ordered_dict_recursive(v)) for k, v in obj.items())
            if hasattr(obj, "__dataclass_fields__"):
                return OrderedDict(
                    (field, to_ordered_dict_recursive(getattr(obj, field))) for field in obj.__dataclass_fields__
                )
            return obj

        return OrderedDict(
            [
                ("app", to_ordered_dict_recursive(self.app)),
                ("redis_queue", to_ordered_dict_recursive(self.redis_queue)),
                ("logging", to_ordered_dict_recursive(self.logging)),
                ("urban_api", to_ordered_dict_recursive(self.urban_api)),
                ("socdemo_api", to_ordered_dict_recursive(self.socdemo_api)),
                ("saving_api", to_ordered_dict_recursive(self.saving_api)),
            ]
        )

    def dump(self, file: str | Path | TextIO) -> None:
        """Export current configuration to a file"""

        class OrderedDumper(yaml.SafeDumper):
            def represent_dict_preserve_order(self, data):
                return self.represent_dict(data.items())

            def represent_file_logger(self, file_logger):
                return self.represent_dict({"filename": file_logger.filename, "level": file_logger.level})

            def represent_logging_level(self, logging_level):
                return self.represent_str(str(logging_level))

        OrderedDumper.add_representer(OrderedDict, OrderedDumper.represent_dict_preserve_order)
        OrderedDumper.add_representer(FileLogger, OrderedDumper.represent_file_logger)
        OrderedDumper.add_representer(LoggingLevel, OrderedDumper.represent_logging_level)

        if isinstance(file, (str, Path)):
            with open(str(file), "w", encoding="utf-8") as file_w:
                yaml.dump(self.to_order_dict(), file_w, Dumper=OrderedDumper, default_flow_style=False)
        else:
            yaml.dump(self.to_order_dict(), file, Dumper=OrderedDumper, default_flow_style=False)

    @classmethod
    def example(cls) -> "PopulationRestoratorApiConfig":
        """Generate an example of configuration."""

        return cls(
            app=AppConfig(host="0.0.0.0", port=8000, debug=True, name="population-restorator-api"),
            population_restorator=PopulationRestoratorConfig(
                working_dirs=WorkingDirConfig(
                    divide_working_db_path="./test.db",
                    forecast_working_dir_path="./calculation_dbs/",
                ),
                fertility_interval=FertilityInterval(start=18, end=40),
            ),
            redis_queue=RedisQueueConfig(host="localhost", port="6379", db=0, queue_name="default"),
            logging=LoggingConfig(level="INFO"),
            urban_api=ApiConfig(
                host="https://urban-api.idu.kanootoko.org",
                port=443,
                api_key="todo",
                const_request_params={"some_path_param": 4},
            ),
            socdemo_api=ApiConfig(host="todo", port=443, api_key=None, const_request_params={"another_param": "test"}),
            saving_api=ApiConfig(host="todo", port=443, api_key=None),
        )

    @classmethod
    def load(cls, file: str | Path | TextIO) -> "PopulationRestoratorApiConfig":
        """Import config from the given filename or raise `ValueError` on error."""

        try:
            if isinstance(file, (str, Path)):
                with open(file, "r", encoding="utf-8") as file_r:
                    data = yaml.safe_load(file_r)
            else:
                data = yaml.safe_load(file)

            population_restorator = data.get("population_restorator", {})
            return cls(
                app=AppConfig(**data.get("app", {})),
                population_restorator=PopulationRestoratorConfig(
                    working_dirs=WorkingDirConfig(**population_restorator["working_dirs"]),
                    fertility_interval=FertilityInterval(
                        **population_restorator["fertility"],
                    ),
                ),
                redis_queue=RedisQueueConfig(**data.get("redis_queue", {})),
                logging=LoggingConfig(**data.get("logging", {})),
                urban_api=ApiConfig(**data.get("urban_api", {})),
                socdemo_api=ApiConfig(**data.get("socdemo_api", {})),
                saving_api=ApiConfig(**data.get("saving_api", {})),
            )
        except Exception as exc:
            raise ValueError(f"Could not read app config file: {file}") from exc

    @classmethod
    def from_file_or_default(cls, config_path: str = os.getenv("CONFIG_PATH")) -> "PopulationRestoratorApiConfig":
        """Try to load configuration from the path specified in the environment variable."""

        if not config_path:
            return cls.example()

        return cls.load(config_path)
