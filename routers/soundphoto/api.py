from routers.soundphoto.schema import AreasResponse,AreanamesResponse,MainExceedDataItem,MainExceedDataResponse,SecondExceedDataResponse,ModifyExceedDataItem,ModifyCarsnoExceedDataItem
from fastapi import APIRouter, Query ,Depends, HTTPException, Path, Response ,Body
from typing import Generator, Tuple ,Optional 
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw,ImageFont
import io ,csv ,zipfile, re, shutil, os
from pathlib import Path as FilePath
from zoneinfo import  ZoneInfo
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import text
from io import BytesIO
import pandas as pd
import chardet


load_dotenv()



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
# BASE_PATH = FilePath(r"\\192.168.1.192\雲中心事件檔案磁碟\EVENTEXPORT")
BASE_PATH = FilePath(r"Z:\\EVENTEXPORT")


### 取得站號清單
@router.get("/areaids",summary='站號清單',response_model=AreasResponse)
def get_areaids(db: dict = Depends(get_dbs)):

    # 確保資料庫連線
    db_main = db['main']  # Session 物件


    # ✅ 查詢清單
    count_query = text("""
            WITH latest AS (
                SELECT 
                    id,
                    areaid,
                    embeedip,
                    ROW_NUMBER() OVER (PARTITION BY areaid ORDER BY id DESC) AS rn
                FROM NoBuSystem_Mobile.dbo.areaids
            )
            SELECT id, areaid ,embeedip
            FROM latest
            WHERE rn = 1;
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
            WITH latest AS (
                SELECT 
                    b.areaid,
                    a.areaname,
                    ROW_NUMBER() OVER (
                        PARTITION BY b.areaid, a.areaname 
                        ORDER BY b.id DESC
                    ) AS rn
                FROM NoBuSystem_Mobile.dbo.areas AS a
                JOIN NoBuSystem_Mobile.dbo.areaids AS b 
                    ON a.embeedip = b.embeedip
            )
            SELECT 
                areaid,
                areaname
            FROM latest
            WHERE rn = 1;
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
@router.get("/datas/main",summary='主頁面聲音照相數據',response_model=MainExceedDataResponse)
def get_main_datas(areaid:     str = Query(..., description="站號名稱，如 OTONO01"),
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
        "areaname": areaname
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
                *
                FROM NoBuSystem_Mobile.dbo.exceed as e
                WHERE {where_sql}
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
        e.areaid,
        e.areaname,
        e.carsno,
        e.lmax,
        e.l90,
        e.windspeed,
        e.tempture,
        e.dba,
        e.fL90,
        e.determination
        FROM NoBuSystem_Mobile.dbo.exceed as e
        WHERE {where_sql}
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


### 取得各類型檔案
@router.get("/datas/main/download/{file_type}",summary='下載條件內校正檔案',response_model=MainExceedDataItem)
def get_data_file(file_type : str = Path(..., description="數據種類 : comparenoisedata"),
                  areaid    : str = Query(..., description="站號名稱，如 OTONO01"),
                  areaname    : str = Query(..., description="站號名稱，如 林口文化二路"),
                  start_time: str = Query(..., description="開始時間，如 2025/08/01 15:20:00"),
                  end_time  : str = Query(..., description="結束時間，如 2025/08/31 15:30:00"),
                  db: dict = Depends(get_dbs)):

    ## 確保資料庫連線
    db_main = db['main']  # Session 物件
    

    if file_type == 'comparenoisedata':
        query = text("""
            SELECT
            e.id,
            e.measurementdatetime, 
            e.areaid,
            e.areaname,
            e.carsno,
            e.lmax,
            e.l90,
            e.windspeed,
            e.tempture,
            e.dba,
            e.fL90,
            e.determination
            FROM NoBuSystem_Mobile.dbo.exceed as e
            WHERE e.measurementdatetime  >= :start_time 
                     AND e.measurementdatetime  <= :end_time 
                     AND e.areaid  = :areaid 
                     AND e.areaname  = :areaname
            ORDER BY e.measurementdatetime;
        """)
    else:
        return {"message":'請輸入正確file_type'}
        

    try:
        if file_type == 'comparenoisedata':
            result = db_main.execute(query, {
                "start_time": start_time,
                "end_time": end_time,
                "areaid": areaid,
                "areaname": areaname
            }).mappings().fetchall()
            print(result)
        else:
            result = db_main.execute(query, {
                "start_time": start_time,
                "end_time": end_time,
            }).mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得zip檔案錯誤：{str(e)}")



    ## 產出csv並壓成zip
    
    column_names = result[0].keys() if result else [] # 取得欄位名稱
    print(column_names)
    
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

### 取得聲音照相次頁面總數據
@router.get("/datas/second/{id}",summary='次頁面聲音照相數據',response_model=SecondExceedDataResponse)
def get_second_datas(id:     int ,
                     db:    dict = Depends(get_dbs)):
        

    # 確保資料庫連線
    db_main = db['main']  # Session 物件
    

    # 添加動態查詢條件
    where_clause = ["e.id  = :id"]
    where_sql = " AND ".join(where_clause)

    params = {
        "id"  : int(str(id).strip()),
    }


    # ✅ 查詢分頁資料
    data_query = text(f"""
        SELECT 
        e.id,
        e.measurementdatetime, 
        e.areaid,
        e.areaname,
        e.carsno,
        e.lmax,
        e.l90,
        e.tempture,
        e.windspeed,
        e.noise,
        e.wet,
        e.windlevel,              
        e.rainday,
        e.determination,
        e.reason        
        FROM NoBuSystem_Mobile.dbo.exceed as e
        WHERE {where_sql}
        ORDER BY measurementdatetime
    """)

    try:
        data_result = db_main.execute(data_query,params).mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得聲音照相錯誤：{str(e)}")


    # 拆解reason => reason1 + reason2
    process_data = []
    exclude_condition = [None,'null','','無效']
    for row in data_result:
        row_dict = dict(row)
        reason = row_dict.get('reason','')
        if reason not in exclude_condition and ':' in reason:
            reason1,reason2 =  reason.split(':', 1)
            row_dict['reason1'] = reason1
            row_dict['reason2'] = reason2
        else:
            row_dict['reason1'] = ''
            row_dict['reason2'] = ''
        
        # 檔案路徑組合邏輯
        measurement = row_dict.get('measurementdatetime')
        carsno = row_dict.get('carsno')
        areaid = str(row_dict.get('areaid'))  # 確保是字串

        if measurement and carsno and areaid:
            try:
                # 轉成 datetime
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

                
                # ✅ 設定你的 HTTP URL 前綴（這要對應 Nginx 或 FastAPI 提供的靜態目錄）
                ip = os.getenv("PublicIP")
                BASE_URL = f"http://{ip}:8010/soundphoto/download"

                row_dict["files"] = {
                    "photo": f"{BASE_URL}/photo/{areaid}/{y}/{mo}/{d}/{filename}",
                    "crest": f"{BASE_URL}/crest/{areaid}/{y}/{mo}/{d}/{filename}",
                    "aicam": f"{BASE_URL}/aicam/{areaid}/{y}/{mo}/{d}/{filename}",
                    "surcam": f"{BASE_URL}/surcam/{areaid}/{y}/{mo}/{d}/{filename}"
                }

            except Exception as e:
                # 若轉換過程出錯，就留空
                row_dict["files"] = {}

        else:
            row_dict["files"] = {}

        process_data.append(row_dict)
      

    return {"data": process_data}




# 檔案下載形式
@router.get("/download/{file_type}/{areaid}/{year}/{month}/{day}/{filename}")
def download_file(file_type: str, areaid: str, year: str, month: str, day: str, filename: str):
    folder_map = {
        "photo": "EVENTPHOTO",
        "crest": "CREST",
        "aicam": "EVENTIMAGE/AICAMMP4",
        "surcam": "EVENTIMAGE/SURCAMMP4"
    }

    if file_type not in folder_map:
        raise HTTPException(status_code=400, detail="無效的檔案類型")

    # 副檔名對應
    ext_map = {
        "photo": ".jpg",
        "crest": ".png",
        "aicam": ".mp4",
        "surcam": ".mp4"
    }

    subfolder = folder_map[file_type]
    ext = ext_map[file_type]

    file_path = BASE_PATH / areaid / year / month / day / filename / subfolder / (filename + ext)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"找不到檔案類型: {subfolder}")

    media_type_map = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".mp4": "video/mp4"
    }
    media_type = media_type_map[ext]

    return FileResponse(str(file_path), media_type=media_type,filename=file_path.name)




### 撰寫修改判定結果欄位
@router.put("/{id}",summary='更新欲異動欄位')
def id_modify(id: int,
              payload: ModifyExceedDataItem,
              db: dict = Depends(get_dbs)):
    

    # 取得資料表
    db_main = db['main']  # Session 物件

    update_fields = payload.dict(exclude_unset=True)

    # reason => reason1 + reason2
    reason1 = update_fields.pop("reason1", None)
    reason2 = update_fields.pop("reason2", None)
    if reason1 is not None or reason2 is not None: 
        r1 = reason1 or ''
        r2 = reason2 or ''
        update_fields["reason"] = f"{r1}:{r2}"

    # ✅ 沒有任何欄位要更新
    if not update_fields:
        raise HTTPException(status_code=400, detail="請提供至少一個欄位進行更新。")
    

    # ✅ 動態組合 SQL SET 子句
    set_clauses = [f"{key} = :{key}" for key in update_fields.keys()]
    set_sql = ", ".join(set_clauses)


    # ✅ 最終 SQL 組合
    update_sql = text(f"""
        UPDATE NoBuSystem_Mobile.dbo.exceed
        SET {set_sql}
        WHERE id = :id
    """)

    # 加上 id 作為條件參數
    update_fields['id'] = id

    try:
        result = db_main.execute(update_sql, update_fields)
        db_main.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失敗：{str(e)}")

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"找不到 id 為 {id} 的資料。")

    return {
        "message": f"id={id} 的資料已成功更新。",
        "updated_fields": list(update_fields.keys())
    }
    





# 重壓照片函式
def update_carsno_photo(photo_path:str ,new_carsno:str):
    # 設定矩形位置與大小（對應 C# 的 RectangleF(180, 0, 400, 50)）
    
    
    # 字型大小（對應 C# 的 30）
    font_size = 32
    
    
    # 載入圖片
    # from fastapi import Path
    photo = photo_path
    with Image.open(photo) as im:
        # 轉成 RGBA 以確保可以用透明或顏色繪製
        im = im.convert("RGBA")
        width, height = im.size
        # 建立 draw 物件
        draw = ImageDraw.Draw(im)
        rect_x = 0
        rect_y = 0
        rect_w = width
        rect_h = 100
        rect_box = (rect_x, rect_y, rect_x + rect_w, rect_y + rect_h)
            
    
    font = None
    if font is None:
        # 嘗試常見系統字型位置（Windows / macOS / Linux）
        tried = False
        for candidate in [
            "C:/Windows/Fonts/msjhbd.ttc",
            "arialbd.ttf",  # Windows / 若系統有設定
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # 常見 Linux
            "/Library/Fonts/Arial.ttf",  # macOS
        ]:
            try:
                font = ImageFont.truetype(candidate, font_size)
                tried = True
                break
            except Exception:
                continue
        if not tried:
            # fallback 到內建字型（但內建字型可能不支援中文）
            font = ImageFont.load_default()
            print("警告：使用 fallback 字型（ImageFont.load_default()），可能不支援中文顯示或大小不同。")
    
    # 先畫黑色矩形覆蓋原標註區域
    draw.rectangle(rect_box, fill=(0, 0, 0, 255))
    
    
    # 準備文字  & 計算矩形中心點
    text = new_carsno
    
    # 繪製文字（黃色）
    draw.text((0, 0), text, font=font, fill=(255, 255, 0, 255))

    # 匯出檔案
    im.convert("RGB").save(photo_path)


# 重塑exceed檔案
def reshape_exceedfile(filepath: str, new_carsno: str):
    filepath = FilePath(filepath)
    with open(filepath, "rb") as f:
        enc = chardet.detect(f.read())
    encoding = enc["encoding"]


    df = pd.read_csv(filepath, encoding=encoding)


    if '車號' not in df.columns:
        raise KeyError("CSV 檔案找不到 '車號' 欄位")

    old_carsno = df.at[0, '車號']     # df['車號'][0] 的更安全寫法
    df['車號'] = df['車號'].replace(old_carsno, new_carsno)
    df.drop('Unnamed: 10',axis=1,inplace=True)
    
    # --- 寫回 CSV ---
    df.to_csv(filepath, encoding=encoding, index=False)

    print(f"✔ 已將車號由 {old_carsno} → {new_carsno}")
    print(f"✔ 已覆寫檔案：{filepath}")


### 撰寫修改車牌號碼邏輯(包含更改資料庫及檔名還有壓照片)
@router.put("/{id}/{modify_carsno}",summary='更新車牌號碼欄位')
def carsno_modify(id    : int ,
                  modify_carsno: str,
                  payload: ModifyCarsnoExceedDataItem = Body(...),
                  db: dict = Depends(get_dbs)):
    
    # 讀取資料庫查找 & 添加動態查詢條件
    db_main = db['main']  # Session 物件
    where_clause = ["e.id  = :id"]
    where_sql = " AND ".join(where_clause)
    params = {
        "id"  : int(str(id).strip()),
    }

    data_query = text(f"""
        SELECT 
        *
        FROM NoBuSystem_Mobile.dbo.exceed as e
        WHERE {where_sql}
        ORDER BY measurementdatetime
    """)

    try:
        data_result = db_main.execute(data_query,params).mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"透由id取得時間錯誤：{str(e)}")


    # 先行解析時間 & 車牌號碼
    for row in data_result:
        row_dict = dict(row)
        measurement = row_dict.get('measurementdatetime','').strip()
        unit   = str(row_dict.get('unit','')).strip()
        areaid = str(row_dict.get('areaid','')).strip()
        areaname = str(row_dict.get('areaname','')).strip()
        carsno = str(row_dict.get('carsno','')).strip()
        lmax   = str(row_dict.get('lmax','')).strip()
        l90    = str(row_dict.get('l90','')).strip()
        tempture = str(row_dict.get('tempture','')).strip()
        windspeed = str(row_dict.get('windspeed','')).strip()
    

    try:
        if isinstance(measurement, str):
            dt = datetime.strptime(measurement, "%Y/%m/%d %H:%M:%S")
        else:
            dt = measurement
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"時間格式解析失敗：{str(e)}")

    
    # 格式化時間欄位已找到目標檔案
    y = f"{dt.year:04}"
    mo = f"{dt.month:02}"
    d = f"{dt.day:02}"
    h = f"{dt.hour:02}"
    mi = f"{dt.minute:02}"
    s = f"{dt.second:02}"

    sourcefile = f"{y}{mo}{d}{h}{mi}{s}_{carsno}"
    targetfile = f"{y}{mo}{d}{h}{mi}{s}_{modify_carsno}"
    
    print(measurement,'\n',carsno,'\n',modify_carsno,'\n',sourcefile)
    

    # 找到相對路徑路複製一份檔案並修改檔案之名稱
    source_path = BASE_PATH / areaid / y / mo / d / sourcefile
    target_path = BASE_PATH / areaid / y / mo / d / targetfile
    targer_csv_path   = target_path / 'EVENTROWDATA' / 'exceed.csv'
    target_image_path = target_path / 'EVENTPHOTO'/ (targetfile + '.jpg')
    
    if not source_path.exists():
        raise FileNotFoundError(f"來源資料夾不存在: {source_path}")
    if target_path.exists():
        raise FileExistsError(f"目標資料夾已存在: {target_path}")


    try:
        shutil.copytree(source_path, target_path)
        print(f"資料夾已複製到: {target_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"複製資料夾失敗：{str(e)}")

    
    def rename_files_in_folder(target_path: Path, old_carsno: str, new_carsno: str):
        if not target_path.exists():
            raise FileNotFoundError(f"資料夾不存在: {target_path}")

        for file in target_path.rglob("*"):
            if file.is_file() and old_carsno in file.name:
                try:
                    new_name = file.name.replace(old_carsno, new_carsno)
                    new_file_path = file.with_name(new_name)
                    file.rename(new_file_path)
                    print(f"✔️ 已重新命名：{file.name} → {new_name}")
                except Exception as e:
                    print(f"⚠️ 檔案重命名失敗：{file.name}，錯誤：{e}")

    try:
        rename_files_in_folder(target_path, old_carsno = carsno, new_carsno = modify_carsno)
        reshape_exceedfile(targer_csv_path ,modify_carsno)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料夾檔案處理失敗：{str(e)}")
    
    # 重壓照片
    multi_texts = f"""日期時間: {measurement}     單位: {unit}     站號: {areaid}     地點: {areaname}\r
車號: {modify_carsno}     噪音值: {lmax} dB(A)    背景噪音: {l90} dB(A)    溫度: {tempture} °C    風速: {windspeed} m/s"""

    try:
        update_carsno_photo(target_image_path ,multi_texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"圖片壓製失敗：{str(e)}")


    # 更改資料庫carsno欄位
    update_fields = payload.dict(exclude_unset=True)
    update_fields['carsno'] = modify_carsno
    update_fields['id'] = id

    update_sql = text(f"""
        UPDATE NoBuSystem_Mobile.dbo.exceed
        SET carsno = :carsno
        WHERE id = :id
    """)

    try:
        result = db_main.execute(update_sql, update_fields)
        db_main.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料庫更新失敗：{str(e)}")

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"找不到 id 為 {id} 的資料。")


    return {
        "code": id,
        "message": f"車牌號碼已成功更新為: {modify_carsno}",
        "file": f"資料夾檔案路徑已成功更新為: {target_path}"
    }
   
   


### 事件檔案匯出
@router.get("/export/{id}",summary='下載指定車號資料夾 ZIP')
def get_export_datas(id:     int ,
                     db:    dict = Depends(get_dbs)):
    
    # 讀取資料庫並塞選日期、車號
    db_main = db['main']  # Session 物件
    where_clause = ["e.id  = :id"]
    where_sql = " AND ".join(where_clause)
    params = {
        "id"  : int(str(id).strip()),
    }

    data_query = text(f"""
        SELECT 
        e.id,
        e.areaid,
        e.measurementdatetime, 
        e.carsno
        FROM NoBuSystem_Mobile.dbo.exceed as e
        WHERE {where_sql}
        ORDER BY measurementdatetime
    """)

    try:
        data_result = db_main.execute(data_query,params).mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"透由id取得時間錯誤：{str(e)}")


    # 先行解析時間 & 車牌號碼
    for row in data_result:
        row_dict = dict(row)
        measurement = row_dict.get('measurementdatetime','').strip()
        carsno = row_dict.get('carsno','').strip()
        areaid = row_dict.get('areaid','').strip()

    try:
        if isinstance(measurement, str):
            dt = datetime.strptime(measurement, "%Y/%m/%d %H:%M:%S")
        else:
            dt = measurement
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"時間格式解析失敗：{str(e)}")

    
    # 格式化時間欄位已找到目標檔案
    y = f"{dt.year:04}"
    mo = f"{dt.month:02}"
    d = f"{dt.day:02}"
    h = f"{dt.hour:02}"
    mi = f"{dt.minute:02}"
    s = f"{dt.second:02}"
    
    folder_name = f"{y}{mo}{d}{h}{mi}{s}_{carsno}"
    source_path = BASE_PATH / areaid / y / mo / d / folder_name


    # 產製zip檔案
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"資料夾不存在: {source_path}")

    # 壓縮資料夾為 zip（存在記憶體中）
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source_path.parent)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)

    filename = f"{folder_name}.zip"

    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )    