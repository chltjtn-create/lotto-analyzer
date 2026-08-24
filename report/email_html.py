"""Build an HTML email body for the weekly Lotto report."""

from __future__ import annotations

from lotto_analyzer.analysis.evaluation import RecommendationEvaluation, RecommendationRecord
from lotto_analyzer.domain.models import LottoDraw

_INK = "#1c1a13"
_INK_MUTED = "#6f6b5c"
_BORDER = "#e3ddcf"
_ACCENT = "#2a5fb0"
_ACCENT_SOFT = "#eaf0fb"
_GOLD = "#a86a06"
_GOLD_SOFT = "#f6ead0"
_GOOD = "#2f7a3d"
_GOOD_SOFT = "#e7f3e8"
_MUTED_SOFT = "#f1efe6"


def build_weekly_email_html(
    latest_draw: LottoDraw,
    evaluations: list[RecommendationEvaluation],
    next_target_draw_no: int,
    next_recommendations: list[RecommendationRecord],
) -> str:
    """Render the weekly report as an inline-styled HTML email body."""
    draw_balls = "".join(_ball(number) for number in latest_draw.numbers)
    draw_balls += _plus() + _ball(latest_draw.bonus, bonus=True)

    if evaluations:
        eval_rows = "".join(_evaluation_row(item) for item in evaluations)
    else:
        eval_rows = _empty_row("아직 채점된 추천 조합이 없습니다.")

    if next_recommendations:
        next_rows = "".join(_recommendation_row(item) for item in next_recommendations)
    else:
        next_rows = _empty_row("생성된 추천 조합이 없습니다.")

    return f"""\
<html>
<body style="margin:0;padding:24px 12px;background:#f6f3ed;font-family:-apple-system,'Segoe UI','Malgun Gothic','맑은 고딕',sans-serif;color:{_INK};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid {_BORDER};border-radius:14px;overflow:hidden;">
    <tr>
      <td style="padding:28px 30px 20px;border-bottom:1px solid {_BORDER};">
        <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:{_ACCENT};font-weight:700;margin-bottom:8px;">로또 6/45 · 주간 리포트</div>
        <div style="font-size:20px;font-weight:700;margin-bottom:4px;">지난 회차 결과 확인</div>
        <div style="font-size:13px;color:{_INK_MUTED};">제 {latest_draw.draw_no}회 · {latest_draw.draw_date.isoformat()} 추첨</div>
      </td>
    </tr>
    <tr>
      <td style="padding:22px 30px;border-bottom:1px solid {_BORDER};">
        <div style="font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#a7a291;font-weight:700;margin-bottom:12px;">당첨 번호</div>
        {draw_balls}
      </td>
    </tr>
    <tr>
      <td style="padding:22px 30px;border-bottom:1px solid {_BORDER};">
        <div style="font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#a7a291;font-weight:700;margin-bottom:14px;">지난주 추천 조합 적중 확인</div>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{eval_rows}</table>
      </td>
    </tr>
    <tr>
      <td style="padding:14px 30px;background:{_ACCENT_SOFT};">
        <span style="font-weight:700;color:{_ACCENT};font-size:14px;">다음 회차 추천</span>
        <span style="font-size:12px;color:{_INK_MUTED};float:right;">제 {next_target_draw_no}회 · 발표 전</span>
      </td>
    </tr>
    <tr>
      <td style="padding:22px 30px;">
        <div style="font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#a7a291;font-weight:700;margin-bottom:14px;">{next_target_draw_no}회 추천 조합</div>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{next_rows}</table>
      </td>
    </tr>
    <tr>
      <td style="padding:20px 30px 26px;font-size:12px;line-height:1.6;color:{_INK_MUTED};">
        <strong style="color:{_INK};">본 결과는 통계 분석 기반 참고자료이며 당첨을 보장하지 않습니다.</strong><br>
        매주 월요일 오전 9시 자동 실행 · 엑셀 리포트와 CSV/JSON 백업이 첨부됩니다.
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _ball(number: int, bonus: bool = False) -> str:
    """Render one inline-styled lotto ball for an email body."""
    background = _GOLD_SOFT if bonus else _ACCENT_SOFT
    color = _GOLD if bonus else _ACCENT
    return (
        f'<span style="display:inline-block;width:30px;height:30px;line-height:30px;'
        f'text-align:center;border-radius:50%;background:{background};color:{color};'
        f'font-weight:700;font-size:13px;margin-right:6px;">{number}</span>'
    )


def _plus() -> str:
    """Render the separator between winning numbers and the bonus ball."""
    return f'<span style="color:{_INK_MUTED};font-size:14px;margin-right:6px;">+</span>'


def _evaluation_row(evaluation: RecommendationEvaluation) -> str:
    """Render one row showing a past recommendation's matched numbers and result."""
    matched = set(evaluation.matched_numbers)
    balls = "".join(
        _ball_result(number, hit=number in matched) for number in evaluation.recommended_numbers
    )
    is_win = evaluation.result_label != "미당첨"
    tag_bg = _GOOD_SOFT if is_win else _MUTED_SOFT
    tag_color = _GOOD if is_win else _INK_MUTED
    bonus_note = (
        f'<span style="font-size:11px;color:{_GOLD};font-weight:700;margin-left:8px;">보너스 일치</span>'
        if evaluation.bonus_matched
        else ""
    )
    return f"""
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid {_BORDER};">
        <div style="margin-bottom:6px;">{balls}</div>
        <span style="display:inline-block;font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;background:{tag_bg};color:{tag_color};">
          {evaluation.match_count}개 일치 · {evaluation.result_label}
        </span>{bonus_note}
      </td>
    </tr>
    """


def _recommendation_row(record: RecommendationRecord) -> str:
    """Render one row for a newly generated recommendation."""
    combo = record.combination
    balls = "".join(_ball(number) for number in combo.numbers)
    return f"""
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid {_BORDER};">
        <div style="margin-bottom:6px;">{balls}</div>
        <span style="font-size:11px;color:{_INK_MUTED};">
          점수 {combo.score:.2f} · 홀짝 {combo.odd_even} · 고저 {combo.high_low} · 합 {combo.total_sum}
        </span>
      </td>
    </tr>
    """


def _empty_row(message: str) -> str:
    """Render a placeholder row for a section that has nothing to show.

    This fires whenever the latest draw has no recommendations of its own - which
    happens after a catch-up run stores two draws at once, so the middle draw was
    never the "next" draw at the time recommendations were generated.
    """
    return f"""
    <tr>
      <td style="padding:14px 0;border-bottom:1px solid {_BORDER};text-align:center;">
        <span style="font-size:12px;color:{_INK_MUTED};">{message}</span>
      </td>
    </tr>
    """


def _ball_result(number: int, hit: bool) -> str:
    """Render one ball highlighted green when it matched the actual draw."""
    if hit:
        style = (
            f"background:{_GOOD_SOFT};color:{_GOOD};box-shadow:inset 0 0 0 1.5px {_GOOD};"
        )
    else:
        style = f"background:{_MUTED_SOFT};color:{_INK_MUTED};opacity:.55;"
    return (
        f'<span style="display:inline-block;width:28px;height:28px;line-height:28px;'
        f'text-align:center;border-radius:50%;font-weight:700;font-size:12px;'
        f'margin-right:5px;{style}">{number}</span>'
    )
