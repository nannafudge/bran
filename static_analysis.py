import io

import anybadge
import pytest
import coverage

from pylint import lint

if __name__ == "__main__":
    print("Running PyLint...")
    pylint_result = lint.Run(['pybran', '--output', 'pylint.json'], do_exit=False)
    print("Pylint Result:", pylint_result)

    print("Generating PyLint Badge")
    pylint_badge = anybadge.Badge('pylint', round(pylint_result.linter.stats['global_note'], 1), thresholds={
        2: 'red', 4: 'orange', 6: 'yellow', 8: 'green'
    })
    pylint_badge.write_badge('pylint.svg', overwrite=True)

    print("Running PyTest with Coverage")
    _coverage = coverage.Coverage()
    _coverage.start()

    ret = pytest.main(["tests", "--junit-xml", "pytest.xml"])

    _coverage.stop()

    print("Generating Coverage Badge")
    coverage_result = _coverage.report(file=io.StringIO())
    print("Coverage Result:", coverage_result)
    coverage_badge = anybadge.Badge('coverage', str(round(coverage_result)) + "%")
    coverage_badge.write_badge('coverage.svg', overwrite=True)

    print("Generating HTML Reports")
    _coverage.html_report()

    exit(ret)