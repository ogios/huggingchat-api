from dataclasses import dataclass
from typing import List
from hugchat_api.core.Exceptions import FillDataException

from hugchat_api.utils import getUUID


@dataclass
class ModelConfig:
    """
    Generation Parameters
    """

    temperature: float
    top_p: float
    repetition_penalty: float
    top_k: int
    truncate: int
    watermark: bool
    max_new_tokens: int
    return_full_text: bool
    stop: List[str]


@dataclass
class RequestOptions:
    id: str
    """uuid"""
    response_id: str
    """uuid"""

    is_retry: bool
    use_cache: bool
    web_search_id: str


@dataclass
class RequestData:
    """
    Post request data (json format)
    """

    inputs: str
    """prompt string"""

    parameters: ModelConfig

    options: RequestOptions

    stream: bool
    """stream response?"""


def getDefaultData() -> RequestData:
    c = ModelConfig(
        temperature=0.9,
        top_p=0.95,
        repetition_penalty=1.2,
        top_k=50,
        truncate=1024,
        watermark=False,
        max_new_tokens=1024,
        return_full_text=False,
        stop=["</s>"],
    )
    o = RequestOptions(
        id=getUUID(),
        response_id=getUUID(),
        is_retry=False,
        use_cache=False,
        web_search_id="",
    )
    return RequestData(inputs="", parameters=c, options=o, stream=True)

def _fill(data: RequestData, ori: RequestData):
    prs = dir(ori)
    for key in prs:
        if getattr(data, key) is None:
            setattr(data, key, getattr(ori, key))
        else:
            if type(getattr(ori, key)) in [ModelConfig, RequestOptions]:
                if getattr(data, key) is None:
                    setattr(data, key, getattr(ori, key))
                else: 
                    setattr(data, key, _fill(getattr(data, key), getattr(ori,key)))
            else:
                raise FillDataException(f"unknow property `{key}` type: `{type(getattr(data, key))}`")
    return data


def fillData(data: RequestData) -> RequestData:
    ori = getDefaultData()
    if not data:
        return ori
    return _fill(data, ori)
        
