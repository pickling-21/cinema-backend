from django.contrib import admin

from .models import FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created",
    )
    search_fields = ("name",)


class GenreFilmWorkInline(admin.TabularInline):
    model = GenreFilmWork


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name",)
    search_fields = ("full_name",)


class PersonFilmWorkInline(admin.TabularInline):
    model = PersonFilmWork
    autocomplete_fields = ("person",)


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmWorkInline, PersonFilmWorkInline)
    list_display = (
        "title",
        "type",
        "creation_date",
        "rating",
        "get_genres",
    )
    list_filter = ("type",)
    list_prefetch_related = ("genres",)
    search_fields = (
        "title",
        "description",
        "id",
    )

    def get_queryset(self, request):
        queryset = (
            super().get_queryset(request).prefetch_related(*self.list_prefetch_related)
        )
        return queryset

    def get_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genres.all()])

    get_genres.short_description = "Жанры фильма"
