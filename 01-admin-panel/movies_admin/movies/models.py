import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'content"."genre'
        verbose_name = _("Genre")
        verbose_name_plural = _("Genres")


class FilmWork(UUIDMixin, TimeStampedMixin):
    class FilmTypes(models.TextChoices):
        MOVIE = _("movie")
        TV_SHOW = _("tv_show")

    title = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    creation_date = models.DateField(_("creation_date"), blank=True)
    rating = models.FloatField(
        _("rating"),
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    type = models.CharField(_("type"), choices=FilmTypes.choices)

    genres = models.ManyToManyField(Genre, through="GenreFilmWork")

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'content"."film_work'
        verbose_name = _("Film")
        verbose_name_plural = _("Films")


class GenreFilmWork(UUIDMixin):
    film_work = models.ForeignKey("FilmWork", on_delete=models.CASCADE)
    genre = models.ForeignKey("Genre", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content"."genre_film_work'


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_("full_name"), max_length=255)
    films = models.ManyToManyField(FilmWork, through="PersonFilmWork")

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'content"."person'
        verbose_name = _("Person")
        verbose_name_plural = _("Persons")


class PersonFilmWork(UUIDMixin):
    film_work = models.ForeignKey("FilmWork", on_delete=models.CASCADE)
    person = models.ForeignKey("Person", on_delete=models.CASCADE)
    role = models.TextField(_("role"))
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'content"."person_film_work'
