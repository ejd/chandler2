import peak.events.trellis as trellis
import chandler.core as core
import chandler.event as event
import itertools

class SidebarEntry(trellis.Component):
    _ITER_HUES = itertools.cycle((210, 120, 0, 30, 50, 300, 170, 330, 270))
    _ITER_SORT_KEY = itertools.count(1)

    @trellis.make(writable=True, optional=False)
    def sort_key(self):
        return self._ITER_SORT_KEY.next()

    @trellis.make(writable=True, optional=False)
    def hsv_color(self):
        return (self._ITER_HUES.next(), 0, 0)

    @trellis.make(writable=True)
    def collection(self):
        return core.Collection()

    checked = trellis.attr(False)

    def __repr__(self):
        return u"<%s(%s) at 0x%x>" % (type(self).__name__,
                                      self.collection.title,
                                      id(self))

class Sidebar(core.Table):
    @trellis.maintain
    def icon_column(self):
        return core.TableColumn(scope=self, label=u'Icon',
            get_value=lambda entry: (entry.hsv_color, entry.checked))

    @trellis.maintain
    def name_column(self):
        return core.TableColumn(scope=self, label=u'Name',
            get_value=lambda entry:entry.collection.title)


    @trellis.make
    def columns(self):
        return trellis.List([self.icon_column, self.name_column])

    @trellis.make
    def filtered_items(self):
        return core.FilteredSubset(
            base=trellis.Cell(lambda: self.selected_item.collection.items),
            predicate=trellis.Cell(lambda:self.filters.value))

    @trellis.maintain
    def filters(self):
        # need to add a hook for the choices
        return core.Choice(
            scope=self,
            choices=trellis.List([
                core.ChoiceItem(
                    label=u'All',
                    help=u'View all items',
                    value=lambda item: True),
                core.ChoiceItem(
                    label=u'Calendar',
                    help=u'View events',
                    value=event.Event.installed_on),
            ])
        )


def load_interaction(app):
    app.sidebar = Sidebar(model=app.collections)