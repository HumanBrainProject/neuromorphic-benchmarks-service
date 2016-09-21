from django.db import models

# Create your models here.

class System(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=100)

    def __str__(self):
        return "{}/{}".format(self.name, self.version)


class Repository(models.Model):
    url = models.URLField(max_length=500)

    def __str__(self):
        return self.url

    class Meta:
        verbose_name_plural = "repositories"


class NetworkModel(models.Model):
    repository = models.ForeignKey(Repository)
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField()

    def get_name(self):
        return self.name or self.description[:20]

    def __str__(self):
        return "{}/{}".format(self.repository, self.get_name())


class Task(models.Model):
    model = models.ForeignKey(NetworkModel)
    name = models.CharField(max_length=100, blank=True)
    command = models.CharField(max_length=500)

    def __str__(self):
        return "{}/{}".format(self.model, self.name or "unknown")


class Run(models.Model):
    task = models.ForeignKey(Task)
    timestamp = models.DateTimeField()
    nmpi_id = models.PositiveIntegerField()
    system = models.ForeignKey(System)

    def __str__(self):
        return "{}/{}/{}".format(self.task, self.system, self.nmpi_id)


class Measure(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField()
    units = models.CharField(max_length=20, blank=True)
    metric = models.CharField(max_length=50,
                              help_text='e.g. "quality", "performance", "energy consumption"')
    type = models.CharField(max_length=50,
                            help_text='the type of the measurement, for example "norm", "p-value", "time".')
    run = models.ForeignKey(Run)

    def __str__(self):
        return "{}#{}={}{}".format(self.run, self.name, self.value, self.units)


# from benchmarks.models import *
# Task.objects.all()
# run_ifcurve, run_spikestats = _
# run_ifcurve
# run_ifcurve.description
# run_ifcurve.command
# run_ifcurve.model.description
# run_ifcurve.model.name="IF_cond_exp"
# run_ifcurve.model.save()
# run_ifcurve
# run_ifcurve.name
# run_ifcurve.name = "I_f_curve"
# run_ifcurve
# run_ifcurve.save()
# run_spikestats.model.name="SpikeSourcePoisson"
# run_spikestats.model.save()
# run_spikestats.name="run20s"
# run_spikestats.save()
# run_spikestats
# run19005a = Run(task=run_ifcurve, nmpi_id=19005)
# from datetime import datetime
# run19005a.timestamp = datetime.now()
# System.objects.all()
# pm1, mc1, nest = _
# pm1
# nest
# mc1
# run19005a.system = mc1
# run19005a.save()
# import tz
# import tzinfo
# import pytz
# cest = pytz.timezone("Europe/Amsterdam")
# run19005a.timestamp = datetime.now(tz=cest)
# run19005a.save()
# run19005b = Run(task=spikestats, nmpi_id=19005, system=mc1, timestamp=run19005a.timestamp)
# run19005b = Run(task=run_spikestats, nmpi_id=19005, system=mc1, timestamp=run19005a.timestamp)
# run19005b.save()
# import json
# results_19005a = json.load("/Users/andrew/Downloads/I_f_curve_result.json")
# with open("/Users/andrew/Downloads/I_f_curve_result.json") as fp: results_19005a = json.load(fp)
# results_19005a
# for result in results_19005a['results']:
#     m = Measure(run=run19005a, value=result['value'], metric=result['type'], type=result['measure'])
#     m.save()
# with open("/Users/andrew/Downloads/spike_train_statistics.json") as fp: results_19005b = json.load(fp)
# for result in results_19005b['results']:
#     m = Measure(run=run19005b, value=result['value'], metric=result['type'], type=result['measure'])
#     m.save()