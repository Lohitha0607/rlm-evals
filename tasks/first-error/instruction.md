## Description
The build in `/app` is failing: `/app/build.sh` exits with an error.

## Requirements
- Find the **first** error in the build output. An error line starts with `error[` followed by an error code such as `E1234`, then `]`.
- Write only that first error's code (for example `E1234`) to `/app/answer.txt`.
- Do not modify `/app/build.sh`.

## Interface
`/app/answer.txt`: a single line containing the error code, for example:

```
E1234
```
