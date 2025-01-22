import uvicorn


def _run_uvicorn():
    # todo make debug mode with reload = true/false
    uvicorn.run(
        "app:app",
        reload=True,
    )


def main():
    _run_uvicorn()


if __name__ == "__main__":
    main()
