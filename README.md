# neuromorphic-benchmarks-service



Benchmark runner -

when triggered (e.g. by a web hook, or manual launching):
    for each benchmark repository:
        pull any changes
        read models and tasks from the benchmarks.json
        for each model:
            for each task:
                submit job to NMPI job manager
                retrieve measures json file from job results
                create entry in benchmark database
                
<div><img src="https://raw.githubusercontent.com/HumanBrainProject/hbp-validation-client/master/eu_logo.jpg" alt="EU Logo" width="15%" align="right"></div>


### Acknowledgements
This open source software code was developed in part or in whole in the Human Brain Project, funded from the European Union's Horizon 2020 Framework Programme for Research and Innovation under Specific Grant Agreements No. 720270 and No. 785907 (Human Brain Project SGA1 and SGA2).
