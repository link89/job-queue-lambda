# job-queue-lambda

Use job queue (Slurm, PBS, etc) as a remote function executor, just like AWS Lambda.

## Installation

```bash
pip install job-queue-lambda
```
## Getting Started

`job-queue-lambda` allows you to forward a HTTP request to a service that running on a remote job queue. Currently only Slurm is supported.

For example, you can use the following configuration:

```yaml
# ./examples/config.yaml
clusters:
  - name: ikkem-hpc
    ssh:
      host: ikkem-hpc
      socks_port: 10801

    lambdas:
      - name: python-http
        forward_to: http://{NODE_NAME}:8080/
        cwd: ./jq-lambda-demo
        script: |
          #!/bin/bash
          #SBATCH -N 1
          #SBATCH --job-name=python-http
          #SBATCH --partition=cpu
          set -e
          timeout 30 python3 -m http.server 8080

    job_queue:
      slurm: {}
```

And then you can start the server by running:
```bash
jq-lambda ./examples/config.yaml
```

Now you can use browser to access the following URL:  http://localhost:9000/clusters/ikkem-hpc/lambdas/python-http

or using `curl`:
```bash
curl http://localhost:9000/clusters/ikkem-hpc/lambdas/python-http
```

The request will be forwarded to the remote job queue, and the response will be returned to you.
