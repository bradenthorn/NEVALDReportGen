from pathlib import Path

from setuptools import find_packages, setup


def read_requirements() -> list[str]:
    """Return a list of requirements for ``install_requires``.

    Reading from ``requirements.txt`` keeps dependency declarations in a single
    place and avoids duplication between the project and its packaging
    configuration.
    """

    req_file = Path("requirements.txt")
    if not req_file.exists():
        return []
    return [
        line.strip()
        for line in req_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


setup(
    name="nevald-report-gen",
    version="0.1.0",
    packages=find_packages(include=["ReportScripts", "ReportScripts.*"]),
    py_modules=["config", "desktop_app"],
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires=">=3.8",
)


