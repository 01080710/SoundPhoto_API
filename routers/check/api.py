from routers.check.schema import AreasResponse,AreanamesResponse,MainExceedDataResponse
from fastapi import APIRouter, Query ,Depends, HTTPException
from typing import Generator, Tuple ,Optional 
from fastapi.responses import FileResponse
from pathlib import Path as FilePath
from datetime import datetime
from sqlalchemy import text
import csv,os,time





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


# 檔案影片相對路徑
BASE_PATH = FilePath(r"\\192.168.1.192\雲中心事件檔案磁碟\EVENTEXPORT")


### 取得站號清單
@router.get("/areaids",summary='站號清單',response_model=AreasResponse)
def get_areaids(db: dict = Depends(get_dbs)):

    # 確保資料庫連線
    db_main = db['main']  # Session 物件


    # ✅ 查詢清單
    count_query = text("""
            SELECT 
            a.id,
            a.areaid
            FROM NoBuSystem_Mobile.dbo.areaids as a
    """)

    try:
        data_result = db_main.execute(count_query).mappings().all()
    except Exception as e:
        # 可以用 logger 來記錄錯誤訊息
        raise HTTPException(status_code=500, detail=f"取得站號清單錯誤：{str(e)}")


    return {
        "data": [dict(row) for row in data_result]
    }





### 取得站點清單
@router.get("/areanames",summary='站點清單',response_model=AreanamesResponse)
def get_areanames(areaid:     str = Query(..., description="站號名稱，如 OTONO01"),
                  db:        dict = Depends(get_dbs)):

    # 確保資料庫連線
    db_main = db['main']  # Session 物件


    # ✅ 查詢清單
    data_query = text("""
            SELECT 
    
            b.areaid,
            a.areaname
             
            FROM NoBuSystem_Mobile.dbo.areas as a
            JOIN NoBuSystem_Mobile.dbo.areaids as b on a.embeedip =  b.embeedip
            WHERE b.areaid = :areaid;
    """)

    try:
        data_result = db_main.execute(data_query, {
            "areaid": areaid,
        }).mappings().fetchall()

    except Exception as e:
        # 可以用 logger 來記錄錯誤訊息
        raise HTTPException(status_code=500, detail=f"取得站點清單錯誤：{str(e)}")


    return {
        "data": [dict(row) for row in data_result]
    }




### 取得聲音照相主頁面總數據
@router.get("/datas",summary='主頁面稽查紀錄數據',response_model=MainExceedDataResponse)
def get_datas(areaid:     str = Query(..., description="站號名稱，如 OTONO01"),
                   areaname:   str = Query(..., description="站點名稱，如 林口文化二路"),
                   carsno:     Optional[str] = Query(None, description="車牌號碼，如 9707-K0"),
                   start_time: Optional[str] = Query(None, description="開始時間，如 2025/05/10 15:20:00"),
                   end_time  : Optional[str] = Query(None, description="結束時間，如 2025/05/10 15:30:00"),
                   limit: int  = Query(50, ge=50, le=100),  # 每頁顯示的數據條數，介於 50 和 100 之間
                   page:  int  = Query(1, ge=1),             # 頁碼，介於 1 和 30 之間
                   db:    dict = Depends(get_dbs)):
   


    # 確保資料庫連線
    db_main = db['main']  # Session 物件
    offset = (page - 1) * limit


    # 添加動態查詢條件
    where_clause = ["e.areaid  = :areaid" ,"e.areaname = :areaname"]
    params = {
        "areaid"  : areaid,
        "areaname": areaname,
        }

    if carsno:
        where_clause.append("e.carsno  = :carsno")
        params['carsno'] = carsno
    if start_time:
        where_clause.append("e.measurementdatetime  >= :start_time")
        params['start_time'] = start_time
    if end_time:
        where_clause.append("e.measurementdatetime  <= :end_time")
        params['end_time'] = end_time

    where_sql = " AND ".join(where_clause)
    print(where_sql)

    # ✅ 查詢總筆數
    count_query = text(f"""
            SELECT COUNT(*) AS total_count
            FROM (
                SELECT 
                e.id,
                e.measurementdatetime, 
                e.carsno
                FROM NoBuSystem_Mobile.dbo.exceed as e
                WHERE {where_sql} AND determination = '有效'
            ) AS combined
            """)
    
    try:
        count_result = db_main.execute(count_query, params).fetchone()
        print(count_result)
        total_count = count_result.total_count if count_result else 0
    except Exception as e:
        raise HTTPException(status_code=500,detail=f'計算筆數錯誤:{str(e)}')


    # ✅ 查詢分頁資料
    params['offset'] = offset
    params['limit']  = limit

    data_query = text(f"""
        SELECT 
        e.id,
        e.measurementdatetime, 
        e.carsno
        
        
        FROM NoBuSystem_Mobile.dbo.exceed as e
        WHERE {where_sql} AND determination = '有效'
        ORDER BY measurementdatetime
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """)


    try:
        data_result = db_main.execute(data_query, params).mappings().fetchall()
        
    except Exception as e:
        # 可以用 logger 來記錄錯誤訊息
        raise HTTPException(status_code=500, detail=f"取得聲音照相錯誤：{str(e)}")


    return {
        "total": total_count,
        "data": [dict(row) for row in data_result]
    }



### 取得產製紀錄表數據
@router.post("/{id}",summary='傳遞id回傳產製紀錄表檔案')
def post_datas(id:     str ,
               db:    dict = Depends(get_dbs)):
   


    # 確保資料庫連線
    db_main = db['main']  # Session 物件
    
    pass
    # 取得
    data_query = text("""
            SELECT 
            e.id,
            e.areaid,
            e.measurementdatetime, 
            e.carsno
            FROM NoBuSystem_Mobile.dbo.exceed as e
            WHERE id = :id AND determination = '有效';
    """)

    
    result = db_main.execute(data_query, {
        "id": id,
    }).mappings().fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="查無資料")
    
    # 處理每筆資料
    for row in result:
        measurement = row['measurementdatetime']
        carsno = row['carsno']

        if isinstance(measurement, str):
            dt = datetime.strptime(measurement, "%Y/%m/%d %H:%M:%S")
        else:
            dt = measurement  # 已是 datetime 物件

        # 格式化組件
        y = f"{dt.year:04}"
        mo = f"{dt.month:02}"
        d = f"{dt.day:02}"
        h = f"{dt.hour:02}"
        mi = f"{dt.minute:02}"
        s = f"{dt.second:02}"

        filename = f"{y}{mo}{d}{h}{mi}{s}_{carsno}"
        txt_path = f"D:/EXPORTEXCELL/{filename}_稽查紀錄工作單.xlsx"
        csv_path = f"D:/EXPORTEXCELL/{filename}.csv"
        
        
        # 如果 .txt 檔案已存在 → 直接回傳
        if os.path.exists(txt_path):
            return FileResponse(
            txt_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{filename}.xlsx"
        )

        # 若無 .txt，先產生 CSV
        try:
            with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
                for r in result:
                    line = "".join([f"{k}={v}\n" for k,v in r.items()])
                    f.write(line)
            print(f"✅ 已寫入 CSV：{csv_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CSV 產生錯誤：{str(e)}")


        # ✅ 等待 C# 程式生成 txt 檔案（最多等 30 秒）
        wait_time = 0
        while not os.path.exists(txt_path) and wait_time < 5:
            time.sleep(1)
            wait_time += 1
            print(f"⏳ 等待 C# 產生 {filename}.xlsx... {wait_time}s")

        # 若超時仍未出現
        if not os.path.exists(txt_path):
            raise HTTPException(status_code=504, detail=f"等待 {filename}.xlsx 超時（未被 C# 轉換）")

        print(f"✅ 偵測到 XLSX 檔案：{txt_path}")



        # 回傳 Excel 檔案
        return FileResponse(
            txt_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{filename}.xlsx"
        )

    

