from pydantic import BaseModel, Field
from typing import List ,Optional,Dict




# 站號物件
class AreasItem(BaseModel):
    id : Optional[int] = None
    areaid: Optional[str] = None  # 允許為 None
    embeedip: Optional[str] = None  # 允許為 None

class AreasResponse(BaseModel):
    data: List[AreasItem]





