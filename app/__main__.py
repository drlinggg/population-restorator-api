import os
import tempfile
import typing as tp

import uvicorn

from app.utils import ApiConfig, AppConfig, DBConfig, PopulationRestoratorApiConfig, RedisQueueConfig


def _run_uvicorn(configuration: dict[str, tp.Any]) -> tp.NoReturn:
    uvicorn.run(
        "app:app",
        **configuration,
    )


def main():
    # it does triple reading rn but i dont sure if its bad
    config = PopulationRestoratorApiConfig.from_file_or_default()
    logging_section = config.logging

    config = PopulationRestoratorApiConfig(
        app=AppConfig(
            host=config.app.host,
            port=config.app.port,
            debug=config.app.debug,
            name=config.app.name,
        ),
        db=DBConfig(
            host=config.db.host,
            port=config.db.port,
            database=config.db.database,
            user=config.db.user,
            password=config.db.password,
            pool_size=config.db.pool_size,
        ),
        redis_queue=RedisQueueConfig(
            host=config.redis_queue.host,
            port=config.redis_queue.port,
            db=config.redis_queue.db,
            queue_name=config.redis_queue.queue_name,
        ),
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
