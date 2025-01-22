# todo desc

from api_app.logic.impl.helpers import get_territories_tree
from api_app.logic.territories import TerritoriesService


class TerritoriesServiceImpl(TerritoriesService):
    # todo desc

    async def balance(self, territory_id: int):
        # todo
        # debug f balance {id}
        print(f"balance {territory_id}")
        """geojson something = """
        await get_territories_tree(territory_id)
        pass

    async def divide(self, territory_id: int):
        # todo
        print(f"divide {territory_id}")
        pass

    async def restore(self, territory_id: int):
        # todo
        print(f"restore {territory_id}")
        pass


def get_territories_service() -> TerritoriesService:
    return TerritoriesServiceImpl()
