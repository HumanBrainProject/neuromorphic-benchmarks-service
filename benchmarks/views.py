from collections import defaultdict
from pprint import pprint
import json
from datetime import datetime
import hmac
from hashlib import sha1
import pytz
import logging
from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseServerError)
from django.conf import settings
from django.utils.encoding import force_bytes
from django.db import IntegrityError
import dateutil.parser
from ipaddress import ip_address, ip_network

from .models import System, NetworkModel, Task, Measure, Run, Repository


cest = pytz.timezone("Europe/Amsterdam")
logger = logging.getLogger("benchmarks")


class ResultFormatError(Exception):
    pass


def system_list(request):
    context = {
        "systems": System.objects.all(),
        "navigation": "by-system",
    }
    return render(request, 'system_list.html', context)


def model_list(request):
    context = {
        "models": NetworkModel.objects.all(),
        "navigation": "by-task",
    }
    return render(request, 'model_list.html', context)


def model_detail(request, model_name):
    context = {
        "model": NetworkModel.objects.get(name=model_name),
        "navigation": "by-task"
    }
    return render(request, 'model_detail.html', context)


class RunListResource(generic.View):

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        """
        Register a new benchmark run
        """
        data = json.loads(request.body)
        try:
            self._add_run(data)
        except (ResultFormatError, ValueError) as err:
            return HttpResponseBadRequest(err.message)
        return HttpResponse('', status=201)  # need to add data validation/error handling
                                             # should perhaps return the data posted, with run id?


    def _add_run(self, data):
        try:
            system = System.objects.get(name=data["hardware_platform"])  #,
                                        #version="unknown")
        except System.DoesNotExist:
            raise ValueError("Hardware system {} not recognized".format(data["hardware_platform"]))
        try:
            repository = Repository.objects.get(url=data["experiment_description"])
        except Repository.DoesNotExist:
            raise ValueError("Repository {} not registered".format(data["experiment_description"]))
        model, created = NetworkModel.objects.get_or_create(
            repository=repository,
            name=data["model"]
        )
        # todo: handle description
        task, created = Task.objects.get_or_create(
            model=model, name=data["task"]
        )
        # todo: handle command
        #timestamp = cest.localize(
        #    datetime.strptime(data["timestamp"],
        #                           "%Y-%m-%dT%H:%M:%S.%f"))
        timestamp = dateutil.parser.parse(data["timestamp"])
        run = Run(task=task,
                  nmpi_id=data["job_id"],
                  timestamp=timestamp,
                  system=system,
                  status=data["status"])
        try:
            run.save()
        except IntegrityError:  # if job with the same nmpi_id already exists
            pass
        else:
            for result in data["results"]:
                try:
                    m = Measure(run=run, value=result["value"], units=result.get("units", ""),
                                metric=result["type"], type=result["measure"], name=result["name"],
                                std_dev=result.get("std_dev", None),
                                min=result.get("min", None), max=result.get("max", None))
                except KeyError as err:
                    raise ResultFormatError("Missing field in results: {}".format(err.message))
                m.save()


def runs_by_system(request, name):
    runs = Run.objects.filter(system__name=name, status="finished")
    context = {
        'system_name': name,
        'runs': runs.order_by("task__name"),
        "navigation": "by-system"
    }
    return render(request, 'runs_by_system.html', context)


def measures_by_task(request, model_name, task_name):
    task = Task.objects.get(model__name=model_name, name=task_name)
    measures = Measure.objects.filter(run__task=task).order_by("metric", "type", "name", "run__system__name")
    datasets = {}
    for measure in measures:
        if measure.name in datasets:
            if measure.run.system.name in datasets[measure.name]['timeseries']:
                datasets[measure.name]['timeseries'][measure.run.system.name]["times"].append(measure.run.timestamp.strftime("%Y-%m-%dT%H:%M"))
                datasets[measure.name]['timeseries'][measure.run.system.name]["values"].append(measure.value)
            else:
                datasets[measure.name]['timeseries'][measure.run.system.name] = {
                    "label": measure.run.system.name,
                    "times": [measure.run.timestamp.strftime("%Y-%m-%dT%H:%M")],
                    "values": [measure.value]
                }
        else:
            datasets[measure.name] = {
                'timeseries': {
                    measure.run.system.name: {
                        "label": measure.run.system.name,
                        "times": [measure.run.timestamp.strftime("%Y-%m-%dT%H:%M")],
                        "values": [measure.value]
                    }
                },
                'type': measure.type,    # we assume all measures with the same name have
                'units': measure.units,  # the same units and type - should assert this
                'identifier': measure.name.replace(" ", "_")
            }
    context = {
        "task": task,
        "measures": measures,
        "datasets": datasets,
        "navigation": "by-task"
    }
    return render(request, 'measures_by_task.html', context)


def latest(request):
    data = {}
    systems = System.objects.all()
    for repository in Repository.objects.all():
        data[repository.url] = {"nrows": 0, "models": []}

        for model in repository.networkmodel_set.all():
            model_name = model.get_name()
            model_dict = {"name": model_name, "nrows": 0, "tasks": []}
            data[repository.url]["models"].append(model_dict)

            for task in model.task_set.all():
                task_dict = {"name": task.name}
                model_dict["tasks"].append(task_dict)

                last_runs = [task.run_set.filter(system=system).last() for system in systems]

                measure_names = set()
                for run in last_runs:
                    if run is not None:
                        measure_names = measure_names.union([measure.name for measure in run.measure_set.all()])

                measures = dict((name, [None]*systems.count()) for name in measure_names)
                for i, last_run in enumerate(last_runs):
                    if last_run:
                        for measure in last_run.measure_set.all():
                            measures[measure.name][i] = measure
                task_dict["measures"] = [{"name": name, "values": values} for name, values in measures.items()]

                n_measures = len(measure_names)
                task_dict["nrows"] = n_measures
                model_dict["nrows"] += n_measures
                data[repository.url]["nrows"] += n_measures

    context = {"data": data, "systems": systems, "navigation": "latest"}
    return render(request, 'latest.html', context)


def home(request):
    context = {"navigation": "home"}
    return render(request, 'home.html', context)


def documentation(request):
    context = {"navigation": "documentation"}
    return render(request, 'documentation.html', context)


@require_POST
@csrf_exempt
def trigger(request):
    """Webhook for signalling updates to benchmark code or to deployed neuromorphic systems"""
    # based on https://simpleisbetterthancomplex.com/tutorial/2016/10/31/how-to-handle-github-webhooks-using-django.html

    # Verify if request came from GitHub
    # todo: extend whitelist to accept pings from Bielefeld, Manchester, Heidelberg
    forwarded_for = u'{}'.format(request.META.get('HTTP_X_FORWARDED_FOR'))
    client_ip_address = ip_address(forwarded_for)
    whitelist = requests.get('https://api.github.com/meta').json()['hooks']

    for valid_ip in whitelist:
        if client_ip_address in ip_network(valid_ip):
            break
    else:
        return HttpResponseForbidden('Permission denied.')

    # Verify the request signature
    header_signature = request.META.get('HTTP_X_HUB_SIGNATURE')
    if header_signature is None:
        return HttpResponseForbidden('Permission denied.')

    sha_name, signature = header_signature.split('=')
    if sha_name != 'sha1':
        return HttpResponseServerError('Operation not supported.', status=501)

    mac = hmac.new(force_bytes(settings.WEBHOOK_KEY), msg=force_bytes(request.body), digestmod=sha1)
    if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
        return HttpResponseForbidden('Permission denied.')

    # Process the GitHub events
    event = request.META.get('HTTP_X_GITHUB_EVENT', 'ping')

    if event == 'ping':
        return HttpResponse('pong')
    elif event == 'push':
        # Deploy some code for example
        data = json.loads(request.body)
        logger.info("Webhook triggered: new code in {}@{}".format(
            data["repository"]["url"], data["ref"]))
        return HttpResponse('success')

    # In case we receive an event that's not ping or push
    return HttpResponse(status=204)
