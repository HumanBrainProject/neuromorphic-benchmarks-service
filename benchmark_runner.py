"""


"""

from time import sleep
from os.path import splitext, join
from urlparse import urlparse
from urllib import urlopen
import json
import nmpi
import requests

BENCHMARKS_SERVER = "https://benchmarks.hbpneuromorphic.eu"


job_manager = nmpi.Client("testuser123")

repositories = (
    "https://github.com/CNRS-UNIC/hardware-benchmarks.git",
)


def main(platform):
    for repository in repositories:
        code_dir = update_repository(repository)
        models = get_models(code_dir)
        for model in models:
            for task in model["tasks"]:
                job = run_job(repository, task, platform)
                results = get_results(job)
                save_results(model, task, results, job)


def update_repository(repository):
    return "/Users/andrew/dev/hardware_benchmarks"


def get_models(code_dir):
    with open(join(code_dir, "benchmarks.json")) as fp:
        models = json.load(fp)
    return models


def run_job(repository, task, platform):
    job_id = job_manager.submit_job(
                    source=repository,
                    command=task["command"],
                    platform=platform,
                    config={"pyNN_version": "0.8"},
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
    raise Exception("No results file found.")


system_name_map = {
    "SpiNNaker": "SpiNNaker",
    "nest-server": "NEST"
}

def save_results(model, task, results, job):
    data = {
        "hardware_platform": system_name_map[job["hardware_platform"]],
        "experiment_description": job["code"],
        "model": model["model"]["name"],
        "task": task["name"],
        "timestamp": job["timestamp_completion"],
        "job_id": job["id"],
        "results": results
    }
    print data
    response = requests.post(BENCHMARKS_SERVER + "/runs/", json=data, verify=False)
    print response


if __name__ == "__main__":
    main("nest-server")
    main("SpiNNaker")
