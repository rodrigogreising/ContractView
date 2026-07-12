"""Fail when the production web boundary regresses into the former monolith."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps/web-app/src"
DIST = ROOT / "apps/web-app/dist"


def main() -> int:
    failures: list[str] = []
    app = (SRC / "App.tsx").read_text()
    for forbidden in ("fetch(", "contract-synthetic-agency-ngo-2026", "Demo-Config-2026!"):
        if forbidden in app:
            failures.append(f"App.tsx contains forbidden boundary literal: {forbidden}")
    fetch_owners = [
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.ts*")
        if ".test." not in path.name and "fetch(" in path.read_text()
    ]
    if fetch_owners != ["api/client.ts"]:
        failures.append(f"fetch must be owned only by api/client.ts, found {fetch_owners}")
    required = {
        "ConfigurationWorkspace.tsx", "NgoPreparerWorkspace.tsx",
        "NgoApproverWorkspace.tsx", "GovernmentWorkspace.tsx", "AuditorWorkspace.tsx",
    }
    existing = {path.name for path in SRC.rglob("*Workspace.tsx")}
    if missing := sorted(required - existing):
        failures.append(f"Missing role workspaces: {missing}")
    if not DIST.exists():
        failures.append("Production web dist is missing; run the build first")
    else:
        bundle = "\n".join(
            path.read_text(errors="ignore") for path in DIST.rglob("*") if path.is_file()
        )
        for forbidden in (
            "Demo-Config-2026!",
            "configuration.admin@example.test",
            "contract-synthetic-agency-ngo-2026",
        ):
            if forbidden in bundle:
                failures.append(f"Production bundle contains demo-only literal: {forbidden}")
    if failures:
        print("\n".join(failures))
        return 1
    print("Web boundary validation passed (transport, workspaces, context, demo bundle).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
