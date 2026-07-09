## How to: Deploying GitOps Pipeline on K8S hosted on vCluster

Welcome to the Rabbit Hole

Came across a nice little bit of tech, just what I was looking for. For those that follow my Blogs would know I dive deep into using Docker-Compose, but fact is, sometimes you need more, you need to get closer to what would be end state, Cloud Native... aka Kubernetes based deployments.

What follows is a short'ish introduction to [vCluster](https://github.com/loft-sh/vcluster) as a solution to run Kubernetes on a desktop/laptop inside Docker.

[vCluster](https://github.com/loft-sh/vcluster) is capable of allot more... But I figured lets keep it simple at first.

We have various README.md files, covering various steps and examples.

- This file, that detail the installation of [vCluster](https://github.com/loft-sh/vcluster), see below.

- Deploying a basic multi node Kubernetes cluster inside vCluster.

- Our deployment of our GitOps pipeline.

All the examples will utilise persistent storage mapped into our Kubernetes environment from the host.

BLOG: [How to: Deploying GitOps Pipeline on K8S hosted on vCluster](???)

GIT: [gitops-pipeline](https://github.com/georgelza/gitops-pipeline)

See `<Project_root>/my-pipeline` for various screen shots during deployment


## Basic Installation/HOST Preperation

1. Install vCluster

```bash
brew install vcluster

# Upgrade vCluster CLI to the latest version
vcluster upgrade --version v0.35.1

# Set Docker as the default driver
vcluster use driver docker

# Start vCluster Platform (optional but recommended)
vcluster platform start
```

## Creating up Multi Node K8S Cluster on vCluster

- See BUILD.md

## Deploying our GitOps pipeline

- See GITOPS.md

## Misc useful commands

Should you need to restart you host environment.

The following is the commands I executed to bring my cluster/s back up after having restarted Docker

- `vcluster use driver docker`

- `vcluster platform start`

- `vcluster resume my-vc`

or

`docker restart $(docker ps -q --filter "name=my-pipeline")`


You can of course also stop/pause a running cluster:

- `vcluster pause my-pipeline`

To apply changes to a previously created cluster.

- `vcluster create --upgrade <cluster-name> -f vcluster.yml`

Tear Down
  
- `vcluster delete <cluster-name>`


## Project Pages

- [VIND](https://github.com/loft-sh/vind)

- [vCluster](https://github.com/loft-sh/vcluster)

- [Full Quickstart Guide](https://www.vcluster.com/docs/vcluster/#deploy-vcluster)

- [Slack Seerver](https://slack.loft.sh/)

**THE END**

And like that we’re done with our little trip down another Rabbit Hole, Till next time.

Thanks for following. 


### The Rabbit Hole

<img src="blog-doc/diagrams/rabbithole.jpg" alt="Our Build" width="450" height="350">


## ABOUT ME

I’m a techie, a technologist, always curious, love data, have for as long as I can remember always worked with data in one form or the other, Database admin, Database product lead, data platforms architect, infrastructure architect hosting databases, backing it up, optimizing performance, accessing it. Data data data… it makes the world go round.
In recent years, pivoted into a more generic Technology Architect role, capable of full stack architecture.

### By: George Leonard

- georgelza@gmail.com
- https://www.linkedin.com/in/george-leonard-945b502/
- https://medium.com/@georgelza



<img src="blog-doc/diagrams/TechCentralFeb2020-george-leonard.jpg" alt="Me" width="400" height="400">

