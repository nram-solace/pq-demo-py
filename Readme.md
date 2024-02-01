# Partitioned Queue Demo with Solace Python API

## About

Repo with python scripts to demonstrate partitioned queues in Solace.




## Requirements

* [Solace Python API](https://www.solace.dev/)
* [Python 3](https://www.python.org/downloads/) (Tested with Python 3.11.5 on MacOS 14.2.1)

### Quick Setup

See [Solace Samples](https://github.com/SolaceSamples/solace-samples-python) for getting started with Python development with Solace.

```
▶ gh repo clone SolaceSamples/solace-samples-python

▶ cd solace-samples-python

▶ python3 -m pip install --user virtualenv

▶ python3 -m venv venv

▶ source venv/bin/activate

▶ pip install --upgrade pip

▶ pip install -r requirements.txt

▶ source bin/activate
```

## Publisher

1. Create the input JSON file. See config/default.json for reference.
2. Run script with

    ``` SH
▶ python bin/pq-demo-pub.py --profile test --maxmsgsize 10 --numtopics 10 --maxmsgs 100 --numkeys 10 --test-id TEST203 -v
```

## Subscriber

TODO

3. To view stats from previous run, run the script with --statsfile option.

## Contact
[Ramesh Natarajan](ramesh.natarajan@solace.com)
