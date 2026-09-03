
`docker-compose build --no-cache`

`docker-compose up -d`


`uv run fastapi dev`

04. 

http://localhost:8000/api/v1/films/3d825f60-9fff-4dfe-b294-1a45fa1e115d


http://localhost:8000/api/v1/films/?sort=-imdb_rating&genre=6c162475-c7ed-4461-9184-001ef3d9f26e

http://localhost:8000/api/v1/films/search/?query=wars

http://localhost:8000/api/v1/films/search/?query=star&page_number=1&page_size=50

http://localhost:8000/api/v1/films?sort=-imdb_rating&page_size=50&page_number=1