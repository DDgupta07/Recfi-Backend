from django.urls import path

from .views import (
    WatchListView,
    PulseTrackerNotification,
    SwapTokenView,
    WatchListDetail,
)


urlpatterns = [
    path("watch-list/", WatchListView.as_view(), name="watch_list"),
    path("notify/", PulseTrackerNotification.as_view(), name="send_notification"),
    path("swap-token/", SwapTokenView.as_view(), name="swap_token"),
    path(
        "watch-list/<uuid:uuid>/", WatchListDetail.as_view(), name="watch_list_detail"
    ),
]
