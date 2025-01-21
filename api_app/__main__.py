import uvicorn
from api_app.utils import try_load_envfile

def _run_uvicorn():
    uvicorn.run(
            "api_app:app"
    )

def main():
    _run_uvicorn()   

if __name__ == "__main__":
    try_load_envfile(os.environ.get("ENVFILE", ".env"))
    main()
