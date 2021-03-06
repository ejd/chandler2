from datetime import datetime, timedelta, time
import peak.events.trellis as trellis
import peak.events.activity as activity

from chandler.core import *
from chandler.time_services import TimeZone, timestamp, is_past
from chandler.triage import Triage, NOW, LATER

one_hour = timedelta(hours=1)
zero_delta = timedelta(0)
midnight = time(0, tzinfo=TimeZone.floating)

class Event(Extension):
    inherited_attrs(
        base_start = None,          # None, or a datetime with a PyICU tzinfo
        base_duration = one_hour,   # a timedelta
        all_day = False,
        base_any_time = False,
        tzinfo = TimeZone.floating,

        # miscellaneous cells that don't affect time
        location = None,
        base_transparency = 'confirmed'
    )

    @property
    def start(self):
        if self.base_start is None:
            return None
        if not self.is_day:
            return self.base_start.astimezone(self.tzinfo)
        else:
            return datetime.combine(self.base_start.date(), midnight)

    @trellis.compute
    def is_started(self):
        if self.start is None:
            return True
        return is_past(self.start)

    @trellis.compute
    def duration(self):
        if not self.is_day:
            return self.base_duration
        else:
            return timedelta(max(1, self.base_duration.days))

    @property
    def end(self):
        return (self.start + self.duration if self.start is not None
                                          else None)

    @trellis.compute
    def any_time(self):
        return self.base_any_time and not self.all_day

    @trellis.compute
    def is_day(self):
        return self.all_day or self.any_time

    @trellis.compute
    def transparency(self):
        if self.implied_transparency:
            return self.implied_transparency
        else:
            return self.base_transparency

    @trellis.compute
    def implied_transparency(self):
        if self.any_time or not self.duration:
            return 'fyi'

    @trellis.maintain
    def constraints(self):
        if self.base_start is not None and self.base_start.tzinfo is None:
            # this won't happen consistently; if base_start is already set,
            # trellis itself will raise a TypeError
            raise NaiveTimezoneError(repr(self.base_start))
        if not isinstance(self.base_duration, timedelta) or self.base_duration < zero_delta:
            raise BadDurationError(self.base_duration)


def event_triage(item):
    """Hook for triage of an event."""
    if not Event.installed_on(item):
        return ()
    else:
        start = Event(item).start
        if not start:
            return ()
        # LATER from distant past until NOW at start time
        return ((0, LATER), (timestamp(start), NOW))


class NaiveTimezoneError(ConstraintError):
    cell_description = "base_start"


class BadDurationError(ConstraintError):
    cell_description = "base_duration"

### Interaction model ###
class EventFieldVisibility(ItemAddOn):

    @trellis.compute
    def event(self):
        if self._item is None or not Event.installed_on(self._item):
            return None
        else:
            return Event(self._item)

    @trellis.compute
    def show_time(self):
        return bool(self.event and not self.event.all_day)

    @trellis.compute
    def clear_time(self):
        return bool(self.event and self.event.any_time)

    @trellis.compute
    def show_timezone(self):
        return bool(self.event and not self.event.is_day)

    @trellis.compute
    def show_transparency(self):
        return bool(self.event and not self.event.implied_transparency)

# is_between
