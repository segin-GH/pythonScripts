import subprocess
import re
from collections import defaultdict


def get_commits_since_tag(tag=None):
    range_spec = f"{tag}..HEAD" if tag else "HEAD"
    result = subprocess.run(
        ["git", "log", "--pretty=format:%s", range_spec],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().split("\n")


def parse_conventional_commits(commits):
    sections = defaultdict(list)
    pattern = re.compile(r"^(?P<type>\w+)(\([\w\-]+\))?:\s*(?P<desc>.+)$")

    for commit in commits:
        match = pattern.match(commit)
        if match:
            type_ = match.group("type").lower()
            desc = match.group("desc")
            sections[type_].append(desc)
        else:
            sections["other"].append(commit)

    return sections


def format_changelog(sections):
    order = [
        "feat",
        "fix",
        "refactor",
        "chore",
        "test",
        "perf",
        "docs",
        "ci",
        "build",
        "other",
    ]
    result = []

    for section in order:
        if section in sections:
            result.append(f"### {section.capitalize()}")
            for item in sections[section]:
                result.append(f"- {item}")
            result.append("")  # blank line

    return "\n".join(result).strip()


def generate_changelog():
    try:
        last_tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        last_tag = None

    commits = get_commits_since_tag(last_tag)
    sections = parse_conventional_commits(commits)
    changelog = format_changelog(sections)

    return last_tag, changelog


last_tag, changelog = generate_changelog()
print(f"Generating changelog since: {last_tag or 'start'}\n")
print(changelog)

# # Then use it in the GitHub release step
# subprocess.run(
#     [
#         "gh",
#         "release",
#         "create",
#         f"v{new_version}",
#         "--title",
#         f"Release v{new_version}",
#         "--notes",
#         changelog,
#     ]
# )
