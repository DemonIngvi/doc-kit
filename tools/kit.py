#!/usr/bin/env python3
"""Создаёт проект документации и подключает к нему инструменты закреплённых версий.

  python kit.py init acme --dir D:/projects   создать acme-docs
  python kit.py sync --root acme-docs         обновить инструменты по doc.lock.yaml

Инструменты кладутся в .doc-kit/ и в git проекта не попадают.
"""
import argparse
import pathlib
import shutil
import subprocess

HERE = pathlib.Path(__file__).resolve().parent.parent
OWNER = "https://github.com/DemonIngvi"
TOOL_REPOS = ("doc-architecture", "doc-gates")
GITIGNORE = ".doc-kit/\n_bmad/\n.claude/skills/\nnode_modules/\n__pycache__/\n.env\n"


def run(*command, cwd=None):
    subprocess.run(list(command), cwd=cwd, check=True, shell=command[0] in ("npm", "npx"))


def configure_author(root):
    """Без автора git не сделает коммит. Личная почта в репозиторий не попадает: берётся адрес noreply."""
    has_author = subprocess.run(["git", "config", "user.email"], cwd=root, capture_output=True, text=True).stdout.strip()
    if has_author:
        return
    done = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True)
    if done.returncode:
        raise SystemExit("Задайте git config user.name и user.email или выполните gh auth login")
    login = done.stdout.strip()
    run("git", "config", "user.name", login, cwd=root)
    run("git", "config", "user.email", f"{login}@users.noreply.github.com", cwd=root)


def read_lock(path):
    """Файл версий простой: строки вида «имя: версия»."""
    return dict(line.split(": ", 1) for line in path.read_text(encoding="utf-8").splitlines() if ": " in line)


def fetch(repo, ref, root):
    target = root / ".doc-kit" / repo
    if target.exists():
        shutil.rmtree(target, onerror=lambda f, p, _: (pathlib.Path(p).chmod(0o700), f(p)))
    run("git", "clone", "-q", "--depth", "1", "--branch", ref, f"{OWNER}/{repo}.git", str(target))
    return target


def install_skills(root, repo_path):
    source = repo_path / "skills"
    if not source.exists():
        return
    for skill in source.iterdir():
        destination = root / ".claude" / "skills" / skill.name
        shutil.copytree(skill, destination, dirs_exist_ok=True)


def sync(root, language):
    lock = read_lock(root / "doc.lock.yaml")
    bmad = fetch("BMAD-METHOD", lock["BMAD-METHOD"], root)
    run("npm", "ci", "--silent", "--ignore-scripts", cwd=bmad)
    run("node", "tools/installer/bmad-cli.js", "install", "--directory", str(root), "--modules", "bmm",
        "--tools", "claude-code", "--communication-language", language, "--document-output-language", language,
        "--yes", cwd=bmad)
    for repo in TOOL_REPOS:
        install_skills(root, fetch(repo, lock[repo], root))


def init(args):
    root = (args.dir / f"{args.name}-docs").resolve()
    if root.exists():
        raise SystemExit(f"Уже существует: {root}")
    (root / "docs" / "architecture").mkdir(parents=True)
    (root / "_quality").mkdir()
    shutil.copy(HERE / "versions.yaml", root / "doc.lock.yaml")
    (root / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (root / "docs" / "terms-reject.txt").write_text("# запрещённый синоним (регулярное выражение) = термин Глоссария\n", encoding="utf-8")
    (root / "docmost.yaml").write_text(
        (HERE / "templates" / "docmost.yaml").read_text(encoding="utf-8").replace("{{name}}", args.name), encoding="utf-8")
    (root / "README.md").write_text(
        (HERE / "templates" / "README.md").read_text(encoding="utf-8").replace("{{name}}", args.name), encoding="utf-8")
    run("git", "init", "-q", "-b", "main", cwd=root)
    configure_author(root)
    sync(root, args.language)
    run("git", "add", "-A", cwd=root)
    run("git", "commit", "-q", "-m", f"Create {args.name} documentation project", cwd=root)
    if args.github:
        run("gh", "repo", "create", f"{args.name}-docs", "--private", "--source", ".", "--remote", "origin", "--push", cwd=root)
    print(f"Готово: {root}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("init")
    cmd.add_argument("name")
    cmd.add_argument("--dir", default=".", type=pathlib.Path)
    cmd.add_argument("--language", default="Russian")
    cmd.add_argument("--github", action="store_true", help="Создать приватный репозиторий на GitHub")
    cmd = sub.add_parser("sync")
    cmd.add_argument("--root", default=".", type=pathlib.Path)
    cmd.add_argument("--language", default="Russian")
    args = parser.parse_args()
    if args.command == "init":
        init(args)
    else:
        sync(args.root.resolve(), args.language)


if __name__ == "__main__":
    main()
