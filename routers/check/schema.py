from pydantic import BaseModel, Field
from typing import List ,Optional,Dict




# 站號物件
class AreasItem(BaseModel):
    id : Optional[int] = None
    areaid: Optional[str] = None  # 允許為 None

class AreasResponse(BaseModel):
    data: List[AreasItem]





# 站點物件
class AreanamesItem(BaseModel):
    areaid  : Optional[str] = None
    areaname: Optional[str] = None  # 允許為 None
    

class AreanamesResponse(BaseModel):
    data: List[AreanamesItem]





# 聲音照相總數據物件 - 主頁面
class MainExceedDataItem(BaseModel):

    # 事件資訊
    id: Optional[int] = Field(None, description='該筆資料唯一值')
    measurementdatetime: Optional[str] = Field(None, description="量測時間（格式：YYYY-MM-DD HH:MM:SS）")
    carsno: Optional[str] = Field(None, description="車牌號碼，如 9707-K0")
    # determination: Optional[str] = Field(None, description="判定結果：有效 / 無效 / NULL")

class MainExceedDataResponse(BaseModel):
    total: int = Field(..., description='資料總筆數')
    data: List[MainExceedDataItem] = Field(...,description='聲音照相主頁面資料列表')


