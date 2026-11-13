"""Local monitor/health jobs; secrets never appear in command arguments or logs."""
import json
import os
import sys
import urllib.request

def main():
    if sys.argv[1] == "monitor":
        request = urllib.request.Request(
            "http://127.0.0.1:8000/operations/monitor/run", method="POST",
            headers={"Authorization": "Bearer " + os.environ["MONITOR_TOKEN"]},
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.load(response)
        if data.get("status") != "completed":
            raise RuntimeError("Monitor did not complete")
        print("Monitor completed; run_id=", data["id"])
    else:
        from etl.load_orders import conectar_banco
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
            assert json.load(response)["status"] == "ok"
        with conectar_banco(somente_leitura=True) as connection:
            assert connection.execute("SELECT count(*) FROM pedidos").fetchone()[0] > 0
        import shutil
        assert shutil.disk_usage("/").free > 2 * 1024**3, "Less than 2 GiB disk free"
        print("API, database and disk healthy")

if __name__ == "__main__":
    main()
