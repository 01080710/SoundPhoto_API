from fastapi import APIRouter, Depends, HTTPException, Path
from routers.edgesite.schema import AreasResponse
from typing import Generator, Tuple 
from sqlalchemy import text
from pathlib import Path






router = APIRouter()



# 取得資料庫 Session 的依賴注入
def get_dbs() -> Generator[Tuple, None, None]:
    from db import SessionMain, SessionHis
    db_main = SessionMain()
    db_his = SessionHis()
    try:
        yield {"main": db_main, "his": db_his}
    finally:
        db_main.close()
        db_his.close()




### 取得邊緣端IP清單
@router.get("",summary='邊緣端IP清單',response_model=AreasResponse)
def get_areaids(db: dict = Depends(get_dbs)):

    # 確保資料庫連線
    db_main = db['main']  # Session 物件


    # ✅ 查詢清單
    count_query = text("""
            SELECT 
            a.id,
            a.areaid,
            a.embeedip 
            FROM NoBuSystem_Mobile.dbo.areaids as a
    """)

    try:
        data_result = db_main.execute(count_query).mappings().all()
    except Exception as e:
        # 可以用 logger 來記錄錯誤訊息
        raise HTTPException(status_code=500, detail=f"取得邊緣端IP清單錯誤：{str(e)}")


    return {
        "data": [dict(row) for row in data_result]
    }





