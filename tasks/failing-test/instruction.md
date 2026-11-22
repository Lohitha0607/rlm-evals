## Description
The test suite in `/app` has one failing test. `/app/run_tests.sh` runs the suite.

## Requirements
- Find the test that failed. A failed test's line ends with ` FAILED`; passing tests end with ` PASSED`.
- Write the failing test's full id (everything before ` FAILED`, for example `tests/foo/test_bar.py::test_baz`) to `/app/answer.txt`.
- Do not modify `/app/run_tests.sh`.

## Interface
`/app/answer.txt`: a single line containing the test id.
