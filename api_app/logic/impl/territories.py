from api_app.logic.territories import TerritoriesService
from api_app.utils import urban_api_config
from api_app.logic.impl.helpers import get_territories_tree

class TerritoriesServiceImpl(TerritoriesService):
    #todo desc

    def __init__(self):
        self.urban_api_config = urban_api_config

    async def balance(self, territory_id: int):
        #todo
        print(f"balance {territory_id}")

        #todo graphTerritories = 
        get_territories_tree(territory_id)
        pass

    async def divide(self, territory_id: int):
        #todo
        print(f"divide {territory_id}")
        pass

    async def restore(self, territory_id: int):
        #todo
        print(f"restore {territory_id}")
        pass


def get_territories_service() -> TerritoriesService:
    return TerritoriesServiceImpl()
