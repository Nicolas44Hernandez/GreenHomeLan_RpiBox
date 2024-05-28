try:
    import httplib  # python < 3.0
except:
    import http.client as httplib


def connected_to_internet() -> bool:
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        print("Connected")
    except Exception:
        print("Not connected")
    finally:
        conn.close()


connected_to_internet()
