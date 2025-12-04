from pydantic import BaseModel, Field
from typing import List ,Optional,Dict




# 站號物件
class AreasItem(BaseModel):
    id : Optional[int] = None
    areaid: Optional[str] = None  # 允許為 None
    embeedip : Optional[str] = None  # 允許為 None

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
    areaid: Optional[str] = Field(None, description="站號名稱，如 OTONO01")
    areaname: Optional[str] = Field(None, description="站點名稱，如 林口文化二路")
    carsno: Optional[str] = Field(None, description="車牌號碼，如 9707-K0")
    lmax: Optional[str] = Field(None, description="噪音值（Lmax）")
    l90: Optional[str] = Field(None, description="背景音量（L90）")
    windspeed: Optional[str] = Field(None, description="瞬間風速（m/s）")
    tempture: Optional[str] = Field(None, description="氣溫（°C）")
    dba: Optional[str] = Field(None, description="管制標準（dBA）")
    fL90: Optional[str] = Field(None, description="校正後背景音量（fL90）")
    determination: Optional[str] = Field(None, description="判定結果：有效 / 無效 / NULL")

class MainExceedDataResponse(BaseModel):
    total: int = Field(..., description='資料總筆數')
    data: List[MainExceedDataItem] = Field(...,description='聲音照相主頁面資料列表')



# 聲音照相總數據物件 - 次頁面
class SecondExceedDataItem(BaseModel):

    # 事件資訊
    id: Optional[int] = Field(None, description='該筆資料唯一值')
    measurementdatetime: Optional[str] = Field(None, description="量測時間（格式：YYYY-MM-DD HH:MM:SS）")
    areaid: Optional[str] = Field(None, description="站號名稱，如 OTONO01")
    areaname: Optional[str] = Field(None, description="站點名稱，如 林口文化二路")
    carsno: Optional[str] = Field(None, description="車牌號碼，如 9707-K0")
    lmax: Optional[str] = Field(None, description="最大噪音值（Lmax）")
    l90: Optional[str] = Field(None, description="背景音量（L90）")
    tempture: Optional[str] = Field(None, description="氣溫（°C）")
    windspeed: Optional[str] = Field(None, description="風速（m/s）")
    
    # 判定結果
    noise: Optional[str] = Field(None, description="前後三秒是否有車：有車 / 無車 / NULL")
    wet: Optional[str] = Field(None, description="地面是否乾燥：地乾 / 地濕 / NULL")
    windlevel: Optional[str] = Field(None, description="風速是否小於 5 m/s：是 / 否 / NULL")
    rainday: Optional[str] = Field(None, description="最近降雨時間")
    determination: Optional[str] = Field(None, description="判定結果：有效 / 無效 / NULL")
    reason1: Optional[str] = Field(None, description="判定原因，如：通知到檢 / 直接開罰 / 非噪音車 / 無法判定 / 其他")
    reason2: Optional[str] = Field(None, description="判定原因，如：通知到檢 / 直接開罰 / 非噪音車 / 無法判定 / 其他")
    files: Optional[Dict[str, str]] = Field(None, description="包含 photo、crest、aicam、surcam 檔案 URL")

class SecondExceedDataResponse(BaseModel):
    data: List[SecondExceedDataItem] = Field(...,description='聲音照相次頁面資料列表')




# 聲音照相欲修改之數據物件
class ModifyExceedDataItem(BaseModel):

    noise: Optional[str] = Field(None, description="前後三秒是否有車：有車 / 無車 / NULL")
    wet: Optional[str] = Field(None, description="地面是否乾燥：地乾 / 地濕 / NULL")
    windlevel: Optional[str] = Field(None, description="風速是否小於 5 m/s：小於 / 大於 / NULL")
    rainday: Optional[str] = Field(None, description="最近降雨時間: 2000/01/01")
    determination: Optional[str] = Field(None, description="判定結果：有效 / 無效 / NULL")
    reason1: Optional[str] = Field(None, description="判定原因，如：'' / 通知到檢 / 直接開罰 / 非噪音車 / 無法判定 / 其他")
    reason2: Optional[str] = Field(None, description="判定原因，如：'' / 通知到檢 / 直接開罰 / 非噪音車 / 無法判定 / 其他")
    

# 聲音照相車牌修改
class ModifyCarsnoExceedDataItem(BaseModel):
    carsno: Optional[str] = Field(None, description="車牌號碼")
    