from __future__ import annotations


def main() -> None:
    import uvicorn

    uvicorn.run("climb_log.app:create_app", factory=True, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
