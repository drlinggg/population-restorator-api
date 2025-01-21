import uvicorn

def _run_uvicorn():
    uvicorn.run(
            "api_app:app"
    )

def main():
    _run_uvicorn()

if __name__ == "__main__":
    main()
