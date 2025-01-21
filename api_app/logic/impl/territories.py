from api_app.logic.territories import TerritoriesService

class TerritoriesServiceImpl(TerritoriesService):
    #todo desc

    #todo add api_config

    async def balance(self, territory_id: int):
        print(f"balance {territory_id}")
        pass

    async def divide(self, territory_id: int):
        print(f"divide {territory_id}")
        pass

    async def restore(self, territory_id: int):
        print(f"restore {territory_id}")
        pass

def get_territories_service() -> TerritoriesService:
    #todo add api_config
    return TerritoriesServiceImpl()
