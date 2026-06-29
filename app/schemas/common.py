from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class MessageResponse(BaseModel):
    message: str


class DataResponse(BaseModel, Generic[DataT]):
    data: DataT
