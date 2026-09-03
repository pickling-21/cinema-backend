from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, Value
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from movies.models import FilmWork, Roles


class MoviesApiMixin:
    http_method_names = ["get"]

    paginate_by = 50

    def get_queryset(self):
        annotations = {}

        roles_list = list(Roles.values)

        for role in roles_list:
            annotations[f"{role}s"] = ArrayAgg(
                "persons__full_name",
                filter=Q(personfilmwork__role=role),
                distinct=True,
                default=Value([]),
            )

        annotations["genres"] = ArrayAgg("genres__name", distinct=True)

        return FilmWork.objects.values(
            "id", "title", "description", "creation_date", "rating", "type"
        ).annotate(**annotations)

    def render_to_response(self, context: dict, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, result_queryset, is_paginated = self.paginate_queryset(
            queryset, self.paginate_by
        )
        context = {
            "count": paginator.count,
            "prev": page.previous_page_number() if page.has_previous() else None,
            "next": page.next_page_number() if page.has_next() else None,
            "results": list(result_queryset),
            "total_pages": paginator.num_pages,
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    def get_context_data(self, **kwargs):
        return self.object
