import sys
import tempfile
from os.path import join
import json
import shutil
sys.path.append("..")
from benchmark_runner import get_results, save_results


def fake_run_job(repository, task, platform):
    tmpdir = tempfile.mkdtemp()
    fake_job = {
        'experiment_description': repository,
        'hardware_platform': platform,
        'id': 9999919,
        "output_data": [
            {"url": join(tmpdir, "fake.png")},
            {"url": join(tmpdir, "results.json")}
        ],
        'status': u'finished',
        'timestamp_completion': u'2014-08-13T21:02:37.541732',
        'timestamp_submission': u'2014-08-13T19:40:43.964541',
    }
    shutil.rmtree(tmpdir)


def test_get_results():
    results = {
        "timestamp": "2015-06-05T11:13:59.535885",
        "results": [
            {
                "type": "quality",
                "name": "https://github.com/CNRS-UNIC/hardware-benchmarks.git/I_f_curve#norm_diff_frequency",
                "value": 0.0073371188622418891,
                "measure": "norm"
            },
            {
                "type": "performance",
                "name": "https://github.com/CNRS-UNIC/hardware-benchmarks.git/I_f_curve#run_time",
                "value": 1.419724941253662,
                "units": "s",
                "measure": "time"
            }
        ],
    }
    # create a temporary directory containing some fake data
    tmpdir = tempfile.mkdtemp()
    with open(join(tmpdir, "results.json"), "w") as fp:
        json.dump(results, fp)

    fake_job = {
        "output_data": [
            {"url": join(tmpdir, "fake.png")},
            {"url": join(tmpdir, "results.json")}
        ]
    }
    retrieved_results = get_results(fake_job)
    shutil.rmtree(tmpdir)
    assert retrieved_results == results["results"]


if __name__ == "__main__":
    test_get_results()