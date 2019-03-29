"""
A script for running neuromorphic benchmarks

"""

from time import sleep
import os
from os.path import splitext, join
try:
    from urlparse import urlparse
    from urllib import urlopen
except ImportError:
    from urllib.parse import urlparse
    from urllib.request import urlopen
import json
import tempfile
import shutil
from sh import git
import nmpi
import requests

BENCHMARKS_SERVER = "https://benchmarks.hbpneuromorphic.eu"


job_manager = nmpi.Client("testuser123",
                          password=os.environ["BENCHMARK_RUNNER_PASSWORD"])

queue_name_map = {
    "SpiNNaker": "SpiNNaker",
    "BrainScaleS": "BrainScaleS",
    "Spikey": "Spikey",
    "NEST": "nest-server"
}

repositories = [
    #"https://github.com/CNRS-UNIC/hardware-benchmarks.git",
    #"https://github.com/apdavison/pynam.git",
    "https://github.com/hbp-unibi/SNABSuite_deploy",
]


def main(platform):
    for repository in repositories:
        models = get_models(repository)
        for model in models:
            for task in model["tasks"]:
                if platform in task.get("target", []):
                    job = run_job(repository, task, platform)
                    results = get_results(job)
                    save_results(model, task, results, job, platform)


def get_models(repository):
    tmpdir = tempfile.mkdtemp()
    git.clone(repository, tmpdir)
    with open(join(tmpdir, "benchmarks.json")) as fp:
        models = json.load(fp)
    shutil.rmtree(tmpdir)
    return models


def run_job(repository, task, platform):
    queue_name = queue_name_map[platform]
    config = {"pyNN_version": "0.8"}
    if "config" in task:
        config.update(task["config"].get(platform, {}))
    job_id = job_manager.submit_job(
                    source=repository,
                    command=task["command"],
                    platform=queue_name,
                    config=config,
                    collab_id=510)
    while job_manager.job_status(job_id) not in ("finished", "error"):
        sleep(10)
    return job_manager.get_job(job_id)


def get_results(job):
    for resource in job["output_data"]:
        path, ext = splitext(urlparse(resource["url"]).path)
        if ext == ".json":
            fp = urlopen(resource["url"])
            data = json.load(fp)
            fp.close()
            if "results" in data:
                return data["results"]
    # add a warning that there are no results
    return []


def save_results(model, task, results, job, platform):
    data = {
        "hardware_platform": platform,
        "experiment_description": job["code"],
        "model": model["model"]["name"],
        "task": task["name"],
        "timestamp": job["timestamp_completion"],
        "job_id": job["id"],
        "results": results
    }
    print(data)
    response = requests.post(BENCHMARKS_SERVER + "/runs/", json=data, verify=False)
    if response.status_code in (200, 201):
        print(response)
    else:
        raise Exception(response.text)


if __name__ == "__main__":
    #main("NEST")
    main("SpiNNaker")
    #main("BrainScaleS")
