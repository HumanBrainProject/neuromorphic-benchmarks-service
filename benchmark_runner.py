"""
A script for running neuromorphic benchmarks

"""

import sys
from time import sleep
import os
from os.path import splitext, join
try:
    from urlparse import urlparse
    from urllib import urlopen
except ImportError:
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.error import HTTPError
import json
import tempfile
import shutil
from sh import git
import nmpi
import requests

BENCHMARKS_SERVER = "https://benchmarks.hbpneuromorphic.eu"
BENCHMARKS_COLLAB = "510"

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


def main(platform, wait_for_results=True):
    for repository in repositories:
        models = get_models(repository)
        for model in models:
            for task in model["tasks"]:
                print(repository, model, task, platform)
                if platform in task.get("target", []):
                    job = run_job(repository, task, platform, wait_for_results=wait_for_results)
                    print(job)
                    if wait_for_results:
                        results = get_results(job)
                        assert model["model"]["name"] == results["model"]
                        assert task["name"] == results["task"]
                        save_results(results["model"], results["task"], results["results"], job, platform)


def get_models(repository):
    print("Getting list of benchmarks from {}".format(repository))
    tmpdir = tempfile.mkdtemp()
    git.clone(repository, tmpdir)
    with open(join(tmpdir, "benchmarks.json")) as fp:
        models = json.load(fp)
    shutil.rmtree(tmpdir)
    return models


def run_job(repository, task, platform, wait_for_results=True):
    queue_name = queue_name_map[platform]
    #config = {"pyNN_version": "0.8"}
    config = {}
    if "config" in task:
        config.update(task["config"].get(platform, {}))
    job = job_manager.submit_job(
                        source=repository,
                        command=task["command"],
                        platform=queue_name,
                        config=config,
                        collab_id=510,
                        wait=wait_for_results)
    return job


def get_results(job):
    for resource in job["output_data"]:
        path, ext = splitext(urlparse(resource["url"]).path)
        if ext == ".json":
            try:
                fp = urlopen(resource["url"])
            except HTTPError as err:
                if err.code == 404:
                    print("JSON file no longer available")
                elif err.code == 500:
                    print("Server error for job {}".format(job["id"]))
                elif err.code == 401:
                    print("Unauthorized to access JSON file")
                else:
                    raise
            else:
                data = json.load(fp)
                fp.close()
                if "results" in data:
                    return data
    # add a warning that there are no results
    return []


def save_results(model_name, task_name, results, job, platform):
    assert job["hardware_platform"] == platform
    data = {
        "hardware_platform": platform,
        "experiment_description": job["code"],
        "model": model_name,
        "task": task_name,
        "timestamp": job["timestamp_completion"],
        "job_id": job["id"],
        "results": results,
        "status": job["status"]
    }
    print(data)
    response = requests.post(BENCHMARKS_SERVER + "/runs/", json=data, verify=True)
    if response.status_code in (200, 201):
        print(response)
    else:
        raise Exception(response.text)


def check_for_finished_runs():
    for job in job_manager.completed_jobs(BENCHMARKS_COLLAB, verbose=True):
        if job["status"] == "finished" and job['timestamp_completion'] > '2019': # todo: only look at jobs within past 1 week or 1 day
            full_job = job_manager.get_job(job["id"])
            results = get_results(full_job)
            if results:
                save_results(results["model"], results["task"], results["results"], job, job["hardware_platform"])
            else:
                print("No data for job {}".format(job["id"]))


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "run":
        #main("NEST")
        main("SpiNNaker", wait_for_results=False)
        main("BrainScaleS", wait_for_results=False)
    elif sys.argv[1] == "check":
        check_for_finished_runs()
