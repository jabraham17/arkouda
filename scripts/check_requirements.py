#!/usr/bin/env python3
from pathlib import Path
import sys
from typing import Mapping, List


def parse_setup_py(root: Path) -> Mapping[str, List[str]]:
    """
    Parse the setup.py file to extract base and dev requirements.

    NOTE: this just looks for lines that start with "install_requires" or "extras_require"
    """
    requirements = {
        "base": [],
        "dev": [],
    }
    sys.path.insert(0, str(root))
    try:
        import setup
        requirements["base"] = setup.install_requires()
        requirements["dev"] = setup.extras_require().get("dev", [])
    except ImportError as e:
        print(f"Error importing setup.py: {e}")
        exit(1)
    finally:
        sys.path.pop(0)

    # remove ipython
    requirements["dev"] = [req for req in requirements["dev"] if not req.startswith("ipython")]

    return requirements

def parse_conda_yaml(path: Path) -> List[str]:
    """
    Parse the conda environment.yml file to extract base and dev requirements.
    """
    import yaml

    requirements = []
    with open(path, "r") as f:
        env = yaml.safe_load(f)
        if "dependencies" in env:
            for dep in env["dependencies"]:
                if isinstance(dep, str):
                    requirements.append(dep)
                elif isinstance(dep, dict) and "pip" in dep:
                    requirements.extend(dep["pip"])

    # convert pytables to tables
    requirements = [req.replace("pytables", "tables") for req in requirements]

    # remove jupyter
    requirements = [req for req in requirements if not req.startswith("jupyter")]

    return requirements


def check_requirements_match(setup_reqs, conda_reqs):
    setup_set = set(setup_reqs)
    conda_set = set(conda_reqs)

    only_in_setup = setup_set - conda_set
    only_in_conda = conda_set - setup_set

    if only_in_setup:
        print("Requirements only in setup.py:")
        for req in sorted(only_in_setup):
            print(f"  {req}")

    if only_in_conda:
        print("Requirements only in conda environment.yml:")
        for req in sorted(only_in_conda):
            print(f"  {req}")

    if not only_in_setup and not only_in_conda:
        print("Requirements match between setup.py and conda environment.yml")
        return True
    else:
        print("Requirements do not match.")
        return False

def main():
    root = Path(__file__).parent.parent
    requirements = parse_setup_py(root)
    user_requirements = requirements["base"]
    dev_requirements = requirements["base"] + requirements["dev"]

    conda_user_requirements = parse_conda_yaml(root / "arkouda-env.yml")

    conda_dev_requirements = parse_conda_yaml(root / "arkouda-env-dev.yml")

    print("Checking user requirements...")
    user_match = check_requirements_match(user_requirements, conda_user_requirements)
    print("\nChecking dev requirements...")
    dev_match = check_requirements_match(dev_requirements, conda_dev_requirements)
    if user_match and dev_match:
        print("\nAll requirements match.")
        sys.exit(0)
    else:
        print("\nSome requirements do not match.")
        sys.exit(1)



if __name__ == "__main__":
    main()
