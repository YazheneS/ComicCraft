"""Match every generated image with its outline data and story text -> one layout list."""
import re

_PANEL_SPLIT = re.compile(r"(?im)^\s*\**\s*panel\s+(\d+)\s*[:\-.]?\s*(.*)$")


def parse_story(story_text: str) -> dict[int, dict]:
    """Split the Gemini Pro text into {panel_number: {title, caption, narration, text}}."""
    matches = list(_PANEL_SPLIT.finditer(story_text))
    parsed: dict[int, dict] = {}
    for idx, m in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(story_text)
        body = story_text[m.end():end].strip()
        caption = re.search(r"(?im)^\s*\**caption\**\s*:\s*(.+?)(?=^\s*\**narration\**\s*:|\Z)", body, re.S | re.M)
        narration = re.search(r"(?im)^\s*\**narration\**\s*:\s*(.+)", body, re.S | re.M)
        cap = caption.group(1).strip() if caption else ""
        nar = narration.group(1).strip() if narration else (body if not caption else "")
        parsed[int(m.group(1))] = {
            "title": m.group(2).strip(" *"),
            "caption": cap.replace("*", ""),
            "narration": nar.replace("*", ""),
            "text": body.replace("*", ""),
        }
    return parsed


def build_comic_layout(outline: list[dict], story_text: str, image_paths: list[str]) -> list[dict]:
    """Return [{panel_number, title, image_path, text, caption, narration, scene_description, image_prompt}, ...]."""
    story = parse_story(story_text)
    layout = []
    for i, panel in enumerate(outline):
        n = panel["panel_number"]
        info = story.get(n, {})
        narration = info.get("narration") or panel["scene_description"]  # graceful fallback
        layout.append(
            {
                "panel_number": n,
                "title": panel["title"],
                "image_path": image_paths[i] if i < len(image_paths) else "",
                "text": info.get("text") or narration,
                "caption": info.get("caption", ""),
                "narration": narration,
                "scene_description": panel["scene_description"],
                "image_prompt": panel["image_prompt"],
            }
        )
    return layout
