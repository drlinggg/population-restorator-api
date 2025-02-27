import os
import tempfile
import typing as tp

import uvicorn

from app.utils import ApiConfig, AppConfig, LoggingConfig, PopulationRestoratorApiConfig


def _run_uvicorn(configuration: dict[str, tp.Any]) -> tp.NoReturn:
    # todo make debug mode with reload = true/false
    uvicorn.run(
        "app:app",
        reload=True,
        **configuration,
    )


def main():
    debug = (True,)
    config_path = "population-restorator-api-config.yaml"
    logger_verbosity = None

    config = PopulationRestoratorApiConfig.load(config_path)
    logging_section = config.logging if logger_verbosity is None else LoggingConfig(level=logger_verbosity)

    config = PopulationRestoratorApiConfig(
        app=AppConfig(
            host=config.app.host,
            port=config.app.port,
            debug=config.app.debug,
            name=config.app.name,
        ),
        db=config.db,
        logging=logging_section,
        urban_api=ApiConfig(
            host=config.urban_api.host,
            port=config.urban_api.port,
            api_key=config.urban_api.api_key,
            base_path=config.urban_api.base_path,
        ),
        socdemo_api=ApiConfig(
            host=config.socdemo_api.host,
            port=config.socdemo_api.port,
            api_key=config.socdemo_api.api_key,
            base_path=config.socdemo_api.base_path,
        ),
    )

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
