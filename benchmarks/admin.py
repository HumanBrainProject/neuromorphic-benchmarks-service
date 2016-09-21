from django.contrib import admin
from .models import System, Repository, NetworkModel, Task, Run, Measure

admin.site.register(System)
admin.site.register(Repository)
admin.site.register(NetworkModel)
admin.site.register(Task)
admin.site.register(Run)
admin.site.register(Measure)
