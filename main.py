import uvicorn
from decouple import config

if __name__ == '__main__':
    reload = config('BACKEND_RELOAD', cast=bool)
    number_of_workers = config('BACKEND_NUMBER_OF_WORKERS', cast=int)
    port = config('BACKEND_SERVER_PORT', cast=int)
    uvicorn.run("server.app:app", host='0.0.0.0', port=port, reload=reload, workers=number_of_workers)