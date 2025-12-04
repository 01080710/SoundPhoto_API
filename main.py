from fastapi.middleware.cors import CORSMiddleware
from routers.soundphoto import api as soundphoto_api
from routers.edgesite import api as edgesite_api
from routers.check import api as check_api
from routers.sensor   import api as sensor_api
# from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
import db , uvicorn




# 讀取資料庫
db.init_db()
print("SessionLocal 是否為 callable_1：", callable(db.SessionMain))
print("SessionLocal 是否為 callable_2：", callable(db.SessionHis))


# 建立 fastapi
app = FastAPI(
    title="Company Internal API Documentation",
    description="This API provides access to Audio-Imaging-Edge-System data for internal monitoring and reporting purposes.",
    version="1.0.0",
    contact={
        "name": "IT Support",
        "email": "peter@otocon.com.tw",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.or/licenses/MIT",
    }
)

# ✅ 正確的靜態檔案掛載：對應你 docker-compose 的 volume
# app.mount("/eventfiles", StaticFiles(directory="/mnt/eventexport"), name="eventfiles")

# 加入跨域共享資源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 允許的來源
    allow_credentials=True,
    allow_methods=["*"],              # GET, POST, PUT, DELETE...
    allow_headers=["*"],              # Authorization, Content-Type...
)




# 加入路由
router_modules = {
    'edgesite': edgesite_api,
    'soundphoto': soundphoto_api,
    'sensor': sensor_api,
    "check": check_api
}
for name, module in router_modules.items():
    app.include_router(module.router, prefix=f'/{name}', tags=[name])




if __name__ == "__main__":
    # 設定 host 為 0.0.0.0，讓應用接受所有 IP 的請求
    uvicorn.run(app, host="0.0.0.0", port=8010)