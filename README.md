# Gerundium Github Event Poller

This tool watches a git repository for new commits and if it finds a commit message that contains **"trigger: Build new image"** it trigger a argo workflow that build a new container image and pushes it to the docker registry.

## Notes

```bash
# Manually build new container image
COMMIT_SHA=$(git rev-parse --short HEAD); docker build -t gerundium/github-event-poller:$COMMIT_SHA -t gerundium/github-event-poller:latest  --file ./Containerfile

# Spin up a simple container
docker run -it --rm --env-file ./env gerundium/github-event-poller:latest

# Spin up a container via docker compose
docker compose --file container/container-compose.yaml up -d
```