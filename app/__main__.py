import os
import tempfile
import typing as tp

import uvicorn

from app.utils import (
    PopulationRestoratorApiConfig,
)


def _run_uvicorn(configuration: dict[str, tp.Any]) -> tp.NoReturn:
    uvicorn.run(
        "app:app",
        **configuration,
    )


def main():
    config = PopulationRestoratorApiConfig.from_file_or_default()

    temp_yaml_config_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    config.dump(temp_yaml_config_path)
    temp_envfile_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    try:
        with open(temp_envfile_path, "w", encoding="utf-8") as env_file:
            env_file.write(f"CONFIG_PATH={temp_yaml_config_path}\n")
        uvicorn_config = {
            "host": config.app.host,
            "port": config.app.port,
            "log_level": config.logging.level.lower(),
            "env_file": temp_envfile_path,
        }
        if config.app.debug:
            try:
                _run_uvicorn(uvicorn_config | {"reload": True})
            except:  # pylint: disable=bare-except
                print("Debug reload is disabled")
                _run_uvicorn(uvicorn_config)
        else:
            _run_uvicorn(uvicorn_config)
    finally:
        if os.path.exists(temp_envfile_path):
            os.remove(temp_envfile_path)
        if os.path.exists(temp_yaml_config_path):
            os.remove(temp_yaml_config_path)


if __name__ == "__main__":
    try_load_envfile(os.environ.get("ENVFILE", ".env"))
    main()
