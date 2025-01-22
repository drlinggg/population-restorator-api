# todo desc

import abc


class TerritoriesService:

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    async def balance(self, territory_id: int):
        pass

    @abc.abstractmethod
    async def divide(self, territory_id: int):
        pass

    @abc.abstractmethod
    async def restore(self, territory_id: int):
        pass
