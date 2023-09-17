from dataclasses import dataclass
from dataclasses_json import dataclass_json, DataClassJsonMixin
from typing import List

from hugchat_api.utils import getUUID

BASE_URL = "https://huggingface.co/chat"
BASE_CONVERSATION = f"{BASE_URL}/conversation"

@dataclass_json
@dataclass
class ModelConfig(DataClassJsonMixin):
    """
    Generation Parameters
    """

    temperature: float | None = None
    top_p: float | None = None
    repetition_penalty: float | None = None
    top_k: int | None = None
    truncate: int | None = None
    watermark: bool | None = None
    max_new_tokens: int | None = None
    return_full_text: bool | None = None
    stop: List[str] | None = None


@dataclass_json
@dataclass
class RequestOptions(DataClassJsonMixin):
    id: str | None = None
    """uuid"""
    response_id: str | None = None
    """uuid"""

    is_retry: bool | None = None
    use_cache: bool | None = None
    web_search_id: str | None = None


@dataclass_json
@dataclass
class RequestData(DataClassJsonMixin):
    """
    Post request data (json format)
    """

    inputs: str | None = None
    """prompt string"""

    parameters: ModelConfig | None = None

    options: RequestOptions | None = None

    stream: bool | None = None
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
        if key.startswith("__"): 
            continue
        if getattr(data, key) is None:
            setattr(data, key, getattr(ori, key))
        else:
            if type(getattr(ori, key)) in [ModelConfig, RequestOptions]:
                if getattr(data, key) is None:
                    setattr(data, key, getattr(ori, key))
                else: 
                    setattr(data, key, _fill(getattr(data, key), getattr(ori,key)))
    return data


def fillData(data: RequestData | None) -> RequestData:
    ori = getDefaultData()
    if not data:
        return ori
    return _fill(data, ori)
        
if __name__ == "__main__":
    c = ModelConfig(
        max_new_tokens=1024,
    )
    d = RequestData(parameters=c)
    d = fillData(d)
    print(d.to_json())
