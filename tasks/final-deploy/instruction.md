## Description
`/app/deploy.sh` deploys the service. Several releases are deployed during the run; earlier ones are rolled back.

## Requirements
- Find the deployment that is live at the end of the run: the line `Deployed <id> (live)`.
- Write only its id (for example `dep-1a2b3c`) to `/app/answer.txt`.
- Do not modify `/app/deploy.sh`.

## Interface
`/app/answer.txt`: a single line containing the deployment id.
