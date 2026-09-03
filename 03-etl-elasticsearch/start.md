docker-compose up -d 

postgres

docker run -d \
  --name db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=example_password \
  -e POSTGRES_DB=movies \
  -p 5432:5432 \
  -v $(pwd)/database_dump.sql:/docker-entrypoint-initdb.d/init.sql \
  postgres:16

psql -h 127.0.0.1 -U postgres -d movies -f database_dump.sql

example_password

elastic search

docker run -d \
  --name es \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -p 9200:9200 \
  -p 9300:9300 \
  docker.elastic.co/elasticsearch/elasticsearch:8.6.2

curl -XPUT http://127.0.0.1:9200/movies -H 'Content-Type: application/json' -d'
{
  "settings": {
    "refresh_interval": "1s",
    "analysis": {
      "filter": {
        "english_stop": {
          "type":       "stop",
          "stopwords":  "_english_"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "english_possessive_stemmer": {
          "type": "stemmer",
          "language": "possessive_english"
        },
        "russian_stop": {
          "type":       "stop",
          "stopwords":  "_russian_"
        },
        "russian_stemmer": {
          "type": "stemmer",
          "language": "russian"
        }
      },
      "analyzer": {
        "ru_en": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "english_stop",
            "english_stemmer",
            "english_possessive_stemmer",
            "russian_stop",
            "russian_stemmer"
          ]
        }
      }
    }
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "id": {
        "type": "keyword"
      },
      "imdb_rating": {
        "type": "float"
      },
      "genres": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "ru_en",
        "fields": {
          "raw": { 
            "type":  "keyword"
          }
        }
      },
      "description": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "directors_names": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "actors_names": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "writers_names": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "directors": {
        "type": "nested",
        "dynamic": "strict",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "analyzer": "ru_en"
          }
        }
      },
      "actors": {
        "type": "nested",
        "dynamic": "strict",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "analyzer": "ru_en"
          }
        }
      },
      "writers": {
        "type": "nested",
        "dynamic": "strict",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "analyzer": "ru_en"
          }
        }
      }
    }
  }
}'



etl

python src/main.py

