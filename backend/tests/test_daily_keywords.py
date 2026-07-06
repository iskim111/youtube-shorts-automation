"""일일 인기 검색어 파싱 테스트."""

from app.services.daily_keywords_service import (
    _expand_to_target,
    _parse_google_rss,
    _parse_signal_realtime,
)


def test_parse_google_rss():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0">
      <channel>
        <item>
          <title>테스트 키워드</title>
          <ht:approx_traffic>10만+</ht:approx_traffic>
        </item>
      </channel>
    </rss>"""
    rows = _parse_google_rss(xml)
    assert len(rows) == 1
    assert rows[0]["keyword"] == "테스트 키워드"


def test_parse_signal_realtime_list_format():
    payload = {"top10": [{"rank": 1, "keyword": "네이버검색어", "state": "s"}]}
    naver = _parse_signal_realtime(payload)
    assert len(naver) == 1
    assert naver[0]["keyword"] == "네이버검색어"


def test_expand_to_target():
    seeds = [{"keyword": "비", "source": "google", "traffic": "100+"}]
    extras = ["비 오는 날", "비트코인", "비", "부산 날씨"]
    rows = _expand_to_target(seeds, extras, source="google", target=5)
    assert len(rows) == 4
    assert rows[0]["keyword"] == "비"
