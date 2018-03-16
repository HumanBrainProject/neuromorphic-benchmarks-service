from datetime import datetime
from django.test import TestCase
from django.test import Client
import json
from .models import System, NetworkModel, Task, Measure, Run, Repository
from .views import RunListResource


class BaseTestCase(TestCase):

    def setUp(self):
        self.example_system = System(name="ANeuromorphicSystem",
                                     version="unknown")
        self.example_system.save()
        self.example_repository = Repository(url="https://path.to/a/git/repository")
        self.example_repository.save()
        self.existing_model = NetworkModel(
            repository=self.example_repository,
            name="AnExistingModel")
        self.existing_model.save()
        self.existing_tasks = [
            Task(model=self.existing_model,
                 name="existing_task_%d" % i,
                 command="run.py {system} %d" % i)
            for i in range(3)
        ]
        for task in self.existing_tasks:
            task.save()


class RunResourceTest(BaseTestCase):

    def setUp(self):
        super(RunResourceTest, self).setUp()
        self.test_data_1 = {
            "hardware_platform": self.example_system.name,
            "experiment_description": self.example_repository.url,
            "model": self.existing_model.name,
            "task": self.existing_tasks[1].name,
            "timestamp": datetime.now().isoformat(),
            "job_id": 469346,
            "results": [
                {
                    "type": "quality",
                    "name": "norm_diff_frequency",
                    "value": 0.0073371188622418891,
                    "measure": "norm"
                },
                {
                    "type": "performance",
                    "name": "setup_time",
                    "value": 0.026206016540527344,
                    "std_dev": 0.0032452,
                    "units": "s",
                    "measure": "time"
                },
                {
                    "type": "performance",
                    "name": "run_time",
                    "value": 1.419724941253662,
                    "min": 1.34352,
                    "max": 1.56366,
                    "units": "s",
                    "measure": "time"
                },
                {
                    "type": "performance",
                    "name": "closing_time",
                    "value": 0.03272294998168945,
                    "units": "s",
                    "measure": "time"
                }
            ]
        }

    def test_add_run_existing_model_and_task(self):
        resource = RunListResource()
        resource._add_run(self.test_data_1)

    def test_post_run(self):
        c = Client()
        response = c.post('/runs/', data=json.dumps(self.test_data_1),
                          content_type="application/json")
        self.assertEqual(response.status_code, 201)


