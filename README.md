# SearchFace

# command memo

```
source venv/bin/activate
```

# 検索エンジンの手動確認

https://programmablesearchengine.google.com/controlpanel/all

# 検索

curl -s "" |
curl -X POST "http://localhost:8000/api/search" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@-"

curl -X POST "http://localhost:8000/api/search" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@data/images/input.jpg"

# docker build

docker build -t searchface:latest .

# docker run

docker run -d -p 8000:8000 --name searchface searchface:latest