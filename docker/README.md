# Docker images:

This repository is responsible to hold all scripts to build the ringer image.

## How to use ringer Jupyter image?

This tag has inheritance from ringer base.

```bash
singularity pull docker://jodafons/root-cern:latest
```

After donwload it, just execute the `run` command:

```bash
singularity run root-cern_latest.sif
```
The jupyter server will starts automatically. 

### Port foward to LPS:

Sometimes, it's commom to execute this image inside of the 
cluster infrastruture. To make the port foward just use these commands:

```bash
ssh -L 8888:caloba51:8888 jodafons@login.lps.ufrj.br
```

And inside of the node:
```bash
singularity run cern-root_latest.sif
source /setup_root.sh
# setup other things before launch...
jupyter-lab --port 8888
```

Use the `token` inside of `~/.jupyter/jupyter_server_config.json` generated by `jupyter server --generate-config` and `jupyter server password` to login.

**NOTE** Using caloba cluster and port 8888 as example.



