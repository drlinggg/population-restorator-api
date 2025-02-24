"""Configs are defined here"""

from __future__ import annotations

import os
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

import yaml

from .logging import LoggingLevel


@dataclass
class AppConfig:
    host: str
    port: int
    debug: bool
    name: str

    def __post_init__(self):
        self.name = f"population-restorator-api (//todo apiversion//)"


@dataclass
class ApiConfig:
    """defaut api config"""

    host: str
    port: int
    api_key: str
    base_path: str


@dataclass
class DBConfig:
    # todo desc
    addr: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int


@dataclass
class FileLogger:
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
class PopulationRestoratorApiConfig:
    app: AppConfig
    db: DBConfig
    logging: LoggingConfig
    urban_api: ApiConfig
    socdemo_api: ApiConfig

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
                ("db", to_ordered_dict_recursive(self.db)),
                ("logging", to_ordered_dict_recursive(self.logging)),
                ("urban_api", to_ordered_dict_recursive(self.urban_api)),
                ("socdemo_api", to_ordered_dict_recursive(self.socdemo_api)),
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
            app=AppConfig(host="0.0.0.0", port=8000, debug=False, name="urban_api"),
            db=DBConfig(
                addr="localhost", port=5432, name="urban_db", user="postgres", password="postgres", pool_size=15
            ),
            logging=LoggingConfig(level="INFO"),
            urban_api=ApiConfig(host="todo", port=443, api_key="todo", base_path="/api/v1"),
            socdemo_api=ApiConfig(host="todo", port=443, api_key="todo", base_path="/api/v1"),
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

            return cls(
                app=AppConfig(**data.get("app", {})),
                db=DBConfig(**data.get("db", {})),
                logging=LoggingConfig(**data.get("logging", {})),
                urban_api=ApiConfig(**data.get("urban_api", {})),
                socdemo_api=ApiConfig(**data.get("socdemo_api", {})),
            )
        except Exception as exc:
            raise ValueError(f"Could not read app config file: {file}") from exc

    @classmethod
    def from_file_or_default(cls, config_path: str = os.getenv("CONFIG_PATH")) -> "PopulationRestoratorApiConfig":
        """Try to load configuration from the path specified in the environment variable."""

        if not config_path:
            return cls.example()

        return cls.load(config_path)

    def update(self, other: "PopulationRestoratorApiConfig") -> None:
        """Update current config attributes with the values from another UrbanAPIConfig instance."""
        for section in ("app", "db", "fileserver", "logging"):
            current_subconfig = getattr(self, section)
            other_subconfig = getattr(other, section)

            for param, value in other_subconfig.__dict__.items():
                if param in current_subconfig.__dict__:
                    setattr(current_subconfig, param, value)
