"""Portable developer targets: invoke test, build, check, publish."""

from pathlib import Path
import subprocess
import sys
from invoke import task

ROOT = Path(__file__).resolve().parent


def run(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


@task
def test(context):
    """Run synthetic and API regression tests."""
    run("-m", "pytest", "-q")


@task
def build(context, no_isolation=False):
    """Build an sdist and wheel (add --no-isolation for a prepared offline environment)."""
    args = ["-m", "build"]
    if no_isolation:
        args.append("--no-isolation")
    run(*args)


@task
def check(context):
    """Check distributions already built in dist/."""
    artifacts = sorted((ROOT / "dist").glob("*.whl")) + sorted(
        (ROOT / "dist").glob("*.tar.gz")
    )
    if not artifacts:
        raise RuntimeError("Run invoke build first")
    run("-m", "twine", "check", *[str(p) for p in artifacts])


@task
def publish(context, repository="testpypi"):
    """Explicit opt-in upload; defaults to TestPyPI. Requires configured credentials."""
    if repository not in ("testpypi", "pypi"):
        raise ValueError("repository must be testpypi or pypi")
    check(context)
    artifacts = sorted((ROOT / "dist").glob("*.whl")) + sorted(
        (ROOT / "dist").glob("*.tar.gz")
    )
    run(
        "-m",
        "twine",
        "upload",
        "--non-interactive",
        "--repository",
        repository,
        *[str(p) for p in artifacts],
    )
