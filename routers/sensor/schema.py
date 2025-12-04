from pydantic import BaseModel
from typing import List,Optional



# 風速物件
class WindDataItem(BaseModel):
    MeasurementDateTime: Optional[str] = None  # 允許為 None
    windspeed: Optional[float] = None  
    tempture:  Optional[float] = None  

class WindDataResponse(BaseModel):
    total: int
    data: List[WindDataItem]





# 噪音物件
class NoiseDataItem(BaseModel):
    MeasurementDateTime: Optional[str] = None
    LP:   Optional[float] = None
    LAeq: Optional[float] = None
    Lmax: Optional[float] = None
    Lmin: Optional[float] = None

class NoiseDataResponse(BaseModel):
    total: int
    data: List[NoiseDataItem]





# 校正紀錄選單物件
class AreaIDModel(BaseModel):
    areaid: Optional[str] = None  # 允許為 None
    
class CalibrationOptionsResponse(BaseModel):
    data: List[AreaIDModel]




# 校正紀錄數據物件
class CalibrationItem(BaseModel):
    id: Optional[int] = None  # 允許為 None
    areaid: Optional[str] = None  # 允許為 None
    acohid: Optional[str] = None  
    correctiondatetime: Optional[str] = None  
    correctdB: Optional[str] = None  
    operator: Optional[str] = None  
    tempture: Optional[str] = None  
    windspeed: Optional[str] = None  
    noilabel: Optional[str] = None  
    noimodel: Optional[str] = None  
    noiseqno: Optional[str] = None  
    noieffectdate: Optional[str] = None  
    anelabel: Optional[str] = None  
    anemodel: Optional[str] = None  
    aneseqno: Optional[str] = None  
    aneeffectdate: Optional[str] = None 
    corlabel: Optional[str] = None  
    cormodel: Optional[str] = None  
    cordeqno: Optional[str] = None  
    coreffectdate: Optional[str] = None  
    compardate: Optional[str] = None  
    # drawing: Optional[str] = None  

class CalibrationItemResponse(BaseModel):
    total: int
    data: List[CalibrationItem]
