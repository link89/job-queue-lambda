# job-queue-lambda
Use job queue (Slurm, PBS, etc) as a remote function executor.

## Introduction

`job-queue-lambda` allows you to forward a HTTP request to a service that running on a remote job queue (Slurm, PBS, etc).
For example, 

```yaml
# job-queue-lambda.yaml
listen: "127.0.0.1:9000"

clusters:
  - name: ikkem-hpc 
    ssh:
      cmd: "ssh ikkem-hpc"
      socks_listen: "127.0.0.1:9001"

    job_queue:
      slurm: {}
    
    lambdas:
      - name: ollama
        forward_to: "http://{NODE_NAME}:11434"
        max_workers: 1
        submit: |
          #SBATCH --job-name=ollama
          #SBATCH --partition=gpu

          module load anaconda/3
          source activate ollama
          # running ollama server
          ollama serve --model llama3.1 --port 11434
```

And then you will be able to forward a HTTP request to the ollama server running on the remote job queue.

```bash
curl -X POST http://127.0.0.1:9000/clusters/ikkem-hpc/lambda/ollama/chat -d '{"prompt": "Hello, world!"}'
```

## Installation

```bash
pip install job-queue-lambda
```
