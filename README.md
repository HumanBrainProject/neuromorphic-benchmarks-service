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