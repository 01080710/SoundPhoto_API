from routers.sensor.schema import WindDataResponse,NoiseDataResponse,CalibrationOptionsResponse,CalibrationItemResponse
from fastapi import APIRouter, Query ,Depends, HTTPException, Response,Path
from typing import Generator, Tuple ,Optional
from zoneinfo import  ZoneInfo
from datetime import datetime
from sqlalchemy import text
import io ,csv ,zipfile




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





### 取得校正紀錄areaids
@router.get("/calibrationoptions",summary='查詢條件內校正選單',response_model=CalibrationOptionsResponse)
def get_calibration_options(db: dict = Depends(get_dbs)):
    # 確保資料庫連線
    db_main = db['main']  # Session 物件

    data_query = text("""
        SELECT DISTINCT a.areaid
        FROM NoBuSystem_Mobile.dbo.areaids as a;
    """)

    try:
        data_result = db_main.execute(data_query).mappings().fetchall()
    except Exception as e:
        # 可以用 logger 來記錄錯誤訊息
        raise HTTPException(status_code=500, detail=f"取得校正選單錯誤：{str(e)}")
    
    return {
        # "total": total_count,
        "data": [dict(row) for row in data_result]
    }



### 取得校正紀錄總數據
@router.get("/calibrationdata",summary='查詢條件內校正數據',response_model=CalibrationItemResponse)
def get_calibrationdata(areaid:     str = Query(..., description="站號名稱，如 OTONO01"),
                        start_time: str = Query(..., description="開始時間，如 2025/09/22 00:00:00"),
                        end_time  : str = Query(..., description="結束時間，如 2025/09/23 00:00:00"),
                        limit: int = Query(50, ge=50, le=100),  # 每頁顯示的數據條數，介於 50 和 100 之間
                        page:  int = Query(1, ge=1),    # 頁碼，介於 1 和 30 之間
                        db: dict = Depends(get_dbs)):
    # 確保資料庫連線
    db_main = db['main']  # Session 物件
    offset = (page - 1) * limit


    # 查詢總數量
    count_query = text("""
        SELECT COUNT(*) AS total_count
            FROM NoBuSystem_Mobile.dbo.correction as c
            WHERE c.correctiondatetime >= :start_time 
            AND c.correctiondatetime <= :end_time 
            AND c.areaid = :areaid
    """)

    count_result = db_main.execute(count_query, {
        "start_time": start_time,
        "end_time"  : end_time,
        'areaid'    : areaid
    }).fetchone()

    total_count = count_result.total_count if count_result else 0



    # 查詢資料列
    data_query = text("""
        SELECT 
        c.id,
        c.areaid, 
        c.acohid,
        c.correctiondatetime,
        c.correctdB,
        c.operator,
        c.tempture,
        c.windspeed,
        c.noilabel,
        c.noimodel,
        c.noiseqno,
        c.noieffectdate,
        c.anelabel,
        c.anemodel,
        c.aneseqno,
        c.aneeffectdate,
        c.corlabel,
        c.cormodel,
        c.cordeqno,
        c.coreffectdate,
        c.compardate
        FROM NoBuSystem_Mobile.dbo.correction as c
        WHERE c.correctiondatetime >= :start_time AND c.correctiondatetime <= :end_time AND  c.areaid = :areaid
        ORDER BY correctiondatetime
        OFFSET :offset ROWS
        FETCH NEXT :limit ROWS ONLY;
    """)

    try:
        data_result = db_main.execute(data_query, {
            "start_time": start_time,
            "end_time": end_time,
            "offset": offset,
            "limit": limit,
            "areaid": areaid
        }).mappings().fetchall()
    except Exception as e:
        # 可以用 logger 來記錄錯誤訊息
        raise HTTPException(status_code=500, detail=f"取得校正數據錯誤：{str(e)}")

    return {
        "total": total_count,
        "data": [dict(row) for row in data_result]
    }



### 取得各類型檔案
@router.get("/download/{file_type}",summary='下載條件內校正檔案',response_model=WindDataResponse)
def get_data_file(file_type : str = Path(..., description="數據種類 : calibrationdata"),
                  areaid    : Optional[str] = Query(None, description="站號名稱，如 OTONO01"),
                  start_time: str = Query(..., description="開始時間，如 2025/05/10 15:20:00"),
                  end_time  : str = Query(..., description="結束時間，如 2025/05/10 15:30:00"),
                  db: dict = Depends(get_dbs)):

    ## 確保資料庫連線
    db_main = db['main']  # Session 物件
    
    # if file_type == 'winddata':
    #     query = text("""
    #             SELECT MeasurementDateTime, windspeed, tempture
    #             FROM NoBuSystem.dbo.windspeedData
    #             WHERE MeasurementDateTime >= :start_time AND MeasurementDateTime <= :end_time

    #             UNION ALL

    #             SELECT MeasurementDateTime, windspeed, tempture
    #             FROM NoBuSystem_His.dbo.windspeedData
    #             WHERE MeasurementDateTime >= :start_time AND MeasurementDateTime <= :end_time
    #             ORDER BY MeasurementDateTime;
    #     """)
    
    # elif file_type == 'noisedata':
    #     query = text("""
    #         SELECT MeasurementDateTime, LP, LAeq,Lmax,Lmin
    #         FROM NoBuSystem.dbo.noisedata
    #         WHERE MeasurementDateTime >= :start_time AND MeasurementDateTime <= :end_time

    #         UNION ALL

    #         SELECT MeasurementDateTime, LP, LAeq,Lmax,Lmin
    #         FROM NoBuSystem_His.dbo.noisedata
    #         WHERE MeasurementDateTime >= :start_time AND MeasurementDateTime <= :end_time
    #         ORDER BY MeasurementDateTime;
    #     """)

    if file_type == 'calibrationdata':
        query = text("""
            SELECT
            c.id,
            c.areaid, 
            c.acohid,
            c.correctiondatetime,
            c.correctdB,
            c.operator,
            c.tempture,
            c.windspeed,
            c.noilabel,
            c.noimodel,
            c.noiseqno,
            c.noieffectdate,
            c.anelabel,
            c.anemodel,
            c.aneseqno,
            c.aneeffectdate,
            c.corlabel,
            c.cormodel,
            c.cordeqno,
            c.coreffectdate,
            c.compardate
            FROM NoBuSystem_Mobile.dbo.correction as c
            WHERE c.correctiondatetime >= :start_time AND c.correctiondatetime <= :end_time AND  c.areaid = :areaid
            ORDER BY correctiondatetime;
        """)
    else:
        return {"message":'請輸入正確file_type'}
        

    try:
        if file_type == 'calibrationdata':
            result = db_main.execute(query, {
                "start_time": start_time,
                "end_time": end_time,
                "areaid": areaid
            }).mappings().fetchall()
        else:
            result = db_main.execute(query, {
                "start_time": start_time,
                "end_time": end_time,
            }).mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得zip檔案錯誤：{str(e)}")



    ## 產出csv並壓成zip
    column_names = result[0].keys() if result else [] # 取得欄位名稱

    
    csv_buffer = io.StringIO() # 將查詢結果寫入 CSV（用記憶體）
    writer = csv.writer(csv_buffer)
    writer.writerow(column_names)  # 寫入欄位名稱
    for row in result:
        writer.writerow([row[col] for col in column_names])
        # writer.writerow(row)
    
    
    def time_transfer(condition_time):  # 時間型態轉換
        dt = datetime.strptime(condition_time, '%Y/%m/%d %H:%M:%S')  
        return dt.strftime('%Y%m%d%H%M%S')
    
    zip_buffer = io.BytesIO()  # 轉成 bytes 並壓縮為 ZIP
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        dt = datetime.strptime(start_time, '%Y/%m/%d %H:%M:%S')  # 先字串轉 datetime
        zip_file.writestr(f"{file_type}({time_transfer(start_time)}~{time_transfer(end_time)}).csv", csv_buffer.getvalue().encode('utf-8-sig'))
    
    zip_buffer.seek(0)  # 將指標重置才能讀取

    
    filename = f"{file_type}_{datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y%m%d%H%M%S')}.zip"  # 建立下載檔案名稱（含日期）

    # 回傳 ZIP 檔案給前端
    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}",
                 "Access-Control-Allow-Origin": "*",
                 "Access-Control-Expose-Headers": "Content-Disposition"
                 }
    )


 


### 刪除校正紀錄數據
@router.delete("/{id}",summary='刪除條件內校正數據')#,response_model=CalibrationItemResponse)
def delete_calibrationdata(id: int,
                           db: dict = Depends(get_dbs)):
    
    # 確保資料庫連線
    db_main = db['main']  # Session 物件


    # 查詢資料列
    data_query = text("""
        DELETE c
        FROM NoBuSystem_Mobile.dbo.correction AS c
        WHERE c.id = :id;
    """)

    try:
        result = db_main.execute(data_query, {"id": id})
        db_main.commit()
        deleted_count = result.rowcount
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除校正數據錯誤：{str(e)}")

    return {
        "message": f"成功刪除 {deleted_count} 筆校正數據",
        "deleted_count": deleted_count
    }
