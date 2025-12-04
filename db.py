from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import os, time
from dotenv import load_dotenv

load_dotenv()


# 全域變數
engine_main = None
SessionMain = None
metadata_main = None

engine_his = None
SessionHis = None
metadata_his = None

def init_db(retries: int = 10, delay: int = 2):
    global engine_main, SessionMain, metadata_main
    global engine_his, SessionHis, metadata_his

    # 從環境變數載入設定
    host = os.getenv('Host')
    port = os.getenv('Port')
    user = os.getenv('User')
    password = os.getenv('Password')
    db_main = os.getenv('Database_Mobile') or 'NoBuSystem_Mobile'
    db_his = os.getenv('Database')                  # NoBuSystem
    # test = os.getenv("Host")
    # print(test)
    # host= r'192.168.1.39\SQLEXPRESS'
    # port= '1433'
    # user= 'sa'
    # password= '000000'
    # db_main = 'NoBuSystem_Mobile'
    # db_his = 'build'


    if not all([host, port, user, password, db_main, db_his]):
        raise ValueError("❌ 環境變數未設定完整")

    # 密碼 URL encode
    pwd_encoded = quote_plus(password)

    # 建立兩個連線字串
    db_url_main = (
        f"mssql+pyodbc://{user}:{pwd_encoded}@{host},{port}/{db_main}?"
        f"driver=ODBC+Driver+17+for+SQL+Server"
    )

    db_url_his = (
        f"mssql+pyodbc://{user}:{pwd_encoded}@{host},{port}/{db_his}?"
        f"driver=ODBC+Driver+17+for+SQL+Server"
    )

    # 測試主資料庫連線
    for attempt in range(1, retries + 1):
        try:
            _engine = create_engine(db_url_main)
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ 主資料庫連線成功")
            break
        except Exception as e:
            print(f"⏳ 第 {attempt}/{retries} 次嘗試連線主資料庫失敗：{e}")
            time.sleep(delay)
    else:
        raise RuntimeError("❌ 無法連線到主資料庫")

    # 初始化主資料庫
    engine_main = create_engine(db_url_main)
    SessionMain = sessionmaker(bind=engine_main)
    metadata_main = MetaData()
    metadata_main.reflect(bind=engine_main)

    # 初始化歷史資料庫
    engine_his = create_engine(db_url_his)
    SessionHis = sessionmaker(bind=engine_his)
    metadata_his = MetaData()
    metadata_his.reflect(bind=engine_his)

    print("✅ 兩個資料庫初始化完成")

# 可取得 table 的通用方法
def get_table(name: str, source: str = 'main'):
    if source == 'main':
        return metadata_main.tables.get(name)
    elif source == 'his':
        return metadata_his.tables.get(name)
    else:
        return None
