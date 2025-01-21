import abc

class TerritoriesService():

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    async def balance(self, territory_id: int):
        """todo"""

    @abc.abstractmethod
    async def divide(self, territory_id: int):
        """todo"""

    @abc.abstractmethod
    async def restore(self, territory_id: int):
        """todo"""
