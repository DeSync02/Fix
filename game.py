"""Fix the Building: a tiny GitHub-profile game.

Visitors click a broken window (💥) -> opens a prefilled issue -> a GitHub
Action fixes that window. Every few hours a villain smashes more windows.
"""
import json
import os
import random
import re

STATE = "game/state.json"
README = "README.md"
ROWS, COLS = 4, 5
SMASHES_PER_RUN = 2
REPO = os.environ["GITHUB_REPOSITORY"]


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    # 1 = broken, 0 = fixed
    grid = [[1 if random.random() < 0.5 else 0 for _ in range(COLS)] for _ in range(ROWS)]
    return {"grid": grid, "fixes": 0, "smashes": 0}


def save(state):
    with open(STATE, "w") as f:
        json.dump(state, f)


def fix(state, title):
    m = re.fullmatch(r"fix-(\d+)-(\d+)", title.strip())
    if not m:
        return
    r, c = int(m.group(1)), int(m.group(2))
    if 0 <= r < ROWS and 0 <= c < COLS and state["grid"][r][c] == 1:
        state["grid"][r][c] = 0
        state["fixes"] += 1


def smash(state):
    fixed = [(r, c) for r in range(ROWS) for c in range(COLS) if state["grid"][r][c] == 0]
    random.shuffle(fixed)
    for r, c in fixed[:SMASHES_PER_RUN]:
        state["grid"][r][c] = 1
        state["smashes"] += 1


def render(state):
    broken = sum(sum(row) for row in state["grid"])
    lines = ["| | | | | |", "|:-:|:-:|:-:|:-:|:-:|"]
    for r in range(ROWS):
        cells = []
        for c in range(COLS):
            if state["grid"][r][c]:
                url = (
                    f"https://github.com/{REPO}/issues/new"
                    f"?title=fix-{r}-{c}&body=Just+press+%22Submit+new+issue%22+to+fix+this+window"
                )
                cells.append(f"[💥]({url})")
            else:
                cells.append("🟨")
        lines.append("| " + " | ".join(cells) + " |")
    table = "\n".join(lines)

    if broken == 0:
        status = "🎉 **The building is fully restored!** Wait for Smasher to strike again..."
    else:
        status = f"👷 **Handy** needs your help! **{broken}** broken window(s) left. Click a 💥 to fix it."

    return (
        f"{table}\n\n{status}\n\n"
        f"🔧 Windows fixed: **{state['fixes']}** &nbsp;|&nbsp; 👹 Windows smashed: **{state['smashes']}**\n"
    )


def update_readme(block):
    with open(README, encoding="utf-8") as f:
        content = f.read()
    new = re.sub(
        r"(<!-- GAME:START -->).*?(<!-- GAME:END -->)",
        lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}",
        content,
        flags=re.DOTALL,
    )
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)


def main():
    state = load()
    event = os.environ.get("EVENT_NAME", "")
    if event == "issues":
        fix(state, os.environ.get("ISSUE_TITLE", ""))
    else:
        smash(state)
    save(state)
    update_readme(render(state))


if __name__ == "__main__":
    main()
