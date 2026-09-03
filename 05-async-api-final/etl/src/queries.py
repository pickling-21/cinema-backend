FILM_WORK_QUERY = """
SELECT 
    fw.id, 
    fw.rating as imdb_rating, 
    COALESCE(ARRAY_AGG(DISTINCT g.name), ARRAY[]::text[]) AS genres_names, 
    fw.title, 
    fw.description,
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', g.id, 'name', g.name)), 
        '[]'
    )AS genres, 
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name))
        FILTER (WHERE pfw.role = 'director'), 
        '[]'
    ) as directors,
    COALESCE(
        json_agg(DISTINCT p.full_name)
        FILTER (WHERE pfw.role = 'actor'),
        '[]'
    ) as actors_names,
    COALESCE(
        json_agg(DISTINCT p.full_name)
        FILTER (WHERE pfw.role = 'director'),
        '[]'
    ) as directors_names,
    COALESCE(
        json_agg(DISTINCT p.full_name)
        FILTER (WHERE pfw.role = 'writer'), 
        '[]'
    ) as writers_names,
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name))
        FILTER (WHERE pfw.role = 'actor'), 
        '[]'
    ) as actors,
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name))
        FILTER (WHERE pfw.role = 'writer'), 
        '[]'
    ) as writers,
    {table}.modified as modified
FROM content.film_work fw
LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
LEFT JOIN content.person p ON p.id = pfw.person_id
LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
LEFT JOIN content.genre g ON g.id = gfw.genre_id
"""
