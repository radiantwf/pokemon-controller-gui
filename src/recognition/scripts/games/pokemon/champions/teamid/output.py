"""Android-compatible rental-code parsing and result logs, with cancellable uploads."""
from datetime import datetime
from pathlib import Path
import time
import urllib.parse
import urllib.request

from recognition.scripts.games.pokemon.champions.teamid.team import Team

DEFAULT_RETRY_INTERVAL_SECONDS = 3


def _normalize_rental_codes(rental_codes):
    if isinstance(rental_codes, str):
        return [code.strip() for code in rental_codes.replace(",", "\n").splitlines() if code.strip()]
    return [str(code).strip() for code in rental_codes if str(code).strip()]


def _safe_code_for_path(rental_code: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in rental_code)


def _new_log_path(rental_codes):
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if len(rental_codes) == 1:
        filename = f"teamid_{timestamp}_{_safe_code_for_path(rental_codes[0])}.log"
    else:
        filename = f"teamid_{timestamp}_batch.log"
    return output_dir / filename


def _format_log_section(rental_code: str, team: Team | None, pokepaste_url: str | None, error: str | None = None):
    lines = [
        "=" * 60,
        f"租借码: {rental_code}",
        f"Pokepaste URL: \n{pokepaste_url or ''}",
        "OCR识别为空日志:",
    ]
    if team is None:
        lines.append("未生成队伍，无法读取错误日志")
    else:
        lines.extend(team.ocr_errors if team.ocr_errors else ["无"])

    lines.extend([
        "中英文转换错误日志:",
    ])
    if team is None:
        lines.append("未生成队伍，无法读取错误日志")
    else:
        lines.extend(team.conversion_errors if team.conversion_errors else ["无"])

    lines.extend([
        "努力值66检查错误日志:",
    ])
    if team is None:
        lines.append("未生成队伍，无法读取错误日志")
    else:
        lines.extend(team.ev_errors if team.ev_errors else ["无"])

    if error:
        lines.extend([
            "处理错误:",
            error,
        ])
    lines.append("")
    return "\n".join(lines)


def append_process_log(log_path, rental_code, team, pokepaste_url, error=None):
    section = _format_log_section(rental_code, team, pokepaste_url, error=error)
    with log_path.open("a", encoding="utf-8") as file:
        file.write(section)
        file.write("\n")
    return section


def create_pokepaste_until_success(
    paste_text, title, author="OCR",
    pokepaste_retry_interval_seconds=DEFAULT_RETRY_INTERVAL_SECONDS,
    stop_event=None, should_stop=None, send_log=print,
):
    def check_stopped():
        if (stop_event is not None and stop_event.is_set()) or (should_stop and should_stop()):
            raise InterruptedError

    while True:
        check_stopped()
        try:
            data = urllib.parse.urlencode({
                "paste": paste_text,
                "title": title,
                "author": author,
            }).encode("utf-8")
            req = urllib.request.Request("https://pokepast.es/create", data=data)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.url and resp.url.rstrip("/") != "https://pokepast.es/create":
                    return resp.url
                send_log(f"生成 Pokepaste 失败: 响应 URL 无效 ({resp.url})，准备重试")
        except InterruptedError:
            raise
        except Exception as error:
            send_log(f"生成 Pokepaste 失败: {error}，{pokepaste_retry_interval_seconds} 秒后重试")

        # Check the GUI stop flag and duration limit during the retry delay.
        deadline = time.monotonic() + pokepaste_retry_interval_seconds
        while True:
            check_stopped()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if stop_event is not None:
                stop_event.wait(min(remaining, 0.1))
            else:
                time.sleep(min(remaining, 0.1))
